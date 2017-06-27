import click
import jmespath

from . import Suite
import related
import json


@click.command()
@click.argument('directories', nargs=-1)
def main(directories):
    # collect
    suite = Suite(directories=directories, domain="http://localhost:8000")

    # execute
    suite.execute()


    # suite_dict = related.to_dict(suite)
    k = 0
    j = 1
    for failure in suite.failed:
        temp = related.to_json(suite)
        suite_dict = json.loads(temp)
        # print(related.to_json(jmespath.search("failed[%s].{case: {domain: case.domain, file_Path: case.file_path, format: case.format, headers: case.headers, is_valid: case.is_valid, name: case.name, scenarios: case.scenarios[], steps: case.steps[]}, fail_step: fail_step, fail_validations: fail_validations[]}" % (k), suite_dict)))
        # print()

        print (related.to_json(jmespath.search("failed[%s].{uri: case.file_path, name: case.name, elements: [{examples: case.steps[].]}, {steps: case.steps}]}" % (k), suite_dict)))

        l = 0
        for step in suite.failed[k].case.steps:
            stp = related.to_json(jmespath.search("failed[%s].case.{steps: [{name: steps[%s].description, result: {extract: steps[%s].extract, request: steps[%s].request}, validate: steps[%s].validate}]}" % (k, l, l, l, l), suite_dict))
            print(stp)
            l += 1
        l = 0
        for scenario in suite.failed[k].case.scenarios:
            scen = related.to_json(jmespath.search("failed[%s].case.{examples: [{name: scenarios[%s].name, description: scenarios[%s].description, result: scenarios[%s].result}]}" % (k, l, l, l), suite_dict))
            print(scen)
            l += 1
        # print (related.to_json(jmespath.search("failed[%s].{uri: case.file_path, name: case.name, elements: [{examples: case.steps[].]}, {steps: case.steps}]}" % (k), suite_dict)))
        k += 1
        j += 1

    # report
    # related.to_json(suite)
    # j = 0
    # for failure in suite.failed:
    #     k = 0
    #     json_str = related.to_json(suite.failed)
    #     temp = json.loads(json_str)
    #     ret = jmespath.search(expression=failure.scenario, data=temp)
        # ret = temp.jmespath(temp[i].{temp.scenario: temp.scenario, temp.fail_validations: temp.fail_validations})pi
        # Upload to a file first?
        # ret = jmespath(temp[0].scenario)
        # print(str(ret))


    # report
    # i = 1
    # for failure in suite.failed:
    #     print("Failure #%s" % i)
    #     print("Scenario:\n%s\n" % related.to_json(failure.scenario))
    #     print("Failed Validations:")
    #     for validation in failure.fail_validations:
    #         print(related.to_json(validation))
    #     print("\n")
    #     i += 1

    print("Passed: %s" % len(suite.passed))
    print("Failed: %s" % len(suite.failed))

if __name__ == '__main__':
    main()
