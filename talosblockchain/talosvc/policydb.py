import virtualchain
import os
import sqlite3
from config import *
from policy import create_policy_from_db_tuple, Policy


DB_SCRIPT = """
CREATE TABLE policy(
                        stream_id TEXT NOT NULL,
                        owner TEXT NOT NULL,
                        owner_pubkey TEXT,
                        nonce TEXT NOT NULL,
                        txid TEXT NOT NULL,
                        PRIMARY KEY(owner, stream_id));

CREATE TABLE shares( tx_policy INT NOT NULL,
                        pubkey TEXT NOT NULL,
                        txid TEXT NOT NULL,
                        PRIMARY KEY(tx_policy, pubkey));

CREATE TABLE timeintervals( tx_policy INT NOT NULL,
                        starttime INT NOT NULL,
                        timeinterval INT NOT NULL,
                        txid TEXT NOT NULL,
                        PRIMARY KEY(tx_policy, txid));


CREATE INDEX shares_idx on shares(tx_policy);
CREATE INDEX time_idx on timeintervals(tx_policy);
CREATE INDEX policy_txid_idx on policy(txid);
CREATE INDEX owner_idx on policy(owner, stream_id);
"""

SQL_INSERT_POLICY="INSERT INTO policy VALUES (?,?,?,?,?)"
SQL_INSERT_SHARES="INSERT INTO shares VALUES (?,?,?)"
SQL_TIMEINTERVALS="INSERT INTO timeintervals VALUES (?,?,?,?)"

SQL_DELETE_SHARE = "DELETE FROM shares WHERE shares.tx_policy=? AND shares.pubkey=?"
SQL_DELETE_INTERVALS_FOR_POLICY = "DELETE FROM timeintervals WHERE timeintervals.tx_policy=?"
SQL_DELETE_SHARES_FOR_POLICY = "DELETE FROM shares WHERE shares.tx_policy=?"
SQL_DELETE_POLICY = "DELETE FROM shares WHERE shares.tx_policy=?"

SQL_FETCH_POLICY = "SELECT * FROM policy WHERE policy.stream_id=? AND policy.owner=?"
SQL_FETCH_SHARES = "SELECT shares.pubkey, shares.txid FROM shares WHERE shares.tx_policy=?"
SQL_FETCH_TIMES = "SELECT timeintervals.starttime, timeintervals.timeinterval, timeintervals.txid  FROM timeintervals WHERE shares.tx_policy=?"
SQL_FETCH_POLICY_TXID = "SELECT policy.txid FROM policy WHERE policy.stream_id=? AND policy.owner=?"

def op_to_sql_args(opcode, op):
    if opcode == CREATE_POLICY:
        return [(op[OPCODE_FIELD_STREAM_ID], op[OPCODE_FIELD_OWNER],
               op[OPCODE_FIELD_OWNER_PK], op[OPCODE_FIELD_NONCE], op[OPCODE__TXTID])]
    elif opcode == GRANT_ACCESS:
        keys =  op[OPCODE_FIELD_PUBLIC_KEYS].split(',')
        return [(op[OPCODE_FIELD_OWNER], op[OPCODE_FIELD_STREAM_ID], key, op[OPCODE__TXTID]) for key in keys]
    elif opcode == REVOKE_ACCESS:
        keys =  op[OPCODE_FIELD_PUBLIC_KEYS].split(',')
        return [(op[OPCODE_FIELD_OWNER], op[OPCODE_FIELD_STREAM_ID], key, op[OPCODE__TXTID]) for key in keys]
    elif opcode == CHANGE_INTERVAL:
        return [(op[OPCODE_FIELD_OWNER], op[OPCODE_FIELD_STREAM_ID],
                 op[OPCODE_FIELD_TIMESTAMP_START], op[OPCODE_FIELD_INTERVAL], op[OPCODE__TXTID])]
    elif opcode == INVALIDATE_POLICY:
        return [op[OPCODE_FIELD_OWNER], op[OPCODE_FIELD_STREAM_ID]]

def create_db(db_filename):
    if os.path.exists(db_filename):
        raise Exception("Database '%s' already exists" % db_filename)
    con = sqlite3.connect(db_filename, timeout=2**30)
    lines = [l + ";" for l in DB_SCRIPT.split(";")]
    for line in lines:
        con.execute(line)
    return con


def connect_to_db(db_filename):
    return sqlite3.connect(db_filename, timeout=2**30)


def commit_create_policy(conn, stream_id, owner, owner_pubkey, txid, starttime, timeinterval, nonce):
    with conn.cursor() as c:
        c.execute(SQL_INSERT_POLICY, (stream_id, owner, owner_pubkey, nonce, txid))
        c.execute(SQL_TIMEINTERVALS, (txid, starttime, timeinterval, txid))
        conn.commit()


def commit_addshare(conn, owner, stream_id, pubkey, txid):
    with conn.cursor() as c:
        c.execute(SQL_FETCH_POLICY_TXID, stream_id, owner)
        idx_policy = c.fetchone()[0]
        c.execute(SQL_INSERT_SHARES, (idx_policy, pubkey, txid))
        conn.commit()


def commit_addinterval(conn, owner, stream_id, starttime, timeinterval, txid):
    with conn.cursor() as c:
        c.execute(SQL_FETCH_POLICY_TXID, stream_id, owner)
        idx_policy = c.fetchone()[0]
        c.execute(SQL_TIMEINTERVALS, (idx_policy, starttime, timeinterval, txid))
        conn.commit()


