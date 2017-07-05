import click
import jmespath

from rigor.reporting.cucumber import Cucumber
from . import Suite
import related
import json
import sys


@click.command()
@click.argument('directories', nargs=-1)
@click.option('--domain', default="http://localhost:8000",
              help="Domain name (e.g. http://localhost:8000)")
@click.option('--include', '-i', multiple=True,
              help="Include tag of cases. (e.g. smoke)")
@click.option('--exclude', '-e', multiple=True,
              help="Exclude tag of cases to run. (e.g. broken)")
@click.option('--prefix', '-p', multiple=True,
              help="Filter cases by file prefix. (e.g. smoke_)")
@click.option('--extensions', '-e', multiple=True,
              help="Filter cases by file extension. (e.g. rigor)")
@click.option('--concurrency', '-c', type=int, default=20,
              help='# of concurrent HTTP requests. (default: 20)')
def main(directories, domain, include, exclude, prefix, extensions,
         concurrency):
    # remove preceding . if provided in extension (.rigor => rigor)
    extensions = [ext[1:] if ext.startswith(".") else ext
                  for ext in extensions or []]

    # collect
    suite = Suite(directories=directories, domain=domain,
                  tags_included=include, tags_excluded=exclude,
                  file_prefixes=prefix, extensions=extensions,
                  concurrency=concurrency)

    # execute
    suite.execute()

    temp = related.to_json(Cucumber.load_init(Cucumber, suite=suite))
    dct = json.loads(temp)
    print(related.to_json(dct))
    # temp = related.to_json(suite)
    # temp = related.to_json(json.loads(temp))
    # print(temp)

    # k = 0
    # j = 1
    # i = 0
    # for failure in suite.failed:
    #     print("Failure #%s" % i)
    #     print("Case:\n%s (%s)\n" % (failure.case.name, failure.case.file_path))
    #     print("Step:\n%s\n" % related.to_json(failure.fail_step))
    #     print("Scenario:\n%s\n" % related.to_json(failure.scenario))
    #     print("Last Response:\n%s\n" % related.to_json(failure.response))
    #     print("Failed Validations:")
    #     for validation in failure.fail_validations:
    #         print(related.to_json(validation))
    #     print("\n")
    #     i += 1
    #
    # print("Passed: %s" % len(suite.passed))
    # print("Failed: %s" % len(suite.failed))

    # report success
    status = 1 if suite.failed else 0
    sys.exit(status)

if __name__ == '__main__':
    main()
