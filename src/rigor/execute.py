from . import SuiteResult, Timer, Session
from . import get_logger


def get_case_scenario(case, scenario_seq_num):
    return next(
        (
            scenario
            for scenario in case.scenarios
            if scenario["__sequence__"] == scenario_seq_num
        ),
        None,
    )


def get_failed_scenarios(scenario_results):
    failed_results = [
        (
            result.case,
            get_case_scenario(result.case, result.scenario["__sequence__"]),
        )
        for result in scenario_results
        if not result.success
    ]

    return [fr for fr in failed_results if fr is not None]


def execute(suite):
    with Timer() as timer:
        log = get_logger()
        log.debug("execute suite start", suite=suite)
        session = Session.create(suite)
        scenario_results = session.run()

        # rerun failed cases again
        retry_scenario_results = []
        failed_scenarios = get_failed_scenarios(scenario_results)

        if len(failed_scenarios) > 0 and suite.retry_failed:
            log.info("retrying failed scenarios", failed=len(failed_scenarios))
            retry_session = Session.create(suite)
            retry_scenario_results = retry_session.run(failed_scenarios)
            scenario_results = [
                result for result in scenario_results if result.success
            ]

        all_results = scenario_results + retry_scenario_results

        suite_result = SuiteResult.create(suite, all_results)

    log.info(
        "execute suite complete",
        passed=len(suite_result.passed),
        failed=len(suite_result.failed),
        timer=timer,
    )

    return suite_result
