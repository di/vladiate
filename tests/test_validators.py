import pytest
from pretend import stub, call, call_recorder

from vladiate.exceptions import BadValidatorException, ValidationException
from vladiate.validators import (
    CastValidator,
    EmptyValidator,
    FloatValidator,
    Ignore,
    IntValidator,
    NotEmptyValidator,
    RangeValidator,
    RegexValidator,
    SetValidator,
    UniqueValidator,
    Validator,
    _stringify_set,
)


class FakeRow(object):
    """A row with side effects"""

    def __init__(self, fields):
        self.fields = fields

    def __getitem__(self, key):
        return self.fields[key].pop(0)

    def keys(self):
        return self.fields.keys()


def test_cast_validator():
    def _raise_valueerror(x):
        raise ValueError

    validator = CastValidator()
    validator.cast = call_recorder(_raise_valueerror)

    assert validator.bad == set()

    with pytest.raises(ValidationException):
        validator.validate("field", "something")

    assert validator.bad == {"field"}

    assert validator.cast.calls == [call("field")]


@pytest.mark.parametrize("field", [("42"), ("42.0"), ("-42.0")])
def test_float_validator_works(field):
    FloatValidator().validate(field)


@pytest.mark.parametrize("field", [("foo"), (" "), ("7..0"), ("4,200")])
def test_float_validator_fails(field):
    with pytest.raises(ValidationException):
        FloatValidator().validate(field)


@pytest.mark.parametrize("field", [("42")])
def test_int_validator_works(field):
    IntValidator().validate(field)


@pytest.mark.parametrize(
    "field", [("foo"), (" "), ("7..0"), ("4,200"), ("42.0"), ("-42.0")]
)
def test_int_validator_fails(field):
    with pytest.raises(ValidationException):
        IntValidator().validate(field)


@pytest.mark.parametrize(
    "field_set, field", [(["foo"], "foo"), (["foo", "bar"], "foo")]
)
def test_set_validator_works(field_set, field):
    validator = SetValidator(field_set)
    validator.validate(field)
    assert field in validator.valid_set


@pytest.mark.parametrize(
    "field_set, field", [([], "bar"), (["foo"], "bar"), (["foo", "bar"], "baz")]
)
def test_set_validator_fails(field_set, field):
    validator = SetValidator(field_set)
    with pytest.raises(ValidationException):
        validator.validate(field)

    assert validator.bad == {field}


@pytest.mark.parametrize(
    "fields, row, unique_with",
    [
        ([], {}, []),
        (["foo", "bar"], {}, []),
        (["foo", ""], {}, []),
        (["foo", "foo"], FakeRow({"some_field": ["bar", "baz"]}), ["some_field"]),
        (
            ["foo", "foo", "foo"],
            FakeRow(
                {
                    "some_field": ["bar", "baz", "bar"],
                    "some_other_field": ["baz", "bar", "bar"],
                }
            ),
            ["some_field", "some_other_field"],
        ),
    ],
)
def test_unique_validator_works(fields, row, unique_with):
    validator = UniqueValidator(unique_with=unique_with)
    for field in fields:
        validator.validate(field, row)


@pytest.mark.parametrize("fields, row, unique_with", [(["foo", "bar", "", ""], {}, [])])
def test_unique_validator_supports_empty_ok(fields, row, unique_with):
    validator = UniqueValidator(unique_with=unique_with, empty_ok=True)
    for field in fields:
        validator.validate(field, row)


@pytest.mark.parametrize(
    "fields, row, unique_with, exception, bad",
    [
        (["foo", "bar", "bar"], {}, [], ValidationException, {("bar",)}),
        (["foo", "", ""], {}, [], ValidationException, {("",)}),
        (["", "", ""], {}, [], ValidationException, {("",)}),
        (
            ["foo", "foo"],
            FakeRow({"some_field": ["bar", "bar"]}),
            ["some_field"],
            ValidationException,
            {("foo", "bar")},
        ),
        (
            ["foo", "foo"],
            FakeRow({"some_field": ["bar", "bar"]}),
            ["other_field"],
            BadValidatorException,
            set(),
        ),
    ],
)
def test_unique_validator_fails(fields, row, unique_with, exception, bad):
    validator = UniqueValidator(unique_with=unique_with)
    with pytest.raises(exception):
        for field in fields:
            validator.validate(field, row)

    assert validator.bad == bad


@pytest.mark.parametrize("pattern, field", [(r"foo.*", "foo"), (r"foo.*", "foobar")])
def test_regex_validator_works(pattern, field):
    RegexValidator(pattern).validate(field)


@pytest.mark.parametrize("pattern, field", [(r"[^\s]+", "foo bar")])
def test_regex_validator_full_works(pattern, field):
    validator = RegexValidator(pattern, full=True)
    with pytest.raises(ValidationException):
        validator.validate(field)

    assert validator.bad == {field}


@pytest.mark.parametrize("pattern, field", [(r"foo.*", "afoo"), (r"^$", "foo")])
def test_regex_validator_fails(pattern, field):
    validator = RegexValidator(pattern)
    with pytest.raises(ValidationException):
        validator.validate(field)

    assert validator.bad == {field}


def test_range_validator_works():
    RangeValidator(0, 100).validate("42")


def test_range_validator_fails():
    validator = RangeValidator(0, 100)
    with pytest.raises(ValidationException):
        validator.validate("-42")

    assert validator.bad == {"-42"}


def test_range_validator_handles_bad_values():
    validator = RangeValidator(0, 100)
    with pytest.raises(ValidationException):
        validator.validate("foobar")

    assert validator.bad == {"foobar"}


def test_empty_validator_works():
    EmptyValidator().validate("")


def test_empty_validator_fails():
    validator = EmptyValidator()
    with pytest.raises(ValidationException):
        validator.validate("foo")

    assert validator.bad == {"foo"}


def test_non_empty_validator_works():
    NotEmptyValidator().validate("foo")


def test_non_empty_validator_fails():
    validator = NotEmptyValidator()
    with pytest.raises(ValidationException):
        validator.validate("")

    assert validator.bad is True


def test_ignore_validator():
    validator = Ignore()
    validator.validate("foo")
    assert validator.bad is None


def test_base_class_raises():
    validator = Validator()

    with pytest.raises(NotImplementedError):
        validator.bad()

    with pytest.raises(NotImplementedError):
        validator.validate(stub(), stub())


@pytest.mark.parametrize(
    "validator_class,args",
    [
        (SetValidator, [["foo"]]),
        (RegexValidator, [r"foo.*"]),
        (IntValidator, []),
        (FloatValidator, []),
        (RangeValidator, [0, 42]),
        (UniqueValidator, []),
    ],
)
def test_all_validators_support_empty_ok(validator_class, args):
    validator = validator_class(*args, empty_ok=True)
    validator.validate("")


@pytest.mark.parametrize(
    "a_set, max_len, stringified",
    [
        ({"A", "B", "C"}, 4, "{'A', 'B', 'C'}"),
        ({"A", "B", "C"}, 3, "{'A', 'B', 'C'}"),
        ({"A", "B", "C"}, 2, "{'A', 'B'} (1 more suppressed)"),
        ({"A", "B", "C"}, 0, "{} (3 more suppressed)"),
        ({}, 5, "{}"),
    ],
)
def test_stringify_set(a_set, max_len, stringified):
    assert _stringify_set(a_set, max_len) == stringified
