from time import time

from .block import Block, BlockHeader, calculate_merkle_root
from .validator import Validator


class Miner:
    def mine(self, block: Block) -> bool:
        """Подобрать nonce для текущей сложности блока."""
        bits = block.header.difficulty_bits
        if type(bits) is not int or not 0 <= bits <= 256:
            raise ValueError("Сложность должна быть целым числом от 0 до 256")

        while not block.has_valid_proof():
            block.header.nonce += 1
        return True

    def mine_next_block(self, validator: Validator) -> Block:
        chain = validator.blockchain
        parent = chain.tip
        transactions = validator.get_valid_transactions()
        header = BlockHeader(
            height=parent.header.height + 1,
            prev_hash=parent.block_hash.hex(),
            tx_root=calculate_merkle_root(transactions),
            timestamp=max(int(time()), parent.header.timestamp),
            difficulty_bits=parent.header.difficulty_bits,
            nonce=0,
        )
        block = Block(header, transactions)
        self.mine(block)
        chain.add_block(block)

        # Удаляем переводы из мемпула только после принятия блока.
        for transaction in transactions:
            validator.mempool.remove(transaction.tx_id)
        return block
