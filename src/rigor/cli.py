import click
from . import Suite
import related


@click.command()
@click.argument('directories', nargs=-1)
def main(directories):
    # collect
    suite = Suite(directories=directories, domain="http://localhost:8000")

    # execute
    suite.execute()

    # report
    i = 1
    for failure in suite.failed:
        print("Failure #%s" % i)
        print("Case:\n%s (%s)\n" % (failure.case.name, failure.case.file_path))
        print("Step:\n%s\n" % related.to_json(failure.fail_step))
        print("Scenario:\n%s\n" % related.to_json(failure.scenario))
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
