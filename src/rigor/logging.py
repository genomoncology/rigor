import logging
import sys
import structlog


LOGGER_NAME = 'rigor'

DEFAULT_PROCESSORS = [
    structlog.stdlib.filter_by_level,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    structlog.stdlib.PositionalArgumentsFormatter(),
    structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M.%S"),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
]


def setup_logging(quiet=False, verbose=False, json=False):
    # verbose supersedes quiet
    level = logging.WARNING if quiet else logging.INFO
    level = logging.DEBUG if verbose else level

    # root logger
    root = logging.getLogger(LOGGER_NAME)
    root.setLevel(level)
    root.addHandler(logging.StreamHandler(sys.stdout))

    # renderer
    renderer = structlog.processors.JSONRenderer() if json else \
        structlog.dev.ConsoleRenderer()

    # https://structlog.readthedocs.io/en/stable/development.html
    structlog.configure(
        processors=DEFAULT_PROCESSORS + [renderer],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(*args, **kwargs):
    return structlog.get_logger(LOGGER_NAME, *args, **kwargs)


def log_with_success(name, success, **kwargs):
    method = get_logger().debug if success else get_logger().error
    msg = "%s %s" % (name, "success" if success else "failed")
    method(msg, **kwargs)
