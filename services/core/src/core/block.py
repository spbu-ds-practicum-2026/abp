from dataclasses import dataclass


@dataclass
class BlockHeader:
    height: int  # Порядковый номер блока в цепочке
    prev_hash: str
    tx_root: str  # Дерево Меркла sha256(concat txId )
    timestamp: int
    version: int = 1  # Версия блока
    difficulty_bits: int = 20
    nonce: int = 0



class Block:
    pass

class GenesisBlock:
    pass
