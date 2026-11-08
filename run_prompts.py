#!/usr/bin/env python3
"""Sequential Codex task runner. Standard library only; see RUNNER_README.md."""
import argparse
import array
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import wave


CONTRACT = '''
Execute ONLY the numbered stage below. Give it the full implementation and
verification effort you would give a separately pasted user prompt. Do not
advance to another stage. Maintain PROJECT_STATUS.md. Never claim unrun checks
passed. Preserve previous work and locked evaluation splits on retries.
Before acting, read PROJECT_STATUS.md from disk, including its latest user-supplied
verification evidence; resumed session history may be stale. Reconcile conflicting
status entries against that evidence. A user-supplied browser screenshot confirms
only the behavior it visibly demonstrates. Do not repeat a sandbox socket preflight
or request an external launch already demonstrated by that evidence. If interaction
checks remain unconfirmed, request those specific observations rather than another
server launch. Never infer unobserved checks passed or skip a required stage audit.
If blocked, explain the precise action the user must take.
Your final response MUST be a JSON object, without Markdown fences:
{"status":"complete|incomplete|blocked", "summary":"...",
 "evidence":["actual file paths and commands/results"], "needs_user":""}
Use complete only when every requirement is satisfied or an omission is
explicitly allowed by the original prompt and justified by evidence.
'''


def extract(source):
    """Return the master instructions and a Python list of numbered prompts."""
    master = None
    prompts = []
    for section in re.split(r'^## ', source, flags=re.M):
        numbered = re.match(r'Prompt (\d+)\b', section)
        if not numbered and not section.startswith('Master instructions'):
            continue
        blocks = re.findall(r'^```text[^\n]*\n(.*?)^```\s*$', section, re.M | re.S)
        if len(blocks) != 1:
            raise ValueError('Expected one text block in ' + section.splitlines()[0])
        if numbered:
            prompts.append({'number': int(numbered[1]),
                            'title': section.splitlines()[0], 'prompt': blocks[0]})
        else:
            master = blocks[0]
    prompts.sort(key=lambda p: p['number'])
    numbers = [p['number'] for p in prompts]
    if not master or not numbers or numbers != list(range(1, len(numbers) + 1)):
        raise ValueError('Missing master instructions or nonconsecutive/duplicate prompts')
    return master, prompts


