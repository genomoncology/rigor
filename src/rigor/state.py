import related
import jmespath
import os

from . import Case, Namespace, Step, Suite, Validator, Timer, Session
from . import enums, get_logger, const, log_with_success, utils

# https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#2xx_Success
HTTP_SUCCESS = [200, 201, 202, 203, 204, 205, 206, 207, 208, 226]


@related.immutable
class ValidationResult(object):
    actual = related.ChildField(object)
    expect = related.ChildField(object)
    success = related.BooleanField()
    validator = related.ChildField(Validator)


@related.immutable
class Fetch(object):
    url = related.StringField()
    method = related.StringField()
    kwargs = related.ChildField(dict)
    is_form = related.BooleanField()

    def get_kwargs(self, is_aiohttp):
        kw = self.kwargs.copy()
        data = kw.get("data", None)

        # aiohttp is different from requests in handling files
        # http://aiohttp.readthedocs.io/en/stable/client.html
        # http://docs.python-requests.org/en/master/user/quickstart
        files = kw.pop("files", None) if is_aiohttp else None

        if self.is_form:
            if isinstance(data, dict) and isinstance(files, dict):
                data.update(files)
        else:
            kw['data'] = related.to_json(data)

        # unlimited timeout if not specified
        kw.setdefault("timeout", None)

        # add verify = False for requests
        if not is_aiohttp:
            kw['verify'] = False

        return kw


@related.mutable
class StepResult(object):
    step = related.ChildField(Step)
    success = related.BooleanField(default=True)
    fetch = related.ChildField(Fetch, required=False)
    response = related.ChildField(object, required=False)
    transform = related.ChildField(object, required=False)
    extract = related.ChildField(Namespace, required=False)
    status = related.IntegerField(required=False)
    validations = related.SequenceField(ValidationResult, required=False)
    duration = related.IntegerField(required=False)

    @property
    def failed_validations(self):
        return [v for v in self.validations if not v.success]


@related.mutable
class ScenarioResult(object):
    uuid = related.UUIDField()
    case = related.ChildField(Case, required=None)
    scenario = related.ChildField(Namespace, required=None)
    success = related.BooleanField(default=True)
    step_results = related.SequenceField(StepResult, default=[])
    suite = related.ChildField(Suite, required=False)


@related.immutable
class CaseResult(object):
    suite = related.ChildField(Suite)
    case = related.ChildField(Case)
    passed = related.SequenceField(ScenarioResult, default=[])
    failed = related.SequenceField(ScenarioResult, default=[])

    @property
    def success(self):
        return bool(self.passed and not self.failed)


@related.immutable
class SuiteResult(object):
    suite = related.ChildField(Suite)
    passed = related.SequenceField(CaseResult, default=[])
    failed = related.SequenceField(CaseResult, default=[])

    @property
    def success(self):
        return bool(self.passed and not self.failed)

    @classmethod
    def create(cls, suite, scenario_results):
        cache = {}

        for result in scenario_results:
            case_result = cache.setdefault(
                result.case.uuid,
                CaseResult(suite=suite, case=result.case)
            )

            sink = case_result.passed if result.success else case_result.failed
            sink.append(result)

        passed, failed = [], []
        for case_result in cache.values():
            sink = passed if case_result.success else failed
            sink.append(case_result)

        return cls(suite=suite, passed=passed, failed=failed)


