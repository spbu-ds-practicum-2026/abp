import asyncio
import sys

import colorama
import structlog
import uvicorn

from node.config import config
from node.http.service import app
from node.logs import configure_logging

BANNER = r"""                                                 ___    ___           __      
                                                /\_ \  /\_ \         /\ \__   
     _____     ___ ___       __  __  __     __  \//\ \ \//\ \      __\ \ ,_\  
    /\ '__`\ /' __` __`\    /\ \/\ \/\ \  /'__`\  \ \ \  \ \ \   /'__`\ \ \/  
    \ \ \L\ \/\ \/\ \/\ \   \ \ \_/ \_/ \/\ \L\.\_ \_\ \_ \_\ \_/\  __/\ \ \_ 
     \ \ ,__/\ \_\ \_\ \_\   \ \___x___/'\ \__/.\_\/\____\/\____\ \____\\ \__\
      \ \ \/  \/_/\/_/\/_/    \/__//__/   \/__/\/_/\/____/\/____/\/____/ \/__/
       \ \_                                                                  
        \/_/                                                                  
                              PM Wallet Node

"""


def print_banner() -> None:
    if sys.stdout.isatty() and config.log.colors:
        print(
            colorama.Style.BRIGHT + colorama.Fore.CYAN + BANNER + colorama.Style.RESET_ALL,
            end="",
            flush=True,
        )
    else:
        print(BANNER, flush=True)


async def run() -> None:
    print_banner()
    configure_logging(config.log)
    log = structlog.get_logger("node")
    log.info("node starting")

    uvicorn_server = uvicorn.Server(
        uvicorn.Config(
            app,
            host=config.http_host,
            port=config.http_port,
            log_config=None,
        )
    )
    await uvicorn_server.serve()


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass
