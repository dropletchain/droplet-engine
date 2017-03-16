import virtualchain
import os
import sqlite3
from config import *


def create_db(db_filename):
    return None


def connect_to_db(db_filename):
    return None


class TalosPolicyDB(virtualchain.StateEngine):

    def __init__(self, db_filename, disposition, expected_snapshots={}, read_only=True):

        # set implementation of virtualchain
        import talosvirtualchain
        blockstack_impl = virtualchain.get_implementation()
        if blockstack_impl is None:
            blockstack_impl = talosvirtualchain

        lastblock = self.get_lastblock(impl=blockstack_impl)

        self.db = None

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


