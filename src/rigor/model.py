import enum
import os

import related

from . import collect


# enums

@enum.unique
class Status(enum.Enum):
    ACTIVE = "ACTIVE"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"


@enum.unique
class Method(enum.Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


# simple objects

class Headers(related.ImmutableDict):
    pass


class Params(related.ImmutableDict):
    pass


class Body(related.ImmutableDict):
    pass


class Validator(str):
    pass


class Extractor(related.ImmutableDict):
    pass


class Scenario(related.ImmutableDict):
    pass


# nested configuration objects

@related.immutable
class Request(object):
    url = related.StringField()
    method = related.ChildField(Method, default=Method.POST)
    headers = related.ChildField(Headers, required=False)
    params = related.ChildField(Params, required=False)
    body = related.ChildField(Body, required=False)


@related.immutable
class Step(object):
    description = related.StringField()
    request = related.ChildField(Request)
    extract = related.ChildField(Extractor, required=False)
    validate = related.SequenceField(Validator, required=False)


@related.immutable
class Case(object):
    name = related.StringField(default=None)
    steps = related.SequenceField(Step, default=[])
    format = related.StringField(default="1.0")
    domain = related.StringField(required=False)
    tags = related.SequenceField(str, required=False)
    headers = related.ChildField(Headers, required=False)
    scenarios = related.SequenceField(Scenario, required=False)
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


@related.mutable
class Suite(object):
    domain = related.StringField(str)
    directories = related.SequenceField(str, default=None)
    file_prefixes = related.SequenceField(str, default=None)
    extensions = related.SequenceField(str, default=["yml", "yaml"])
    tags_included = related.SequenceField(str, default=None)
    tags_excluded = related.SequenceField(str, default=None)
    active = related.MappingField(Case, "file_path", default={})
    skipped = related.MappingField(Case, "file_path", default={})

    def __attrs_post_init__(self):
        collect(self)

    def get_active_case(self, path, filename=None):
        file_path = os.path.join(path, filename) if filename else path
        return self.active.get(file_path)

    def add_case(self, case):
        if case.is_active(self.tags_included, self.tags_excluded):
            self.active.add(case)
        else:
            self.skipped.add(case)


# utilities

def overlap(l1, l2):
    return set(l1 or []) & set(l2 or [])
