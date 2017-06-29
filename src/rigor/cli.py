import click
import jmespath

from . import Suite
import related
import json


@click.command()
@click.argument('directories', nargs=-1)
def main(directories):
    # collect
    suite = Suite(directories=directories)

    # execute
    suite.execute()


    # suite_dict = related.to_dict(suite)
    k = 0
    j = 1
    i = 0
    for failure in suite.failed:
        print("Failure #%s" % i)
        print("Case:\n%s (%s)\n" % (failure.case.name, failure.case.file_path))
        print("Step:\n%s\n" % related.to_json(failure.fail_step))
        print("Scenario:\n%s\n" % related.to_json(failure.scenario))
        print("Last Fetch:\n%s\n" % related.to_json(failure.fetch))
        print("Last Response:\n%s\n" % related.to_json(failure.response))
        print("Failed Validations:")
        for validation in failure.fail_validations:
            print(related.to_json(validation))
        print("\n")
        i += 1

    print("Passed: %s" % len(suite.passed))
    print("Failed: %s" % len(suite.failed))

if __name__ == '__main__':
    main()
