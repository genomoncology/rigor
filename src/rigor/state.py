import related
import jmespath
import os

from . import Case, Namespace, Step, Suite, Validator, Timer, Session
from . import enums, get_logger, const, log_with_success

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


@related.mutable
class StepResult(object):
    step = related.ChildField(Step)
    success = related.BooleanField()
    fetch = related.ChildField(Fetch, required=False)
    response = related.ChildField(Namespace, required=False)
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
        self.suite = self.session.suite if self.session else None
        self.globals = Namespace(self.suite.globals if self.suite else {})
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

    def create_fetch(self, request):
        namespace = self.namespace

        # url host (request > case > cli > rigor.yml > localhost:8000)
        host = request.host or self.case.host or self.suite.host

        # url path
        path = Namespace.render(request.path, namespace)
        url = "%s/%s" % (host, path)

        # construct method
        method = request.method.value.lower()

        # get data
        data = request.get_data(self.case.dir_path, namespace)

        # headers
        headers = {}

        if isinstance(data, str):
            headers[const.CONTENT_TYPE] = "application/json"

        headers.update(related.to_dict(self.suite.headers) or {})
        headers.update(related.to_dict(self.case.headers) or {})
        headers.update(related.to_dict(request.headers) or {})
        headers = Namespace(headers).evaluate(namespace)

        # kwargs
        kwargs = dict(headers=headers, timeout=None, data=data,
                      params=request.get_params(namespace))

        return Fetch(method=method, url=url, kwargs=kwargs)

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

    def check_validation(self, validator):
        actual = Namespace.render(validator.actual, self.namespace)
        expect = Namespace.render(validator.expect, self.namespace)
        success = validator.compare.evaluate(actual, expect)
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
                         timer=self.duration)

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
            duration=self.duration
        )
