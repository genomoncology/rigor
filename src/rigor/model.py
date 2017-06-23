import enum
import os
import aiohttp
import jmespath
import ast
import json

from mako.template import Template

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
    def render_value(cls, value, state, do_eval=True):
        if isinstance(value, str):
            template = Template(value)

            try:
                rendered = template.render(**state.namespace)
            except:
                rendered = value

            try:
                value = ast.literal_eval(rendered) if do_eval else rendered
            except:
                value = rendered

        if isinstance(value, dict) and not isinstance(value, Namespace):
            value = Namespace(value)

        return value


class Extractor(Namespace):

    def evaluate(self, state, existing=None):
        existing = related.to_dict(state.extract) if state.extract else {}
        return super(Extractor, self).evaluate(state, existing)

    @classmethod
    def render_value(cls, value, state):
        value = value if value.startswith("${") else "${%s}" % value
        return super(Extractor, cls).render_value(value, state)


@related.immutable
class ValidationResult(object):
    actual = related.ChildField(object)
    expect = related.ChildField(object)
    success = related.BooleanField()


@related.immutable
class Validator(object):
    expect = related.ChildField(object)
    actual = related.ChildField(object)

    def evaluate(self, state):
        actual = Namespace.render_value(self.actual, state)
        expect = Namespace.render_value(self.expect, state)
        success = actual == expect

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
    data = related.ChildField(Namespace, required=False)
    status = related.SequenceField(int, required=False)

    def get_url(self, state):
        domain = self.domain or state.case.domain or state.suite.domain
        path = Namespace.render_value(self.path, state)
        return "%s/%s" % (domain, path)

    def get_headers(self, case):
        case_headers = related.to_dict(case.headers) or {}
        case_headers.update(related.to_dict(self.headers) or {})
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
        # flatten to a string that will include ${expressions} to render
        data_string = json.dumps(self.data)

        # do_eval = False because this is one case we want to keep a string
        return Namespace.render_value(data_string, state, do_eval=False)


@related.immutable
class Step(object):
    description = related.StringField()
    request = related.ChildField(Request)
    extract = related.ChildField(Extractor, default=Namespace())
    validate = related.SequenceField(Validator, required=False)

    async def fetch(self, state):

        # construct request
        method = self.request.method.value.lower()
        url = self.request.get_url(state)
        kwargs = dict(headers=self.request.get_headers(state.case))
        if self.request.data:
            kwargs['data'] = self.request.get_data(state)
        else:
            kwargs['params'] = self.request.get_params(state)

        # make request and store response
        async with state.session.request(method, url, **kwargs) as response:
            try:
                response_json = await response.json()
            except Exception as exc:
                response_json = {}  # todo: logging

            state.response = Namespace(response_json)
            state.status = response.status

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


@related.immutable
class Result(object):
    case = related.ChildField(Case)
    scenario = related.ChildField(Namespace)
    success = related.BooleanField()
    fail_step = related.ChildField(Step, required=False)
    fail_validations = related.SequenceField(ValidationResult, required=False)
    running_time = related.FloatField(required=False)
    response = related.ChildField(Namespace, required=False)
    status = related.IntegerField(required=False)


@related.mutable
class Suite(object):
    # cli options
    domain = related.StringField(str)
    directories = related.SequenceField(str, default=None)
    file_prefixes = related.SequenceField(str, default=None)
    extensions = related.SequenceField(str, default=["yml", "yaml"])
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

    # last request's response and http status code (e.g. 200)
    response = related.ChildField(Namespace, required=False)
    status = related.IntegerField(required=False)

    @property
    def namespace(self):
        values = self.extract.copy() if self.extract else {}
        values.update(dict(__uuid__=self.uuid,
                           scenario=self.scenario,
                           extract=self.extract,
                           response=self.response))
        return values


# utilities

def overlap(l1, l2):
    return set(l1 or []) & set(l2 or [])
