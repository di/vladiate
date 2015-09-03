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
