import asyncio
import sys

import structlog
import uvicorn
from grpclib.server import Server

from node.config import config
from node.grps_service import NodeService
from node.http_service import app
from node.logs import configure_logging

BANNER = r"""
                                                 ___    ___           __      
                                                /\_ \  /\_ \         /\ \__   
     _____     ___ ___       __  __  __     __  \//\ \ \//\ \      __\ \ ,_\  
    /\ '__`\ /' __` __`\    /\ \/\ \/\ \  /'__`\  \ \ \  \ \ \   /'__`\ \ \/  
    \ \ \L\ \/\ \/\ \/\ \   \ \ \_/ \_/ \/\ \L\.\_ \_\ \_ \_\ \_/\  __/\ \ \_ 
     \ \ ,__/\ \_\ \_\ \_\   \ \___x___/'\ \__/.\_\/\____\/\____\ \____\\ \__\
      \ \ \/  \/_/\/_/\/_/    \/__//__/   \/__/\/_/\/____/\/____/\/____/ \/__/
       \ \_                                                                  
        \/_/                                                                  
"""


def print_banner() -> None:
    if sys.stdout.isatty():
        print(f"\033[96m{BANNER.rstrip()}\033[0m", flush=True)
    else:
        print(BANNER.rstrip(), flush=True)


async def run() -> None:
    print_banner()
    configure_logging(config.log)
    log = structlog.get_logger("node")
    log.info("node starting")

    grpc_server = Server([NodeService()])
    uvicorn_server = uvicorn.Server(
        uvicorn.Config(
            app,
            host=config.http_host,
            port=config.http_port,
            log_level=config.log.level,
            log_config=None,
        )
    )

    try:
        await grpc_server.start(config.grpc_host, config.grpc_port)
    except BaseException:
        log.exception("application.failed")
        raise

    log.info("gRPC listening", address=f"{config.grpc_host}:{config.grpc_port}")

    try:
        await asyncio.gather(uvicorn_server.serve(), grpc_server.wait_closed())
    except asyncio.CancelledError:
        raise
    except BaseException:
        log.exception("application.failed")
        raise
    finally:
        log.info("node stopping")
        uvicorn_server.should_exit = True
        grpc_server.close()
        await grpc_server.wait_closed()


if __name__ == "__main__":
    asyncio.run(run())
