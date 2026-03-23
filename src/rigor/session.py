import asyncio
import attrs
import bs4
import time
from httpx._client import BaseClient, Client, AsyncClient, Limits
from httpx._transports.asgi import ASGITransport
from httpx._transports.wsgi import WSGITransport

from . import Suite, const, get_logger
from .converter import converter


@attrs.frozen
class Session:
    suite: Suite
    http: BaseClient

    @staticmethod
    def create(suite):
        if suite.concurrency > 0:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            limits = Limits(
                max_connections=suite.concurrency,
                max_keepalive_connections=suite.concurrency,
            )
            kw = {"limits": limits}
            if suite.app:
                kw["transport"] = ASGITransport(app=suite.app)
            http = AsyncClient(**kw)
            return AsyncSession(suite=suite, http=http, loop=loop)

        else:
            kw = {"transport": WSGITransport(app=suite.app)} if suite.app else {}
            http = Client(**kw)
            return Session(suite=suite, http=http)

    def case_scenarios(self):
        for case in self.suite.queued.values():
            for scenario in case.scenarios:
                yield case, scenario

    def run(self, case_scenarios=None):
        return self.run_suite(case_scenarios)

    def run_suite(self, case_scenarios=None):
        results = []
        if case_scenarios is None:
            case_scenarios = self.case_scenarios()
        for case, scenario in case_scenarios:
            scenario_result = self.run_case_scenario(case, scenario)
            results.append(scenario_result)

        return results

    def run_case_scenario(self, case, scenario):
        from . import State

        with State(session=self, case=case, scenario=scenario) as state:
            for step_result in self.iter_steps(state):
                state.add_step(step_result)
            return state.result()

    def iter_steps(self, state):
        for step in state.case.steps:
            for state.iterate in step.iterate.iterate(state.namespace):
                if state.should_run_step(step):
                    yield self.do_step(state, step)

    def get_retries(self, state, step):
        if step.is_retryable():
            return state.suite.retries
        else:
            return 0

    def do_step(self, state, step):
        from . import StepState

        retries = self.get_retries(state, step)
        step_state = None

        for retry in range(retries + 1):
            with StepState(step=step, state=state, retry=retry) as step_state:
                # sleep if any
                logger = get_logger().info if retry else get_logger().debug
                logger("do_step", sleep=step_state.sleep, retry=retry)
                time.sleep(step_state.sleep)

                # do fetch
                (response, status) = self.do_fetch(step_state)

                # process response
                step_state.process_response(response, status)

            if step_state.success:
                break

        step_state.process_success()

        return step_state.result()

    def do_fetch(self, step_state):
        fetch = step_state.get_fetch()
        get_logger().debug("fetch request", **converter.unstructure(fetch))

        kw = fetch.get_kwargs()

        try:
            method, url = fetch.method, fetch.url
            context = self.http.request(method, url, **kw)
            response = self.get_response(context)
            status = context.status_code
        except Exception as e:  # pragma: no cover
            get_logger().error(
                "do_fetch exception", error=e, **converter.unstructure(fetch)
            )
            response = "Error"
            status = 500

        get_logger().debug(
            "fetch response",
            response=response,
            status=status,
            **converter.unstructure(fetch)
        )

        return response, status

    def get_response(self, context):
        content_type = context.headers.get(const.CONTENT_TYPE, "")
        content_type = content_type.lower()

        if const.TEXT_HTML in content_type:
            html = OurSoup(context.content, "html.parser")
            response = html

        elif const.APPLICATION_JSON in content_type:
            response = context.json()

        else:
            response = None

        return response


@attrs.frozen
class AsyncSession(Session):
    loop: asyncio.AbstractEventLoop

    def run(self, case_scenarios=None):
        # recreate semaphores bound to the current event loop
        for key in list(self.suite.semaphores.keys()):
            self.suite.semaphores[key] = asyncio.Semaphore()

        # run and get results
        results = self.loop.run_until_complete(self.run_suite(case_scenarios))

        # close http
        self.loop.run_until_complete(self.close_http())

        return results

    async def close_http(self):
        # await self.http.close()
        pass

    async def run_suite(self, case_scenarios=None):
        tasks = []
        if case_scenarios is None:
            case_scenarios = self.case_scenarios()
        for case, scenario in case_scenarios:
            tasks.append(
                asyncio.create_task(self.run_case_scenario(case, scenario))
            )
        return await asyncio.gather(*tasks, return_exceptions=False)

    async def run_case_scenario(self, case, scenario):
        # Allows only 1 scenario run at a time with same semaphore name
        if case.semaphore is not None:
            async with self.suite.semaphores[case.semaphore]:
                return await self.run_single_case_scenario(case, scenario)
        else:
            return await self.run_single_case_scenario(case, scenario)

    async def run_single_case_scenario(self, case, scenario):
        from . import State

        with State(session=self, case=case, scenario=scenario) as state:
            async for step_result in self.iter_steps(state):
                state.add_step(step_result)
            scenario_result = state.result()
            return scenario_result

    async def iter_steps(self, state):
        for step in state.case.steps:
            for state.iterate in step.iterate.iterate(state.namespace):
                if state.should_run_step(step):
                    yield await self.do_step(state, step)

    async def do_step(self, state, step):
        from . import StepState

        retries = self.get_retries(state, step)
        step_state = None

        for retry in range(retries + 1):
            with StepState(step=step, state=state, retry=retry) as step_state:
                # sleep if any
                logger = get_logger().info if retry else get_logger().debug
                logger("do_step", sleep=step_state.sleep, retry=retry)
                await asyncio.sleep(step_state.sleep)

                # do fetch
                (response, status) = await self.do_fetch(step_state)

                # process response
                step_state.process_response(response, status)

            if step_state.success:
                break

        step_state.process_success()

        return step_state.result()

    async def do_fetch(self, step_state):
        fetch = step_state.get_fetch()
        get_logger().debug("fetch request", **converter.unstructure(fetch))

        kw = fetch.get_kwargs()

        try:
            method, url = fetch.method, fetch.url
            context = await self.http.request(method, url, **kw)
            response = await self.get_response(context)
            status = context.status_code

        except Exception as e:  # pragma: no cover
            get_logger().error(
                "do_fetch exception", error=e, **converter.unstructure(fetch)
            )
            response = "Error"
            status = 500

        get_logger().debug(
            "fetch response",
            response=response,
            status=status,
            **converter.unstructure(fetch)
        )

        return response, status

    async def get_response(self, context):
        content_type = context.headers.get(const.CONTENT_TYPE, "")
        content_type = content_type.lower()

        if const.TEXT_HTML in content_type:
            html = OurSoup(context.text, "html.parser")
            response = html

        elif const.APPLICATION_JSON in content_type:
            response = context.json()

        elif const.TEXT_PLAIN in content_type:
            response = context.text

        else:
            response = None

        return response


class OurSoup(bs4.BeautifulSoup):
    def __repr__(self, **kwargs):
        title = self.title.string if self.title else ""
        body = self.body.text if self.body else ""
        return "{}\n\n{}".format(title, body)


converter.register_unstructure_hook(OurSoup, lambda obj: str(obj))
