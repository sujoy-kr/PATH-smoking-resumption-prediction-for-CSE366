"""Verify the included model, then start Streamlit with this Python interpreter."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def main():
    check = subprocess.run([sys.executable, str(ROOT/'scripts/verify_runtime.py')], cwd=ROOT)
    if check.returncode:
        return check.returncode
    return subprocess.call([sys.executable, '-m', 'streamlit', 'run',
        str(ROOT/'app/streamlit_app.py'), *sys.argv[1:]], cwd=ROOT)


if __name__ == '__main__':
    raise SystemExit(main())
