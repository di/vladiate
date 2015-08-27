import pytest

from ..validators import *
from ..exceptions import *


class FakeRow(object):
    ''' A row with side effects '''

    def __init__(self, fields):
        self.fields = fields

    def __getitem__(self, key):
        return self.fields[key].pop(0)

    def keys(self):
        return self.fields.keys()


@pytest.mark.parametrize('field', [('42'), ('42.0'), ('-42.0'), ])
def test_float_validator_works(field):
    FloatValidator().validate(field)


@pytest.mark.parametrize('field', [('foo'), (' '), ('7..0'), ('4,200'), ])
def test_float_validator_fails(field):
    with pytest.raises(ValidationException):
        FloatValidator().validate(field)


@pytest.mark.parametrize('field', [('42'), ])
def test_int_validator_works(field):
    IntValidator().validate(field)


@pytest.mark.parametrize('field', [
    ('foo'),
    (' '),
    ('7..0'),
    ('4,200'),
    ('42.0'),
    ('-42.0'),
])
def test_int_validator_fails(field):
    with pytest.raises(ValidationException):
        IntValidator().validate(field)


@pytest.mark.parametrize('field_set, field', [
    (['foo'], 'foo'),
    (['foo', 'bar'], 'foo'),
])
def test_set_validator_works(field_set, field):
    SetValidator(field_set).validate(field)


@pytest.mark.parametrize('field_set, field', [
    ([], 'bar'),
    (['foo'], 'bar'),
    (['foo', 'bar'], 'baz'),
])
def test_set_validator_fails(field_set, field):
    with pytest.raises(ValidationException):
        SetValidator(field_set).validate(field)


@pytest.mark.parametrize('fields, row, unique_with', [
    ([], {}, []),
    (['foo', 'bar'], {}, []),
    (['foo', 'foo'], FakeRow({'some_field': ['bar', 'baz']}), ['some_field']),
    (['foo', 'foo', 'foo'], FakeRow({
        'some_field': ['bar', 'baz', 'bar'],
        'some_other_field': ['baz', 'bar', 'bar']
    }), ['some_field', 'some_other_field']),
])
def test_unique_validator_works(fields, row, unique_with):
    v = UniqueValidator(unique_with=unique_with)
    for field in fields:
        v.validate(field, row)


@pytest.mark.parametrize('fields, row, unique_with, exception', [
    (['foo', 'bar', 'bar'], {}, [], ValidationException),
    (['foo', 'foo'], FakeRow({'some_field': ['bar', 'bar']}), ['some_field'],
        ValidationException),
    (['foo', 'foo'], FakeRow({'some_field': ['bar', 'bar']}), ['other_field'],
        BadValidatorException),
])
def test_unique_validator_fails(fields, row, unique_with, exception):
    with pytest.raises(exception):
        v = UniqueValidator(unique_with=unique_with)
        for field in fields:
            v.validate(field, row)


@pytest.mark.parametrize('pattern, field', [
    (r'foo.*', 'foo'),
    (r'foo.*', 'foobar'),
])
def test_regex_validator_works(pattern, field):
    RegexValidator(pattern).validate(field)


@pytest.mark.parametrize('pattern, field', [
    (r'foo.*', 'afoo'),
    (r'^$', 'foo'),
])
def test_regex_validator_fails(pattern, field):
    with pytest.raises(ValidationException):
        RegexValidator(pattern).validate(field)


def test_empty_validator_works():
    EmptyValidator().validate("")


def test_empty_validator_fails():
    with pytest.raises(ValidationException):
        EmptyValidator().validate("foo")


def test_ignore_validator():
    Ignore().validate("foo")
