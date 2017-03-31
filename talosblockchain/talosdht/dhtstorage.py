import time

from talosstorage.chunkdata import CloudChunk
from talosstorage.storage import LevelDBStorage
from kademlia.storage import IStorage
import sqlite3
import os
import base64
from zope.interface import implements

DB_SCRIPT = """
CREATE TABLE updatetimes(
                        lastupdate INT NOT NULL,
                        key TEXT INT NOT NULL,
                        PRIMARY KEY(lastupdate, key));

CREATE INDEX lastupdate_idx  on updatetimes(lastupdate);
"""

SQL_UPDATE_TIME = "INSERT OR REPLACE INTO updatetimes VALUES (?,?)"
SQL_FETCH_KEYS_OLDER_THAN = "SELECT updatetimes.key FROM updatetimes WHERE updatetimes.lastupdate<?"
SQL_FETCH_KEYS = "SELECT updatetimes.key FROM updatetimes"
SQL_CHECK_KEY_EXISTS = "SELECT COUNT(*) FROM updatetimes WHERE updatetimes.key=?"


def create_db(db_filename):
    if os.path.exists(db_filename):
        raise Exception("Database '%s' already exists" % db_filename)
    con = sqlite3.connect(db_filename, timeout=2 ** 30)
    lines = [l + ";" for l in DB_SCRIPT.split(";")]
    for line in lines:
        con.execute(line)
    return con


def connect_to_db(db_filename):
    return sqlite3.connect(db_filename, timeout=2 ** 30)


def update_key_time(conn, key):
    time_update = int(time.time())
    c = conn.cursor()
    try:
        c.execute(SQL_UPDATE_TIME, (time_update, str(base64.b64encode(key))))
        conn.commit()
    finally:
        c.close()


def get_keys_older_than(conn, unix_time):
    c = conn.cursor()
    try:
        return [base64.b64decode(x[0]) for x in c.execute(SQL_FETCH_KEYS_OLDER_THAN, (unix_time,))]
    finally:
        c.close()


def check_key_exists(conn, chunk_key):
    c = conn.cursor()
    try:
        c.execute(SQL_CHECK_KEY_EXISTS, (base64.b64encode(chunk_key),))
        data = c.fetchall()
        return len(data) > 0
    finally:
        c.close()


class TalosLevelDBDHTStorage(LevelDBStorage):
    implements(IStorage)

    def __init__(self, db_dir, time_db_name="dhttimedb"):
        db_path_sqlite = os.path.join(db_dir, time_db_name)
        LevelDBStorage.__init__(self, db_dir)
        if os.path.exists(db_path_sqlite):
            self.db_update = connect_to_db(db_path_sqlite)
        else:
            self.db_update = create_db(db_path_sqlite)

    def iteritemsOlderThan(self, secondsOld):
        for key in get_keys_older_than(int(time.time()) - secondsOld):
            yield (key, self.db.Get(key))

    def _store_chunk(self, chunk):
        update_key_time(self.db_update, chunk.key)
        self.db.Put(chunk.key, chunk.encode())

    def iteritems(self):
        c = self.db_update.cursor()
        try:
            for x in c.execute(SQL_FETCH_KEYS):
                key = base64.b64decode(x[0])
                yield (key, self.db.Get(key))
        finally:
            c.close()

    def __setitem__(self, key, value):
        self._store_chunk(value)

    def __getitem__(self, key):
        self._get_chunk(key)

    def get(self, key, default=None):
        res = self._get_chunk(key)
        return default if res is None else res

    def has_value(self, to_find):
        try:
            self.db.Get(to_find)
            return True
        except KeyError:
            return False

    def _get_chunk(self, chunk_key):
        update_key_time(self.db_update, chunk_key)
        try:
            bin_chunk = self.db.Get(chunk_key)
        except KeyError:
            return None
        return CloudChunk.decode(bin_chunk)


