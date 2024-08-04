import pytest
from jsoner import Database
from jsoner.database import __version__

db = Database('data.json')

def drop_db():
    global db
    db.drop()

drop_db()

@pytest.fixture
def clear_db():
    drop_db()

@pytest.fixture(scope='package', autouse=True)
def package_fixture():
    drop_db()