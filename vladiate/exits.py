""" A collection of exit codes that mimic that values returned by LINUX systems """
import os

__all__ = ['OK', 'NO_INPUT', 'UNAVAILABLE', 'DATAERR']
_WINDOWS = 'nt'

_OK_CODE = 0
_DATAERR = 65
_NOINPUT = 66
_UNAVAILABLE = 69


def on_windows():
    return os.name == _WINDOWS


@property
def OK():
    if on_windows():
        return _OK_CODE
    return os.EX_OK


@property
def DATAERR():
    if on_windows():
        return _DATAERR
    return os.EX_DATAERR


@property
def NOINPUT():
    if on_windows():
        return _OK_CODE
    return os.EX_NOINPUT


@property
def UNAVAILABLE():
    if on_windows():
        return _UNAVAILABLE
    return os.EX_UNAVAILABLE
