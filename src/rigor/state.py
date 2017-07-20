import asyncio
import time

import aiohttp
import related

from . import (Case, Namespace, Step, Suite, Functions, Validator, Comparison, enums,
               get_logger)

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


@related.immutable
class StepResult(object):
    step = related.ChildField(Step)
    success = related.BooleanField()
    fetch = related.ChildField(Fetch, required=False)
    response = related.ChildField(Namespace, required=False)
    status = related.IntegerField(required=False)
    validations = related.SequenceField(ValidationResult, required=False)


@related.immutable
class ScenarioResult(object):
    suite = related.ChildField(Suite)
    case = related.ChildField(Case)
    scenario = related.ChildField(Namespace)
    success = related.BooleanField()
    uuid = related.UUIDField()
    step_results = related.SequenceField(StepResult, default=[])
    running_time = related.FloatField(required=False)


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
        case_results = {}

        for result in scenario_results:
            # todo: handle exceptions...
            case_result = case_results.setdefault(result.case.uuid,
                                                  CaseResult(suite=suite,
                                                             case=result.case))

            sink = case_result.passed if result.success else case_result.failed
            sink.append(result)

        passed, failed = [], []
        for case_result in case_results.values():
            sink = passed if case_result.success else failed
            sink.append(case_result)

        return cls(suite=suite, passed=passed, failed=failed)


@related.mutable
class Runner(object):
    uuid = related.UUIDField()
    session = related.ChildField(aiohttp.ClientSession, required=False)
    suite = related.ChildField(Suite, required=False)
    case = related.ChildField(Case, required=False)

    scenario = related.ChildField(Namespace, default=Namespace())
    extract = related.ChildField(Namespace, default=Namespace())
    iterate = related.ChildField(Namespace, default=Namespace())
    response = related.ChildField(Namespace, default=Namespace())

    def __attrs_post_init__(self):
        self.scenario = self.scenario.evaluate(self.namespace)

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

    async def do_run(self):
        success = True
        start_time = time.time()
        step_results = []
        f = []

        # iterate steps
        async for step_result in self.iter_steps():
            step_results.append(step_result)
            success = step_result.success
            if not success:
                fail_step = step_result
                for val in fail_step.validations:
                    f.append(val)
                break

        running_time = time.time() - start_time

        if not success:
            # error logging - display failed scenario
            get_logger().error("scenario failed", Feature=self.case.name, Scenario=self.scenario.__name__)

        get_logger().debug("scenario complete", case=self.case,
                           scenario=self.scenario, success=success,
                           running_time=running_time)

        return ScenarioResult(
            uuid=self.uuid,
            suite=self.suite,
            case=self.case,
            scenario=self.scenario,
            success=success,
            step_results=step_results,
            running_time=running_time,
        )

    async def iter_steps(self):
        for step in self.case.steps:
            await asyncio.sleep(2.0)  # todo: replace...

            for self.iterate in step.iterate.iterate(self.namespace):
                # create and do fetch
                fetch = self.create_fetch(step.request)
                self.response, status = await self.do_fetch(fetch)

                # extract response
                self.extract = self.do_extract(step)

                # validate response
                validations, success = self.do_validate(step, status)

                # add step result
                yield StepResult(step=step, fetch=fetch,
                                 response=self.response, status=status,
                                 validations=validations, success=success)

    def create_fetch(self, request):
        namespace = self.namespace

        # construct url
        domain = request.domain or self.case.domain or self.suite.domain
        path = Namespace.render(request.path, namespace)
        url = "%s/%s" % (domain, path)

        # construct method
        method = request.method.value.lower()

        # headers
        headers = {"content-type": "application/json"}
        headers.update(related.to_dict(self.case.headers) or {})
        headers.update(related.to_dict(request.headers) or {})
        headers = Namespace(headers)

        # kwargs
        kwargs = dict(headers=headers, timeout=None,
                      data=request.get_data(namespace),
                      params=request.get_params(namespace))

        return Fetch(method=method, url=url, kwargs=kwargs)

    async def do_fetch(self, fetch):
        # make request and store response
        get_logger().debug("fetch", method=fetch.method, url=fetch.url,
                           kwargs=fetch.kwargs)

        async with self.session.request(fetch.method, fetch.url,
                                        **fetch.kwargs) as context:
            try:
                response = Namespace(await context.json())
            except:
                response = Namespace()

            status = context.status

            get_logger().debug("response", method=fetch.method, url=fetch.url,
                               kwargs=fetch.kwargs, status=status)

            return response, status

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
        success = all([result.success for result in results])

        # debug logging - scenario uuid and all validations
        vals = []

        # figure out how to get these all into one list?
        for val in results:
            if val is not None:
                vals.append(val)
        get_logger().debug("Scenario Validations", Scenario_UUID=self.uuid, Validations=vals)

        # error logging - only failed validations returned
        fail_vals = []
        for val in results:
            if val.success is False and val is not None:
                fail_vals.append(val)
        if fail_vals != []:
            get_logger().error("Validator(s) failed", Fail_Validations=fail_vals)

        return results, success

    def check_validation(self, validator):
        actual = Namespace.render(validator.actual, self.namespace)
        expect = Namespace.render(validator.expect, self.namespace)
        success = validator.compare.evaluate(actual, expect)
        return ValidationResult(actual=actual, expect=expect, success=success,
                                validator=validator)
