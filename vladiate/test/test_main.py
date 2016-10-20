import os
import sys
import inspect

import pytest
from pretend import stub, call, call_recorder

from ..main import (  # NOQA
    parse_args, is_vlad, find_vladfile, load_vladfile, _vladiate, main, run,
    _is_package
)

from ..vlad import Vlad
from ..inputs import String
from ..examples import vladfile
from ..examples.vladfile import YourFirstFailingValidator


def test_parse_args():
    options = parse_args()

    assert options.list_commands is False
    assert options.processes == 1
    assert options.show_version is False
    assert options.vladfile == 'vladfile'
    assert options.vlads == ['test']


@pytest.mark.parametrize('tup, expected', [
    (('foo', 'bar'), False),
    (('YourFirstFailingValidator', YourFirstFailingValidator), True),
])
def test_is_vlad(tup, expected):
    assert is_vlad(tup) == expected


@pytest.mark.parametrize('name, path', [
    ('vladfile', './vladiate/examples/'),
    ('./vladiate/examples/vladfile', '.'),
])
def test_find_vladfile(name, path):
    assert find_vladfile(name, path)


@pytest.mark.parametrize('path', [
    ('./vladiate/examples/vladfile'),
    (os.path.join(sys.path[0], 'vladfile')),
    (os.path.join(sys.path[1], 'vladfile')),
])
def test_load_vladfile(path):
    doc, vlads = load_vladfile(path)
    available = dict(inspect.getmembers(
        vladfile,
        lambda x: inspect.isclass(x) and issubclass(x, Vlad) and x != Vlad
    ))

    assert set(vlads.keys()) == set(available.keys())


def test_vladiate(monkeypatch):
    put = call_recorder(lambda *args, **kwargs: stub())
    result_queue = stub(put=put)

    validate_result = stub()

    monkeypatch.setattr('vladiate.main.result_queue', result_queue)

    class TestVlad(Vlad):
        source = String('foo')
        validators = {}

        def validate(self):
            return validate_result

    _vladiate(TestVlad)

    assert put.calls == [
        call(validate_result)
    ]


def test_run(monkeypatch):
    main_ret = stub()
    main = call_recorder(lambda: main_ret)
    exit = call_recorder(lambda x: stub())
    monkeypatch.setattr('vladiate.main.main', main)
    try:
        monkeypatch.setattr('__builtin__.exit', exit)
    except:
        monkeypatch.setattr('builtins.exit', exit)

    run('__main__')

    assert main.calls == [
        call()
    ]

    assert exit.calls == [
        call(main_ret)
    ]


def test_main_when_get_nowait_raises(monkeypatch):
    monkeypatch.setattr(
        'vladiate.main.parse_args', lambda: stub(
            list_commands=False,
            show_version=False,
            vladfile=stub(),
            vlads=['Something'],
            processes=2,
        )
    )
    monkeypatch.setattr(
        'vladiate.main.find_vladfile', lambda *args, **kwargs: stub()
    )
    vlad = call_recorder(lambda *args, **kwargs: stub(validate=lambda: stub()))
    vlad.source = stub()

    monkeypatch.setattr(
        'vladiate.main.load_vladfile',
        lambda *args, **kwargs: (None, {'Something': vlad})
    )

    Pool = call_recorder(
        lambda *args, **kwargs: stub(map=lambda *args, **kwargs: stub())
    )
    monkeypatch.setattr('vladiate.main.Pool', Pool)

    class MockEmpty(BaseException):
        pass

    def _raise_empty():
        raise MockEmpty

    result_queue = stub(get_nowait=_raise_empty)
    monkeypatch.setattr('vladiate.main.result_queue', result_queue)
    monkeypatch.setattr('vladiate.main.Empty', MockEmpty)

    assert main() is os.EX_OK


