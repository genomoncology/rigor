import enum
import os
import aiohttp
import jmespath
import ast
import json

from itertools import product
from mako.template import Template
from . import Functions

import related


# enums

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
    EQUALS = "equals"
    SAME = "same"
    IN = "in"
    NOT_IN = "not in"

    def is_equals(self, actual, expect):
        return actual == expect

    def is_in(self, actual, expect):
        return actual in expect

    def is_not_in(self, actual, expect):
        return actual not in expect

    def is_same(self, actual, expect):
        """
        Returns true if equal or if 2 lists, have the same items
        regardless of order.
        """
        same = actual == expect
        if not same and isinstance(actual, list) and isinstance(expect, list):
            same = bool(len(actual) and len(expect))
            same = same and all([item in expect for item in actual])
            same = same and all([item in actual for item in expect])
        return same

    def evaluate(self, actual, expected):
        method = getattr(self, "is_%s" % self.value.replace(" ", "_"))
        return method(actual, expected)


# https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#2xx_Success
HTTP_SUCCESS = [200, 201, 202, 203, 204, 205, 206, 207, 208, 226]


class Namespace(related.ImmutableDict):

    def __getattr__(self, item):
        return self.__getitem__(item)

    def __getitem__(self, name):
        return self.get(name) if name in self else jmespath.search(name, self)

    def evaluate(self, state, existing=None):
        values = existing or {}

        for key, value in self.items():
            values[key] = self.render_value(value, state)

        return Namespace(values)

    @classmethod
    def wrap_namespace(cls, value):
        if isinstance(value, dict) and not isinstance(value, cls):
            return cls(value)

        if isinstance(value, list):
            new_list = []
            for item in value:
                new_list.append(cls.wrap_namespace(item))
            value = new_list

        return value

    @classmethod
    def render_value(cls, value, state):
        if isinstance(value, str):
            template = Template(value)

            try:
                rendered = template.render(**state.namespace)
            except:
                raise

            try:
                value = ast.literal_eval(rendered)
            except:
                value = rendered

        value = cls.wrap_namespace(value)

        return value


class Extractor(Namespace):

    def evaluate(self, state, existing=None):
        existing = related.to_dict(state.extract) if state.extract else {}
        return super(Extractor, self).evaluate(state, existing)

    @classmethod
    def render_value(cls, value, state, **kwargs):
        value = value if value.startswith("${") else "${%s}" % value
        return super(Extractor, cls).render_value(value, state)


class Iterator(Namespace):

    def iterate(self, state):
        if len(self):
            # determine method (product or zip)
            d = self.copy()
            method_key = d.pop("__method__", "zip")
            method = dict(zip=zip, product=product).get(method_key, zip)

            values = [self.render_value(value, state) for value in d.values()]

            # *values => assumes all values are iterable and thus can zipped.
            for zipped_values in method(*values):
                # combine zipped values and construct a Namespace object
                yield Namespace(dict(zip(d.keys(), zipped_values)))
        else:
            yield Namespace()


@related.immutable
class ValidationResult(object):
    actual = related.ChildField(object)
    expect = related.ChildField(object)
    success = related.BooleanField()


@related.immutable
class Validator(object):
    actual = related.ChildField(object)
    expect = related.ChildField(object)
    compare = related.ChildField(Comparison, default=Comparison.EQUALS)

    def evaluate(self, state):
        actual = Namespace.render_value(self.actual, state)
        expect = Namespace.render_value(self.expect, state)
        success = self.compare.evaluate(actual, expect)

        return ValidationResult(actual=actual,
                                expect=expect,
                                success=success)


@related.immutable
class Request(object):
    path = related.StringField()
    method = related.ChildField(Method, default=Method.GET)
    domain = related.StringField(required=False)
    headers = related.ChildField(Namespace, required=False)
    params = related.ChildField(Namespace, required=False)
    data = related.ChildField(object, required=False)
    status = related.SequenceField(int, required=False)

    def get_url(self, state):
        domain = self.domain or state.case.domain or state.suite.domain
        path = Namespace.render_value(self.path, state)
        return "%s/%s" % (domain, path)

    def get_headers(self, case):
        case_headers = related.to_dict(case.headers) or {}
        case_headers.update(related.to_dict(self.headers) or {})

        # todo: content-type not really figured out.
        if "content-type" not in case_headers:
            case_headers['content-type'] = "application/json"

        return Namespace(case_headers)

    def get_params(self, state):
        as_dict = self.params.evaluate(state) if self.params else Namespace()

        params = []
        for key, value in as_dict.items():
            if isinstance(value, (tuple, list, set)):
                for item in value:
                    params.append((key, str(item)))
            else:
                params.append((key, str(value)))

        return params

    def get_data(self, state):
        # flatten data to a string that will include ${expressions} to render
        ds = self.data if isinstance(self.data, str) else json.dumps(self.data)

        # render data string (ds) template
        rendered = Namespace.render_value(ds, state)

        # dump rendered value to a json string, if not already a string
        return rendered if isinstance(rendered, str) else json.dumps(rendered)


