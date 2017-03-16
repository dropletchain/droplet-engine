from pybitcoin import BitcoinPrivateKey, BitcoindClient, broadcast_transaction
from pybitcoin import make_op_return_tx
import util
import time

version_byte_private=111

class BitcoinTestnetPrivateKey(BitcoinPrivateKey):
    _pubkeyhash_version_byte = version_byte_private


def write_data(client, data, private_key):
    tx = make_op_return_tx(data, private_key, client, fee=10000, format='bin')
    broadcast_transaction(tx, client)


private_key_hex = 'cVErDAfoyAZ7oNSgtiARpTdqGNKL2Bjkeg1WRo4tw4zcoQGxhCs1'
private_key = BitcoinTestnetPrivateKey(private_key_hex)
client = BitcoindClient("talos", "talos", port=18332, version_byte=111)

from_id=20
max_id = 30

for i in range(from_id, max_id):
    if i>10:
        uid="%d" % i
    else:
        uid="0%d" % i
    data1 = util.MAGIC_BYTES + util.ADD + uid + "Hello"
    data2 = util.MAGIC_BYTES + util.CHANGE + uid + "Hello World"
    data3 = util.MAGIC_BYTES + util.DELETE + uid

    write_data(client, data1, private_key)
    write_data(client, data2, private_key)
    write_data(client, data3, private_key)
    client.bitcoind.generate(1)
    time.sleep(1)

