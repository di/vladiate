import pytest

from ..inputs import *
from ..validators import *
from ..vlad import *


@pytest.mark.parametrize('kwargs', [
    ({'path':'s3://some.bucket/some/s3/key.csv'}),
    ({'bucket':'some.bucket', 'key':'/some/s3/key.csv'}),
])
def test_s3_input_works(kwargs):
    S3File(**kwargs)


@pytest.mark.parametrize('kwargs', [
    ({}),
    ({'path':'s3://some.bucket/some/s3/key.csv', 'bucket':'some.bucket'}),
    ({'path':'s3://some.bucket/some/s3/key.csv', 'key':'/some/s3/key.csv'}),
    ({'bucket':'some.bucket'}),
    ({'key':'/some/s3/key.csv'}),
])
def test_s3_input_fails(kwargs):
    with pytest.raises(ValueError):
        S3File(**kwargs)


@pytest.mark.parametrize('kwargs', [
    ({'string_input':'ColA,ColB\n,'}),
    ({'string_io':StringIO('ColA,ColB\n,')}),
])
def test_string_input_works(kwargs):
    source = String(**kwargs)
    validators = {'ColA': [], 'ColB': []}
    assert Vlad(source=source, validators=validators).validate()
