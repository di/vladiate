import re
from itertools import islice

from vladiate.exceptions import ValidationException, BadValidatorException


class Validator(object):
    """Generic Validator class"""

    def __init__(self, empty_ok=False):
        self.fail_count = 0
        self.empty_ok = empty_ok

    @property
    def bad(self):
        """Return something containing the "bad" fields"""
        raise NotImplementedError

    def validate(self, field, row):
        """Validate the given field. Also is given the row context"""
        raise NotImplementedError


class CastValidator(Validator):
    """Validates that a field can be cast to a float"""

    def __init__(self, **kwargs):
        super(CastValidator, self).__init__(**kwargs)
        self.invalid_set = set([])

    def validate(self, field, row={}):
        try:
            if field or not self.empty_ok:
                self.cast(field)
        except ValueError as e:
            self.invalid_set.add(field)
            raise ValidationException(e)

    @property
    def bad(self):
        return self.invalid_set


class FloatValidator(CastValidator):
    """Validates that a field can be cast to a float"""

    def __init__(self, **kwargs):
        super(FloatValidator, self).__init__(**kwargs)
        self.cast = float


class IntValidator(CastValidator):
    """Validates that a field can be cast to an int"""

    def __init__(self, **kwargs):
        super(IntValidator, self).__init__(**kwargs)
        self.cast = int


class SetValidator(Validator):
    """Validates that a field is in the given set"""

    def __init__(self, valid_set=[], **kwargs):
        super(SetValidator, self).__init__(**kwargs)
        self.valid_set = set(valid_set)
        self.invalid_set = set([])
        if self.empty_ok:
            self.valid_set.add("")

    def validate(self, field, row={}):
        if field not in self.valid_set:
            self.invalid_set.add(field)
            raise ValidationException(
                "'{}' is not in {}".format(field, _stringify_set(self.valid_set, 100))
            )

    @property
    def bad(self):
        return self.invalid_set


class UniqueValidator(Validator):
    """Validates that a field is unique within the file"""

    def __init__(self, unique_with=[], **kwargs):
        super(UniqueValidator, self).__init__(**kwargs)
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
        if field == "" and self.empty_ok:
            return
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
                        field, key[1:]
                    )
                )
            else:
                raise ValidationException("'{}' is already in the column".format(field))

    @property
    def bad(self):
        return self.duplicates


class RegexValidator(Validator):
    """Validates that a field matches a given regex"""

    def __init__(self, pattern=r"di^", full=False, **kwargs):
        super(RegexValidator, self).__init__(**kwargs)
        self.failures = set([])
        if full:
            self.regex = re.compile(r"(?:" + pattern + r")\Z")
        else:
            self.regex = re.compile(pattern)

    def validate(self, field, row={}):
        if not self.regex.match(field) and (field or not self.empty_ok):
            self.failures.add(field)
            raise ValidationException(
                "'{}' does not match pattern /{}/".format(field, self.regex)
            )

    @property
    def bad(self):
        return self.failures


class RangeValidator(Validator):
    def __init__(self, low, high, **kwargs):
        super(RangeValidator, self).__init__(**kwargs)
        self.fail_count = 0
        self.low = low
        self.high = high
        self.outside = set()

    def validate(self, field, row={}):
        if field == "" and self.empty_ok:
            return
        try:
            value = float(field)
            if not self.low <= value <= self.high:
                raise ValueError
        except ValueError:
            self.outside.add(field)
            raise ValidationException(
                "'{}' is not in range {} to {}".format(field, self.low, self.high)
            )

    @property
    def bad(self):
        return self.outside


class EmptyValidator(Validator):
    """Validates that a field is always empty"""

    def __init__(self, **kwargs):
        super(EmptyValidator, self).__init__(**kwargs)
        self.nonempty = set([])

    def validate(self, field, row={}):
        if field != "":
            self.nonempty.add(field)
            raise ValidationException("'{}' is not an empty string".format(field))

    @property
    def bad(self):
        return self.nonempty


class NotEmptyValidator(Validator):
    """Validates that a field is not empty"""

    def __init__(self, **kwargs):
        super(NotEmptyValidator, self).__init__(**kwargs)
        self.fail_count = 0
        self.failed = False

    def validate(self, field, row={}):
        if field == "":
            self.failed = True
            raise ValidationException("Row has empty field in column")

    @property
    def bad(self):
        return self.failed


class Ignore(Validator):
    """Ignore a given field. Never fails"""

    def validate(self, field, row={}):
        pass

    @property
    def bad(self):
        pass


def _stringify_set(a_set, max_len, max_sort_size=8192):
    """Stringify `max_len` elements of `a_set` and count the remainings

    Small sets (len(a_set) <= max_sort_size) are displayed sorted.
    Large sets won't be sorted for performance reasons.
    This may result in an arbitrary ordering in the returned string.
    """
    # Don't convert `a_set` to a list for performance reasons
    text = "{{{}}}".format(
        ", ".join(
            "'{}'".format(value)
            for value in islice(
                sorted(a_set) if len(a_set) <= max_sort_size else a_set, max_len
            )
        )
    )
    if len(a_set) > max_len:
        text += " ({} more suppressed)".format(len(a_set) - max_len)
    return text
