from .transaction import Transaction


class Mempool:
    def __init__(self) -> None:
        self._transactions: dict[bytes, Transaction] = {}

    def add(self, transaction: Transaction) -> bool:
        tx_id = transaction.tx_id
        if tx_id in self._transactions:
            return False

        self._transactions[tx_id] = transaction
        return True

    def get(self, tx_id: bytes) -> Transaction | None:
        """Найти транзакцию по ID или вернуть None"""
        return self._transactions.get(tx_id)

    def get_transactions(self) -> tuple[Transaction, ...]:
        """Вернуть текущие транзакции в порядке добавления"""
        return tuple(self._transactions.values())

    def remove(self, tx_id: bytes) -> Transaction | None:
        """Удалить транзакцию, например после включения в блок"""
        return self._transactions.pop(tx_id, None)

    def __len__(self) -> int:
        return len(self._transactions)
