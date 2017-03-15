from pybitcoin import BitcoinPrivateKey, BitcoindClient, broadcast_transaction
from pybitcoin import make_op_return_tx
import util

version_byte_private=111

class BitcoinTestnetPrivateKey(BitcoinPrivateKey):
    _pubkeyhash_version_byte = version_byte_private


def write_data(client, data, private_key):
    tx = make_op_return_tx(data, private_key, client, fee=10000, format='bin')
    broadcast_transaction(tx, client)


private_key_hex = 'cRzqZ5sD7e8hL12x381SPNMiXFd9VaUSnKS5kTtNbWD8cyJjMFL7'
private_key = BitcoinTestnetPrivateKey(private_key_hex)
client = BitcoindClient("talos", "talos", port=18332, version_byte=111)


data1 = util.MAGIC_BYTES + util.ADD + "05" + "Hello"
data2 = util.MAGIC_BYTES + util.CHANGE + "05" + "Hello World"
data3 = util.MAGIC_BYTES + util.DELETE + "05"

write_data(client, data1, private_key)
write_data(client, data2, private_key)
write_data(client, data3, private_key)