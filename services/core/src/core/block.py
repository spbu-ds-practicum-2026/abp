from dataclasses import dataclass

@dataclass
class BlockHeader():
    version: int = 1 # Версия блока 
    height: int # Порядковый номер блока в цепочке 
    prev_hash: str
    tx_root: str # Дерево Меркла sha256(concat txId )
    timestamp: int
    diffculity_bits: int = 20
    nonce: int 

class Block():
    
class GenesisBlock():
