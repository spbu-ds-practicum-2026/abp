from fastapi import FastAPI

app = FastAPI(title="PMWallet Node")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
