import click
import related
import json
import sys
import os

from . import Suite, ReportEngine, setup_logging


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
@click.option('--report', '-r', multiple=True, default=["json"],
              help='Generate report. (e.g. cucumber)')
@click.option('--output', '-o', default=".",
              help='Report output folder. (default: .)')
@click.option('--quiet', '-q', is_flag=True,
              help='Run in quiet mode. (warning/critical level only)')
@click.option('--verbose', '-v', is_flag=True,
              help='Run in verbose mode. (debug level logging)')
@click.option('--json', '-j', is_flag=True,
              help='JSON-style logging.')
def main(directories, domain, include, exclude, prefix, extensions,
         concurrency, report, output, quiet, verbose, json):

    # setup logging
    setup_logging(quiet=quiet, verbose=verbose, json=json)

    # remove preceding . if provided in extension (.rigor => rigor)
    extensions = [ext[1:] if ext.startswith(".") else ext
                  for ext in extensions or []]

    # collect suite
    suite = Suite(directories=directories, domain=domain,
                  tags_included=include, tags_excluded=exclude,
                  file_prefixes=prefix, extensions=extensions,
                  concurrency=concurrency)

    # execute suite
    suite_result = suite.execute()

    # construct report engine
    report_engine = ReportEngine(report_types=report, output_path=output,
                                 suite_result=suite_result)

    # generate report
    report_engine.generate()

    # report success
    return 1 if suite_result.failed else 0


if __name__ == '__main__':
    sys.exit(main())
