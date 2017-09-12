import click
import sys

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
@click.option('--output', '-o', default=".",
              help='Report output folder. (default: .)')
@click.option('--quiet', '-q', is_flag=True,
              help='Run in quiet mode. (warning/critical level only)')
@click.option('--verbose', '-v', is_flag=True,
              help='Run in verbose mode. (debug level logging)')
@click.option('--json', '-j', is_flag=True,
              help='JSON-style logging.')
def main(directories, domain, include, exclude, prefix, extensions,
         concurrency, output, quiet, verbose, json):

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
    report_engine = ReportEngine(output_path=output, suite_result=suite_result)

    # generate report
    report_engine.generate()

    # system error code
    if suite_result.failed:
        raise click.ClickException(
            "%s test(s) failed." % len(suite_result.failed)
        )

if __name__ == '__main__':
    main()
