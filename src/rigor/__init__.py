# -*- coding: utf-8 -*-

from .collect import (
    collect
)

from .execute import (
    execute
)

from .model import (
    Case,
    Result,
    Namespace,
    State,
    Suite,
)

__all__ = [
    # collect.py
    "collect",

    # execute.py
    "execute",

    # model.py
    "Case",
    "Result",
    "Namespace",
    "State",
    "Suite",
]


__author__ = """Ian Maurer"""
__email__ = 'ian@genomoncology.com'
__version__ = '0.1'

__uri__ = "http://www.github.com/genomoncology/rigor"
__copyright__ = "Copyright (c) 2017 genomoncology.com"
__description__ = "Rigor: No-Nonsense Asynchronous REST API Testing"
__doc__ = __description__ + " <" + __uri__ + ">"
__license__ = "MIT"
__title__ = "rigor"
