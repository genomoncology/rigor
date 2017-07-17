import logging
import sys
import structlog
from structlog.stdlib import LoggerFactory


LOGGER_NAME = 'rigor'


def setup_logging(quiet=False, verbose=False):
    # verbose supersedes quiet
    level = logging.WARNING if quiet else logging.INFO
    level = logging.DEBUG if verbose else level

    # root logger
    root = logging.getLogger(LOGGER_NAME)
    root.setLevel(level)
    root.addHandler(logging.StreamHandler(sys.stdout))

    # https://structlog.readthedocs.io/en/stable/development.html
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M.%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(*args, **kwargs):
    return structlog.get_logger(LOGGER_NAME, *args, **kwargs)