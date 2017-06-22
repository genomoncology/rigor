import enum
import os
import aiohttp
import jmespath
import ast

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
    def render_value(cls, value, state):
        if isinstance(value, str):
            template = Template(value)

            try:
                rendered = template.render(**state.namespace)
            except:
                rendered = value

            try:
                value = ast.literal_eval(rendered)
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
    body = related.ChildField(Namespace, required=False)

    def get_url(self, state):
        domain = self.domain or state.case.domain or state.suite.domain
        path = Namespace.render_value(self.path, state)
        return "%s/%s" % (domain, path)

    def get_headers(self, case):
        case_headers = related.to_dict(case.headers) or {}
        case_headers.update(related.to_dict(self.headers) or {})
        return Namespace(case_headers)

    def get_params(self, state):
        return self.params.evaluate(state) if self.params else Namespace()


@related.immutable
class Step(object):
    description = related.StringField()
    request = related.ChildField(Request)
    extract = related.ChildField(Extractor, default=Namespace())
    validate = related.SequenceField(Validator, required=False)

    async def fetch(self, state):

        # construct request
        method = getattr(state.session, self.request.method.value.lower())
        url = self.request.get_url(state)
        headers = self.request.get_headers(state.case)
        params = self.request.get_params(state)

        # make request and store response
        async with method(url, headers=headers, params=params) as response:
            try:
                json = await response.json()
            except Exception as exc:
                json = {}  # todo: logging

            json['http_status_code'] = response.status
            state.response = Namespace(json)

    def validate_response(self, state):
        failures = []

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


@related.mutable
class Suite(object):
    # cli options
    domain = related.StringField(str)
    directories = related.SequenceField(str, default=None)
    file_prefixes = related.SequenceField(str, default=None)
    extensions = related.SequenceField(str, default=["yml", "yaml"])
    tags_included = related.SequenceField(str, default=None)
    tags_excluded = related.SequenceField(str, default=None)
    concurrency = related.IntegerField(default=50)

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

    # last request's response
    response = related.ChildField(Namespace, required=False)

    @property
    def namespace(self):
        values = self.extract.copy() if self.extract else {}
        values.update(dict(scenario=self.scenario,
                           extract=self.extract,
                           response=self.response))
        return values


# utilities

def overlap(l1, l2):
    return set(l1 or []) & set(l2 or [])
