import json
import pytest

from unittest.mock import Mock, patch
from pathlib import Path
import pakon
from pakon_api import create_app
from pakon import Config

from pathlib import Path
# import tempfile


def _get_result():
    """Gets raw string"""
    with open("tests/test_result.json", "r") as f:
        return json.load(f)


def pytest_configure():
    pytest.api_url = "/pakon/api/query/"
    pytest.pakon_url = "/pakon/"


@pytest.fixture(autouse=True)
def mock_root_path(monkeypatch):
    # def mockreturn():
    #     return Path(, "")
    with monkeypatch.context() as m:
        m.setattr(pakon.Config, "ROOT_PATH", Config.PROJECT_ROOT / "tests" / "root")
        yield


@pytest.fixture(scope="function")
def mock_socket():
    """pakon-socket mock, query not supported"""
    mock = Mock()
    mock.return_value = (json.dumps(_get_result()), "")

    with patch("pakon_api.backend.pakon_socket", mock) as m_sock:
        yield m_sock


@pytest.fixture(scope="function")
def app():
    """Basic app fixture"""
    #  db_fd, db_path = tempfile.mkstemp()
    #  app = create_app({"TESTING": True, "DATABASE": db_path})
    app = create_app({"TESTING": True})
    with app.app_context():
        yield app

    # os.close(db_fd)
    # os.unlink(db_path)


@pytest.fixture(scope="function")

def client(app):
    """Fixture to wrap flask client. Provides test function access to api and
    wraps client in correct app_context."""
    with app.test_client() as client:
        yield client
