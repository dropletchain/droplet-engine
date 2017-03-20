import json
from collections import OrderedDict

from talosvc.config import *


class Policy:
    def __init__(self, owner, owner_pk, stream_id, nonce, txid):
        self._shares = []
        self._times = []
        self._owner = owner
        self._stream_id = stream_id
        self._nonce = nonce
        self._txid = txid
        self._owner_pk = owner_pk

    def add_share(self, share):
        if isinstance(share, list):
            self._shares = self._shares + share
        else:
            self._shares.append(share)

    def remove_share(self, share):
        self._shares = [(a, b) for (a, b) in self._shares if a != share]

    def add_time_tuple(self, time):
        if isinstance(time, list):
            self._times += time
        else:
            self._times.append(time)

    def get_shares(self):
        return self._shares

    def get_owner(self):
        return self._owner

    def get_stream_id(self):
        return self._stream_id

    def get_start_timepoints(self):
        return [x for (x, _, _) in self._times]

    def get_intervals(self):
        return [x for (_, x, _) in self._times]

    def get_nonce(self):
        return self._nonce

    def get_txid(self):
        return self._txid

    def has_shared_key(self, key):
        for (a, _) in self._shares:
            if a == key:
                return True
        return False

    def to_json(self):
        out = OrderedDict([
            (OPCODE_FIELD_OWNER, self._owner),
            (OPCODE_FIELD_STREAM_ID, self._stream_id),
            (OPCODE_FIELD_OWNER_PK, self._owner_pk),
            (OPCODE_FIELD_NONCE, self._nonce),
            (OPCODE_FIELD_TXTID, self._txid),
            ("shares", [OrderedDict([('pk_addr', pk), (OPCODE_FIELD_TXTID, txid)]) for (pk, txid) in self._shares]),
            ("times", [OrderedDict([(OPCODE_FIELD_TIMESTAMP_START, ts_start),
                                    (OPCODE_FIELD_INTERVAL, ts_interval),
                                    (OPCODE_FIELD_TXTID, txid)]) for (ts_start, ts_interval, txid) in self._times])
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
