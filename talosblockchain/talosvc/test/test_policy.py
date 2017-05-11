import unittest

from talosvc.policy import Policy, create_policy_from_json_str
from talosvc.config import *
from talosvc.policydb import create_db, TalosPolicyDB

import binascii


class TestPolicy(unittest.TestCase):

    def test_1(self):
        policy = Policy("Me", 12, 1, "nonce")
        policy.add_share(["A", "B"])
        policy.add_time_interval(12, 3)
        print policy.to_json()
        res = """{"_start_points": [12], "_shares": ["A", "B"], "_intervals": [12]
        , "_version": 1, "_owner": "Me", "_stream_id": 12, "_nonce": "nonce"}"""
        self.assertEquals(res, policy.to_json())

    def test_2(self):
        state = TalosPolicyDB("./talos-virtualchain.db")
        policyA = state.get_policy("mtr5ENEQ73HZMeZvUEjXdWRJvMhQJMHzcJ", 1)
        policyA_str = policyA.to_json()
        polcyB = create_policy_from_json_str(policyA_str)
        self.assertEquals(policyA_str, polcyB.to_json())
        print policyA_str


class TestRandom(unittest.TestCase):

    def test_rand(self):
        str = get_policy_cmd_create_str(1, 12, 13, 24, "ABDGFHDTARSGDTSF")
        res = parse_policy_cmd_create_data(str[3:])
        print res

    def test_addd(self):
        str = get_policy_cmd_addaccess_str()
        res = parse_policy_cmd_create_data(str[3:])
        print res

    def test_rand(self):
        db = create_db("test.db")
        db.close()
        print "ok"

    def test_dem1(self):
        data = get_policy_cmd_create_str(1, 1, 100, 200, '\x00' * 16)
        print binascii.hexlify(data)