class ValidationException(Exception):
    ''' Thrown when validation fails '''
    pass


class BadValidatorException(Exception):
    ''' Thrown when a validator is bad '''
    def __init__(self, extra):
        message = 'Row does not contain the following unique_with fields: {}'
        super(BadValidatorException, self).__init__(message.format(extra))
