import json
import os
from itertools import product

import related

from . import Comparison, Method, Namespace, get_logger


class Iterator(Namespace):

    def iterate(self, namespace):
        if len(self):
            # determine method (product or zip)
            d = self.copy()
            method_key = d.pop("__method__", "zip")
            method = dict(zip=zip, product=product).get(method_key, zip)

            # evaluate values in namespace
            values = [self.render(value, namespace)
                      for value in d.values()]

            # *values => assumes all values are iterable and thus can zipped.
            for zipped_values in method(*values):

                # combine zipped values and construct a Namespace object
                yield Namespace(dict(zip(d.keys(), zipped_values)))
        else:
            yield Namespace()


@related.immutable
class Validator(object):
    actual = related.ChildField(object)
    expect = related.ChildField(object)
    compare = related.ChildField(Comparison, default=Comparison.EQUALS)


@related.immutable
class Requestor(object):
    path = related.StringField()
    method = related.ChildField(Method, default=Method.GET)
    domain = related.StringField(required=False)
    headers = related.ChildField(Namespace, required=False)
    params = related.ChildField(Namespace, required=False)
    data = related.ChildField(object, required=False)
    status = related.SequenceField(int, required=False)

    def get_params(self, namespace):
        dd = self.params.evaluate(namespace) if self.params else {}

        params = []
        for key, value in dd.items():
            if isinstance(value, (tuple, list, set)):
                for item in value:
                    params.append((key, str(item)))
            else:
                params.append((key, str(value)))

        return params

    def get_data(self, namespace):
        # flatten data to a string that will include ${expressions} to render
        ds = self.data if isinstance(self.data, str) else json.dumps(self.data)

        # render data string (ds) template
        rendered = Namespace.render(ds, namespace)

        # dump rendered value to a json string, if not already a string
        return rendered if isinstance(rendered, str) else json.dumps(rendered)


@related.immutable
class Step(object):
    description = related.StringField()
    request = related.ChildField(Requestor)
    extract = related.ChildField(Namespace, default=Namespace())
    iterate = related.ChildField(Iterator, default=Iterator())
    validate = related.SequenceField(Validator, required=False)
    name = related.StringField(required=False, default=None)


@related.immutable
class Case(object):
    scenarios = related.SequenceField(Namespace)
    name = related.StringField(required=False, default=None)
    steps = related.SequenceField(Step, default=[])
    format = related.StringField(default="1.0")
    domain = related.StringField(required=False)
    tags = related.SequenceField(str, required=False)
    headers = related.ChildField(Namespace, required=False)
    file_path = related.StringField(default=None)
    is_valid = related.BooleanField(default=True)
    uuid = related.UUIDField()

    @classmethod
    def load(cls, file_path):
        return related.from_yaml(open(file_path), Case, file_path=file_path)

    @classmethod
    def prep_scenarios(cls, original, dir_path):
        updated = []
        counter = 1
        for scenario in original or [{}]:
            if isinstance(scenario, str):
                scenario_file_path = os.path.join(dir_path, scenario)
                scenario = related.from_yaml(open(scenario_file_path),
                                             object_pairs_hook=dict)

            scenario.setdefault("__name__", "Scenario #%s" % counter)
            counter += 1
            updated.append(scenario)

        return updated

    @classmethod
    def loads(cls, content, file_path=None):
        try:
            as_dict = related.from_yaml(content, file_path=file_path,
                                        object_pairs_hook=dict)

            scenarios = as_dict.get("scenarios", [])
            dir_path = os.path.dirname(file_path)
            as_dict['scenarios'] = cls.prep_scenarios(scenarios, dir_path)

            return related.to_model(Case, as_dict)

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

    def __attrs_post_init__(self):
        from . import collect
        collect(self)

    def get_case(self, path, filename=None):
        file_path = os.path.join(path, filename) if filename else path
        return self.queued.get(file_path) or self.skipped.get(file_path)

    def add_case(self, case):
        if case.is_active(self.tags_included, self.tags_excluded):
            self.queued.add(case)
            get_logger().debug("case queued", case=case.file_path)
        else:
            self.skipped.add(case)
            get_logger().debug("case skipped", case=case.file_path)

    def execute(self):
        from . import execute
        return execute(self)


# utilities

def overlap(l1, l2):
    return set(l1 or []) & set(l2 or [])
