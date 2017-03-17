import json


class Policy:
    def __init__(self, owner, stream_id, nonce, txid):
        self._shares = []
        self._times = []
        self._owner = owner
        self._stream_id = stream_id
        self._nonce = nonce
        self._txid = txid

    def add_share(self, share):
        if isinstance(share, list):
            self._shares = self._shares + share
        else:
            self._shares.append(share)

    def remove_share(self, share):
         self._shares.remove(share)

    def add_time_tuple(self, time):
        if isinstance(time, list):
            self._times = self._times + time
        else:
            self._times.append(time)

    def update_version(self, version):
        self._version = version

    def get_shares(self):
        return self._shares

    def get_owner(self):
        return self._owner

    def get_stream_id(self):
        return self._stream_id

    def get_start_timepoints(self):
        return self._start_points

    def get_intervals(self):
        return self._intervals

    def get_version(self):
        return self._version

    def get_nonce(self):
        return self._nonce

    def get_txid(self):
        return self._txtid

    def to_json(self):
        return json.dumps(self.__dict__)


def create_policy_from_db_tuple(policy_tuple):
    """
    tuple form: (stream_id, owner, owner_pubkey, nonce, txid)
    """
    return Policy(policy_tuple[1], policy_tuple[0], policy_tuple[3], policy_tuple[4])