def commit_revokeshare(conn, owner, stream_id, pubkey):
    with conn.cursor() as c:
        c.execute(SQL_FETCH_POLICY_TXID, stream_id, owner)
        idx_policy = c.fetchone()[0]
        c.execute(SQL_DELETE_SHARE, (idx_policy, pubkey))
        conn.commit()


def commit_invalidate_policy(conn, owner, stream_id):
    with conn.cursor() as c:
        c.execute(SQL_FETCH_POLICY_TXID, stream_id, owner)
        idx_policy = c.fetchone()[0]
        c.execute(SQL_DELETE_POLICY, (idx_policy,))
        c.execute(SQL_DELETE_SHARES_FOR_POLICY, (idx_policy,))
        c.execute(SQL_DELETE_INTERVALS_FOR_POLICY, (idx_policy,))
        conn.commit()


def fetch_policy(conn, owner, stream_id):
     with conn.cursor() as c:
        c.execute(SQL_FETCH_POLICY, (owner, stream_id))
        policy_data = c.fetchone()
        if policy_data is None:
            return None
        policy = create_policy_from_db_tuple(policy_data)

        #Add shares to policy
        c.execute(SQL_FETCH_SHARES, (policy.get_txid(),))
        for share in c:
            policy.add_share(share)

        c.execute(SQL_DELETE_INTERVALS_FOR_POLICY, (policy.get_txid(),))
        for time in c:
            policy.add_time_tuple(time)
        return policy


class PolicyState:

    def __init__(self, policy):
        self.policy = policy
        self.ops = []

    def handle_op(self, opcode, op):
        method = getattr(PolicyState, "handle_" + OPCODE_NAMES[opcode])
        method(self, op)

    @staticmethod
    def handle_CREATE_POLICY(policy_state, op):
        args = (op[OPCODE_FIELD_STREAM_ID], op[OPCODE_FIELD_OWNER], op[OPCODE_FIELD_OWNER_PK], op[OPCODE_FIELD_NONCE], op[OPCODE__TXTID])
        policy_state.ops.append((commit_create_policy, args))
        policy_state.policy = Policy(op[OPCODE_FIELD_OWNER], op[OPCODE_FIELD_STREAM_ID], op[OPCODE_FIELD_NONCE], op[OPCODE__TXTID])

    @staticmethod
    def handle_GRANT_ACCESS(policy_state, op):
        keys =  op[OPCODE_FIELD_PUBLIC_KEYS].split(',')
        args =  [(op[OPCODE_FIELD_OWNER], op[OPCODE_FIELD_STREAM_ID], key, op[OPCODE__TXTID]) for key in keys]
        for arg in args:
            policy_state.ops.append((commit_addshare, arg))
        for key in key:
            policy_state.policy.add_share((key, op[OPCODE__TXTID]))

    @staticmethod
    def handle_REVOKE_ACCESS(policy_state, op):
        keys =  op[OPCODE_FIELD_PUBLIC_KEYS].split(',')
        args =  [(op[OPCODE_FIELD_OWNER], op[OPCODE_FIELD_STREAM_ID], key, op[OPCODE__TXTID]) for key in keys]
        for arg in args:
            policy_state.ops.append((commit_revokeshare, arg))
        for key in key:
            policy_state.policy.remove_share((key, op[OPCODE__TXTID]))

    @staticmethod
    def handle_CHANGE_INTERVAL(policy_state, op):
        args = (op[OPCODE_FIELD_OWNER], op[OPCODE_FIELD_STREAM_ID],
                 op[OPCODE_FIELD_TIMESTAMP_START], op[OPCODE_FIELD_INTERVAL], op[OPCODE__TXTID])
        policy_state.ops.append((commit_addinterval, args))
        policy_state.policy.add_time_tuple((op[OPCODE_FIELD_TIMESTAMP_START], op[OPCODE_FIELD_INTERVAL], op[OPCODE__TXTID]))

    @staticmethod
    def handle_INVALIDATE_POLICY(policy_state, op):
        args = (op[OPCODE_FIELD_OWNER], op[OPCODE_FIELD_STREAM_ID])
        policy_state.ops.append((commit_invalidate_policy, args))
        policy_state.policy = None


class TalosPolicyDB(virtualchain.StateEngine):

    def __init__(self, db_filename, expected_snapshots={}, read_only=True):

        # set implementation of virtualchain
        import talosvirtualchain
        blockstack_impl = virtualchain.get_implementation()
        if blockstack_impl is None:
            blockstack_impl = talosvirtualchain

        lastblock = self.get_lastblock(impl=blockstack_impl)

        self.db = None

        self.blockstate = {}

        self.db_filename = db_filename
        if os.path.exists(db_filename):
            self.db = connect_to_db(db_filename)
        else:
            self.db = create_db(db_filename)

        super(TalosPolicyDB, self).__init__(MAGIC_BYTES,
                                            OPCODES,
                                            OPCODE_FIELDS,
                                            impl=blockstack_impl,
                                            initial_snapshots=None,
                                            state=self,
                                            expected_snapshots=None,
                                            read_only=read_only)

    def close(self):
        if self.db is not None:
            self.db.commit()
            self.db.close()
            self.db = None

    def get_db_path(self):
        return self.db_filename

    def _reset_temporary_blockstate(self):
        self.blockstate = {}

    def get_policystate_temporary(self, owner, streamid):
        if owner + streamid in self.blockstate:
            return self.blockstate[owner + streamid]
        else:
            self.blockstate[owner + streamid] = PolicyState(fetch_policy(self.db, owner, streamid))

    def store_temporary_state(self):
        state = self.blockstate
        self._reset_temporary_blockstate()
        for _, value in state.iteritems():
            for op in value.ops:
                try:
                    op[0](self.db, *op[1])
                except RuntimeError:
                    return False

        return True





