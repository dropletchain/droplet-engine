import struct
import os
import base64

from pybitcoin import BitcoinPrivateKey, address

from virtualchain import get_working_dir, get_db_filename

#################
# BITCOIN RELATED#
#################

MAX_BITCOIN_BYTES = 80

FIRST_BLOCK_OF_INTEREST = 1000

DEFAULT_FEE = 10000

VERSION_BYTE_TESTNET = 111
VERSION_BYTE_MAIN = 0

if 'TALOS_MAINNET' in os.environ and os.environ['TALOS_MAINNET'] == "1":
    USED_VERSIONBYTE = VERSION_BYTE_MAIN
else:
    USED_VERSIONBYTE = VERSION_BYTE_TESTNET


class BitcoinVersionedPrivateKey(BitcoinPrivateKey):
    _pubkeyhash_version_byte = USED_VERSIONBYTE


def get_private_key(private_key):
    return BitcoinVersionedPrivateKey(private_key)


def get_default_talos_config():
    import talosvirtualchain
    return {"bitcoind_port": 18332,
            "bitcoind_user": "talos",
            "bitcoind_passwd": "talos",
            "bitcoind_server": "127.0.0.1",
            "bitcoind_p2p_port": 18444,
            "bitcoind_spv_path": os.path.join(get_working_dir(impl=talosvirtualchain), "tmp.dat")}


def get_working_db():
    import talosvirtualchain
    return get_db_filename(impl=talosvirtualchain)

def get_working_path_file():
    import talosvirtualchain
    return os.path.join(get_working_dir(impl=talosvirtualchain), "tmp.dat")

##############
# Virtualchain#
##############

"""
Operations brackets indicate size in bytes:
CREATE_POLICY(1) <type>(1) <Stream-id>(4) <TS-Start>(8) <TS-Interval>(8) <policy-nonce>(16)
GRANT_ACCESS(1) <Stream-id>(4) <num_keys>(1) <hash pub-key-share1>(32) [<hash pub-key-share2>(32) optional]
REVOKE_ACCESS(1) <Stream-id>(4) <num_keys>(1) <hash pub-key-share1>(32) [<hash pub-key-share2>(32) optional]
CHANGE_INTERVAL(1) <Stream-id>(4) <TS-Start>(8) <TS-Interval>(8)
INVALIDATE_POLICY(1) <Stream-id>(4)
"""

MAGIC_BYTES = 'ta'

# Opcodes
CREATE_POLICY = '+'
GRANT_ACCESS = '>'
REVOKE_ACCESS = '<'
CHANGE_INTERVAL = ':'
INVALIDATE_POLICY = '-'

OPCODES = [
    CREATE_POLICY,
    GRANT_ACCESS,
    REVOKE_ACCESS,
    CHANGE_INTERVAL,
    INVALIDATE_POLICY
]

OPCODE_NAMES = {
    CREATE_POLICY: "CREATE_POLICY",
    GRANT_ACCESS: "GRANT_ACCESS",
    REVOKE_ACCESS: "REVOKE_ACCESS",
    CHANGE_INTERVAL: "CHANGE_INTERVAL",
    INVALIDATE_POLICY: "INVALIDATE_POLICY"
}

OPCODE_FIELD_TYPE = 'type'
OPCODE_FIELD_STREAM_ID = 'streamid'
OPCODE_FIELD_TIMESTAMP_START = 'ts_start'
OPCODE_FIELD_INTERVAL = 'ts_interval'
OPCODE_FIELD_NONCE = 'nonce'
OPCODE_FIELD_PUBLIC_KEYS = 'pks'
OPCODE_FIELD_OWNER = 'owner'
OPCODE_FIELD_OWNER_PK = 'owner_pk'
OPCODE_FIELD_TXTID = 'txid'

OPCODE_FIELDS = {
    CREATE_POLICY: [OPCODE_FIELD_TYPE, OPCODE_FIELD_STREAM_ID, OPCODE_FIELD_TIMESTAMP_START,
                    OPCODE_FIELD_INTERVAL, OPCODE_FIELD_NONCE],
    GRANT_ACCESS: [OPCODE_FIELD_STREAM_ID, OPCODE_FIELD_PUBLIC_KEYS],
    REVOKE_ACCESS: [OPCODE_FIELD_STREAM_ID, OPCODE_FIELD_PUBLIC_KEYS],
    CHANGE_INTERVAL: [OPCODE_FIELD_STREAM_ID, OPCODE_FIELD_TIMESTAMP_START, OPCODE_FIELD_INTERVAL],
    INVALIDATE_POLICY: [OPCODE_FIELD_STREAM_ID]
}

NAME_OPCODES = {
    "CREATE_POLICY": CREATE_POLICY,
    "GRANT_ACCESS": GRANT_ACCESS,
    "REVOKE_ACCESS": REVOKE_ACCESS,
    "CHANGE_INTERVAL": CHANGE_INTERVAL,
    "INVALIDATE_POLICY": "INVALIDATE_POLICY"
}


