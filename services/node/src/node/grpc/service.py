import structlog
from adaptix.conversion import get_converter
from core import InsufficientFundsError, TransactionService
from core.transaction import Transaction
from grpclib import GRPCError
from grpclib.const import Status

from node.grpc.generated.pmwallet.v1 import (
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
from node.grpc.generated.pmwallet.v1 import (
    Transaction as TransactionMessage,
)
from node.grpc.mempool import Mempool

log = structlog.get_logger("node.grpc.access")

transaction_from_message = get_converter(TransactionMessage, Transaction)
transaction_to_message = get_converter(Transaction, TransactionMessage)

class NodeService(NodeServiceBase):
    def __init__(self, mempool: Mempool, transaction_service: TransactionService) -> None:
        self._mempool = mempool
        self._transactions = transaction_service

    async def get_balance(self, message: GetBalanceRequest) -> GetBalanceResponse:
        try:
            balance = await self._transactions.get_balance(message.address.hex())
        except ValueError as error:
            raise GRPCError(Status.INVALID_ARGUMENT, str(error)) from error
        return GetBalanceResponse(balance=balance)

    async def prepare_transaction(
        self, message: PrepareTransactionRequest
    ) -> PrepareTransactionResponse:
        reserved = await self._mempool.reserved_outpoints()
        try:
            unsigned_transaction = await self._transactions.prepare_transaction(
                sender_public_key=message.sender_public_key,
                recipient_address=message.recipient_address,
                amount=message.amount,
                reserved_outpoints=reserved,
            )
        except InsufficientFundsError as error:
            raise GRPCError(Status.FAILED_PRECONDITION, str(error)) from error
        except ValueError as error:
            raise GRPCError(Status.INVALID_ARGUMENT, str(error)) from error
        return PrepareTransactionResponse(
            unsigned_transaction=transaction_to_message(unsigned_transaction)
        )

    async def submit_transaction(
        self, message: SubmitTransactionRequest
    ) -> SubmitTransactionResponse:
        try:
            if message.signed_transaction is None:
                raise ValueError("Не передана подписанная транзакция")
            transaction = transaction_from_message(message.signed_transaction)
            await self._transactions.validate_transaction(transaction)
            accepted = await self._mempool.add_validated(transaction)
        except ValueError as error:
            raise GRPCError(Status.INVALID_ARGUMENT, str(error)) from error

        log.info("Transaction accepted into mempool", tx_id=accepted)
        return SubmitTransactionResponse(tx_id=accepted)

    async def get_transaction_status(
        self, message: GetTransactionStatusRequest
    ) -> GetTransactionStatusResponse:
        signed_transaction = await self._mempool.get_transaction(message.tx_id)
        status = (
            TransactionStatus.PENDING
            if signed_transaction is not None
            else TransactionStatus.NOT_FOUND
        )
        return GetTransactionStatusResponse(status=status, confirmations=0)
