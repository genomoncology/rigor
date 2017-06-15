# -*- coding: utf-8 -*-

from .collect import (
    collect
)

from .model import (
    Case,
    Suite,
)

__all__ = [
    # collect.py
    "collect",

    # model.py
    "Case",
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
