from fastapi import FastAPI

from node.lifespan import node_lifespan

app = FastAPI(title="PMWallet Node", lifespan=node_lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