@related.immutable
class Step(object):
    description = related.StringField()
    request = related.ChildField(Request)
    extract = related.ChildField(Extractor, default=Namespace())
    iterate = related.ChildField(Iterator, default=Iterator())
    validate = related.SequenceField(Validator, required=False)

    def create_fetch(self, state):
        kwargs = dict(headers=self.request.get_headers(state.case))
        if self.request.data:
            kwargs['data'] = self.request.get_data(state)
        else:
            kwargs['params'] = self.request.get_params(state)

        return Namespace(dict(
            method=self.request.method.value.lower(),
            url=self.request.get_url(state),
            kwargs=kwargs
        ))

    async def fetch(self, state):
        # construct fetch
        f = state.fetch = self.create_fetch(state)

        # make request and store response
        async with state.session.request(f.method, f.url, **f.kwargs) as resp:
            try:
                response_json = await resp.json()
            except Exception as exc:
                response_json = {}  # todo: logging

            state.response = Namespace(response_json)
            state.status = resp.status

    def validate_response(self, state):
        failures = []

        # status check
        status = self.request.status or HTTP_SUCCESS
        if state.status not in status:
            failures.append(ValidationResult(actual=state.status,
                                             expect=status,
                                             success=False))

        # validators check
        for validator in self.validate or []:
            result = validator.evaluate(state)
            if not result.success:
                failures.append(result)

        return failures


@related.immutable
class Case(object):
    name = related.StringField(required=False, default=None)
    steps = related.SequenceField(Step, default=[])
    scenarios = related.SequenceField(Namespace, default=[Namespace()])
    format = related.StringField(default="1.0")
    domain = related.StringField(required=False)
    tags = related.SequenceField(str, required=False)
    headers = related.ChildField(Namespace, required=False)
    file_path = related.StringField(default=None)
    is_valid = related.BooleanField(default=True)

    @classmethod
    def load(cls, file_path):
        return related.from_yaml(open(file_path), Case, file_path=file_path)

    @classmethod
    def loads(cls, content, file_path=None):
        try:
            return related.from_yaml(content, Case, file_path=file_path,
                                     object_pairs_hook=dict)
        except Exception as exc:
            print("Load Failed: %s: %s" % (file_path, exc))  # todo: logging
            return Case(file_path=file_path, is_valid=False)

    def is_active(self, included, excluded):
        has_steps = len(self.steps) > 0
        is_included = not included or overlap(included, self.tags)
        is_excluded = excluded and overlap(excluded, self.tags)
        return self.is_valid and has_steps and is_included and not is_excluded

    @property
    def dir_path(self):
        return os.path.dirname(self.file_path)


@related.immutable
class Result(object):
    case = related.ChildField(Case)
    scenario = related.ChildField(Namespace)
    success = related.BooleanField()
    fail_step = related.ChildField(Step, required=False)
    fail_validations = related.SequenceField(ValidationResult, required=False)
    running_time = related.FloatField(required=False)
    fetch = related.ChildField(Namespace, required=False)
    response = related.ChildField(Namespace, required=False)
    status = related.IntegerField(required=False)


@related.mutable
class Suite(object):
    # cli options
    domain = related.StringField(default="http://localhost:8000")
    directories = related.SequenceField(str, default=None)
    file_prefixes = related.SequenceField(str, default=None)
    extensions = related.SequenceField(str, default=["rigor"])
    tags_included = related.SequenceField(str, default=None)
    tags_excluded = related.SequenceField(str, default=None)
    concurrency = related.IntegerField(default=20)

    # collect
    queued = related.MappingField(Case, "file_path", default={})
    skipped = related.MappingField(Case, "file_path", default={})

    # execute
    passed = related.SequenceField(Result, default=[])
    failed = related.SequenceField(Result, default=[])

    def __attrs_post_init__(self):
        from . import collect
        collect(self)

    def get_case(self, path, filename=None):
        file_path = os.path.join(path, filename) if filename else path
        return self.queued.get(file_path) or self.skipped.get(file_path)

    def add_case(self, case):
        if case.is_active(self.tags_included, self.tags_excluded):
            self.queued.add(case)
        else:
            self.skipped.add(case)

    def add_result(self, result):
        if result.success:
            self.passed.append(result)
        else:
            self.failed.append(result)

    def execute(self):
        from . import execute
        return execute(self)


@related.mutable
class State(object):
    # unique id of the running scenario, available in namespace
    uuid = related.UUIDField()

    # handle to shared asynchronous, http client
    session = related.ChildField(aiohttp.ClientSession, required=False)

    # final success/failure of this scenario execution
    success = related.BooleanField(default=True)

    # scenario links (immutable)
    suite = related.ChildField(Suite, required=False)
    case = related.ChildField(Case, required=False)
    scenario = related.ChildField(Namespace, required=False)

    # namespace of extracted variables
    extract = related.ChildField(Namespace, required=False)

    # namespace of iterated variables
    iterate = related.ChildField(Namespace, required=False)

    # request but with template-values rendered
    fetch = related.ChildField(Namespace, required=False)

    # last request's response and http status code (e.g. 200)
    response = related.ChildField(Namespace, required=False)
    status = related.IntegerField(required=False)

    @property
    def namespace(self):
        # make iterate namespace top-level
        values = self.iterate.copy() if self.iterate else {}

        # make extract namespace top-level accessors (overrides iterate!)
        values.update(self.extract if self.extract else {})

        # add handles to namespaces (overrides extract and iterate!)
        values.update(dict(__uuid__=self.uuid,
                           scenario=self.scenario,
                           extract=self.extract,
                           response=self.response,
                           iterate=self.iterate))

        # add state-aware functions such as list_yaml (overrides all before!)
        values.update(Functions(self).function_map())

        return values


# utilities

def overlap(l1, l2):
    return set(l1 or []) & set(l2 or [])
