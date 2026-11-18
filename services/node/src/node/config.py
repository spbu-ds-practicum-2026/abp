from dataclasses import dataclass

import dature


@dataclass
class NodeConfig:
    http_host: str = "0.0.0.0"
    http_port: int = 8000
    grpc_host: str = "0.0.0.0"
    grpc_port: int = 1337
    log_level: str = "info"


config = dature.load(dature.EnvSource(), schema=NodeConfig)
