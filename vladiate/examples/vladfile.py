from vladiate import Vlad
from vladiate.validators import UniqueValidator, SetValidator
from vladiate.inputs import LocalFile


class YourFirstValidator(Vlad):
    source = LocalFile("vampires.csv")
    validators = {
        "Column A": [UniqueValidator()],
        "Column B": [SetValidator(["Vampire", "Not A Vampire"])],
    }


class YourFirstNonCommaDelimitedValidator(Vlad):
    source = LocalFile("bats.csv")
    validators = {
        "Column A": [UniqueValidator()],
        "Column B": [SetValidator(["Vampire", "Not A Vampire"])],
    }
    delimiter = "|"


class YourFirstFailingValidator(Vlad):
    source = LocalFile("potential_vampires.csv")
    validators = {
        "Column A": [UniqueValidator()],
        "Column B": [SetValidator(["Vampire", "Not A Vampire"])],
    }


class YourFirstEmptyValidator(Vlad):
    source = LocalFile("real_vampires.csv")
    validators = {}


class YourSecondEmptyValidator(Vlad):
    source = LocalFile("real_vampires.csv")
    validators = {"Column A": [], "Column B": [], "Column C": []}
