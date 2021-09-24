import os
import pytest
from pakon_api import create_app
# import tempfile


def pytest_configure():
    pytest.api_url = '/pakon/api/query/'
    pytest.pakon_url = '/pakon/'


@pytest.fixture(scope='function')
def app():
    #  db_fd, db_path = tempfile.mkstemp()
    #  app = create_app({"TESTING": True, "DATABASE": db_path})
    app = create_app()
    with app.app_context():
        yield app

    # os.close(db_fd)
    # os.unlink(db_path)


@pytest.fixture(scope='function')
def client(app):
    """ Fixture to wrap flask client. Provides test function access to api and
wraps client in correct app_context. """
    with app.test_client() as client:
        yield client
