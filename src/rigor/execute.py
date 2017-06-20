import asyncio
import aiohttp
import os
import time


def execute(suite):
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(async_execute(loop, suite))
    loop.run_until_complete(future)

    success = True
    for result in future.result():
        suite.add_result(result)
        success = success and result.success

    return success

async def async_execute(loop, suite):
    from . import State, Namespace

    tasks = []
    connector = aiohttp.TCPConnector(limit_per_host=suite.concurrency)

    with aiohttp.ClientSession(loop=loop, connector=connector) as session:
        for case in suite.queued.values():
            for scenario in case.scenarios:
                task = asyncio.ensure_future(do_scenario(
                        State(session=session,
                              suite=suite,
                              case=case,
                              scenario=scenario)
                ))

                tasks.append(task)

        results = await asyncio.gather(*tasks)

    return results


async def do_scenario(state):
    from . import Result

    failing_step = None
    error_message = None
    start_time = time.time()

    for step in state.case.steps:
        # fetch
        await step.fetch(state)

        # extract response
        state.extract = step.extract.evaluate(state)

        # validate response
        failures = step.validate_response(state)

        # check status
        state.success = failures == []

        # break if step fails
        if not state.success:
            failing_step = step
            break

    running_time = time.time() - start_time

    return Result(case=state.case, scenario=state.scenario,
                  success=state.success, failing_step=failing_step,
                  error_message=error_message, running_time=running_time)