@related.mutable
class State(ScenarioResult, Timer):
    session = related.ChildField(Session, required=False)
    globals = related.ChildField(Namespace, default=Namespace())
    extract = related.ChildField(Namespace, default=Namespace())
    iterate = related.ChildField(Namespace, default=Namespace())
    response = related.ChildField(Namespace, default=Namespace())
    transform = related.ChildField(Namespace, default=Namespace())

    def __attrs_post_init__(self):
        if self.suite is None:
            self.suite = self.session.suite if self.session else None

        globals = self.suite.globals if self.suite else {}
        globals = globals or {}
        self.globals = Namespace(globals)

        if self.scenario:
            self.scenario = self.scenario.evaluate(self.namespace)
        else:
            self.scenario = Namespace({})

    @property
    def namespace(self):
        # make globals namespace top-level
        values = self.globals.copy()

        # make scenario namespace top-level accessors (overrides globals!)
        values.update(self.scenario if self.scenario else {})

        # make iterate namespace top-level accessors (overrides scenario!)
        values.update(self.iterate if self.iterate else {})

        # make extract namespace top-level accessors (overrides iterate!)
        values.update(self.extract if self.extract else {})

        # add handles to namespaces (overrides scenario, extract and iterate!)
        values.update(dict(__uuid__=self.uuid,
                           globals=self.globals,
                           scenario=self.scenario,
                           transform=self.transform,
                           extract=self.extract,
                           response=self.response,
                           iterate=self.iterate,
                           env=os.environ))

        return values

    def should_run_step(self, step):
        condition = step.condition  # todo: evaluation here
        return self.success if condition is None else condition

    def do_transform(self, step):
        # make request and store response
        if step.transform:
            transform = Namespace.render(step.transform, self.namespace)
            output = jmespath.search(transform, self.response)
            get_logger().debug("transform",
                               response=self.response,
                               original=self.transform,
                               input=transform,
                               output=transform)
            return output

    def do_extract(self, step):
        existing = related.to_dict(self.extract) if self.extract else {}
        return step.extract.evaluate(self.namespace, existing)

    def do_validate(self, step, status):
        results = []

        # status check
        expected_status = step.request.status or HTTP_SUCCESS
        validator = Validator(actual="${status}",
                              expect=expected_status,
                              compare=enums.Comparison.IN)
        results.append(ValidationResult(actual=status,
                                        expect=expected_status,
                                        success=status in expected_status,
                                        validator=validator))

        # validators check
        for validator in step.validate or []:
            results.append(self.check_validation(validator))

        # determine success and return
        success = True
        for validator in results:
            kw = dict(validator=validator, step=step)
            log_with_success("validator", validator.success, **kw)
            success = success and validator.success

        return results, success

    def is_feature_table(self, s):
        return isinstance(s, str) and s.strip().startswith("|") and "\n" in s

    def check_validation(self, validator):
        actual, expect = validator.actual, validator.expect

        if self.is_feature_table(expect):
            expect = utils.parse_into_rows_of_dicts(expect)

        actual = Namespace.render(actual, self.namespace)
        expect = Namespace.render(expect, self.namespace)

        compare = Namespace.render(validator.compare, self.namespace)
        compare = related.to_model(enums.Comparison, compare)
        success = compare.evaluate(actual, expect)

        return ValidationResult(actual=actual, expect=expect, success=success,
                                validator=validator)

    def add_step(self, step_result):
        self.step_results.append(step_result)
        self.success = self.success and step_result.success

    def result(self):
        log_with_success("scenario", self.success,
                         feature=self.case.name,
                         scenario=self.scenario.__name__,
                         file_path=self.case.file_path,
                         num_steps=len(self.step_results),
                         timer=self.get_duration())

        return ScenarioResult(
            uuid=self.uuid,
            suite=self.suite,
            case=self.case,
            scenario=self.scenario,
            success=self.success,
            step_results=self.step_results
        )


@related.mutable
class StepState(StepResult, Timer):
    state = related.ChildField(State, required=False)

    @property
    def namespace(self):
        return self.state.namespace

    @property
    def request(self):
        return self.step.request

    @property
    def suite(self):
        return self.state.suite

    @property
    def case(self):
        return self.state.case

    @property
    def host(self):
        # url host (request > case > cli > rigor.yml > localhost:8000)
        return self.request.host or self.case.host or self.suite.host

    @property
    def url(self):
        path = Namespace.render(self.request.path, self.namespace)
        return "%s/%s" % (self.host, path)

    @property
    def method(self):
        return self.request.method.value.lower()

    def get_data(self):
        return self.request.get_data(self.namespace)

    def get_files(self):
        return self.request.get_files(self.case.dir_path, self.namespace)

    def get_headers(self, content_type=None):
        headers = {}

        # right now
        if content_type:
            headers[const.CONTENT_TYPE] = content_type

        headers.update(related.to_dict(self.suite.headers) or {})

        if self.case:
            headers.update(related.to_dict(self.case.headers) or {})

        headers.update(related.to_dict(self.request.headers) or {})

        return Namespace(headers).evaluate(self.namespace)

    def get_fetch(self):
        if self.fetch is None:
            data, is_form = self.get_data()

            # libraries (requests, aiohttp) take care of CT for forms
            content_type = None if is_form else "application/json"
            headers = self.get_headers(content_type)

            params = self.request.get_params(self.namespace)
            files = self.get_files()
            kw = dict(headers=headers, data=data, params=params, files=files)
            self.fetch = Fetch(method=self.method, url=self.url, kwargs=kw,
                               is_form=is_form)

        return self.fetch

    def process_response(self, response, status):
        state = self.state

        # capture response
        self.response = state.response = response
        self.status = status

        # transform response
        self.transform = state.transform = state.do_transform(self.step)

        # extract response
        self.extract = state.extract = state.do_extract(self.step)

        # validate response
        self.validations, self.success = state.do_validate(self.step, status)

        # track overall success
        state.success = state.success and self.success

    def result(self):
        return StepResult(
            step=self.step,
            success=self.success,
            fetch=self.fetch,
            response=self.response,
            transform=self.transform,
            extract=self.extract,
            status=self.status,
            validations=self.validations,
            duration=self.get_duration(),
        )
