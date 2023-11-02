from __future__ import division
import csv
from collections import defaultdict
from vladiate.exceptions import ValidationException
from vladiate.validators import EmptyValidator
from vladiate import logs


class Vlad(object):
    def __init__(
        self,
        source,
        validators={},
        default_validator=EmptyValidator,
        delimiter=None,
        ignore_missing_validators=False,
        file_validation_failure_threshold=None,
        quiet=False,
        row_validators=[],
    ):
        self.logger = logs.logger
        self.failures = defaultdict(lambda: defaultdict(list))
        self.row_failures = defaultdict(list)
        self.missing_validators = None
        self.missing_fields = None
        self.source = source
        self.validators = validators or getattr(self, "validators", {})
        self.row_validators = row_validators or getattr(self, "row_validators", [])
        self.delimiter = delimiter or getattr(self, "delimiter", ",")
        self.line_count = 0
        self.ignore_missing_validators = ignore_missing_validators
        self.logger.disabled = quiet
        self.invalid_lines = set()
        self.file_validation_failure_threshold = file_validation_failure_threshold
        self.total_lines = 0

        self.validators.update(
            {
                field: [default_validator()]
                for field, value in self.validators.items()
                if not value
            }
        )

    def _log_debug_failures(self):
        for line, errors in self.row_failures.items():
            self.logger.debug("\nFailure on line number {}".format(line))
            for error in errors:
                self.logger.debug("    {}".format(error))

        for field_name, field_failure in self.failures.items():
            self.logger.debug('\nFailure on field: "{}":'.format(field_name))
            for i, (row, errors) in enumerate(field_failure.items()):
                self.logger.debug("  {}:{}".format(self.source, row))
                for error in errors:
                    self.logger.debug("    {}".format(error))

    def _log_validator_failures(self):
        for validator in self.row_validators:
            if validator.bad:
                self.logger.error(
                    " {} failed {} time(s) ({:.1%})".format(
                        validator.__class__.__name__,
                        validator.fail_count,
                        validator.fail_count / self.line_count,
                    )
                )
                try:
                    # If validator.bad is iterable, it contains the rows
                    # which caused it to fail
                    invalid = list(validator.bad)
                    shown = ["'{}'".format(row) for row in invalid[:99]]
                    hidden = ["'{}'".format(row) for row in invalid[99:]]
                    self.logger.error(
                        "   Invalid rows: \n{}".format("    \n".join(shown))
                    )
                    if hidden:
                        self.logger.error("    ({} more suppressed".format(len(hidden)))
                except TypeError:
                    pass

        for field_name, validators_list in self.validators.items():
            for validator in validators_list:
                if validator.bad:
                    self.logger.error(
                        "  {} failed {} time(s) ({:.1%}) on field: '{}'".format(
                            validator.__class__.__name__,
                            validator.fail_count,
                            validator.fail_count / self.line_count,
                            field_name,
                        )
                    )
                    try:
                        # If self.bad is iterable, it contains the fields which
                        # caused it to fail
                        invalid = list(validator.bad)
                        shown = ["'{}'".format(field) for field in invalid[:99]]
                        hidden = ["'{}'".format(field) for field in invalid[99:]]
                        self.logger.error(
                            "    Invalid fields: [{}]".format(", ".join(shown))
                        )
                        if hidden:
                            self.logger.error(
                                "    ({} more suppressed)".format(len(hidden))
                            )
                    except TypeError:
                        pass

    def _log_missing_validators(self):
        self.logger.error("  Missing validators for:")
        self._log_missing(self.missing_validators)

    def _log_missing_fields(self):
        self.logger.error("  Missing expected fields:")
        self._log_missing(self.missing_fields)

    def _log_missing(self, missing_items):
        self.logger.error(
            "{}".format(
                "\n".join(
                    ["    '{}': [],".format(field) for field in sorted(missing_items)]
                )
            )
        )

    def _get_total_lines(self):
        reader = csv.DictReader(self.source.open(), delimiter=self.delimiter)
        self.total_lines = sum(1 for _ in reader)
        return self.total_lines

    def validate(self):
        self.logger.info(
            "\nValidating {}(source={})".format(self.__class__.__name__, self.source)
        )
        reader = csv.DictReader(self.source.open(), delimiter=self.delimiter)

        if not reader.fieldnames:
            self.logger.info(
                "\033[1;33m" + "Source file has no field names" + "\033[0m"
            )
            return False

        self.missing_validators = set(reader.fieldnames) - set(self.validators)
        if self.missing_validators:
            self.logger.info("\033[1;33m" + "Missing..." + "\033[0m")
            self._log_missing_validators()

            if not self.ignore_missing_validators:
                return False

        self.missing_fields = set(self.validators) - set(reader.fieldnames)
        if self.missing_fields:
            self.logger.info("\033[1;33m" + "Missing..." + "\033[0m")
            self._log_missing_fields()
            return False

        if self.file_validation_failure_threshold:
            self.total_lines = self._get_total_lines()

        for line, row in enumerate(reader):
            self.line_count += 1

            for validator in self.row_validators:
                try:
                    validator.validate(row)
                except ValidationException as e:
                    self.row_failures[line].append(e)
                    self.invalid_lines.add(self.line_count)
                    validator.fail_count += 1

            for field_name, field in row.items():
                if field_name in self.validators:
                    for validator in self.validators[field_name]:
                        try:
                            validator.validate(field, row=row)
                        except ValidationException as e:
                            self.failures[field_name][line].append(e)
                            self.invalid_lines.add(self.line_count)
                            validator.fail_count += 1
                if (
                    self.file_validation_failure_threshold
                    and self.total_lines > 0
                    and validator.fail_count / self.total_lines
                    > self.file_validation_failure_threshold
                ):
                    self.logger.error(
                        "  {} failed {} time(s) ({:.1%})".format(
                            validator.__class__.__name__,
                            validator.fail_count,
                            validator.fail_count / self.total_lines,
                        )
                    )
                    return False

        if self.failures or self.row_failures:
            self.logger.info("\033[0;31m" + "Failed :(" + "\033[0m")
            self._log_debug_failures()
            self._log_validator_failures()
            return False
        else:
            self.logger.info("\033[0;32m" + "Passed! :)" + "\033[0m")
            return True
