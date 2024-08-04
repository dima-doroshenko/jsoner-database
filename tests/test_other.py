from tests.conftest import db
import pytest
from jsoner import errors, tags
from tests.conftest import clear_db, drop_db

@pytest.fixture
def create_items():
    global items
    items = (
            ('key_1', 1,),
            ('key_2', 2,),
            ('key_3', 3),
        )
    [db.add(*item) for item in items]

def test_keys(create_items):
    assert db.keys() == list(map(lambda x: x[0], items))

def test_values():
    assert db.values() == list(map(lambda x: x[1], items))

def test_items():
    assert db.items() == list(items)

def test_getitem():
    assert db['key_1'] == 1

def test_setitem():
    db['key_1'] = 2
    assert db['key_1'] == 2
    db['key_1'] = 1

def test_with(clear_db):
    db.add('key_1', 1)

    with db:
        db.add('key', 'value')

    assert db.items() == [('key', 'value')]

    drop_db()

def test_set_default():
    db.set_default(1)
    assert db.data[db.settings]['default'] == 1

def test_set_global_tag():
    db.set_global_tag(tags.const_tag, True)
    db.set_global_tag('ttl', 60)

    assert db.data[db.settings]['global_tags'] == {'const': True, 'ttl': 60}

def test_find_all(clear_db):
    for item in [('key 0', 0), ('key 1', 1), ('key 2', 2)]:
        db.add(*item)

    assert db.find_all(lambda x: x > 0) == [('key 1', 1), ('key 2', 2)]

def test_find_one():
    assert db.find_one(lambda x: x > 0) == ('key 1', 1)
