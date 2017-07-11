import click

from . import Suite
import related
import json
import sys
from rigor.reporting.cucumber import Cucumber
import os


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
    results = suite.execute()

    temp = related.to_json(Cucumber.load_init(Cucumber, suite_result=results))
    dct = json.loads(temp)
    final = related.to_json(dct)
    print(final)

    # Opens and closes file to clear contents

    path1 = os.path.expanduser('~/code/knowledge/qa/response/responsejson')
    path2 = os.path.expanduser('~/code/knowledge/qa/response/result')
    f = open((str(path1) + "/responsejson"), "wb+")
    f.close()

    # File is actually written to here
    f = open((str(path1) + "/response.json"), "r+")
    f.write(final)
    f.close()
    print("\n\n\nResponse Successfully Written to File\n\n\n")
    from subprocess import call
    call(["java", "-jar", "/Users/edward/code/cucumber-sandwich/target/cucumber-sandwich.jar", "-n", "-f", path1, "-o",
          path2])
    click.launch((str(path2) + '/cucumber-html-reports/cucumber-html-reports/overview-features.html'))

    status = 1 if results.failed else 0
    sys.exit(status)

if __name__ == '__main__':
    main()
