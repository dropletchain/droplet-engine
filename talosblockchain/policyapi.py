from cmd import Cmd
import argparse
import time
import os

from pybitcoin import BitcoindClient

from talosvc.config import BitcoinVersionedPrivateKey
from talosvc.talosclient.policycreation import BitcoinPolicyCreator

TESTNET = True

class TalosPrompt(Cmd):

    def __init__(self, policy_creator):
        self.policy_creator = policy_creator
        Cmd.__init__(self)

    def _generate_block(self):
        if TESTNET:
            self.policy_creator.bitcoind_client.bitcoind.generate(1)

    def do_create_policy(self, args):
        """Creates a policy <stream-id> <ts_start> <interval>"""
        parser = argparse.ArgumentParser("Create Policy")
        parser.add_argument('stream_id', type=int)
        parser.add_argument('timestamp_start', type=long, nargs='?', default=long(time.time()))
        parser.add_argument('interval', type=long, nargs='?', default=86200)
        args = parser.parse_args(args.split())
        self.policy_creator.create_policy(1, args.stream_id,
                                          args.timestamp_start, args.interval, os.urandom(16))
        self._generate_block()

    def do_add_share(self, args):
        """Add Share <stream-id> <pk-address>"""
        parser = argparse.ArgumentParser("Add Sahre")
        parser.add_argument('stream_id', type=int)
        parser.add_argument('pk_address')
        args = parser.parse_args(args.split())
        self.policy_creator.add_share_to_policy(args.stream_id, [args.pk_address])
        self._generate_block()

    def do_remove_share(self, args):
        """Remove Share <stream-id> <pk-address>"""
        parser = argparse.ArgumentParser("Remove Share")
        parser.add_argument('stream_id', type=int)
        parser.add_argument('pk_address')
        args = parser.parse_args(args.split())
        self.policy_creator.remove_share_from_policy(args.stream_id, [args.pk_address])
        self._generate_block()

    def do_change_interval(self, args):
        """Remove Share <stream-id> <ts_start> <interval>"""
        parser = argparse.ArgumentParser("Change Interval")
        parser.add_argument('stream_id', type=int)
        parser.add_argument('timestamp_start', type=long)
        parser.add_argument('interval', type=long)
        args = parser.parse_args(args.split())
        self.policy_creator.change_interval_in_policy(args.stream_id, args.timestamp_start, args.interval)
        self._generate_block()

    def do_invalidate_policy(self, args):
        parser = argparse.ArgumentParser("Interval")
        parser.add_argument('stream_id', type=int)

    def do_exit(self, args):
        print "Quitting."
        raise SystemExit

    def do_quit(self, args):
        print "Quitting."
        raise SystemExit


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Run bitcoin client")
    parser.add_argument('--port', type=int, help='dir', default=18332, required=False)
    parser.add_argument('--server', type=str, help='server', default="127.0.0.1", required=False)
    parser.add_argument('--vbyte', type=int, help='server', default=111, required=False)
    parser.add_argument('private_key', type=str)
    args = parser.parse_args()

    TESTNET = args.vbyte == 111

    private_key = BitcoinVersionedPrivateKey(args.private_key)
    client = BitcoindClient("talos", "talos", server=args.server, port=args.port, version_byte=args.vbyte)
    pclient = BitcoinPolicyCreator(client, args.private_key)

    prompt = TalosPrompt(pclient)
    prompt.prompt = '> '
    prompt.cmdloop('Starting prompt...')