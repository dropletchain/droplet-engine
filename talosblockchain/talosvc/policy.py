import json
import base64
from collections import OrderedDict

from talosvc.config import *


class Policy:
    """
    Represents a Policy in the system, which has to be enforced on the datastreams.
    """
    def __init__(self, owner, owner_pk, stream_id, nonce, txid):
        """
        :param owner: owner bitcoin address
        :param owner_pk: public key as hex
        :param stream_id: stream identifier as an integer
        :param nonce: a 16 byte random nonce
        :param txid: the transaction id of the policy creation
        """
        self.shares = []
        self.times = []
        self.owner = str(owner)
        self.stream_id = stream_id
        self.nonce = nonce
        self.txid = str(txid)
        self.owner_pk = str(owner_pk)

    def add_share(self, share):
        if isinstance(share, list):
            self.shares = self.shares + share
        else:
            self.shares.append(share)

    def remove_share(self, share):
        self.shares = [(a, b) for (a, b) in self.shares if a != share]

    def add_time_tuple(self, time):
        if isinstance(time, list):
            self.times += time
        else:
            self.times.append(time)

    def get_shares(self):
        return self.shares

    def get_owner(self):
        return self.owner

    def get_stream_id(self):
        return self.stream_id

    def get_start_timepoints(self):
        return [x for (x, _, _) in self.times]

    def get_intervals(self):
        return [x for (_, x, _) in self.times]

    def get_nonce(self):
        return self.nonce

    def get_txid(self):
        return self.txid

    def get_nonce_bin(self):
        return base64.b64decode(self.nonce)

    def has_shared_key(self, key):
        for (a, _) in self.shares:
            if a == key:
                return True
        return False

    def to_json(self):
        out = OrderedDict([
            (OPCODE_FIELD_OWNER, self.owner),
            (OPCODE_FIELD_STREAM_ID, self.stream_id),
            (OPCODE_FIELD_OWNER_PK, self.owner_pk),
            (OPCODE_FIELD_NONCE, self.nonce),
            (OPCODE_FIELD_TXTID, self.txid),
            ("shares", [OrderedDict([('pk_addr', pk), (OPCODE_FIELD_TXTID, txid)]) for (pk, txid) in self.shares]),
            ("times", [OrderedDict([(OPCODE_FIELD_TIMESTAMP_START, ts_start),
                                    (OPCODE_FIELD_INTERVAL, ts_interval),
                                    (OPCODE_FIELD_TXTID, txid)]) for (ts_start, ts_interval, txid) in self.times])
        ])
        return json.dumps(out)


def create_policy_from_json_str(json_str):
    json_map = json.loads(json_str)
    policy = Policy(json_map[OPCODE_FIELD_OWNER],
                    json_map[OPCODE_FIELD_OWNER_PK],
                    json_map[OPCODE_FIELD_STREAM_ID],
                    json_map[OPCODE_FIELD_NONCE],
                    json_map[OPCODE_FIELD_TXTID])
    for map in json_map["shares"]:
        policy.add_share((map['pk_addr'], map[OPCODE_FIELD_TXTID]))
    for map in json_map["times"]:
        policy.add_time_tuple((map[OPCODE_FIELD_TIMESTAMP_START], map[OPCODE_FIELD_INTERVAL], map[OPCODE_FIELD_TXTID]))
    return policy


def create_policy_from_db_tuple(policy_tuple):
    """
    tuple form: (stream_id, owner, owner_pubkey, nonce, txid)
    """
    return Policy(policy_tuple[1], policy_tuple[2],  policy_tuple[0], policy_tuple[3], policy_tuple[4])
