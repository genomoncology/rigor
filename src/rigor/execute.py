import asyncio
import aiohttp

from . import SuiteResult, Runner


def execute(suite):
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(do_suite(loop, suite))
    loop.run_until_complete(future)

    passed = []
    failed = []

    for result in future.result():
        # todo: handle exceptions...
        sink = passed if result.success else failed
        sink.append(result)

    success = bool(passed and not failed)

    return SuiteResult(
        suite=suite,
        passed=passed,
        failed=failed,
        success=success,
    )

async def do_suite(loop, suite):
    tasks = []
    connector = aiohttp.TCPConnector(limit_per_host=suite.concurrency)

    with aiohttp.ClientSession(loop=loop, connector=connector) as session:
        for case in suite.queued.values():
            for scenario in case.scenarios:
                runner = Runner(session=session, suite=suite, case=case,
                                scenario=scenario)

                tasks.append(asyncio.ensure_future(runner.do_run()))

        results = await asyncio.gather(*tasks, return_exceptions=True)

    return results
