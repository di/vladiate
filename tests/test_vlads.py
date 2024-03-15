import pytest

from vladiate.inputs import LocalFile, String
from vladiate.validators import (
    EmptyValidator,
    FloatValidator,
    NotEmptyValidator,
    RowLengthValidator,
    SetValidator,
    UniqueValidator,
)
from vladiate.vlad import Vlad


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


def test_row_validators():
    source = LocalFile("vladiate/examples/vampires.csv")
    row_validators = [RowLengthValidator()]
    validators = {
        "Column A": [UniqueValidator()],
        "Column B": [SetValidator(["Vampire", "Not A Vampire"])],
    }
    assert Vlad(
        source=source, row_validators=row_validators, validators=validators
    ).validate()


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


def test_explicit_fieldnames():
    source = String("Dracula,Vampire")

    class TestVlad(Vlad):
        validators = {
            "Name": [UniqueValidator()],
            "Status": [SetValidator(["Vampire", "Not A Vampire"])],
        }
        fieldnames = ["Name", "Status"]

    assert TestVlad(source=source).validate()


def test_explicit_fieldnames_conflict_fails():
    source = LocalFile("vladiate/examples/vampires.csv")

    class TestVlad(Vlad):
        validators = {
            "Name": [UniqueValidator()],
            "Status": [SetValidator(["Vampire", "Not A Vampire"])],
        }
        fieldnames = ["Name", "Status"]

    assert not TestVlad(source=source).validate()


def test_fails_validation():
    source = LocalFile("vladiate/examples/vampires.csv")

    class TestVlad(Vlad):
        validators = {"Column A": [EmptyValidator()], "Column B": [EmptyValidator()]}

    vlad = TestVlad(source=source)
    assert not vlad.validate()
    assert vlad.validators["Column A"][0].fail_count == 3
    assert vlad.validators["Column B"][0].fail_count == 3
    assert vlad.invalid_lines == {1, 2, 3}


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


def test_quiet(caplog):
    source = LocalFile("vladiate/examples/vampires.csv")

    class TestVlad(Vlad):
        validators = {
            "Column A": [UniqueValidator()],
            "Column B": [SetValidator(["Vampire", "Not A Vampire"])],
        }

    vlad = TestVlad(source=source, quiet=True)

    assert vlad.validate()
    assert len(caplog.records) == 0


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


def test_stop_file_validation_at_invalid_threshold():
    source = LocalFile("vladiate/examples/real_vampires.csv")

    class TestVlad(Vlad):
        validators = {
            "Column A": [EmptyValidator()],
            "Column B": [EmptyValidator()],
            "Column C": [UniqueValidator()],
        }

    vlad = TestVlad(source=source, file_validation_failure_threshold=0.1)

    assert not vlad.validate()
    assert vlad.validators["Column A"][0].fail_count == 1
    assert vlad.validators["Column B"][0].fail_count == 0
    assert vlad.validators["Column C"][0].fail_count == 0
    assert vlad.invalid_lines == {1}
