import pytest

from ..inputs import *


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
