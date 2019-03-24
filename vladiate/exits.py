""" A collection of exit codes that work on non-UNIX systems """

import os

OK = getattr(os, "EX_OK", 0)
DATAERR = getattr(os, "EX_DATAERR", 65)
NOINPUT = getattr(os, "EX_NOINPUT", 66)
UNAVAILABLE = getattr(os, "EX_UNAVAILABLE", 69)
