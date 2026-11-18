from dataclasses import dataclass



@dataclass(frozen=True)
class TxInput:
    previous_tx_id: bytes
    output_index: int
    public_key: bytes
    signature: bytes


@dataclass(frozen=True)
class TxOutput:
    recipient: str
    amount: int


@dataclass(frozen=True)
class Transaction:
    inputs: tuple[TxInput, ...]
    outputs: tuple[TxOutput, ...]


    @property
    def tx_id(self) -> bytes:
        return 0




class UTXOSet:
    def __init__(self):
        self.outputs: dict[tuple[bytes, int], TxOutput] = {}

    def add(
        self,
        tx_id: bytes,
        output_index: int,
        output: TxOutput,
    ) -> None:
        """Добавить новый непотраченный выход."""
        return 0

    def get(self, tx_id: bytes, output_index: int) -> TxOutput:
        """Найти непотраченный выход."""
        return 0

    def spend(self, tx_id: bytes, output_index: int) -> TxOutput:
        """Удалить потраченный выход и вернуть его."""
        return 0

    def apply(
        self,
        tx: Transaction,
        verify_signature ,
    ) -> None:
        """Проверить транзакцию и обновить набор UTXO."""
        return 0