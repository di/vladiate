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
        quiet=False,
    ):
        self.logger = logs.logger
        self.failures = defaultdict(lambda: defaultdict(list))
        self.missing_validators = None
        self.missing_fields = None
        self.source = source
        self.validators = validators or getattr(self, "validators", {})
        self.delimiter = delimiter or getattr(self, "delimiter", ",")
        self.line_count = 0
        self.ignore_missing_validators = ignore_missing_validators
        self.logger.disabled = quiet
        self.invalid_lines = set()

        self.validators.update(
            {
                field: [default_validator()]
                for field, value in self.validators.items()
                if not value
            }
        )

    def _log_debug_failures(self):
        for field_name, field_failure in self.failures.items():
            self.logger.debug('\nFailure on field: "{}":'.format(field_name))
            for i, (row, errors) in enumerate(field_failure.items()):
                self.logger.debug("  {}:{}".format(self.source, row))
                for error in errors:
                    self.logger.debug("    {}".format(error))

    def _log_validator_failures(self):
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

        for line, row in enumerate(reader):
            self.line_count += 1
            for field_name, field in row.items():
                if field_name in self.validators:
                    for validator in self.validators[field_name]:
                        try:
                            validator.validate(field, row=row)
                        except ValidationException as e:
                            self.failures[field_name][line].append(e)
                            self.invalid_lines.add(self.line_count)
                            validator.fail_count += 1

        if self.failures:
            self.logger.info("\033[0;31m" + "Failed :(" + "\033[0m")
            self._log_debug_failures()
            self._log_validator_failures()
            return False
        else:
            self.logger.info("\033[0;32m" + "Passed! :)" + "\033[0m")
            return True
