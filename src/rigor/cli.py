import click

from . import Suite, Config, ReportEngine, CoverageReport
from . import setup_logging, get_logger, execute


@click.command()
@click.argument('paths', nargs=-1)
@click.option('--profile', default="__root__",
              help="Profile name (e.g. test)")
@click.option('--host', help="Host name (e.g. http://localhost:8000)")
@click.option('--includes', '-i', multiple=True,
              help="Include tag of cases. (e.g. smoke)")
@click.option('--excludes', '-e', multiple=True,
              help="Exclude tag of cases to run. (e.g. broken)")
@click.option('--prefixes', '-p', multiple=True,
              help="Filter cases by file prefix. (e.g. smoke_)")
@click.option('--extensions', '-e', multiple=True,
              help="Filter cases by file extension. (e.g. rigor)")
@click.option('--concurrency', '-c', type=int, default=None,
              help='# of concurrent HTTP requests. (default: 5)')
@click.option('--output', '-o', default=None,
              help='Report output folder.')
@click.option('--quiet', '-q', is_flag=True,
              help='Run in quiet mode. (warning/critical level only)')
@click.option('--verbose', '-v', is_flag=True,
              help='Run in verbose mode. (debug level logging)')
@click.option('--json', '-j', is_flag=True,
              help='JSON-style logging.')
@click.option('--html', '-h', is_flag=True,
              help='Generate HTML report.')
@click.option('--coverage', '-g', is_flag=True,
              help='Generate Coverage report.')
def main(paths, profile, output, quiet, verbose, json, html, coverage, **cli):
    # default paths
    paths = paths or ["."]

    # setup logging
    setup_logging(quiet=quiet, verbose=verbose, json=json)

    # cli = host, includes, excludes, prefixes, extensions, concurrency
    get_logger().debug("cli options", **cli)

    # load profile from rigor.yml file (if found)
    profile = Config.load(paths).get_profile(profile)
    get_logger().debug("profile", profile=profile)

    # create/collect suite
    suite = Suite.create(paths, profile, **cli)

    # execute suite
    suite_result = execute(suite)

    # generate reports
    generate_reports(suite_result, html, output, coverage)

    # system error code
    if suite_result.failed or not suite_result.passed:
        raise click.ClickException(
            "%s test(s) failed. %s test(s) passed." % (
                len(suite_result.failed),
                len(suite_result.passed)
            )
        )


def generate_reports(suite_result, html, output, coverage):
    # construct report engine
    if output or html:
        report_engine = ReportEngine(output_path=output,
                                     suite_result=suite_result,
                                     with_html=html)

        # generate report
        report_path = report_engine.generate()
        if report_path:
            click.launch(report_path)
            get_logger().info("launching browser", report_path=report_path)

    # coverage
    if coverage:
        coverage_report = CoverageReport.create(suite_result)
        report_path = coverage_report.generate(output)
        if report_path:
            click.launch(report_path)
            get_logger().info("launching excel", report_path=report_path)


if __name__ == '__main__':
    main()
