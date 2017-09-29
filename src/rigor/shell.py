"""
Shell POC

def enter_shell(suite):
    scenario_results = []

    loop = asyncio.get_event_loop()
    connector = aiohttp.TCPConnector(limit_per_host=suite.concurrency)
    with aiohttp.ClientSession(loop=loop, connector=connector) as session:
        for case in suite.queued.values():
            print("New Case: %s" % case)

            for scenario in case.scenarios:
                print("New Scenario: %s" % scenario)
                runner = Runner(session=session, suite=suite, case=case,
                                scenario=scenario)

                success = True
                for step_result in runner.iter_steps():
                    step_results.append(step_result)
                    success = success and step_result.success
                    print("Step Complete: %s" % step_result.success)
                    prompt("rigor>")

                scenario_result = ScenarioResult(uuid=self.uuid,
                                                 suite=self.suite,
                                                 case=self.case,
                                                 scenario=self.scenario,
                                                 success=success,
                                                 step_results=step_results,
                                                 duration=duration)

                print("Scenario Complete: %s" % success)
                scenario_results.append(scenario_result)

    suite_result = SuiteResult.create(suite, scenario_results)
    print("Suite Complete: %s" % suite_result.success)
    return suite_result
"""
