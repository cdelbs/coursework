# Root conftest.py
import os
import sys
from pathlib import Path
import pytest

# Make sure tests can import Fish modules (Common, Admin, Player, etc.)
ROOT = Path(__file__).resolve().parent
FISH_DIR = ROOT / "Fish"
if str(FISH_DIR) not in sys.path:
    sys.path.insert(0, str(FISH_DIR))

# Run Qt headless when GUI tests are enabled
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

def pytest_addoption(parser):
    parser.addoption("--gui", action="store_true", help="run GUI tests")

# File name keywords that indicate a GUI test
GUI_KEYWORDS = (
    "drawboard",
    "qt",
    "pyqt",
    "paint",
    "fullscreen",
    "keypress",
    "primitives",
)

def pytest_ignore_collect(collection_path: Path, config) -> bool:
    """
    Completely skip collecting GUI test files unless --gui is set.
    This prevents import time errors for PyQt5 on headless servers.
    """
    if config.getoption("--gui"):
        return False
    nid = str(collection_path).lower()
    return any(k in nid for k in GUI_KEYWORDS)

def pytest_collection_modifyitems(config, items):
    """
    If not running with --gui, mark GUI-like tests skipped.
    """
    if not config.getoption("--gui"):
        skip_gui = pytest.mark.skip(
            reason="GUI tests skipped by default. Use --gui to run them."
        )
        for item in items:
            nid = item.nodeid.lower()
            if any(k in nid for k in GUI_KEYWORDS) or item.get_closest_marker("gui"):
                item.add_marker(skip_gui)

@pytest.fixture(scope="session")
def qapp(request):
    """
    A single QApplication for GUI tests.
    Only created when --gui is set.
    """
    if not request.config.getoption("--gui"):
        pytest.skip("GUI tests skipped by default. Use --gui to run them.")
    from PyQt5.QtWidgets import QApplication  # lazy import
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app
