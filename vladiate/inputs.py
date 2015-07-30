class VladInput(object):
    ''' A generic input class '''

    def __init__(self):
        raise NotImplementedError

    def open(self):
        raise NotImplementedError

    def __repr__(self):
        raise NotImplementedError


class LocalFile(VladInput):
    ''' Read from a local file path '''

    def __init__(self, filename):
        self.filename = filename

    def open(self):
        return open(self.filename, 'r')

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self.filename)
