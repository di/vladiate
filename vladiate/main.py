import vladiate
from vladiate import Vlad
from vladiate import logs

import os
import sys
import inspect
from optparse import OptionParser
from pkg_resources import get_distribution


def parse_options():
    """
    Handle command-line options with optparse.OptionParser.
    Return list of arguments, largely for use in `parse_arguments`.
    """

    # Initialize
    parser = OptionParser(
        usage="vladiate [options] [VladClass [VladClass2 ... ]]")

    parser.add_option(
        '-f', '--vladfile',
        dest='vladfile',
        default='vladfile',
        help=
        "Python module file to import, e.g. '../other.py'. Default: vladfile")

    # List vladiate commands found in loaded vladiate files/source files
    parser.add_option(
        '-l', '--list',
        action='store_true',
        dest='list_commands',
        default=False,
        help="Show list of possible vladiate classes and exit")

    # Version number (optparse gives you --version but we have to do it
    # ourselves to get -V too. sigh)
    parser.add_option(
        '-V', '--version',
        action='store_true',
        dest='show_version',
        default=False,
        help="show program's version number and exit")

    # Finalize
    # Return three-tuple of parser + the output from parse_args (opt obj, args)
    opts, args = parser.parse_args()
    return parser, opts, args


def is_vlad(tup):
    """
    Takes (name, object) tuple, returns True if it's a public Vlad subclass.
    """
    name, item = tup
    return bool(
        inspect.isclass(item) and issubclass(item, Vlad) and
        hasattr(item, "source") and getattr(item, "source") and
        hasattr(item, "validators") and not name.startswith('_'))


def find_vladfile(vladfile):
    """
    Attempt to locate a vladfile, either explicitly or by searching parent dirs.
    """
    # Obtain env value
    names = [vladfile]
    # Create .py version if necessary
    if not names[0].endswith('.py'):
        names += [names[0] + '.py']
    # Does the name contain path elements?
    if os.path.dirname(names[0]):
        # If so, expand home-directory markers and test for existence
        for name in names:
            expanded = os.path.expanduser(name)
            if os.path.exists(expanded):
                if name.endswith('.py') or _is_package(expanded):
                    return os.path.abspath(expanded)
    else:
        # Otherwise, start in cwd and work downwards towards filesystem root
        path = '.'
        # Stop before falling off root of filesystem (should be platform
        # agnostic)
        while os.path.split(os.path.abspath(path))[1]:
            for name in names:
                joined = os.path.join(path, name)
                if os.path.exists(joined):
                    if name.endswith('.py') or _is_package(joined):
                        return os.path.abspath(joined)
            path = os.path.join('..', path)
    # Implicit 'return None' if nothing was found


def load_vladfile(path):
    """
    Import given vladfile path and return (docstring, callables).
    Specifically, the vladfile's ``__doc__`` attribute (a string) and a
    dictionary of ``{'name': callable}`` containing all callables which pass
    the "is a vlad" test.
    """
    # Get directory and vladfile name
    directory, vladfile = os.path.split(path)
    # If the directory isn't in the PYTHONPATH, add it so our import will work
    added_to_path = False
    index = None
    if directory not in sys.path:
        sys.path.insert(0, directory)
        added_to_path = True
    # If the directory IS in the PYTHONPATH, move it to the front temporarily,
    # otherwise other vladfiles -- like vlads's own -- may scoop the intended
    # one.
    else:
        i = sys.path.index(directory)
        if i != 0:
            # Store index for later restoration
            index = i
            # Add to front, then remove from original position
            sys.path.insert(0, directory)
            del sys.path[i + 1]
    # Perform the import (trimming off the .py)
    imported = __import__(os.path.splitext(vladfile)[0])
    # Remove directory from path if we added it ourselves (just to be neat)
    if added_to_path:
        del sys.path[0]
    # Put back in original index if we moved it
    if index is not None:
        sys.path.insert(index + 1, directory)
        del sys.path[0]
    # Return our two-tuple
    vlads = dict(filter(is_vlad, vars(imported).items()))
    return imported.__doc__, vlads


def main():
    parser, options, arguments = parse_options()
    logger = logs.logger

    if options.show_version:
        print "Vladiate %s" % (get_distribution('vladiate').version, )
        sys.exit(0)

    vladfile = find_vladfile(options.vladfile)
    if not vladfile:
        logger.error(
            "Could not find any vladfile! Ensure file ends in '.py' and see --help for available options.")
        sys.exit(1)

    docstring, vlads = load_vladfile(vladfile)

    if options.list_commands:
        logger.info("Available vlads:")
        for name in vlads:
            logger.info("    " + name)
        sys.exit(0)

    if not vlads:
        logger.error("No vlad class found!")
        sys.exit(1)

    # make sure specified vlad exists
    if arguments:
        missing = set(arguments) - set(vlads.keys())
        if missing:
            logger.error("Unknown vlad(s): %s\n" % (", ".join(missing)))
            sys.exit(1)
        else:
            names = set(arguments) & set(vlads.keys())
            vlad_classes = [vlads[n] for n in names]
    else:
        vlad_classes = vlads.values()

    # validate all the vlads
    for vlad in vlad_classes:
        vlad(vlad.source, validators=vlad.validators).validate()


if __name__ == '__main__':
    main()
