# Node

## Запуск

```bash
uv run --package node python -m node
```

Остановить сервер: `Ctrl+C`.

Сервис одновременно поднимает:

- HTTP healthcheck через FastAPI/Uvicorn: `http://127.0.0.1:8000/health`;
- gRPC NodeService: `http://127.0.0.1:1337`.

Настройка через env: `HTTP_HOST`, `HTTP_PORT`, `GRPC_HOST`, `GRPC_PORT` и `LOG_LEVEL`.

## Проверить

```bash
uv run --package node python - <<'PY'
import grpc
from node.generated.pmwallet.v1 import *

channel = grpc.insecure_channel("127.0.0.1:1337")
grpc.channel_ready_future(channel).result(timeout=5)
stub = NodeServiceStub(channel)

print(stub.get_balance(GetBalanceRequest(address=b"address")))
print(stub.prepare_transaction(PrepareTransactionRequest(
    sender_public_key=b"sender",
    recipient_address=b"recipient",
    amount=100,
)))
print(stub.submit_transaction(SubmitTransactionRequest(
    signed_transaction=b"signed",
)))
print(stub.get_transaction_status(GetTransactionStatusRequest(
    tx_id="submitted",
)))
channel.close()
PY
```
