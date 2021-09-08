class ValidationException(Exception):
    """Thrown when validation fails"""

    pass


class BadValidatorException(Exception):
    """Thrown when a validator is bad"""

    def __init__(self, extra):
        message = "Row does not contain the following unique_with fields: {}"
        super(BadValidatorException, self).__init__(message.format(extra))


class MissingExtraException(Exception):
    """Thrown when an extra dependency is missing"""

    def __init__(self):
        super(MissingExtraException, self).__init__(
            "The `s3` extra is required to use the `S3File` class. Install"
            " it via `pip install vladiate[s3]`."
        )
