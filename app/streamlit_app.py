"""Single-model local application entry point."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name('longitudinal_app.py')), run_name='__main__')
