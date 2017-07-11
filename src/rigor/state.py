import asyncio
import time

import aiohttp
import related

from . import Case, Namespace, Step, Suite, Validator, Functions

# https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#2xx_Success
HTTP_SUCCESS = [200, 201, 202, 203, 204, 205, 206, 207, 208, 226]


@related.immutable
class ValidationResult(object):
    actual = related.ChildField(object)
    expect = related.ChildField(object)
    success = related.BooleanField()


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
class SuiteResult(object):
    success = related.BooleanField()
    suite = related.ChildField(Suite)
    passed = related.SequenceField(ScenarioResult, default=[])
    failed = related.SequenceField(ScenarioResult, default=[])


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

        # iterate steps
        async for step_result in self.iter_steps():
            step_results.append(step_result)
            success = step_result.success
            if not success:
                break

        running_time = time.time() - start_time

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
            await asyncio.sleep(0.5)  # todo: replace...

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
        async with self.session.request(fetch.method, fetch.url,
                                        **fetch.kwargs) as context:
            try:
                response = Namespace(await context.json())
            except:
                response = Namespace()

            status = context.status
            return response, status

    def do_extract(self, step):
        existing = related.to_dict(self.extract) if self.extract else {}
        return step.extract.evaluate(self.namespace, existing)

    def do_validate(self, step, status):
        results = []

        # status check
        expected_status = step.request.status or HTTP_SUCCESS
        results.append(ValidationResult(actual=status,
                                        expect=expected_status,
                                        success=status in expected_status))

        # validators check
        for validator in step.validate or []:
            results.append(self.check_validation(validator))

        # determine success and return
        success = all([result.success for result in results])
        return results, success

    def check_validation(self, validator):
        actual = Namespace.render(validator.actual, self.namespace)
        expect = Namespace.render(validator.expect, self.namespace)
        success = validator.compare.evaluate(actual, expect)
        return ValidationResult(actual=actual,
                                expect=expect, success=success)
