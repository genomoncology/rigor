import os
import io
import json

from itertools import product

import related

from . import Method, Namespace, Profile, get_logger, utils


class Iterator(Namespace):

    def __init__(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], str) and not kwargs:
            data = utils.parse_into_dicts_of_rows(args[0])
            super(Iterator, self).__init__(**data)
        else:
            super(Iterator, self).__init__(*args, **kwargs)

    def iterate(self, namespace):
        if len(self):
            # determine method (product or zip)
            d = self.copy()
            method_key = d.pop("__method__", "zip")
            method = dict(zip=zip, product=product).get(method_key, zip)

            # evaluate values in namespace
            values = [self.render(value, namespace) for value in d.values()]

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
    compare = related.StringField(default="equals")


@related.immutable
class Requestor(object):
    path = related.StringField()
    method = related.ChildField(Method, default=Method.GET)
    host = related.StringField(required=False)
    headers = related.ChildField(Namespace, required=False)
    params = related.ChildField(Namespace, required=False)
    data = related.ChildField(object, required=False)
    form = related.ChildField(Namespace, required=False)
    files = related.ChildField(Namespace, required=False)
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

    def get_form(self, namespace):
        return self.form.evaluate(namespace) if self.form else {}

    def get_files(self, dir_path, namespace):
        files = self.files.evaluate(namespace) if self.files else {}
        files = {k: open(os.path.join(dir_path, v), "rb")
                 for k, v in files.items()}
        return files

    def get_body(self, namespace):
        get_logger().debug("enter get_body", data_type=type(self.data),
                           data=self.data)

        body = None
        if isinstance(self.data, str):
            try:
                # if valid JSON, convert to dictionary and evaluate
                body = Namespace(json.loads(self.data)).evaluate(namespace)

            except json.decoder.JSONDecodeError:
                # else, treat like a string that might contain a variable.
                body = Namespace.render(self.data, namespace)
                if isinstance(body, Namespace):
                    body = body.evaluate(namespace)

        elif isinstance(self.data, dict):
            body = Namespace(self.data).evaluate(namespace)

        get_logger().debug("render get_body", body_type=type(body), body=body)

        return body

    def get_data(self, namespace):
        """ Returns body or form and a flag indicating if a form or not."""
        body = self.get_body(namespace) if self.data else None
        form = self.get_form(namespace) if self.form else None
        return (body, False) if body else (form, True)


@related.immutable
class Step(object):
    description = related.StringField()
    request = related.ChildField(Requestor)
    extract = related.ChildField(Namespace, default=Namespace())
    iterate = related.ChildField(Iterator, default=Iterator())
    validate = related.SequenceField(Validator, required=False)
    condition = related.BooleanField(required=False, default=None)
    transform = related.StringField(required=False, default=None)
    name = related.StringField(required=False, default=None)
    sleep = related.FloatField(required=False, default=0.01)


@related.immutable
class Case(object):
    scenarios = related.SequenceField(Namespace)
    name = related.StringField(required=False, default=None)
    steps = related.SequenceField(Step, default=[])
    format = related.StringField(default="1.0")
    host = related.StringField(required=False)
    tags = related.SequenceField(str, required=False)
    headers = related.ChildField(Namespace, required=False)
    file_path = related.StringField(default=None)
    is_valid = related.BooleanField(default=True)
    uuid = related.UUIDField()

    @classmethod
    def prep_scenarios(cls, original, dir_path):
        updated = []
        counter = 1

        if isinstance(original, str):
            original = utils.parse_into_rows_of_dicts(original)

        for scenario in original or [{}]:
            if isinstance(scenario, str):
                scenario_file_path = os.path.join(dir_path, scenario)
                scenario = related.from_yaml(open(scenario_file_path),
                                             object_pairs_hook=dict)

            name = scenario.get("__name__") or "Scenario #%s" % counter
            scenario["__name__"] = name
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

        except Exception as e:
            # raise e
            get_logger().error("Failed to Load Case", file_path=file_path,
                               error=str(e))
            return Case(file_path=file_path, is_valid=False, scenarios=[])

    def is_active(self, included, excluded):
        has_steps = len(self.steps) > 0
        is_included = not included or utils.overlap(included, self.tags)
        is_excluded = excluded and utils.overlap(excluded, self.tags)
        return self.is_valid and has_steps and is_included and not is_excluded

    @property
    def dir_path(self):
        return os.path.dirname(self.file_path)


@related.mutable
class Suite(Profile):
    paths = related.SequenceField(str, default=None)
    queued = related.MappingField(Case, "file_path", default={})
    skipped = related.MappingField(Case, "file_path", default={})

    def __attrs_post_init__(self):
        from . import collect
        collect(self)
        get_logger().debug("suite constructed",
                           host=self.host,
                           paths=self.paths,
                           prefixes=self.prefixes,
                           extensions=self.extensions,
                           includes=self.includes,
                           excludes=self.excludes,
                           concurrency=self.concurrency)

    def get_case(self, path, filename=None):
        file_path = os.path.join(path, filename) if filename else path
        return self.queued.get(file_path) or self.skipped.get(file_path)

    def add_case(self, case):
        if case.is_active(self.includes, self.excludes):
            self.queued.add(case)
            get_logger().debug("case queued", case=case.file_path)
        else:
            self.skipped.add(case)
            get_logger().debug("case skipped", case=case.file_path)

    @classmethod
    def create(cls, paths, profile, **cli):
        # start kwargs using profile
        kwargs = profile.as_dict()

        # remove none and empty lists from cli keyword args (0/False is ok)
        cli = dict([(k, v) for k, v in cli.items() if v not in (None, [], ())])

        # update kwargs with cli (cli takes higher precedence)
        kwargs.update(cli)

        # construct Suite
        return cls(paths=paths, **kwargs)


# dispatch

@related.to_dict.register(io.BufferedReader)
def _(obj, **kwargs):
    return "<file: %s>" % obj.name
