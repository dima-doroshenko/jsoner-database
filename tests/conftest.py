import pytest
from jsoner import Database
from jsoner.database import __version__

db = Database('data.json')

def drop_db():
    global db
    db.data = {}
    db.data[db.settings] = {'__version__': __version__, 
                                        'default': None,
                                        'tags': {}, 
                                        'global_tags': {}}
    db.commit()

drop_db()

@pytest.fixture
def clear_db():
    drop_db()  

@pytest.fixture(scope='package', autouse=True)
def package_fixture():
    drop_db()