from pybitcoin import BitcoinPrivateKey, BitcoindClient, broadcast_transaction
from pybitcoin import make_op_return_tx
import util

version_byte_private=111

class BitcoinTestnetPrivateKey(BitcoinPrivateKey):
    _pubkeyhash_version_byte = version_byte_private


def write_data(client, data, private_key):
    tx = make_op_return_tx(data, private_key, client, fee=10000, format='bin')
    broadcast_transaction(tx, client)


private_key_hex = 'cNroeSoDjaHGFGRz1DYVDj1euaBYuh2nLzzsTTtJxd4kpfWRCzAX'
private_key = BitcoinTestnetPrivateKey(private_key_hex)
client = BitcoindClient("talos", "talos", port=18332, version_byte=111)

max_id = 10

for i in range(max_id):
    data1 = util.MAGIC_BYTES + util.ADD + "0%d" % i + "Hello"
    data2 = util.MAGIC_BYTES + util.CHANGE + "0%d" % i + "Hello World"
    data3 = util.MAGIC_BYTES + util.DELETE + "0%d" % i

    write_data(client, data1, private_key)
    write_data(client, data2, private_key)
    write_data(client, data3, private_key)

