# Node

## Запуск

```bash
uv run --package node python -m node
```

Остановить сервер: `Ctrl+C`.

Сервис одновременно поднимает:

- HTTP healthcheck через FastAPI/Uvicorn: `http://127.0.0.1:8000/health`;
- gRPC NodeService: `http://127.0.0.1:5051`.

Настройка через env: `HTTP_HOST`, `HTTP_PORT`, `GRPC_HOST`, `GRPC_PORT`, `LOG__LEVEL`, `LOG__COLORS` и `LOG__TIMESTAMP_FORMAT`.

## Проверить

```bash
uv run --package node python - <<'PY'
import grpc
from node.grpc.generated.pmwallet.v1 import *

channel = grpc.insecure_channel("127.0.0.1:5051")
grpc.channel_ready_future(channel).result(timeout=5)
stub = NodeServiceStub(channel)

print(stub.get_balance(GetBalanceRequest(address=b"address")))
channel.close()
PY
```
