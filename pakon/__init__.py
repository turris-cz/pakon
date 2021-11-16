import os
from pathlib import Path

__version__ = '1.2.2'

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if os.environ.get("FLASK_ENV") in ("testing", "development"):
    ROOT_PATH = PROJECT_ROOT / "tests" / "root"
else:
    ROOT_PATH = Path("/")
