import asyncio

from grpclib.server import Server

from node.generated.pmwallet.v1 import (
    GetBalanceRequest,
    GetBalanceResponse,
    GetTransactionStatusRequest,
    GetTransactionStatusResponse,
    NodeServiceBase,
    PrepareTransactionRequest,
    PrepareTransactionResponse,
    SubmitTransactionRequest,
    SubmitTransactionResponse,
    TransactionStatus,
)


class NodeService(NodeServiceBase):
    async def get_balance(self, message: GetBalanceRequest) -> GetBalanceResponse:
        return GetBalanceResponse(balance=1000)

    async def prepare_transaction(
        self, message: PrepareTransactionRequest
    ) -> PrepareTransactionResponse:
        """1 стадия create transaction"""

        return PrepareTransactionResponse(
            signing_hashes=[bytes([33])],
            unsigned_transaction=bytes([33]),
        )

    async def submit_transaction(
        self, message: SubmitTransactionRequest
    ) -> SubmitTransactionResponse:
        return SubmitTransactionResponse(tx_id="submitted")

    async def get_transaction_status(
        self, message: GetTransactionStatusRequest
    ) -> GetTransactionStatusResponse:
        return GetTransactionStatusResponse(status=TransactionStatus.CONFIRMED)


async def start_server():
    HOST = "127.0.0.1"
    PORT = 1337
    server = Server([NodeService()])
    await server.start(HOST, PORT)
    await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(start_server())
