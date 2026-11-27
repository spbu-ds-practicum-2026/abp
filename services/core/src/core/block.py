from dataclasses import dataclass
import json
import hashlib

from .transaction import Transaction


def calculate_merkle_root(
    transactions: list[Transaction] | tuple[Transaction, ...],
) -> str:
    # Листья дерева — tx_id транзакций в том же порядке, что и в блоке.
    level = [transaction.tx_id for transaction in transactions]

    if not level:
        return hashlib.sha256(b"").hexdigest()

    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])

        level = [
            hashlib.sha256(level[index] + level[index + 1]).digest()
            for index in range(0, len(level), 2)
        ]

    return level[0].hex()


@dataclass
class BlockHeader():
    height: int # Порядковый номер блока в цепочке 
    prev_hash: str
    tx_root: str # Корень дерева Меркла транзакций
    timestamp: int
    difficulty_bits: int
    nonce: int 
    version: int = 1 # Версия блока 

    def to_bytes(self) -> bytes:
        data = {
            "version": self.version,
            "height": self.height,
            "prev_hash": self.prev_hash,
            "tx_root": self.tx_root,
            "timestamp": self.timestamp,
            "difficulty_bits": self.difficulty_bits,
            "nonce": self.nonce,
        }

        text = json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        return text.encode("utf-8")

    @property
    def block_hash(self) -> bytes:
        return hashlib.sha256(self.to_bytes()).digest()

    def has_valid_proof(self) -> bool:
        # difficulty_bits — число нулевых битов в начале хеша.
        if not 0 <= self.difficulty_bits <= 256:
            return False
        target = 1 << (256 - self.difficulty_bits)
        return int.from_bytes(self.block_hash, "big") < target


class Block:
    def __init__(
        self,
        header: BlockHeader,
        transactions: list[Transaction] | tuple[Transaction, ...],
    ) -> None:
        self.transactions = tuple(transactions)

        tx_root = calculate_merkle_root(self.transactions)
        if header.tx_root != tx_root:
            raise ValueError("Корень Меркла не совпадает со списком транзакций")

        self.header = header

    def to_bytes(self) -> bytes:
        # Сохраняем в одном JSON заголовок и полные транзакции
        block_data = {
            "header": json.loads(self.header.to_bytes()),
            "transactions": [
                json.loads(transaction.to_bytes())
                for transaction in self.transactions
            ],
        }

        block_text = json.dumps(
            block_data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        return block_text.encode("utf-8")

    @property
    def block_hash(self) -> bytes:
        return self.header.block_hash

    def has_valid_proof(self) -> bool:
        return self.header.has_valid_proof()


class GenesisBlock(Block):
    def __init__(self, difficulty_bits: int = 20, timestamp: int = 0) -> None:
        transactions: tuple[Transaction, ...] = ()
        header = BlockHeader(
            height=0,
            prev_hash="0" * 64,
            tx_root=calculate_merkle_root(transactions),
            timestamp=timestamp,
            difficulty_bits=difficulty_bits,
            nonce=0,
        )
        super().__init__(header, transactions)
