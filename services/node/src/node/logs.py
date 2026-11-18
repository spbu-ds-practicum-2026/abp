import logging
import sys

import structlog

from node.config import LogConfig


def configure_logging(config: LogConfig) -> None:
    level = logging.getLevelNamesMapping()[config.level.upper()]
    foreign_pre_chain = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt=config.timestamp_format, utc=True),
    ]
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(
            colors=config.colors,
            pad_event_to=22,
            pad_level=True,
        ),
        foreign_pre_chain=foreign_pre_chain,
    )

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            *foreign_pre_chain,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)
    logging.basicConfig(
        level=level,
        handlers=[handler],
        force=True,
    )

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "grpclib"):
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.handlers = [handler]
        logger.propagate = False
