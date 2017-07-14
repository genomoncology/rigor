import enum
from pydoc import locate  # https://stackoverflow.com/a/29831586
from re import search


@enum.unique
class Status(enum.Enum):
    ACTIVE = "ACTIVE"
    SKIPPED = "SKIPPED"
    PASSED = "PASSED"
    FAILED = "FAILED"


@enum.unique
class Method(enum.Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


@enum.unique
class Comparison(enum.Enum):
    # equality

    EQUALS = "equals"

    def is_equals(self, actual, expect):
        return actual == expect

    NOT_EQUALS = "not equals"

    def is_not_equals(self, actual, expect):
        return actual != expect

    SAME = "same"

    def is_same(self, actual, expect):
        """
        Returns true if equal or if 2 lists, have the same items
        regardless of order.
        """
        ts = (list, tuple)
        same = actual == expect
        if not same and isinstance(actual, ts) and isinstance(expect, ts):
            same = bool(len(actual) and len(expect))
            same = same and all([item in expect for item in actual])
            same = same and all([item in actual for item in expect])
        return same

    # lists

    CONTAINS = "contains"

    def is_contains(self, actual, expect):
        return expect in actual

    NOT_CONTAINS = "not contains"

    def is_not_contains(self, actual, expect):
        return expect not in actual

    IN = "in"

    def is_in(self, actual, expect):
        return actual in expect

    NOT_IN = "not in"

    def is_not_in(self, actual, expect):
        return actual not in expect

    # greater/less than

    GREATER_THAN = "greater than"

    def is_greater_than(self, actual, expect):
        return actual > expect

    GT = "gt"

    def is_gt(self, actual, expect):
        return actual > expect

    GREATER_THAN_OR_EQUALS = "greater than or equals"

    def is_greater_than_or_equals(self, actual, expect):
        return actual >= expect

    GTE = "gte"

    def is_gte(self, actual, expect):
        return actual >= expect

    LESS_THAN = "less than"

    def is_less_than(self, actual, expect):
        return actual < expect

    LT = "lt"

    def is_lt(self, actual, expect):
        return actual < expect

    LESS_THAN_OR_EQUALS = "less than or equals"

    def is_less_than_or_equals(self, actual, expect):
        return actual <= expect

    LTE = "lte"

    def is_lte(self, actual, expect):
        return actual <= expect

    # type

    TYPE = "type"

    def is_type(self, actual, expect):
        return isinstance(actual, locate(expect))

    # regex

    REGEX = "regex"

    def is_regex(self, actual, expect):
        return bool(search(expect, actual))

    # evaluate

    def evaluate(self, actual, expected):
        method = getattr(self, "is_%s" % self.value.replace(" ", "_"))
        try:
            return method(actual, expected)
        except:
            return False
