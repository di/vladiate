import pytest

from vladiate.inputs import LocalFile, String
from vladiate.validators import (
    EmptyValidator,
    FloatValidator,
    NotEmptyValidator,
    SetValidator,
    UniqueValidator,
)
from vladiate.vlad import Vlad
from vladiate.exceptions import ValidationException


def test_initialize_vlad():
    source = LocalFile("vladiate/examples/vampires.csv")
    validators = {
        "Column A": [UniqueValidator()],
        "Column B": [SetValidator(["Vampire", "Not A Vampire"])],
    }
    assert Vlad(source=source, validators=validators).validate()


def test_initialize_vlad_with_alternative_delimiter():
    source = LocalFile("vladiate/examples/bats.csv")
    validators = {
        "Column A": [UniqueValidator()],
        "Column B": [SetValidator(["Vampire", "Not A Vampire"])],
    }
    delimiter = "|"
    vlad = Vlad(source=source, validators=validators, delimiter=delimiter)
    assert vlad.validate()


def test_initialize_vlad_no_source():
    with pytest.raises(TypeError):
        Vlad().validate()


def test_unused_validator_fails_validation():
    source = LocalFile("vladiate/examples/vampires.csv")
    validators = {
        "Column A": [UniqueValidator()],
        "Column B": [SetValidator(["Vampire", "Not A Vampire"])],
        "Column C": [FloatValidator()],
    }

    assert not Vlad(source=source, validators=validators).validate()


def test_validators_in_class_variable_are_used():
    source = LocalFile("vladiate/examples/vampires.csv")

    class TestVlad(Vlad):
        validators = {
            "Column A": [UniqueValidator()],
            "Column B": [SetValidator(["Vampire", "Not A Vampire"])],
        }

    assert TestVlad(source=source).validate()


def test_missing_validators():
    source = LocalFile("vladiate/examples/vampires.csv")

    class TestVlad(Vlad):
        validators = {"Column A": [UniqueValidator()]}

    assert not TestVlad(source=source).validate()


def test_no_fieldnames():
    source = String("")

    class TestVlad(Vlad):
        validators = {"Foo": [], "Bar": []}

    assert not TestVlad(source=source).validate()


def test_fails_validation():
    source = LocalFile("vladiate/examples/vampires.csv")

    class TestVlad(Vlad):
        validators = {"Column A": [EmptyValidator()], "Column B": [EmptyValidator()]}

    vlad = TestVlad(source=source)
    assert not vlad.validate()
    assert vlad.validators["Column A"][0].fail_count == 3
    assert vlad.validators["Column B"][0].fail_count == 3
    assert len(vlad.failures) == 0


def test_verbose_and_fails_validation():
    source = LocalFile('vladiate/examples/vampires.csv')

    class TestVlad(Vlad):
        validators = {
            'Column A': [
                EmptyValidator()
            ],
            'Column B': [
                EmptyValidator()
            ]
        }

    vlad = TestVlad(source=source, verbose=True)
    assert not vlad.validate()
    assert list(map(type, vlad.failures['Column A'][0])) == [ValidationException]
    assert list(map(type, vlad.failures['Column A'][1])) == [ValidationException]
    assert list(map(type, vlad.failures['Column A'][2])) == [ValidationException]
    assert list(map(type, vlad.failures['Column B'][0])) == [ValidationException]
    assert list(map(type, vlad.failures['Column B'][1])) == [ValidationException]
    assert list(map(type, vlad.failures['Column B'][2])) == [ValidationException]


def test_gt_99_failures():
    source = String("\n".join(["Foo"] + [str(x) for x in range(100)]))

    class TestVlad(Vlad):
        validators = {"Foo": [EmptyValidator()]}

    assert not TestVlad(source=source).validate()


def test_ignore_missing_validators():
    source = LocalFile("vladiate/examples/vampires.csv")

    class TestVlad(Vlad):
        validators = {"Column A": [UniqueValidator()]}

    vlad = TestVlad(source=source, ignore_missing_validators=True)

    assert vlad.validate()
    assert vlad.missing_validators == {"Column B"}


def test_when_bad_is_non_iterable():
    source = String("Column A,Column B\n,foo")

    class TestVlad(Vlad):
        validators = {
            "Column A": [NotEmptyValidator()],
            "Column B": [NotEmptyValidator()],
        }

    vlad = TestVlad(source=source)

    assert not vlad.validate()
    assert vlad.validators["Column A"][0].fail_count == 1
    assert vlad.validators["Column A"][0].bad
    assert vlad.validators["Column B"][0].fail_count == 0
    assert not vlad.validators["Column B"][0].bad
