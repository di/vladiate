import re

from vladiate.exceptions import ValidationException, BadValidatorException


class Validator(object):
    ''' Generic Validator class '''

    def __init__(self):
        self.fail_count = 0

    @property
    def bad(self):
        ''' Return something containing the "bad" fields '''
        raise NotImplementedError

    def validate(self, field, row):
        ''' Validate the given field. Also is given the row context '''
        raise NotImplementedError


class CastValidator(Validator):
    ''' Validates that a field can be cast to a float '''

    def __init__(self):
        super(CastValidator, self).__init__()
        self.invalid_set = set([])

    def validate(self, field, row={}):
        try:
            if (field or not self.empty_ok):
                self.cast(field)
        except ValueError as e:
            self.invalid_set.add(field)
            raise ValidationException(e)

    @property
    def bad(self):
        return self.invalid_set


class FloatValidator(CastValidator):
    ''' Validates that a field can be cast to a float '''

    def __init__(self, empty_ok=False):
        super(FloatValidator, self).__init__()
        self.empty_ok = empty_ok
        self.cast = float


class IntValidator(CastValidator):
    ''' Validates that a field can be cast to an int '''

    def __init__(self, empty_ok=False):
        super(IntValidator, self).__init__()
        self.empty_ok = empty_ok
        self.cast = int


class SetValidator(Validator):
    ''' Validates that a field is in the given set '''

    def __init__(self, valid_set=[], empty_ok=False):
        super(SetValidator, self).__init__()
        self.valid_set = set(valid_set)
        self.invalid_set = set([])
        if empty_ok:
            self.valid_set.add('')

    def validate(self, field, row={}):
        if field not in self.valid_set:
            self.invalid_set.add(field)
            raise ValidationException(
                "'{}' is not in {}".format(field, self.valid_set))

    @property
    def bad(self):
        return self.invalid_set


class UniqueValidator(Validator):
    ''' Validates that a field is unique within the file '''

    def __init__(self, unique_with=[]):
        super(UniqueValidator, self).__init__()
        self.unique_values = set([])
        self.duplicates = set([])
        self.unique_with = unique_with
        self.unique_check = False

    def _precheck_unique_with(self, row):
        extra = set(self.unique_with) - set(row.keys())
        if extra:
            raise BadValidatorException(extra)
        self.unique_check = True

    def validate(self, field, row={}):
        if self.unique_with and not self.unique_check:
            self._precheck_unique_with(row)

        key = tuple([field] + [row[k] for k in self.unique_with])
        if key not in self.unique_values:
            self.unique_values.add(key)
        else:
            self.duplicates.add(key)
            if self.unique_with:
                raise ValidationException(
                    "'{}' is already in the column (unique with: {})".format(
                        field, key[1:]))
            else:
                raise ValidationException(
                    "'{}' is already in the column".format(field))

    @property
    def bad(self):
        return self.duplicates


class RegexValidator(Validator):
    ''' Validates that a field matches a given regex '''

    def __init__(self, pattern=r'di^', empty_ok=False):
        super(RegexValidator, self).__init__()
        self.regex = re.compile(pattern)
        self.empty_ok = empty_ok
        self.failures = set([])

    def validate(self, field, row={}):
        if not self.regex.match(field) and (field or not self.empty_ok):
            self.failures.add(field)
            raise ValidationException(
                "'{}' does not match pattern /{}/".format(field, self.regex))

    @property
    def bad(self):
        return self.failures


class RangeValidator(Validator):
    def __init__(self, low, high):
        self.fail_count = 0
        self.low = low
        self.high = high
        self.outside = set()

    def validate(self, field, row={}):
        try:
            value = float(field)
            if not self.low <= value <= self.high:
                raise ValueError
        except ValueError:
            self.outside.add(field)
            raise ValidationException(
                "'{}' is not in range {} to {}".format(
                    field, self.low, self.high
                )
            )

    @property
    def bad(self):
        return self.outside


class EmptyValidator(Validator):
    ''' Validates that a field is always empty '''

    def __init__(self):
        super(EmptyValidator, self).__init__()
        self.nonempty = set([])

    def validate(self, field, row={}):
        if field != '':
            self.nonempty.add(field)
            raise ValidationException(
                "'{}' is not an empty string".format(field)
            )

    @property
    def bad(self):
        return self.nonempty


class NotEmptyValidator(Validator):
    ''' Validates that a field is not empty '''

    def __init__(self):
        self.fail_count = 0
        self.failed = False

    def validate(self, field, row={}):
        if field == '':
            self.failed = True
            raise ValidationException("Row has emtpy field in column")

    @property
    def bad(self):
        return self.failed


class Ignore(Validator):
    ''' Ignore a given field. Never fails '''

    def validate(self, field, row={}):
        pass

    @property
    def bad(self):
        pass
