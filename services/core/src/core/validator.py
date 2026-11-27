from .blockchain import Blockchain
from .mempool import Mempool
from .transaction import Transaction, UTXOSet


class Validator:
    def __init__(self, blockchain: Blockchain, mempool: Mempool) -> None:
        self.blockchain = blockchain
        self.mempool = mempool

    def get_valid_transactions(self) -> tuple[Transaction, ...]:
        """Вернуть транзакции из мемпула, которые можно включить в блок."""
        # Проверяем на копии, чтобы сохранить выходы в основной цепочке.
        staged_utxos = UTXOSet()
        staged_utxos.outputs = self.blockchain.utxo_set.outputs.copy()
        valid_transactions: list[Transaction] = []

        # Идём по порядку. Если две транзакции тратят один выход, пройдёт только первая допустимая.
        for transaction in self.mempool.get_transactions():
            try:
                staged_utxos.apply(transaction, self.blockchain.verify_signature)
            except (ValueError, KeyError):
                continue
            valid_transactions.append(transaction)

        return tuple(valid_transactions)
