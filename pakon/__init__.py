from pathlib import Path

__version__ = "1.2.2"


class Config:
    """Global variables to be patched for testing purposes"""

    ROOT_PATH = Path("/")
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
