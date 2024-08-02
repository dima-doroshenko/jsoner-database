import time
from tests.conftest import clear_db, db
import pytest
from jsoner.tags import const_tag, unique_tag, foreign_key_tag, ttl_tag, typing_tag
from jsoner.errors import ValueIsConstant, UniqueValueError, ForeignKeyError

def test_const():
    db.add('pi', 3.14, {const_tag: True})
    with pytest.raises(ValueIsConstant):
        db.update('pi', 6)

def test_const_2():
    assert db['pi'] == 3.14

def test_unique_add():
    db.add('key', 1)
    with pytest.raises(UniqueValueError):
        db.add('key_1', 1, {unique_tag: True})
    db.add('unique_key', 10, {unique_tag: True})

def test_unique_update():
    with pytest.raises(UniqueValueError):
        db.update('unique_key', 1)

def test_foreign_key(clear_db):
    db.set('user_roles', ['admin', 'moderator', 'member'])
    db.set('user1', 'admin', {foreign_key_tag: 'user_roles'})
    with pytest.raises(ForeignKeyError):
        db.set('user1', 0)

def test_ttl(clear_db):
    db.set('key', 'value', {ttl_tag: 0.1})
    assert db['key'] == 'value'
    time.sleep(0.1)
    assert db['key'] == db.data[db.settings]['default']

def test_typing_list(clear_db):
    db.add('list', [0, 1, 2, 3, 4], {typing_tag: True})

    db.set('list', (0, 'Первый  элемент списка') )
    assert db['list'][0] == 'Первый  элемент списка'

    db.set('list', (-1, 'Последний элемент списка') )
    assert db['list'][-1] == 'Последний элемент списка'

    db.set('list', ('append', 'Теперь это последний элемент списка') )
    assert db['list'][-1] == 'Теперь это последний элемент списка'

    db.set('list', ('remove', 'Последний элемент списка') )
    assert db['list'][-2] == 3

def test_typing_dict(clear_db):
    db.add('dict', {}, {typing_tag: True})

    db.set('dict', ('id', 11111111) )
    assert db['dict'] == {'id': 11111111}

    db.set('dict', ('data.text', 'Hello world') )
    assert db['dict'] =={"id": 11111111, "data": {"text": "Hello world"}}
