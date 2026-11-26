# ABP

## Структура

- `proto/` — исходные `.proto`-файлы;
- `services/node/` — Python Node-сервис;
- `services/client/` — Rust-клиент;
- `services/core/` — Python Core-сервис;
- `docs/` — техническая документация.

## Предварительные требования

- [`uv`](https://docs.astral.sh/uv/) — установка Python, окружения и зависимостей;
- [`Buf CLI`](https://buf.build/docs/cli/) — lint и генерация `.proto`-файлов.

## Установка

```bash
uv python install 3.14
uv lock
uv sync --all-packages
```

## Сервисы

- [`Node`](services/node/README.md) — Python gRPC-сервис;
- `Client` — Rust-клиент;
- `Core` — Python Core-сервис.

## Buf

Из корня репозитория:

```bash
buf lint
buf generate # for python
```

Rust-типы клиента генерируются при Cargo build