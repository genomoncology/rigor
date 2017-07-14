# -*- coding: utf-8 -*-

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

from .functions import (
    Functions
)

from .model import (
    Case,
    Step,
    Suite,
    Validator,
)

from .state import (
    Runner,
    SuiteResult,
)

from .execute import (
    execute
)

from .cli import (
    main
)


__all__ = [
    # collect.py
    "collect",

    # enums.py
    "Comparison",
    "Method",
    "Status",

    # execute.py
    "execute",

    # functions.py
    "Functions",

    # namespace.py
    "Namespace",

    # model.py
    "Case",
    "Step",
    "Suite",
    "Validator",

    # state.py
    "Runner",
    "SuiteResult",

    # cli.py
    "main",
]


__author__ = """Ian Maurer"""
__email__ = 'ian@genomoncology.com'
__version__ = '0.0.13'

__uri__ = "http://www.github.com/genomoncology/rigor"
__copyright__ = "Copyright (c) 2017 genomoncology.com"
__description__ = "Rigor: No-Nonsense Asynchronous REST API Testing"
__doc__ = __description__ + " <" + __uri__ + ">"
__license__ = "MIT"
__title__ = "rigor"