@pytest.mark.parametrize('get_nowait, expected', [
    (lambda: stub(), os.EX_OK),
    (lambda: False, os.EX_DATAERR),
])
def test_main_with_multiprocess(monkeypatch, get_nowait, expected):
    monkeypatch.setattr(
        'vladiate.main.parse_args', lambda: stub(
            list_commands=False,
            show_version=False,
            vladfile=stub(),
            vlads=['Something'],
            processes=2,
        )
    )
    monkeypatch.setattr(
        'vladiate.main.find_vladfile', lambda *args, **kwargs: stub()
    )
    vlad = call_recorder(lambda *args, **kwargs: stub(validate=lambda: stub()))
    vlad.source = stub()

    monkeypatch.setattr(
        'vladiate.main.load_vladfile',
        lambda *args, **kwargs: (None, {'Something': vlad})
    )

    Pool = call_recorder(
        lambda *args, **kwargs: stub(map=lambda *args, **kwargs: stub())
    )
    monkeypatch.setattr('vladiate.main.Pool', Pool)
    result_queue = stub(get_nowait=get_nowait)
    monkeypatch.setattr('vladiate.main.result_queue', result_queue)

    assert main() is expected


def test_main_with_vlads_in_args(monkeypatch):
    monkeypatch.setattr(
        'vladiate.main.parse_args', lambda: stub(
            list_commands=False,
            show_version=False,
            vladfile=stub(),
            vlads=['Something'],
            processes=1,
        )
    )
    monkeypatch.setattr(
        'vladiate.main.find_vladfile', lambda *args, **kwargs: stub()
    )
    vlad = call_recorder(lambda *args, **kwargs: stub(validate=lambda: stub()))
    vlad.source = stub()

    monkeypatch.setattr(
        'vladiate.main.load_vladfile',
        lambda *args, **kwargs: (None, {'Something': vlad})
    )
    assert main() is None


def test_main_no_vlads_in_args(monkeypatch):
    monkeypatch.setattr(
        'vladiate.main.parse_args', lambda: stub(
            list_commands=False,
            show_version=False,
            vladfile=stub(),
            vlads=[],
            processes=1,
        )
    )
    monkeypatch.setattr(
        'vladiate.main.find_vladfile', lambda *args, **kwargs: stub()
    )

    vlad = call_recorder(lambda *args, **kwargs: stub(validate=lambda: stub()))
    vlad.source = stub()
    monkeypatch.setattr(
        'vladiate.main.load_vladfile',
        lambda *args, **kwargs: (None, {'Something Else': vlad})
    )
    assert main() is None


def test_main_missing_vlads(monkeypatch):
    monkeypatch.setattr(
        'vladiate.main.parse_args', lambda: stub(
            list_commands=False,
            show_version=False,
            vladfile=stub(),
            vlads=['Something'],
        )
    )
    monkeypatch.setattr(
        'vladiate.main.find_vladfile', lambda *args, **kwargs: stub()
    )
    monkeypatch.setattr(
        'vladiate.main.load_vladfile',
        lambda *args, **kwargs: (None, {'Something Else': stub()})
    )
    assert main() == os.EX_UNAVAILABLE


def test_main_no_vlads_loaded(monkeypatch):
    monkeypatch.setattr(
        'vladiate.main.parse_args', lambda: stub(
            list_commands=False,
            show_version=False,
            vladfile=stub(),
        )
    )
    monkeypatch.setattr(
        'vladiate.main.find_vladfile', lambda *args, **kwargs: stub()
    )
    vlads = []
    monkeypatch.setattr(
        'vladiate.main.load_vladfile', lambda *args, **kwargs: (None, vlads)
    )
    assert main() == os.EX_NOINPUT


def test_main_list_commands(monkeypatch):
    monkeypatch.setattr(
        'vladiate.main.parse_args', lambda: stub(
            list_commands=True,
            show_version=False,
            vladfile=stub(),
        )
    )
    monkeypatch.setattr(
        'vladiate.main.find_vladfile', lambda *args, **kwargs: stub()
    )
    vlads = ['Something']
    monkeypatch.setattr(
        'vladiate.main.load_vladfile', lambda *args, **kwargs: (None, vlads)
    )
    assert main() == os.EX_OK


def test_main_show_version(monkeypatch):
    monkeypatch.setattr(
        'vladiate.main.parse_args', lambda: stub(show_version=True)
    )
    assert main() == os.EX_OK


def test_main_no_vladfile(monkeypatch):
    monkeypatch.setattr(
        'vladiate.main.find_vladfile', lambda *args, **kwargs: None
    )
    assert main() == os.EX_NOINPUT


@pytest.mark.parametrize('path, expected', [
    ('foo/bar', False),
    ('vladiate/test', True),
])
def test_is_package(path, expected):
    assert _is_package(path) == expected