def save(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def make_sound(path):
    samples = array.array('h')
    rate = 22050
    for frequency in (880, 0, 660, 0, 880):
        for i in range(rate // 4):
            samples.append(int(14000 * math.sin(2 * math.pi * frequency * i / rate)))
    if sys.byteorder != 'little':
        samples.byteswap()
    with wave.open(str(path), 'wb') as output:
        output.setparams((1, 2, rate, 0, 'NONE', 'not compressed'))
        output.writeframes(samples.tobytes())


def ring(path):
    for executable, options in [('paplay', []), ('aplay', ['-q']),
                                ('ffplay', ['-nodisp', '-autoexit', '-loglevel', 'quiet']),
                                ('afplay', [])]:
        if shutil.which(executable):
            try:
                result = subprocess.run([executable, *options, str(path)],
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL, timeout=8)
                if result.returncode == 0:
                    return
            except (OSError, subprocess.TimeoutExpired):
                pass
    print('\a\a\a', end='', flush=True)


def attention(message, directory, interval):
    print('\nATTENTION REQUIRED: ' + message, flush=True)
    save(directory / 'attention.json', {'message': message, 'time': time.time()})
    sound = directory / 'alert.wav'
    make_sound(sound)
    if shutil.which('notify-send'):
        subprocess.Popen(['notify-send', 'Codex runner needs you', message],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    stop = threading.Event()

    def alarm():
        while not stop.is_set():
            ring(sound)
            if stop.wait(interval):
                break

    thread = threading.Thread(target=alarm, daemon=True)
    thread.start()
    try:
        if sys.stdin.isatty():
            input('\nPress Enter to acknowledge. Then fix the issue and rerun the command. ')
        else:
            time.sleep(3)
    finally:
        stop.set()
        thread.join(timeout=9)


def report(text):
    text = text.strip()
    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text)
    result = json.loads(text)
    if (result.get('status') not in ('complete', 'incomplete', 'blocked')
            or not isinstance(result.get('summary'), str)
            or not isinstance(result.get('evidence'), list)
            or not isinstance(result.get('needs_user'), str)):
        raise ValueError('Invalid completion report')
    if result['status'] == 'complete' and (not result['evidence'] or result['needs_user']):
        raise ValueError('Completion requires evidence and no unresolved user action')
    return result


def run_turn(args, state, directory, state_path, prompt, label):
    state['turn'] = state.get('turn', 0) + 1
    save(state_path, state)
    prefix = directory / f"{state['turn']:04d}-{label}"
    prefix.with_suffix('.prompt.txt').write_text(prompt)
    command = [args.codex, '-a', 'never', '-s', 'workspace-write']
    if args.model:
        command += ['-m', args.model]
    if args.reasoning:
        command += ['-c', 'model_reasoning_effort=' + json.dumps(args.reasoning)]
    command += ['exec']
    if state.get('session_id'):
        command += ['resume', state['session_id']]
    command += ['--json', '--skip-git-repo-check', '-']
    final = ''
    completed = False
    failed = False
    print(f"\nStarting {label}; logs: {prefix}", flush=True)
    with prefix.with_suffix('.stderr.log').open('w') as errors, \
            prefix.with_suffix('.jsonl').open('w') as events:
        process = subprocess.Popen(command, cwd=args.source.parent, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=errors, text=True,
                                   start_new_session=True)
        try:
            process.stdin.write(prompt)
            process.stdin.close()
            for line in process.stdout:
                events.write(line)
                events.flush()
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                kind = event.get('type')
                if kind == 'thread.started':
                    state['session_id'] = event['thread_id']
                    save(state_path, state)
                elif kind == 'turn.completed':
                    completed = True
                elif kind in ('turn.failed', 'error'):
                    print(line.strip(), flush=True)
                    if kind == 'turn.failed':
                        failed = True
                elif kind == 'item.completed':
                    item = event.get('item', {})
                    if item.get('type') == 'agent_message':
                        final = item.get('text', '')
                        print(final, flush=True)
            code = process.wait()
        except BaseException:
            try:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=10)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
            raise
        finally:
            process.stdout.close()
            if not process.stdin.closed:
                process.stdin.close()
    if code or failed or not completed or not state.get('session_id'):
        raise RuntimeError(f'{label} failed (exit {code}); see {prefix}.stderr.log and .jsonl')
    prefix.with_suffix('.final.txt').write_text(final)
    return report(final)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path(__file__).with_name('Build_Project_Prompts.md'))
    parser.add_argument('--codex', default='codex', help='CLI executable or path')
    parser.add_argument('--model', help='Use the same model as your manual sessions')
    parser.add_argument('--reasoning', help='Reasoning effort supported by your selected model')
    parser.add_argument('--repairs', type=int, default=2, help='Correction turns per stage')
    parser.add_argument('--alert-interval', type=float, default=15)
    parser.add_argument('--dry-run', action='store_true', help='List stages without running Codex')
    parser.add_argument('--test-sound', action='store_true')
    args = parser.parse_args()
    args.source = args.source.resolve()
    if args.repairs < 0 or args.alert_interval < 1:
        parser.error('repairs must be nonnegative and alert-interval at least 1')
    master, prompts = extract(args.source.read_text())
    if args.dry_run:
        for stage in prompts:
            print(f"{stage['title']} ({len(stage['prompt'])} characters)")
        print('Master instructions loaded; recovery and optional prompts excluded. No tasks run.')
        return 0
    directory = args.source.parent / '.prompt-runner'
    directory.mkdir(exist_ok=True)
    # Hold a process lock so two runners cannot modify the same session/state.
    with (directory / 'runner.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error('Another runner is already active for this project')
        if args.test_sound:
            make_sound(directory / 'alert.wav')
            ring(directory / 'alert.wav')
            print('Sound test sent. If inaudible, check volume and audio output.')
            return 0
        try:
            if not shutil.which(args.codex):
                raise RuntimeError('Codex CLI not found. Install it, run codex login, then rerun.')
            fingerprint = hashlib.sha256(args.source.read_bytes()).hexdigest()
            state_path = directory / 'state.json'
            settings = {'model': args.model, 'reasoning': args.reasoning}
            if state_path.exists():
                state = json.loads(state_path.read_text())
                if state['source_hash'] != fingerprint or state['settings'] != settings:
                    raise RuntimeError('Prompt file or model settings changed. Restore the original '
                                       'settings/file before resuming; state was preserved.')
            else:
                state = {'source_hash': fingerprint, 'settings': settings,
                         'stage': 1, 'session_id': None, 'turn': 0}
                save(state_path, state)
            for stage in prompts:
                number = stage['number']
                if number < state['stage']:
                    continue
                prompt = master + '\n\n' + CONTRACT + '\n\n' + stage['prompt']
                for attempt in range(args.repairs + 1):
                    result = run_turn(args, state, directory, state_path, prompt,
                                      f'stage-{number}-implement-{attempt}')
                    if result['status'] == 'blocked':
                        raise RuntimeError(result['needs_user'] or result['summary'])
                    if result['status'] == 'complete':
                        review = (master + '\n\n' + CONTRACT + '\n\nAudit ONLY this stage. '
                                  'Inspect the actual outputs and verify its completion check. '
                                  'Do not modify project files or run later stages. Do not retrain, '
                                  'retune, or rerun reserved final evaluation. Use saved evidence '
                                  'where repetition would invalidate the research protocol. '
                                  'Return incomplete with concrete corrections if anything required '
                                  'is missing. Return blocked if user action is necessary.\n\n'
                                  + stage['prompt'])
                        result = run_turn(args, state, directory, state_path, review,
                                          f'stage-{number}-audit-{attempt}')
                    if result['status'] == 'blocked':
                        raise RuntimeError(result['needs_user'] or result['summary'])
                    if result['status'] == 'complete':
                        state['stage'] = number + 1
                        save(state_path, state)
                        print(f'Stage {number} accepted after audit.', flush=True)
                        break
                    prompt = (master + '\n\n' + CONTRACT + '\n\n' + stage['prompt']
                              + '\n\nContinue from existing work and correct these findings:\n'
                              + json.dumps(result))
                else:
                    raise RuntimeError(f'Stage {number} still incomplete after correction turns: '
                                       + result['summary'])
            print('\nAll numbered stages passed the Codex completion audit. See PROJECT_STATUS.md.')
            return 0
        except KeyboardInterrupt:
            print('\nStopped. Progress preserved; rerun the same command to continue.')
            return 130
        except (OSError, ValueError, RuntimeError) as error:
            attention(str(error), directory, args.alert_interval)
            return 1


if __name__ == '__main__':
    sys.exit(main())
