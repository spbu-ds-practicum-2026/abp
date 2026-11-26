from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from dishka import make_async_container
from fastapi import FastAPI
from grpclib.server import Server

from node.config import config
from node.di import NodeProvider
from node.grpc.service import NodeService

grpc_log = structlog.get_logger("node.grpc")
node_log = structlog.get_logger("node")


@asynccontextmanager
async def node_lifespan(_app: FastAPI) -> AsyncIterator[None]:
    async with make_async_container(NodeProvider()) as container:
        grpc_service = await container.get(NodeService)
        grpc_server = Server([grpc_service])

        try:
            await grpc_server.start(config.grpc_host, config.grpc_port)
        except OSError:
            grpc_log.exception("Could not start gRPC server")
            raise SystemExit(1) from None

        try:
            async with grpc_server:
                grpc_log.info("Listening", address=f"{config.grpc_host}:{config.grpc_port}")
                yield
        finally:
            node_log.info("node stopping")
