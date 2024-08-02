from jsoner import errors
import pytest
from contextlib import nullcontext as does_not_raise
from tests.conftest import db, drop_db, clear_db

@pytest.mark.parametrize(
        'key, value, expectation',
        [
            ['key', 'value', does_not_raise()], 
            [1,     'value', pytest.raises(errors.KeyMustBeStr)],
            ['key', 'value', pytest.raises(errors.KeyAddError)],
            ['key0',  db,     pytest.raises(TypeError)]
        ]
)
def test_add(key, value, expectation):
    with expectation:
        db.add(key, value)


@pytest.mark.parametrize(
        'key, expected_value',
        [
            ['key', 'value'],
            ['key0', db.data[db.settings]['default']]
        ]
)
def test_get(key, expected_value):
    assert db.get(key) == expected_value


@pytest.mark.parametrize(
        'key, expectation',
        [
            ['key',  does_not_raise()], 
            ['key0', pytest.raises(errors.KeyNotFound)],
        ]
)
def test_update(key, expectation):
    with expectation:
        db.update(key, 0)


def test_incr():
    db.incr('key', 1)
    assert db.get('key') == 1

def test_delete():
    db.delete('key')
    assert db.keys() == []
