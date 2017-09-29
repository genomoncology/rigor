import asyncio

import aiohttp
import related
import jmespath
import bs4
import os

from . import Case, Namespace, Step, Suite, Validator, Timer
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


@related.immutable
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


@related.immutable
class ScenarioResult(object):
    suite = related.ChildField(Suite)
    case = related.ChildField(Case)
    scenario = related.ChildField(Namespace)
    success = related.BooleanField()
    uuid = related.UUIDField()
    step_results = related.SequenceField(StepResult, default=[])


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
    transform = related.ChildField(Namespace, default=Namespace())

    def __attrs_post_init__(self):
        self.scenario = self.scenario.evaluate(self.namespace)

    @property
    def namespace(self):
        # make globals namespace top-level
        globals = self.suite.globals if self.suite else {}
        values = (globals or {}).copy()

        # make scenario namespace top-level accessors (overrides globals!)
        values.update(self.scenario if self.scenario else {})

        # make iterate namespace top-level accessors (overrides scenario!)
        values.update(self.iterate if self.iterate else {})

        # make extract namespace top-level accessors (overrides iterate!)
        values.update(self.extract if self.extract else {})

        # add handles to namespaces (overrides scenario, extract and iterate!)
        values.update(dict(__uuid__=self.uuid,
                           globals=globals,
                           scenario=self.scenario,
                           transform=self.transform,
                           extract=self.extract,
                           response=self.response,
                           iterate=self.iterate,
                           env=os.environ))

        return values

    async def do_run(self):
        with Timer() as timer:
            success = True
            step_results = []

            # iterate steps
            async for step_result in self.iter_steps():
                step_results.append(step_result)
                success = success and step_result.success

        log_with_success("scenario", success,
                         feature=self.case.name,
                         scenario=self.scenario.__name__,
                         file_path=self.case.file_path,
                         num_steps=len(step_results),
                         timer=timer)

        return ScenarioResult(
            uuid=self.uuid,
            suite=self.suite,
            case=self.case,
            scenario=self.scenario,
            success=success,
            step_results=step_results
        )

    def should_run_step(self, step, success):
        condition = step.condition  # todo: evaluation here
        return success if condition is None else condition

    async def iter_steps(self):
        success = True

        for step in self.case.steps:
            for self.iterate in step.iterate.iterate(self.namespace):
                if self.should_run_step(step, success):
                    step_result, success = await self.do_step(step, success)
                    yield step_result

    async def do_step(self, step, success):
        with Timer() as timer:
            # sleep if any
            await asyncio.sleep(step.sleep)

            # create and do fetch
            fetch = self.create_fetch(step.request)
            self.response, status = await self.do_fetch(fetch)

            # transform response
            self.transform = self.do_transform(step)

            # extract response
            self.extract = self.do_extract(step)

            # validate response
            validations, step_success = self.do_validate(step, status)

            # track overall success
            success = success and step_success

        # add step result
        step_result = StepResult(
            step=step,
            fetch=fetch,
            transform=self.transform,
            extract=self.extract,
            response=self.response,
            status=status,
            validations=validations,
            success=step_success,
            duration=timer.duration,
        )

        return step_result, success

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

    async def do_fetch(self, fetch):
        # make request and store response
        get_logger().debug("fetch", method=fetch.method, url=fetch.url,
                           kwargs=fetch.kwargs)

        async with self.session.request(fetch.method, fetch.url,
                                        **fetch.kwargs) as context:
            response = await self.get_response(context)
            status = context.status

            get_logger().debug("response", method=fetch.method, url=fetch.url,
                               kwargs=fetch.kwargs, status=status,
                               response=response)

            return response, status

    async def get_response(self, context):
        content_type = context.headers.get(const.CONTENT_TYPE, '')
        content_type = content_type.lower()

        if const.TEXT_HTML in content_type:
            html = OurSoup(await context.text(), 'html.parser')
            response = Namespace(html=html)

        elif const.APPLICATION_JSON in content_type:
            response = Namespace(await context.json())

        else:
            response = Namespace()

        return response

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


# dispatch

class OurSoup(bs4.BeautifulSoup):
    def __repr__(self, **kwargs):
        content = self.title.string if self.title else ""
        content += "\n\n" + self.body.text
        return content
