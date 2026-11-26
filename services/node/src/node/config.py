import sys
from dataclasses import dataclass, field
from typing import Literal

import dature

type LogLevel = Literal["debug", "info", "warning", "error", "critical"]


@dataclass
class LogConfig:
    level: LogLevel = "info"
    colors: bool = sys.stderr.isatty()
    timestamp_format: str = "%H:%M:%S"
    http_level: LogLevel | None = None
    grpc_level: LogLevel | None = None


@dataclass
class NodeConfig:
    http_host: str = "0.0.0.0"
    http_port: int = 8000
    grpc_host: str = "0.0.0.0"
    grpc_port: int = 5051
    log: LogConfig = field(default_factory=LogConfig)


config = dature.load(dature.EnvSource(), schema=NodeConfig)
