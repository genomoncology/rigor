import click

from . import Suite, Config, ReportEngine, setup_logging, get_logger, execute


@click.command()
@click.argument('paths', nargs=-1)
@click.option('--profile', default="__root__",
              help="Profile name (e.g. test)")
@click.option('--domain', help="Domain name (e.g. http://localhost:8000)")
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
def main(paths, profile, domain, include, exclude, prefix, extensions,
         concurrency, output, quiet, verbose, json, html):

    # default paths
    paths = paths or ["."]

    # setup logging
    setup_logging(quiet=quiet, verbose=verbose, json=json)

    # remove preceding . if provided in extension (.rigor => rigor)
    extensions = [ext[1:] if ext.startswith(".") else ext
                  for ext in extensions or []]

    # load config
    config = Config.load(paths)

    # get profile using name
    profile = config.get_profile(profile)

    # collect suite
    suite = Suite(paths=paths, profile=profile, domain=domain,
                  tags_included=include, tags_excluded=exclude,
                  file_prefixes=prefix, extensions=extensions,
                  concurrency=concurrency)

    # execute suite
    suite_result = execute(suite, config)

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

    # system error code
    if suite_result.failed or not suite_result.passed:
        raise click.ClickException(
            "%s test(s) failed. %s test(s) passed." % (
                len(suite_result.failed),
                len(suite_result.passed)
            )
        )


if __name__ == '__main__':
    main()
