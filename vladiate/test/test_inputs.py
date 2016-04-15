import pytest
from pretend import stub, call, call_recorder

from ..inputs import S3File, StringIO, String, VladInput
from ..vlad import Vlad


@pytest.mark.parametrize('kwargs', [
    ({'path': 's3://some.bucket/some/s3/key.csv'}),
    ({'bucket': 'some.bucket', 'key': '/some/s3/key.csv'}),
])
def test_s3_input_works(kwargs):
    S3File(**kwargs)


@pytest.mark.parametrize('kwargs', [
    ({}),
    ({'path': 's3://some.bucket/some/s3/key.csv', 'bucket': 'some.bucket'}),
    ({'path': 's3://some.bucket/some/s3/key.csv', 'key': '/some/s3/key.csv'}),
    ({'bucket': 'some.bucket'}),
    ({'key': '/some/s3/key.csv'}),
])
def test_s3_input_fails(kwargs):
    with pytest.raises(ValueError):
        S3File(**kwargs)


@pytest.mark.parametrize('kwargs', [
    ({'string_input': 'ColA,ColB\n,'}),
    ({'string_io': StringIO('ColA,ColB\n,')}),
])
def test_string_input_works(kwargs):
    source = String(**kwargs)
    validators = {'ColA': [], 'ColB': []}
    assert Vlad(source=source, validators=validators).validate()


def test_open_s3file(monkeypatch):
    new_key = call_recorder(lambda *args, **kwargs: stub(
        get_contents_as_string=lambda: 'contents'.encode()
    ))

    get_bucket = call_recorder(lambda *args, **kwargs: stub(new_key=new_key))

    mock_boto = stub(connect_s3=lambda: stub(get_bucket=get_bucket))

    monkeypatch.setattr('vladiate.inputs.boto', mock_boto)

    result = S3File('s3://some.bucket/some/s3/key.csv').open()

    assert get_bucket.calls == [
        call('some.bucket')
    ]

    assert new_key.calls == [
        call('/some/s3/key.csv')
    ]

    assert result.readlines() == [b'contents']


def test_repr_s3file():
    s3_file = S3File('s3://some.bucket/some/s3/key.csv')
    assert repr(s3_file) == "S3File('s3://some.bucket/some/s3/key.csv')"


def test_base_class_raises():
    with pytest.raises(NotImplementedError):
        VladInput()

    class PartiallyImplemented(VladInput):
        def __init__(self):
            pass

    with pytest.raises(NotImplementedError):
        PartiallyImplemented().open()

    with pytest.raises(NotImplementedError):
        repr(PartiallyImplemented())
