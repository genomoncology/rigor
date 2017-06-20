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
        value = jmespath.search(name, self)
        return value

    def evaluate(self, state, existing=None):
        values = existing or {}

        for key, value in self.items():
            values[key] = self.render_value(value, state)

        return Namespace(values)

    @classmethod
    def render_value(cls, value, state):
        template = Template(value)
        rendered = template.render(**state.namespace)
        try:
            value = ast.literal_eval(rendered)
        except:
            value = rendered

        return value

    @classmethod
    def render_expression(cls, expression, state):
        # 1 - resolve any inline ${variables} with state values
        resolved = cls.render_value(expression, state)

        # 2 - evaluate full expression by wrapping entire string
        return cls.render_value("${%s}" % resolved, state)


class Extractor(Namespace):

    def evaluate(self, state, existing=None):
        existing = related.to_dict(state.extract) if state.extract else {}
        return super(Extractor, self).evaluate(state, existing)

    @classmethod
    def render_value(cls, value, state):
        value = value if value.startswith("${") else "${%s}" % value
        return super(Extractor, cls).render_value(value, state)


class Validator(str):

    def is_valid(self, state):
        return Namespace.render_expression(self, state)


@related.immutable
class Request(object):
    path = related.StringField()
    method = related.ChildField(Method, default=Method.GET)
    domain = related.StringField(required=False)
    headers = related.ChildField(Namespace, required=False)
    params = related.ChildField(Namespace, required=False)
    body = related.ChildField(Namespace, required=False)

    def get_url(self, suite, case):
        domain = self.domain or case.domain or suite.domain
        return "%s/%s" % (domain, self.path)

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
        valid_statuses = [200]

        # construct request
        method = getattr(state.session, self.request.method.value.lower())
        url = self.request.get_url(state.suite, state.case)
        headers = self.request.get_headers(state.case)
        params = self.request.get_params(state)

        # make request and store response
        async with method(url, headers=headers, params=params) as response:
            json = await response.json()
            state.response = Namespace(json)
            state.success = response.status in valid_statuses

    def validate_response(self, state):
        failures = []

        for validator in self.validate or []:
            is_valid = validator.is_valid(state)

            if not is_valid:
                failures.append(validator)

        return failures


@related.immutable
class Case(object):
    name = related.StringField(default=None)
    steps = related.SequenceField(Step, default=[])
    scenarios = related.SequenceField(Namespace, default=[Namespace()])
    format = related.StringField(default="1.0")
    domain = related.StringField(required=False)
    tags = related.SequenceField(str, required=False)
    headers = related.ChildField(Namespace, required=False)
    file_path = related.StringField(default=None)

    @classmethod
    def load(cls, file_path):
        return related.from_yaml(open(file_path), Case, file_path=file_path)

    @classmethod
    def loads(cls, content, file_path=None):
        return related.from_yaml(content, Case, file_path=file_path)

    def is_active(self, included, excluded):
        has_steps = len(self.steps) > 0
        is_included = not included or overlap(included, self.tags)
        is_excluded = excluded and overlap(excluded, self.tags)
        return has_steps and is_included and not is_excluded


@related.immutable
class Result(object):
    case = related.ChildField(Case)
    scenario = related.ChildField(Namespace)
    success = related.BooleanField()
    failing_step = related.ChildField(Step, required=False)
    error_message = related.StringField(required=False)
    running_time = related.FloatField(required=False)


@related.mutable
class Suite(object):
    domain = related.StringField(str)
    directories = related.SequenceField(str, default=None)
    file_prefixes = related.SequenceField(str, default=None)
    extensions = related.SequenceField(str, default=["yml", "yaml"])
    tags_included = related.SequenceField(str, default=None)
    tags_excluded = related.SequenceField(str, default=None)
    queued = related.MappingField(Case, "file_path", default={})
    skipped = related.MappingField(Case, "file_path", default={})
    passed = related.SequenceField(Result, default=[])
    failed = related.SequenceField(Result, default=[])
    concurrency = related.IntegerField(default=10)

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
    session = related.ChildField(aiohttp.ClientSession, required=False)
    success = related.BooleanField(default=True)

    suite = related.ChildField(Suite, required=False)
    case = related.ChildField(Case, required=False)
    scenario = related.ChildField(Namespace, required=False)
    extract = related.ChildField(Namespace, required=False)
    response = related.ChildField(Namespace, required=False)

    @property
    def namespace(self):
        return dict(
            scenario=self.scenario,
            extract=self.extract,
            response=self.response,
        )


# utilities

def overlap(l1, l2):
    return set(l1 or []) & set(l2 or [])
