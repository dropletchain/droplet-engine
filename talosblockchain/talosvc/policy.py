import json

class Policy:

    def __init__(self, owner, stream_id, version, nonce):
        self._shares = []
        self._start_points = []
        self._intervals = []
        self._owner = owner
        self._stream_id = stream_id
        self._version = version
        self._nonce = nonce

    def add_share(self, share):
        if isinstance(share, list):
            self._shares = self._shares + share
        else:
            self._shares.append(share)

    def add_time_interval(self, time, interval):
        if isinstance(time, list) and isinstance(interval, list):
            self._intervals = self._intervals + interval
            self._start_points = self._start_points + time
        else:
            self._start_points.append(time)
            self._intervals.append(time)

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

    def to_json(self):
        return json.dumps(self.__dict__)
