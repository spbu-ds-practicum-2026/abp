from dataclasses import dataclass
import hashlib
import json
from typing import Callable


@dataclass(frozen=True)
class TxInput:
    previous_tx_id: bytes
    output_index: int
    public_key: bytes
    signature: bytes


@dataclass(frozen=True)
class TxOutput:
    recipient: str #hex(SHA-256(public_key)).
    amount: int


@dataclass(frozen=True)
class Transaction:
    inputs: tuple[TxInput, ...]

    outputs: tuple[TxOutput, ...]

    #Данные которые подписывает клиент
    def signing_bytes(self) -> bytes:
        data = {
            "inputs": [
                {
                    "previous_tx_id": tx_input.previous_tx_id.hex(),
                    "output_index": tx_input.output_index,
                    "public_key": tx_input.public_key.hex(),
                }
                for tx_input in self.inputs
            ],
            "outputs": [
                {
                    "recipient": tx_output.recipient,
                    "amount": tx_output.amount,
                }
                for tx_output in self.outputs
            ],
        }

        text = json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        return text.encode("utf-8")

    #финальное представление tx 
    def to_bytes(self) -> bytes:
        data = {
            "inputs": [
                {
                    "previous_tx_id": tx_input.previous_tx_id.hex(),
                    "output_index": tx_input.output_index,
                    "public_key": tx_input.public_key.hex(),
                    "signature": tx_input.signature.hex(),
                }
                for tx_input in self.inputs
            ],
            "outputs": [
                {
                    "recipient": tx_output.recipient,
                    "amount": tx_output.amount,
                }
                for tx_output in self.outputs
            ],
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
    def tx_id(self) -> bytes:
        return hashlib.sha256(self.to_bytes()).digest()


# Функция получает публичный ключ, байты для подписи и подпись
# результат True означает, что подпись корректна
VerifySignature = Callable[[bytes, bytes, bytes], bool]


class UTXOSet:
    def __init__(self) -> None:
        # Ключ — (ID создавшей транзакции, индекс выхода), значение — выход
        self.outputs: dict[tuple[bytes, int], TxOutput] = {}

    def add(
        self,
        tx_id: bytes,
        output_index: int,
        output: TxOutput,
    ) -> None:
        key = (tx_id, output_index)
        if key in self.outputs:
            raise ValueError("Такой выход уже добавлен")
        self.outputs[key] = output

    def get(self, tx_id: bytes, output_index: int) -> TxOutput:
        return self.outputs[(tx_id, output_index)]

    def spend(self, tx_id: bytes, output_index: int) -> TxOutput:
        return self.outputs.pop((tx_id, output_index))

    def apply(
        self,
        tx: Transaction,
        verify_signature: VerifySignature,
    ) -> None:
        if not tx.inputs:
            raise ValueError("В транзакции нет входов")
        if not tx.outputs:
            raise ValueError("В транзакции нет выходов")

        for output in tx.outputs:
            if type(output.amount) is not int or output.amount <= 0:
                raise ValueError("Сумма каждого выхода должна быть положительным целым числом")

        spent_outputs: list[TxOutput] = []
        seen_inputs: set[tuple[bytes, int]] = set()
        message = tx.signing_bytes()

        for tx_input in tx.inputs:
            # Индекс должен обозначать существующее место в списке выходов
            if type(tx_input.output_index) is not int or tx_input.output_index < 0:
                raise ValueError("Индекс выхода должен быть неотрицательным целым числом")

            key = (tx_input.previous_tx_id, tx_input.output_index)
            if key in seen_inputs:
                raise ValueError("Один выход указан во входах несколько раз")
            seen_inputs.add(key)

            # Отсутствующий выход неизвестен или уже был потрачен.
            try:
                previous_output = self.get(*key)
            except KeyError as error:
                raise ValueError("Вход ссылается на неизвестный или потраченный выход") from error

            # Связываем публичный ключ из входа с владельцем найденного выхода.
            expected_recipient = hashlib.sha256(tx_input.public_key).hexdigest()
            if previous_output.recipient != expected_recipient:
                raise ValueError("Публичный ключ не владеет указанным выходом")

            try:
                is_valid = verify_signature(
                    tx_input.public_key,
                    message,
                    tx_input.signature,
                )
            except Exception as error:
                raise ValueError("Не удалось проверить подпись") from error
            if not is_valid:
                raise ValueError("Подпись входа неверна")

            spent_outputs.append(previous_output)

        input_amount = sum(output.amount for output in spent_outputs)
        output_amount = sum(output.amount for output in tx.outputs)
        if input_amount != output_amount:
            raise ValueError("Суммы входов и выходов не совпадают")

        updated_outputs = self.outputs.copy()
        for tx_input in tx.inputs:
            updated_outputs.pop((tx_input.previous_tx_id, tx_input.output_index))

        new_tx_id = tx.tx_id
        for index, output in enumerate(tx.outputs):
            key = (new_tx_id, index)
            if key in updated_outputs:
                raise ValueError("Новый выход с таким ключом уже существует")
            updated_outputs[key] = output

        self.outputs = updated_outputs


if __name__ == "__main__":
    # Создаём тестовый выход, принадлежащий публичному ключу входа.
    utxo_set = UTXOSet()
    previous_tx_id = b"debug-transaction"
    public_key = b"debug-public-key"
    alice_address = hashlib.sha256(public_key).hexdigest()
    output = TxOutput(recipient=alice_address, amount=10)
    utxo_set.add(previous_tx_id, 0, output)

    assert utxo_set.get(previous_tx_id, 0) == output
    print("Выход найден:", utxo_set.get(previous_tx_id, 0))

    transaction = Transaction(
        inputs=(
            TxInput(
                previous_tx_id=previous_tx_id,
                output_index=0,
                public_key=public_key,
                signature=b"debug-signature",
            ),
        ),
        outputs=(
            TxOutput(recipient="debug-recipient", amount=7),
            TxOutput(recipient=alice_address, amount=3),
        ),
    )

    def debug_verify_signature(key: bytes, message: bytes, signature: bytes) -> bool:
        # Это заглушка для демонстрации apply, а не настоящая криптопроверка.
        return (
            key == public_key
            and message == transaction.signing_bytes()
            and signature == b"debug-signature"
        )

    assert transaction.to_bytes() == transaction.to_bytes()
    assert len(transaction.tx_id) == 32
    utxo_set.apply(transaction, debug_verify_signature)

    # Проверяем, что старый выход удалён, а оба новых доступны.
    assert (previous_tx_id, 0) not in utxo_set.outputs
    assert utxo_set.get(transaction.tx_id, 0).amount == 7
    assert utxo_set.get(transaction.tx_id, 1).amount == 3
    print("Перевод применён: старый выход потрачен, новые выходы созданы")
    print("tx_id (32 байта):", transaction.tx_id.hex())
