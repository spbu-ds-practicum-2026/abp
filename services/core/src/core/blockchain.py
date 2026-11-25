from .block import Block, BlockHeader, GenesisBlock, calculate_merkle_root
from .transaction import UTXOSet, VerifySignature


class Blockchain:
    def __init__(
        self,
        verify_signature: VerifySignature,
        genesis_block: Block | None = None,
        initial_utxos: UTXOSet | None = None,
    ) -> None:
        genesis = genesis_block if genesis_block is not None else GenesisBlock()
        if genesis.header.height != 0:
            raise ValueError("Genesis-блок должен иметь высоту 0")
        if genesis.header.prev_hash != "0" * 64:
            raise ValueError("У genesis-блока не должно быть предыдущего хеша")

        self.blocks: list[Block] = [genesis]
        self.verify_signature = verify_signature

        self.utxo_set = UTXOSet()
        if initial_utxos is not None:
            self.utxo_set.outputs = initial_utxos.outputs.copy()

    @property
    def tip(self) -> Block:
        return self.blocks[-1]

    def add_block(self, block: Block) -> None:
        header = block.header
        previous_header = self.tip.header

        if header.height != previous_header.height + 1:
            raise ValueError("Высота блока должна быть на единицу больше предыдущей")
        if header.prev_hash != self.tip.block_hash.hex():
            raise ValueError("Блок ссылается не на текущую вершину цепочки")
        if header.difficulty_bits != previous_header.difficulty_bits:
            raise ValueError("Сложность блока не совпадает со сложностью цепочки")
        if header.timestamp < previous_header.timestamp:
            raise ValueError("Время блока меньше времени предыдущего блока")
        if header.tx_root != calculate_merkle_root(block.transactions):
            raise ValueError("Корень Меркла не совпадает со списком транзакций")
        if not block.has_valid_proof():
            raise ValueError("Блок не прошёл Proof of Work")

        updated_utxos = UTXOSet()
        updated_utxos.outputs = self.utxo_set.outputs.copy()
        for transaction in block.transactions:
            updated_utxos.apply(transaction, self.verify_signature)

        self.blocks.append(block)
        self.utxo_set = updated_utxos

    def get_block(self, height: int) -> Block:
        """Вернуть блок по высоте."""
        if type(height) is not int or not 0 <= height < len(self.blocks):
            raise IndexError("Блока с такой высотой нет в цепочке")
        return self.blocks[height]


if __name__ == "__main__":
    # Сложность 0 нужна только для быстрого локального примера.
    genesis = GenesisBlock(difficulty_bits=0)
    blockchain = Blockchain(
        verify_signature=lambda public_key, message, signature: True,
        genesis_block=genesis,
    )

    transactions = ()
    next_block = Block(
        header=BlockHeader(
            height=1,
            prev_hash=genesis.block_hash.hex(),
            tx_root=calculate_merkle_root(transactions),
            timestamp=1,
            difficulty_bits=0,
            nonce=0,
        ),
        transactions=transactions,
    )

    blockchain.add_block(next_block)
    print("Высота вершины:", blockchain.tip.header.height)
    print("Хеш вершины:", blockchain.tip.block_hash.hex())
