import sys
import csv
import logging
from collections import defaultdict
from vladiate.exceptions import ValidationException
from vladiate.validators import EmptyValidator


class Vlad(object):
    def __init__(self, default_validator=EmptyValidator):
        self.default_validator = default_validator
        self.logger = logging.getLogger("vlad_logger")
        self.failures = defaultdict(lambda: defaultdict(list))
        self.missing_fields = None

    def _log_debug_failures(self):
        for field_name, field_failure in self.failures.iteritems():
            self.logger.debug("\nFailure on field: \"{}\":".format(field_name))
            for i, (row, errors) in enumerate(field_failure.iteritems()):
                self.logger.debug("  {}:{}".format(self.source.filename, row))
                for error in errors:
                    self.logger.debug("    {}".format(error))

    def _log_validator_failures(self):
        for field_name, validators_list in self.validators.iteritems():
            for validator in validators_list:
                if validator.bad:
                    self.logger.error(
                        "  {} failed {} time(s) on field: '{}'".format(
                            validator.__class__.__name__, validator.fail_count,
                            field_name))
                    self.logger.error(
                        "    Invalid fields: [{}]".format(", ".join(
                            ["'{}'".format(bad) for bad in validator.bad])))

    def _log_missing_fields(self):
        self.logger.error("  Missing validators for:")
        self.logger.error(
            "{}".format("\n".join(["    '{}': [],".format(
                field.encode('string-escape'))
                                   for field in sorted(self.missing_fields)])))

    def validate(self):
        self.logger.info("\nValidating {}(source={})".format(
            self.__class__.__name__, self.source))

        self.validators.update({
            field: [self.default_validator()]
            for field, value in self.validators.iteritems() if not value
        })

        with self.source.open() as csvfile:
            reader = csv.DictReader(csvfile)
            self.missing_fields = set(reader.fieldnames) - set(self.validators)
            if not self.missing_fields:
                for line, row in enumerate(reader):
                    for field_name, field in row.iteritems():
                        for validator in self.validators[field_name]:
                            try:
                                validator.validate(field, row=row)
                            except ValidationException, e:
                                self.failures[field_name][line].append(e)
                                validator.fail_count += 1

        if self.missing_fields:
            self.logger.info("\033[1;33m" + "Missing..." + "\033[0m")
            self._log_missing_fields()
        elif self.failures:
            self.logger.info("\033[0;31m" + "Failed :(" + "\033[0m")
            self._log_debug_failures()
            self._log_validator_failures()
        else:
            self.logger.info("\033[0;32m" + "Passed! :)" + "\033[0m")
