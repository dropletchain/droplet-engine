#© 2017-2020, ETH Zurich, D-INFK, lubu@inf.ethz.ch

from pybitcoin import broadcast_transaction
from pybitcoin import make_op_return_tx

from talosvc.config import *


class BitcoinPolicyCreator:
    """
    Class for interacting with the Bitcoin blockchain
    Write, change and delete policies.
    """

    def __init__(self, bitcoind_client, private_key, fee=DEFAULT_FEE):
        self.bitcoind_client = bitcoind_client
        self.fee = fee
        if isinstance(private_key, BitcoinPrivateKey):
            self.private_key = private_key
        else:
            self.private_key = get_private_key(private_key)

    def _send_op_return_txt(self, cmd):
        tx = make_op_return_tx(cmd, self.private_key, self.bitcoind_client, fee=self.fee, format='bin')
        broadcast_transaction(tx, self.bitcoind_client)

    def create_policy(self, type, stream_id, timestamp_start, interval, nonce):
        cmd = get_policy_cmd_create_str(type, stream_id, timestamp_start, interval, nonce)
        self._send_op_return_txt(cmd)

    def add_share_to_policy(self, stream_id, keys):
        cmd = get_policy_cmd_addaccess_str(stream_id, keys)
        self._send_op_return_txt(cmd)

    def remove_share_from_policy(self, stream_id, keys):
        cmd = get_policy_cmd_removeacces_str(stream_id, keys)
        self._send_op_return_txt(cmd)

    def change_interval_in_policy(self, stream_id, time, interval):
        cmd = get_policy_change_interval_str(stream_id, time, interval)
        self._send_op_return_txt(cmd)

    def invalidate_policy(self, stream_id):
        cmd = get_policy_invalidate_str(stream_id)
        self._send_op_return_txt(cmd)