def get_policy_cmd_create_str(type, stream_id, timestamp_start, interval, nonce):
    cmd = MAGIC_BYTES + CREATE_POLICY + struct.pack("BIQQ", type, stream_id, timestamp_start, interval) + nonce
    assert len(cmd) <= MAX_BITCOIN_BYTES
    return cmd


def get_policy_cmd_addaccess_str(stream_id, keys):
    assert len(keys) <= 2
    cmd = MAGIC_BYTES + GRANT_ACCESS + struct.pack("IB", stream_id, len(keys))
    for key in keys:
        bin_key = address.address_to_bin_hash160(key)
        cmd += struct.pack("B", len(bin_key)) + bin_key
    assert len(cmd) <= MAX_BITCOIN_BYTES
    return cmd


def get_policy_cmd_removeacces_str(stream_id, keys):
    assert len(keys) <= 2
    cmd = MAGIC_BYTES + REVOKE_ACCESS + struct.pack("IB", stream_id, len(keys))
    for key in keys:
        bin_key = address.address_to_bin_hash160(key)
        cmd += struct.pack("B", len(bin_key)) + bin_key
    assert len(cmd) <= MAX_BITCOIN_BYTES
    return cmd


def get_policy_change_interval_str(stream_id, timestamp_start, interval):
    cmd = MAGIC_BYTES + CHANGE_INTERVAL + struct.pack("IQQ", stream_id, timestamp_start, interval)
    assert len(cmd) <= MAX_BITCOIN_BYTES
    return cmd


def get_policy_invalidate_str(stream_id):
    cmd = MAGIC_BYTES + INVALIDATE_POLICY + struct.pack("I", stream_id)
    assert len(cmd) <= MAX_BITCOIN_BYTES
    return cmd


def parse_policy_cmd_create_data(create_str_data):
    size_struct = struct.calcsize("BIQQ")
    type, stream_id, timestamp_start, interval = struct.unpack("BIQQ", create_str_data[:size_struct])
    nonce = create_str_data[size_struct:]
    return {
        OPCODE_FIELD_TYPE: type,
        OPCODE_FIELD_STREAM_ID: stream_id,
        OPCODE_FIELD_TIMESTAMP_START: timestamp_start,
        OPCODE_FIELD_INTERVAL: interval,
        OPCODE_FIELD_NONCE: base64.b64encode(nonce)
    }


def parse_policy_cmd_addaccess_data(addaccess_str_data):
    size_struct = struct.calcsize("IB")
    stream_id, num_keys = struct.unpack("IB", addaccess_str_data[:size_struct])

    keys = []
    for key_id in range(num_keys):
        len, = struct.unpack("B", addaccess_str_data[size_struct:(size_struct + 1)])
        bin_key = addaccess_str_data[(size_struct + 1):(size_struct + 1 + len)]
        keys.append(address.bin_hash160_to_address(bin_key, USED_VERSIONBYTE))
        size_struct += len + 1

    return {
        OPCODE_FIELD_STREAM_ID: stream_id,
        OPCODE_FIELD_PUBLIC_KEYS: ",".join(keys)
    }


def parse_policy_removeacces_data(removeacces_str_data):
    size_struct = struct.calcsize("IB")
    stream_id, num_keys = struct.unpack("IB", removeacces_str_data[:size_struct])

    keys = []
    for key_id in range(num_keys):
        len, = struct.unpack("B", removeacces_str_data[size_struct:(size_struct + 1)])
        bin_key = removeacces_str_data[(size_struct + 1):(size_struct + 1 + len)]
        keys.append(address.bin_hash160_to_address(bin_key, USED_VERSIONBYTE))
        size_struct += len + 1
    return {
        OPCODE_FIELD_STREAM_ID: stream_id,
        OPCODE_FIELD_PUBLIC_KEYS: ",".join(keys)
    }


def parse_policy_change_interval_data(change_interval_data_str):
    size_struct = struct.calcsize("IQQ")
    stream_id, timestamp_start, interval = struct.unpack("IQQ", change_interval_data_str[:size_struct])
    return {
        OPCODE_FIELD_STREAM_ID: stream_id,
        OPCODE_FIELD_TIMESTAMP_START: timestamp_start,
        OPCODE_FIELD_INTERVAL: interval
    }


def parse_policy_invalidate_data(invalidate_interval_data_str):
    size_struct = struct.calcsize("I")
    stream_id, = struct.unpack("I", invalidate_interval_data_str[:size_struct])
    return {
        OPCODE_FIELD_STREAM_ID: stream_id
    }


PARSE_HANDLERS = {
    CREATE_POLICY: parse_policy_cmd_create_data,
    GRANT_ACCESS: parse_policy_cmd_addaccess_data,
    REVOKE_ACCESS: parse_policy_removeacces_data,
    CHANGE_INTERVAL: parse_policy_change_interval_data,
    INVALIDATE_POLICY: parse_policy_invalidate_data
}
