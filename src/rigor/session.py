import asyncio
import related
import bs4

from aiohttp import TCPConnector, ClientSession
from . import Suite, Namespace, const, get_logger, Timer


@related.immutable
class Session(object):
    suite = related.ChildField(Suite)

    @staticmethod
    def create(suite):
        if suite.concurrency > 0:
            loop = asyncio.get_event_loop()
            connector = TCPConnector(limit_per_host=suite.concurrency)
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
        pass
        # for case in suite.queued.values():
        #     for scenario in case.scenarios:
        #         session.add_task(Runner(session=self,
        #                                 suite=suite,
        #                                 case=case,
        #                                 scenario=scenario))
        #
        # results = session.collect()
        # return results


@related.immutable
class AsyncSession(Session):
    loop = related.ChildField(object)
    connector = related.ChildField(TCPConnector)
    http = related.ChildField(object)

    def run(self):
        future = asyncio.ensure_future(self.run_suite())
        self.loop.run_until_complete(future)
        return future.result()

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
        from . import StepResult

        with Timer() as timer:
            # sleep if any
            state.session.sleep(step.sleep)

            # create and do fetch
            fetch = state.create_fetch(step.request)
            state.response, status = await self.do_fetch(fetch)

            # transform response
            state.transform = state.do_transform(step)

            # extract response
            state.extract = state.do_extract(step)

            # validate response
            validations, step_success = state.do_validate(step, status)

            # track overall success
            state.success = state.success and step_success

        return StepResult(
            step=step,
            fetch=fetch,
            transform=state.transform,
            extract=state.extract,
            response=state.response,
            status=status,
            validations=validations,
            success=step_success,
            duration=timer.duration,
        )

    async def sleep(self, sleep):
        await asyncio.sleep(sleep)

    async def do_fetch(self, fetch):
        get_logger().debug("fetch request", **related.to_dict(fetch))

        async with self.http.request(fetch.method, fetch.url,
                                     **fetch.kwargs) as context:
            response = await self.get_response(context)
            status = context.status

        get_logger().debug("fetch response", response=response, status=status,
                           **related.to_dict(fetch))

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


class OurSoup(bs4.BeautifulSoup):
    def __repr__(self, **kwargs):
        content = self.title.string if self.title else ""
        content += "\n\n" + self.body.text
        return content
