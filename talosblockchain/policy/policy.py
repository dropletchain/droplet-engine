

class Policy:

    def __init__(self):
        self._shares = []
        pass

    def get_shares(self):
        return self._shares

    def get_owner(self):
        return self._owner

    def get_user_id(self):
        return self._user_id

    def get_stream_id(self):
        return self._stream_id

    def get_start_timepoint(self):
        return self._start_point

    def get_interval(self):
        return self.get_interval()