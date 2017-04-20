import requests

from talosvc.policy import create_policy_from_json_str


class TalosVCRestClientError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class TalosVCRestClient(object):
    def __init__(self, ip='127.0.0.1', port=5000):
        self.ip = ip
        self.port = port

    def _check_code(self, code, reason):
        if not code == 200:
            raise TalosVCRestClientError(reason)

    def get_policy(self, owner, streamid):
        req = requests.get("http://%s:%d/policy?owner=%s&stream-id=%d" % (self.ip, self.port, owner, int(streamid)))
        self._check_code(req.status_code, req.reason)
        return create_policy_from_json_str(req.text)

    def get_policies_for_owner(self, owner):
        req = requests.get("http://%s:%d/streamids?owner=%s" % (self.ip, self.port, owner))
        self._check_code(req.status_code, req.reason)
        return [int(i) for i in req.json()['stream-ids']]

    def get_owners(self, limit=10, offset=0):
        req = requests.get("http://%s:%d/owners?limit=%d&offset=%d" % (self.ip, self.port, limit, offset))
        self._check_code(req.status_code, req.reason)
        return [str(x) for x in req.json()['owners']]

    def get_policy_with_txid(self, txid):
        req = requests.get("http://%s:%d/policy?txid=%s" % (self.ip, self.port, txid))
        self._check_code(req.status_code, req.reason)
        return create_policy_from_json_str(req.text)
