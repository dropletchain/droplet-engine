#© 2017-2020, ETH Zurich, D-INFK, lubu@inf.ethz.ch

from pybitcoin import BitcoinPrivateKey, BitcoindClient, broadcast_transaction
from pybitcoin import make_op_return_tx

version_byte_private = 111

"""
Test Network requires a diffrent  version byte!!!!!!!!
"""


class BitcoinTestnetPrivateKey(BitcoinPrivateKey):
    _pubkeyhash_version_byte = version_byte_private


private_key_hex = 'cSi82vbDR5NQUJ2eB55C4oz1LxEsA6NePmXM7zNGNSXYbSt6Aop1'
msg = "Lubu is great2"

private_key = BitcoinTestnetPrivateKey(private_key_hex)
print private_key.to_wif()
print private_key.to_hex()
print private_key.public_key().address()

client = BitcoindClient("talos", "talos", port=18332, version_byte=111)

tx = make_op_return_tx(msg, private_key, client, fee=10000, format='bin')
broadcast_transaction(tx, client)
