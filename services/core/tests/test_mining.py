import hashlib
import unittest

from core.block import Block, BlockHeader, GenesisBlock, calculate_merkle_root
from core.blockchain import Blockchain
from core.mempool import Mempool
from core.miner import Miner
from core.transaction import Transaction, TxInput, TxOutput, UTXOSet
from core.validator import Validator


class MiningTests(unittest.TestCase):
    def test_mine_requires_valid_nonce(self):
        block = Block(BlockHeader(1, "0" * 64, calculate_merkle_root(()), 1, 8, 0), ())
        while block.has_valid_proof():
            block.header.nonce += 1
        start = block.header.nonce
        self.assertTrue(Miner().mine(block))
        self.assertGreater(block.header.nonce, start)
        self.assertEqual(block.block_hash[0], 0)

    def test_invalid_difficulty(self):
        block = GenesisBlock(difficulty_bits=-1)
        with self.assertRaises(ValueError):
            Miner().mine(block)

    def test_transfer_from_mempool_to_block(self):
        key = b"alice"
        alice = hashlib.sha256(key).hexdigest()
        bob = hashlib.sha256(b"bob").hexdigest()
        initial_id = bytes(32)
        initial = UTXOSet()
        initial.add(initial_id, 0, TxOutput(alice, 10))
        good_input = TxInput(initial_id, 0, key, b"ok")
        outputs = (TxOutput(bob, 7), TxOutput(alice, 3))
        valid = Transaction((good_input,), outputs)
        bad = Transaction((TxInput(initial_id, 0, key, b"bad"),), outputs)
        conflict = Transaction((good_input,), (TxOutput(alice, 10),))

        # Подпись проверяет тестовая функция. Поиск хеша выполняет майнер.
        chain = Blockchain(lambda k, m, s: k == key and s == b"ok", GenesisBlock(8), initial)
        pool = Mempool()
        for tx in (bad, valid, conflict):
            pool.add(tx)
        validator = Validator(chain, pool)
        self.assertEqual(validator.get_valid_transactions(), (valid,))
        self.assertEqual(chain.utxo_set.outputs, initial.outputs)

        block = Miner().mine_next_block(validator)
        self.assertIs(chain.tip, block)
        self.assertEqual(block.header.prev_hash, chain.get_block(0).block_hash.hex())
        self.assertEqual(block.header.height, 1)
        self.assertEqual(block.block_hash[0], 0)
        self.assertEqual(block.transactions, (valid,))
        self.assertEqual(chain.utxo_set.outputs, {(valid.tx_id, i): out for i, out in enumerate(outputs)})
        self.assertEqual(pool.get_transactions(), (bad, conflict))

    def test_spend_mined_output_in_next_block(self):
        alice_key, bob_key = b"alice", b"bob"
        alice, bob, carol = [hashlib.sha256(key).hexdigest() for key in (alice_key, bob_key, b"carol")]
        initial_id = bytes(32)
        initial = UTXOSet()
        initial.add(initial_id, 0, TxOutput(alice, 10))

        payment = Transaction(
            (TxInput(initial_id, 0, alice_key, b"alice-signature"),),
            (TxOutput(bob, 7), TxOutput(alice, 3)),
        )
        onward = Transaction(
            (TxInput(payment.tx_id, 0, bob_key, b"bob-signature"),),
            (TxOutput(carol, 5), TxOutput(bob, 2)),
        )
        # Тестовый проверяющий принимает только эти два подписанных сообщения.
        signatures = {
            (alice_key, payment.signing_bytes(), b"alice-signature"),
            (bob_key, onward.signing_bytes(), b"bob-signature"),
        }
        genesis = GenesisBlock(difficulty_bits=8)
        chain = Blockchain(lambda k, m, s: (k, m, s) in signatures, genesis, initial)
        pool = Mempool()
        validator = Validator(chain, pool)
        miner = Miner()

        # В первом блоке Алиса платит Бобу и получает сдачу.
        pool.add(payment)
        first = miner.mine_next_block(validator)
        self.assertEqual(first.transactions, (payment,))
        self.assertEqual(first.header.prev_hash, genesis.block_hash.hex())
        self.assertEqual(first.block_hash[0], 0)
        self.assertEqual(chain.utxo_set.outputs, {
            (payment.tx_id, 0): TxOutput(bob, 7),
            (payment.tx_id, 1): TxOutput(alice, 3),
        })
        self.assertEqual(len(pool), 0)

        # Во втором блоке Боб тратит полученный выход. Повтор платежа Алисы уже недействителен.
        pool.add(payment)
        pool.add(onward)
        second = miner.mine_next_block(validator)
        self.assertEqual(second.transactions, (onward,))
        self.assertEqual(second.header.prev_hash, first.block_hash.hex())
        self.assertEqual(second.block_hash[0], 0)
        self.assertEqual(chain.blocks, [genesis, first, second])
        self.assertEqual(chain.tip.header.height, 2)
        self.assertEqual(chain.utxo_set.outputs, {
            (payment.tx_id, 1): TxOutput(alice, 3),
            (onward.tx_id, 0): TxOutput(carol, 5),
            (onward.tx_id, 1): TxOutput(bob, 2),
        })
        self.assertEqual(pool.get_transactions(), (payment,))
