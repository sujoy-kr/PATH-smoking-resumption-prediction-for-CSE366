# Sequential prompt runner

`run_prompts.py` uses Python's standard library and the installed Codex CLI.
It reads the master instructions and numbered text blocks directly from
`Build_Project_Prompts.md` into a Python list. The Markdown stays the source of
truth; recovery and optional PowerPoint prompts are excluded.

## Setup and use

Install Codex CLI and authenticate with `codex login` first. The current workspace
shell did not have `codex` installed when this runner was created.
Official instructions: https://learn.chatgpt.com/docs/non-interactive-mode

From this directory:

```bash
python3 run_prompts.py --dry-run
python3 run_prompts.py --test-sound
python3 run_prompts.py
```

To match a manual session's model and effort, explicitly supply its exact values:

```bash
python3 run_prompts.py --model YOUR_MODEL_ID --reasoning YOUR_EFFORT
```

Without these options the CLI's configured defaults apply. The runner does not
inherit the model/settings of this chat. Keep the same options when restarting.
Use `--codex /absolute/path/to/codex` if the CLI is outside your PATH.

## Behavior

- Each numbered stage receives its full original text and master instructions.
- All turns resume the runner's explicit session ID, never another recent chat.
- A separate Codex audit turn checks actual outputs before advancing. This is
  model-based verification, not a guarantee or an independent human review.
- Incomplete work gets up to two correction turns (`--repairs N`). Blockers,
  exhausted corrections, CLI errors, or malformed final reports stop progression.
- The runner never requests interactive CLI approvals: it uses `workspace-write`
  and approval policy `never`. Required operations denied by those permissions
  must be reported as blockers; fix them outside the runner before retrying.
- There is no task timeout: slow training is allowed to finish. A hung process
  that never exits or reports a blocker will need Ctrl+C; silence alone is not
  treated as failure. Keep the computer awake and terminal running while AFK.
- Ctrl+C terminates the active CLI process group and preserves stage progress.
  Rerun the same command to retry the current unaccepted stage in the same session.
  Prompts instruct Codex to inspect existing outputs before repeating work.
- Changing the source file or model settings after starting stops resumption
  rather than silently mixing workflows. Do not delete state just to retry.

## Audible alerts

Test the sound before leaving. A generated WAV plays through `paplay`, `aplay`,
`ffplay`, or `afplay`, falling back to the terminal bell. Volume, mute settings,
remote terminals, and audio devices can prevent audible playback.

When blocked, the runner prints the reason, saves `attention.json`, and sends a
desktop notification if `notify-send` exists. With a terminal attached, the sound
repeats every 15 seconds until Enter is pressed (`--alert-interval SECONDS`).
Acknowledging exits the runner: resolve the issue, then rerun the same command.
Without interactive stdin, it emits one alert and exits with status 1.

## State and logs

`.prompt-runner/` contains atomic progress state, the session ID, each submitted
prompt, streamed JSON events, stderr, final reports, and the alert WAV. These logs
can contain local data; keep this directory out of version control. A filesystem
lock prevents concurrent runners for the same source directory.

Successful process exit alone never advances a stage. The implementation and
audit must both return valid completion reports with evidence. This preserves
the intended workload but cannot guarantee identical quality to manual review.
