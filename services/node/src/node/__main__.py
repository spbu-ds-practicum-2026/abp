import asyncio

import uvicorn
from grpclib.server import Server

from node.config import config
from node.grps_service import NodeService
from node.http_service import app


async def start_grpc_server() -> None:
    server = Server([NodeService()])
    await server.start(config.grpc_host, config.grpc_port)
    await server.wait_closed()


async def start_http_server() -> None:
    uvicorn_config = uvicorn.Config(
        app,
        host=config.http_host,
        port=config.http_port,
        log_level=config.log_level,
    )
    await uvicorn.Server(uvicorn_config).serve()


async def start_servers() -> None:
    print(r"""
                                                 ___    ___           __      
                                                /\_ \  /\_ \         /\ \__   
     _____     ___ ___       __  __  __     __  \//\ \ \//\ \      __\ \ ,_\  
    /\ '__`\ /' __` __`\    /\ \/\ \/\ \  /'__`\  \ \ \  \ \ \   /'__`\ \ \/  
    \ \ \L\ \/\ \/\ \/\ \   \ \ \_/ \_/ \/\ \L\.\_ \_\ \_ \_\ \_/\  __/\ \ \_ 
     \ \ ,__/\ \_\ \_\ \_\   \ \___x___/'\ \__/.\_\/\____\/\____\ \____\\ \__\
      \ \ \/  \/_/\/_/\/_/    \/__//__/   \/__/\/_/\/____/\/____/\/____/ \/__/
       \ \_\                                                                  
        \/_/                                                                  
    """)

    await asyncio.gather(start_grpc_server(), start_http_server())


if __name__ == "__main__":
    asyncio.run(start_servers())
