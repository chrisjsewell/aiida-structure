import tempfile
import shutil
import pytest

try:
    from aiida.manage.fixtures import fixture_manager
except ImportError:
    from aiida.utils.fixtures import fixture_manager


@pytest.fixture(scope='session')
def aiida_profile():
    """setup a test profile for the duration of the tests"""
    with fixture_manager() as fixture_mgr:
        yield fixture_mgr


@pytest.fixture(scope='function')
def new_database(aiida_profile):
    """Get a the database for the test and clean it up after it finishes"""
    aiida_profile.reset_db()
    return


@pytest.fixture(scope='function')
def new_workdir():
    """get a new temporary folder to use as the computer's wrkdir"""
    dirpath = tempfile.mkdtemp()
    yield dirpath
    shutil.rmtree(dirpath)
