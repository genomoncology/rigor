# -*- coding: utf-8 -*-

from . import const, utils

from .logging import (
    setup_logging,
    get_logger,
    log_with_success,
)

from .metrics import (
    Timer
)

from .collect import (
    collect
)

from .enums import (
    Comparison,
    Method,
    Status,
)

from .namespace import (
    Namespace,
)

from .config import (
    Config,
    Profile
)

from .model import (
    Case,
    Requestor,
    Step,
    Suite,
    Validator,
)

from .session import (
    Session
)

from .state import (
    State,
    SuiteResult,
    StepState,
)

from .execute import (
    execute
)

from .reporting import (
    ReportEngine
)

from .swagger import (
    Path,
    Swagger
)

from .coverage import (
    CoverageReport
)

from .cli import (
    main
)


__all__ = [
    # const.py
    "const",
    "utils",

    # logging.py
    "setup_logging",
    "get_logger",
    "log_with_success",

    # metrics.py
    "Timer",

    # collect.py
    "collect",

    # enums.py
    "Comparison",
    "Method",
    "Status",

    # execute.py
    "execute",

    # namespace.py
    "Namespace",

    # config.py
    "Config",
    "Profile",

    # model.py
    "Case",
    "Requestor",
    "Step",
    "Suite",
    "Validator",

    # session.py
    "Session",

    # reporting.py
    "ReportEngine",

    # state.py
    "State",
    "StepState",
    "SuiteResult",

    # swagger.py
    "Path",
    "Swagger",

    # coverage.py
    "CoverageReport",

    # cli.py
    "main",
]


__author__ = """Ian Maurer"""
__email__ = 'ian@genomoncology.com'
__version__ = '0.4.3'

__uri__ = "http://www.github.com/genomoncology/rigor"
__copyright__ = "Copyright (c) 2017 genomoncology.com"
__description__ = "Rigor: REST API Testing"
__doc__ = __description__ + " <" + __uri__ + ">"
__license__ = "MIT"
__title__ = "rigor"
