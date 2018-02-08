<img src='./.images/logo.png' width='140' align="left" />
<a href='https://codecov.io/github/genomoncology/rigor/'><img src='https://codecov.io/github/genomoncology/rigor/branch/master/graph/badge.svg' align="right" /></a>
<a href='https://travis-ci.org/genomoncology/rigor'><img src='https://img.shields.io/travis/genomoncology/rigor.svg' align="right" /></a>
<a href='https://pypi.python.org/pypi/rigor'><img src='https://img.shields.io/pypi/v/rigor.svg' align="right" /></a>

<br/><br/>

`Rigor` is a Domain Specific Language (DSL) and Command Line Interface (CLI)
for making HTTP requests, extracting data, and validating responses. The main
intent of Rigor is to be an HTTP-based API (e.g. REST) Testing Framework for
automated functional or integration testing.


# Requirements

* Python 3.6


# Installation

Install using `pip3`...

    pip3 install rigor


# Feature List


* Functional testing without the need to write glue code. (e.g. Cucumber)
* Runs in either synchronous ([requests]) or asynchronous ([aiohttp]) mode.
* YAML-based format for Test Case files for easy test creation and maintenance.
* Response transformation using [jmespath.py] to reduce test fragility.
* Pretty HTML test execution reports using [cucumber-sandwich].
* [Swagger] path coverage report to ensure API surface area coverage.
* Syntax highlighted console or JSON-based logging using [structlog].
* Profiles for switching between different environments and settings.
* Tags and CLI options for selectively executing subsets of the test suite.


# Command Line Interface (CLI) Options

    $ rigor --help
    Usage: rigor [OPTIONS] [PATHS]...

    Options:
      --profile TEXT             Profile name (e.g. test)
      --host TEXT                Host name (e.g. http://localhost:8000)
      -i, --includes TEXT        Include tag of cases. (e.g. smoke)
      -e, --excludes TEXT        Exclude tag of cases to run. (e.g. broken)
      -p, --prefixes TEXT        Filter cases by file prefix. (e.g. smoke_)
      -e, --extensions TEXT      Filter cases by file extension. (e.g. rigor)
      -c, --concurrency INTEGER  # of concurrent HTTP requests. (default: 5)
      -o, --output TEXT          Report output folder.
      -q, --quiet                Run in quiet mode. (warning/critical level only)
      -v, --verbose              Run in verbose mode. (debug level logging)
      -j, --json                 JSON-style logging.
      -h, --html                 Generate HTML report.
      -g, --coverage             Generate Coverage report.
      --help                     Show this message and exit.

# Simple Example

    (rigor) /p/tmp> cat test.rigor
    name: Simple case.

    steps:
      - description: Simple step.
        request:
          host: https://httpbin.org
          path: get

    (rigor) /p/tmp> rigor test.rigor --html
    2018-02-08 13:18.06 [info     ] no config file not found       [rigor] paths=('test.rigor',)
    2018-02-08 13:18.06 [info     ] collecting tests               [rigor] cwd=/private/tmp paths=['test.rigor']
    2018-02-08 13:18.06 [info     ] tests collected                [rigor] queued=1 skipped=0
    2018-02-08 13:18.06 [info     ] execute suite complete         [rigor] failed=0 passed=1 timer=0.119s
    2018-02-08 13:18.07 [info     ] launching browser              [rigor] report_path=/var/folders/b_/2hlrn_7930x81r009mfzl50m0000gn/T/tmps_8d7nn_/html-2018-02-08-08-18-06/cucumber-html-reports/cucumber-html-reports/overview-features.html

![list]

![detail]


# Related Projects

* [Tavern] is an extremely similar project that was released a little too late for us to use.
* [Pyresttest] was the first library we used before deciding to roll our own testing framework.
* [Click] is the library used to build out the command-line options.
* [Related] is the library used for parsing the YAML test suite into an Python object model.


# More Examples

More examples can be found by reviewing the [tests/] folder of this project.


# License

The MIT License (MIT)
Copyright (c) 2017 [Ian Maurer], [Genomoncology LLC]


[Click]: http://click.pocoo.org/
[PyRestTest]: https://github.com/svanoort/pyresttest/
[Related]: https://github.com/genomoncology/related
[Swagger]: https://swagger.io/specification/
[Tavern]: https://taverntesting.github.io/
[aiohttp]: http://aiohttp.readthedocs.io/en/stable/
[cucumber-sandwich]: https://github.com/damianszczepanik/cucumber-sandwich
[jmespath.py]: https://github.com/jmespath/jmespath.py
[requests]: http://docs.python-requests.org/en/master/
[structlog]: http://www.structlog.org/en/stable/
[tests/]: ./tests/

[list]: ./.images/low.png
[detail]: ./.images/low.png
