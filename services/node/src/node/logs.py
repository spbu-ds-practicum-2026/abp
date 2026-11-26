import logging

import structlog

from node.config import LogConfig


def configure_logging(config: LogConfig) -> None:
    foreign_pre_chain = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt=config.timestamp_format, utc=True),
    ]
    shared_processors = foreign_pre_chain
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            *shared_processors,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    http_level = config.http_level.upper() if config.http_level else "NOTSET"
    grpc_level = config.grpc_level.upper() if config.grpc_level else "NOTSET"
    renderer = structlog.dev.ConsoleRenderer(
        colors=config.colors,
        pad_event_to=0,
        pad_level=True,
        exception_formatter=structlog.dev.plain_traceback,
    )
    columns = renderer.columns
    logger_columns = [column for column in columns if column.key in ("logger", "logger_name")]
    columns = [column for column in columns if column.key not in ("logger", "logger_name")]
    event_index = next(index for index, column in enumerate(columns) if column.key == "event")
    renderer.columns = [*columns[:event_index], *logger_columns, *columns[event_index:]]

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=foreign_pre_chain,
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logging.basicConfig(level=config.level.upper(), handlers=[handler], force=True)

    for name, level in (
        ("node", "NOTSET"),
        ("node.http", http_level),
        ("fastapi", http_level),
        ("uvicorn", http_level),
        ("node.grpc", grpc_level),
        ("grpclib", grpc_level),
    ):
        logging.getLogger(name).setLevel(level)
