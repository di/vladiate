import os
import sys
import inspect

import pytest
from pretend import stub, call, call_recorder

from vladiate import exits
from vladiate.examples import vladfile
from vladiate.examples.vladfile import YourFirstFailingValidator
from vladiate.inputs import String
from vladiate.main import (
    parse_args,
    is_vlad,
    find_vladfile,
    load_vladfile,
    _vladiate,
    main,
    run,
    _is_package,
)
from vladiate.vlad import Vlad


def test_parse_args():
    options = parse_args()

    assert options.list_commands is False
    assert options.processes == 1
    assert options.show_version is False
    assert options.vladfile == "vladfile"
    assert options.vlads == ["test"]


@pytest.mark.parametrize(
    "tup, expected",
    [
        (("foo", "bar"), False),
        (("YourFirstFailingValidator", YourFirstFailingValidator), True),
    ],
)
def test_is_vlad(tup, expected):
    assert is_vlad(tup) == expected


@pytest.mark.parametrize(
    "name, path",
    [("vladfile", "./vladiate/examples/"), ("./vladiate/examples/vladfile", ".")],
)
def test_find_vladfile(name, path):
    assert find_vladfile(name, path)


@pytest.mark.parametrize(
    "path",
    [
        ("./vladiate/examples/vladfile"),
        (os.path.join(sys.path[0], "vladfile")),
        (os.path.join(sys.path[1], "vladfile")),
    ],
)
def test_load_vladfile(path):
    doc, vlads = load_vladfile(path)
    available = dict(
        inspect.getmembers(
            vladfile, lambda x: inspect.isclass(x) and issubclass(x, Vlad) and x != Vlad
        )
    )

    assert set(vlads.keys()) == set(available.keys())


def test_vladiate(monkeypatch):
    put = call_recorder(lambda *args, **kwargs: stub())
    result_queue = stub(put=put)

    validate_result = stub()

    monkeypatch.setattr("vladiate.main.result_queue", result_queue)

    class TestVlad(Vlad):
        source = String("foo")
        validators = {}

        def validate(self):
            return validate_result

    _vladiate(TestVlad)

    assert put.calls == [call(validate_result)]


def test_run(monkeypatch):
    main_ret = stub()
    main = call_recorder(lambda: main_ret)
    exit = call_recorder(lambda x: stub())
    monkeypatch.setattr("vladiate.main.main", main)
    try:
        monkeypatch.setattr("__builtin__.exit", exit)
    except ImportError:
        monkeypatch.setattr("builtins.exit", exit)

    run("__main__")

    assert main.calls == [call()]

    assert exit.calls == [call(main_ret)]


@pytest.mark.parametrize(
    "get, expected", [(lambda: True, exits.OK), (lambda: False, exits.DATAERR)]
)
def test_main_with_multiprocess(monkeypatch, get, expected):
    monkeypatch.setattr(
        "vladiate.main.parse_args",
        lambda: stub(
            list_commands=False,
            show_version=False,
            vladfile=stub(),
            vlads=["Something"],
            processes=2,
            quiet=False,
        ),
    )
    monkeypatch.setattr("vladiate.main.find_vladfile", lambda *args, **kwargs: stub())
    vlad = call_recorder(lambda *args, **kwargs: stub(validate=lambda: stub()))
    vlad.source = stub()

    monkeypatch.setattr(
        "vladiate.main.load_vladfile",
        lambda *args, **kwargs: (None, {"Something": vlad}),
    )

    Pool = call_recorder(
        lambda *args, **kwargs: stub(map=lambda *args, **kwargs: stub())
    )
    monkeypatch.setattr("vladiate.main.Pool", Pool)

    def empty(calls=[]):
        if calls:
            return True
        calls.append(None)
        return False

    result_queue = stub(get=get, empty=empty)
    monkeypatch.setattr("vladiate.main.result_queue", result_queue)

    assert main() is expected


def test_main_with_vlads_in_args(monkeypatch):
    monkeypatch.setattr(
        "vladiate.main.parse_args",
        lambda: stub(
            list_commands=False,
            show_version=False,
            vladfile=stub(),
            vlads=["Something"],
            processes=1,
            quiet=False,
        ),
    )
    monkeypatch.setattr("vladiate.main.find_vladfile", lambda *args, **kwargs: stub())
    vlad = call_recorder(lambda *args, **kwargs: stub(validate=lambda: stub()))
    vlad.source = stub()

    monkeypatch.setattr(
        "vladiate.main.load_vladfile",
        lambda *args, **kwargs: (None, {"Something": vlad}),
    )
    assert main() is exits.OK


def test_main_no_vlads_in_args(monkeypatch):
    monkeypatch.setattr(
        "vladiate.main.parse_args",
        lambda: stub(
            list_commands=False,
            show_version=False,
            vladfile=stub(),
            vlads=[],
            processes=1,
            quiet=False,
        ),
    )
    monkeypatch.setattr("vladiate.main.find_vladfile", lambda *args, **kwargs: stub())

    vlad = call_recorder(lambda *args, **kwargs: stub(validate=lambda: stub()))
    vlad.source = stub()
    monkeypatch.setattr(
        "vladiate.main.load_vladfile",
        lambda *args, **kwargs: (None, {"Something Else": vlad}),
    )
    assert main() == exits.OK


def test_main_missing_vlads(monkeypatch):
    monkeypatch.setattr(
        "vladiate.main.parse_args",
        lambda: stub(
            list_commands=False,
            show_version=False,
            vladfile=stub(),
            vlads=["Something"],
        ),
    )
    monkeypatch.setattr("vladiate.main.find_vladfile", lambda *args, **kwargs: stub())
    monkeypatch.setattr(
        "vladiate.main.load_vladfile",
        lambda *args, **kwargs: (None, {"Something Else": stub()}),
    )
    assert main() == exits.UNAVAILABLE


def test_main_no_vlads_loaded(monkeypatch):
    monkeypatch.setattr(
        "vladiate.main.parse_args",
        lambda: stub(list_commands=False, show_version=False, vladfile=stub()),
    )
    monkeypatch.setattr("vladiate.main.find_vladfile", lambda *args, **kwargs: stub())
    vlads = []
    monkeypatch.setattr(
        "vladiate.main.load_vladfile", lambda *args, **kwargs: (None, vlads)
    )
    assert main() == exits.NOINPUT


def test_main_list_commands(monkeypatch):
    monkeypatch.setattr(
        "vladiate.main.parse_args",
        lambda: stub(list_commands=True, show_version=False, vladfile=stub()),
    )
    monkeypatch.setattr("vladiate.main.find_vladfile", lambda *args, **kwargs: stub())
    vlads = ["Something"]
    monkeypatch.setattr(
        "vladiate.main.load_vladfile", lambda *args, **kwargs: (None, vlads)
    )
    assert main() == exits.OK


def test_main_show_version(monkeypatch):
    monkeypatch.setattr("vladiate.main.parse_args", lambda: stub(show_version=True))
    assert main() == exits.OK


def test_main_no_vladfile(monkeypatch):
    monkeypatch.setattr("vladiate.main.find_vladfile", lambda *args, **kwargs: None)
    assert main() == exits.NOINPUT


@pytest.mark.parametrize(
    "path, expected", [("foo/bar", False), ("vladiate/examples", True)]
)
def test_is_package(path, expected):
    assert _is_package(path) == expected
