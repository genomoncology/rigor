import asyncio
import requests
import related
import bs4
import time

from aiohttp import TCPConnector, ClientSession
from . import Suite, const, get_logger

# disable warning
requests.packages.urllib3.disable_warnings()


@related.immutable
class Session(object):
    suite = related.ChildField(Suite)

    @staticmethod
    def create(suite):
        if suite.concurrency > 0:
            loop = asyncio.get_event_loop()
            connector = TCPConnector(limit_per_host=suite.concurrency,
                                     verify_ssl=False)
            http = ClientSession(loop=loop, connector=connector)
            return AsyncSession(suite=suite, http=http, loop=loop,
                                connector=connector)

        else:
            return Session(suite=suite)

    def case_scenarios(self):
        for case in self.suite.queued.values():
            for scenario in case.scenarios:
                yield case, scenario

    def run(self):
        return self.run_suite()

    def run_suite(self):
        results = []
        for case, scenario in self.case_scenarios():
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

    def do_step(self, state, step):
        from . import StepState

        with StepState(step=step, state=state) as step_state:
            # sleep if any
            time.sleep(step.sleep)

            # do fetch
            (response, status) = self.do_fetch(step_state)

            # process response
            step_state.process_response(response, status)

        return step_state.result()

    def do_fetch(self, step_state):
        fetch = step_state.get_fetch()
        get_logger().debug("fetch request", **related.to_dict(fetch))

        kw = fetch.get_kwargs(is_aiohttp=False)
        context = requests.request(fetch.method, fetch.url, **kw)
        response = self.get_response(context)
        status = context.status_code

        get_logger().debug("fetch response", response=response, status=status,
                           **related.to_dict(fetch))

        return response, status

    def get_response(self, context):
        content_type = context.headers.get(const.CONTENT_TYPE, '')
        content_type = content_type.lower()

        if const.TEXT_HTML in content_type:
            html = OurSoup(context.content, 'html.parser')
            response = html

        elif const.APPLICATION_JSON in content_type:
            response = context.json()

        else:
            response = None

        return response


@related.immutable
class AsyncSession(Session):
    loop = related.ChildField(object)
    connector = related.ChildField(TCPConnector)
    http = related.ChildField(object)

    def run(self):
        future = asyncio.ensure_future(self.run_suite())
        self.loop.run_until_complete(future)
        results = future.result()
        self.http.close()
        return results

    async def run_suite(self):
        tasks = []
        for case, scenario in self.case_scenarios():
            tasks.append(asyncio.ensure_future(
                self.run_case_scenario(case, scenario)
            ))
        return await asyncio.gather(*tasks, return_exceptions=False)

    async def run_case_scenario(self, case, scenario):
        from . import State

        with State(session=self, case=case, scenario=scenario) as state:
            async for step_result in self.iter_steps(state):
                state.add_step(step_result)
            return state.result()

    async def iter_steps(self, state):
        for step in state.case.steps:
            for state.iterate in step.iterate.iterate(state.namespace):
                if state.should_run_step(step):
                    yield await self.do_step(state, step)

    async def do_step(self, state, step):
        from . import StepState

        with StepState(step=step, state=state) as step_state:
            # sleep if any
            await asyncio.sleep(step.sleep)

            # do fetch
            (response, status) = await self.do_fetch(step_state)

            # process response
            step_state.process_response(response, status)

        return step_state.result()

    async def do_fetch(self, step_state):
        fetch = step_state.get_fetch()
        get_logger().debug("fetch request", **related.to_dict(fetch))

        kw = fetch.get_kwargs(is_aiohttp=True)

        try:
            method, url = fetch.method, fetch.url
            async with self.http.request(method, url, **kw) as context:
                response = await self.get_response(context)
                status = context.status

        except Exception as e:  # pragma: no cover
            get_logger().error("do_fetch exception", error=e,
                               **related.to_dict(fetch))
            response = "Error"
            status = 500

        get_logger().debug("fetch response", response=response, status=status,
                           **related.to_dict(fetch))

        return response, status

    async def get_response(self, context):
        content_type = context.headers.get(const.CONTENT_TYPE, '')
        content_type = content_type.lower()

        if const.TEXT_HTML in content_type:
            html = OurSoup(await context.text(), 'html.parser')
            response = html

        elif const.APPLICATION_JSON in content_type:
            response = await context.json()

        else:
            response = None

        return response


class OurSoup(bs4.BeautifulSoup):
    def __repr__(self, **kwargs):
        title = self.title.string if self.title else ""
        body = self.body.text if self.body else ""
        return "{}\n\n{}".format(title, body)


@related.to_dict.register(OurSoup)
def _(obj, **kwargs):
    return str(obj)
