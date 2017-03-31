from config import *
import virtualchain
import sys
from talosvc.policydb import TalosPolicyDB
from threading import Thread
import time

"""
Implementation of the blockstack virtualchain library hooks.
The updates are feeded to our state machine implementation.
"""


def get_virtual_chain_name():
    """
    Get the name of the virtual chain we're building.
    """
    return "talos-virtualchain"


def get_virtual_chain_version():
    """
    Get the version string for this virtual chain.
    """
    return "v1.0"


def get_first_block_id():
    """
    Get the id of the first block to start indexing.
    """
    return FIRST_BLOCK_OF_INTEREST


def get_db_state():
    """
    Return an opaque 'state' object that will be preserved across calls
    to the blockchain indexing callbacks.
    """

    impl = virtualchain.get_implementation()
    if impl is None:
        impl = sys.modules[__name__]

    db_filename = virtualchain.get_db_filename(impl=impl)

    db_inst = TalosPolicyDB(db_filename)

    return db_inst


def get_opcodes():
    """
    Return the set of opcodes we're looking for.
    """
    return OPCODES


def get_magic_bytes():
    """
    Return the magic byte sequence we're scanning OP_RETURNs for.
    """
    return MAGIC_BYTES


def get_op_processing_order():
    """
    Return a sequence of opcodes as a hint to the order in which
    the indexer should process opcodes.
    """
    return OPCODES


def db_parse(block_id, txid, txind, opcode, op_payload, senders, inputs, outputs, fee, db_state=None):
    """
    Given the block ID, and information from what looks like
    an OP_RETURN transaction that is part of the virtual chain, parse the
    transaction's OP_RETURN nulldata into a dict.

    Return the dict if this is a valid op.
    Return None if not.

    NOTE: the virtual chain indexer reserves all keys that start with 'virtualchain_'
    
    Talos: 
    Parses the OP_RETURN data of the transactions belonging to our operation sequence.
    """

    def match(to_compare):
        return to_compare == opcode

    # check op and parse data
    data = None
    for opcode_lst in OPCODES:
        if match(opcode_lst):
            try:
                data = PARSE_HANDLERS[opcode_lst](op_payload)
                break
            except RuntimeError:
                return None
    if data is None:
        return data

    # parse txtid
    sender_pk = str(inputs[0]['scriptSig']['asm'].split()[1])
    sender_address = str(senders[0]['addresses'][0])
    data[OPCODE_FIELD_TXTID] = txid
    data[OPCODE_FIELD_OWNER] = sender_address
    data[OPCODE_FIELD_OWNER_PK] = sender_pk
    return data


def db_scan_block(block_id, op_list, db_state=None):
    """
    Given the block ID and a tx-ordered list of operations, do any
    block-level initial preprocessing.  This method does not
    affect the operations (the op_list will be discarded), nor
    does it return anything.  It is only meant to give the state
    engine implementation information on what is to come in the
    sequence of db_check() calls.
    """
    return


def db_check(block_id, new_ops, opcode, op, txid, vtxindex, checked, db_state=None):
    """
    Given the block ID and a parsed operation, check to see if this is a *valid* operation
    for the purposes of this virtual chain's database.

    Return True if so; False if not.
    
    Talos:
    Checks the if a operation is valid on the current temporary state
    """
    if (not OPCODE_FIELD_OWNER in op) and (not OPCODE_FIELD_STREAM_ID in op):
        return False
    owner = op[OPCODE_FIELD_OWNER]
    stream_id = op[OPCODE_FIELD_STREAM_ID]

    cur_policy = db_state.get_policystate_temporary(owner, stream_id)

    # Check fields
    for field in OPCODE_FIELDS[opcode]:
        if field not in op:
            return False

    return cur_policy.check_op(opcode, op)


def db_commit(block_id, opcode, op, txid, vtxindex, db_state=None):
    """
    Given a block ID and checked opcode, record it as
    part of the database.  This does *not* need to write
    the data to persistent storage, since save() will be
    called once per block processed.
    This method must return either the updated op with the
    data to pass on to db_serialize, or False if the op
    is to be rejected.
    """
    if op is None:
        return op
    owner = op[OPCODE_FIELD_OWNER]
    stream_id = op[OPCODE_FIELD_STREAM_ID]
    cur_policy = db_state.get_policystate_temporary(owner, stream_id)
    cur_policy.handle_op(opcode, op)
    return op


def db_save(block_id, consensus_hash, pending_ops, filename, db_state=None):
    """
    Save all persistent state to stable storage.

    Return True on success
    Return False on failure.
    """
    return db_state.store_temporary_state()


def db_continue(block_id, consensus_hash):
    """
    Signal to the implementation that all state for this block
    has been saved, and that this is now the new consensus hash.
    Return value indicates whether or not we should continue indexing.
    """
    return True


def _get_newest_block(bc_config):
    rpc_connection = virtualchain.AuthServiceProxy("http://%s:%s@%s:%s" % (bc_config['bitcoind_user'],
                                                                           bc_config['bitcoind_passwd'],
                                                                           bc_config['bitcoind_server'],
                                                                           bc_config['bitcoind_port']))
    resp = rpc_connection.getblockcount()
    return int(resp)


def sync_blockchain(bc_config, last_block=None, expected_snapshots={}, **virtualchain_args):
    """
    synchronize state with the blockchain.
    Return True on success
    Return False if we're supposed to stop indexing
    Abort on error
    """

    impl = sys.modules[__name__]
    if virtualchain.get_implementation() is not None:
        impl = None

    db_filename = virtualchain.get_db_filename(impl=impl)

    new_db = TalosPolicyDB(db_filename, expected_snapshots=expected_snapshots, read_only=False)
    try:
        if last_block is None:
            last_block = _get_newest_block(bc_config)
        rc = virtualchain.sync_virtualchain(bc_config, last_block, new_db, expected_snapshots=expected_snapshots)
    finally:
        new_db.close()
    return rc


class Synchronizer(Thread):
    """
    A thread that synchronizes the virtualchain in a certain interval
    """

    def __init__(self, logger, config=get_default_talos_config(), sleep_interval=60):
        self.sleep_interval = sleep_interval
        self.config = config
        self.running = False
        self.logger = logger
        Thread.__init__(self)

    def set_runnning_flag(self):
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            self.logger.info("Sync Virtualchain")
            sync_blockchain(self.config)
            time.sleep(self.sleep_interval)

