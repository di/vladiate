import pytest

from ..vlad import Vlad
from ..inputs import *
from ..validators import *


def test_initialize_vlad():
    source = LocalFile('vladiate/examples/vampires.csv')
    validators = {
        'Column A': [
            UniqueValidator()
        ],
        'Column B': [
            SetValidator(['Vampire', 'Not A Vampire'])
        ]
    }
    assert Vlad(source=source, validators=validators).validate()


def test_initialize_vlad_no_source():
    with pytest.raises(TypeError):
        Vlad().validate()


def test_unused_validator_fails_validation():
    source = LocalFile('vladiate/examples/vampires.csv')
    validators = {
        'Column A': [
            UniqueValidator()
        ],
        'Column B': [
            SetValidator(['Vampire', 'Not A Vampire'])
        ],
        'Column C': [
            FloatValidator()
        ]
    }

    assert not Vlad(source=source, validators=validators).validate()


def test_validators_in_class_variable_are_used():
    source = LocalFile('vladiate/examples/vampires.csv')
    class TestVlad(Vlad):
        validators = {
            'Column A': [
                UniqueValidator()
            ],
            'Column B': [
                SetValidator(['Vampire', 'Not A Vampire'])
            ]
        }

    assert TestVlad(source=source).validate()
