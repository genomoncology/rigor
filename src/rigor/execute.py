from . import SuiteResult, Timer, Session
from . import get_logger


def execute(suite):
    with Timer() as timer:
        log = get_logger()
        log.debug("execute suite start", suite=suite)
        session = Session.create(suite)
        scenario_results = session.run()
        suite_result = SuiteResult.create(suite, scenario_results)

    log.info("execute suite complete",
             passed=len(suite_result.passed),
             failed=len(suite_result.failed),
             timer=timer)

    return suite_result
