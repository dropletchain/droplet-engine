import os
import re

import sqlite3

BENCH_TAG = "[BENCH]"
TIME_TAG = "[TIMES]"

TYPE_ADD_CHUNK = "[ADD_CHUNK]"
TYPE_QUERY_CHUNK_ADDR = "[QUERY_CHUNK_ADDR]"
TYPE_QUERY_CHUNK_LOCAL= "[QUERY_CHUNK_LOCAL]"
TYPE_STORE_CHUNK_LOCAL = "[STORE_CHUNK]"
TYPE_STORE_CHUNK_REMOTE = "[CALL_STORE_CHUNK]"

ENTRY_TOTAL_STORE_LOCAL = "time_total_rpc_store"
ENTRY_TOTAL_LOCAL_QUERY = "time_total_local_query"
ENTRY_GET_AND_CHECK = "time_get_and_check_chunk"
ENTRY_CHECK_TOKEN_VALID = "time_check_token_valid"
ENTRY_TIME_FIND_VALUE = "time_find_value"
ENTRY_CRAWL_NEAREST = "time_crawl_nearest"
ENTRY_TOTAL_ADD_CHUNK = "time_total_add_chunk"
ENTRY_TOTAL_QUERY_CHUNK = "time_total_query_chunk"
ENTRY_FETCH_POLICY = "time_fetch_policy"
ENTRY_STORE_CHECK = "time_store_check_chunk"
ENTRY_STORE_TO_ALL_NODES = "time_store_to_nodes"
ENTRY_TIME_WELCOME_NODE = "time_welcome_node"
ENTRY_STORE_ONE_NODE = "time_call_store"

ENTRY_GET_CHECK_ACCESS = "time_check_access_valid"
ENTRY_GET_DB = "time_db_get_chunk"
ENTRY_GET_TAG_CHECK = "time_check_tag_matches"

ENTRY_PUT_CHECK_CHUNK = "time_check_chunk_valid"
ENTRY_PUT_DB = 'time_db_store_chunk'
ENTRY_PUT_CHECK_CHUNK_KEY_MATCH = "time_check_chunk_valid_key_matches"
ENTRY_PUT_CHECK_CHUNK_TAG_MATCH = "time_check_chunk_valid_tag_matches"
ENTRY_PUT_CHECK_CHUNK_SIGNATURE = "time_check_chunk_valid_signature"

entry_pattern = re.compile("(.*): (.*) ms")

types = [TYPE_ADD_CHUNK, TYPE_QUERY_CHUNK_ADDR, TYPE_QUERY_CHUNK_LOCAL, TYPE_STORE_CHUNK_LOCAL, TYPE_STORE_CHUNK_REMOTE]

types_to_entries = {
    TYPE_ADD_CHUNK: [ENTRY_TOTAL_ADD_CHUNK, ENTRY_CRAWL_NEAREST, ENTRY_STORE_TO_ALL_NODES,
                     ENTRY_STORE_CHECK, ENTRY_PUT_CHECK_CHUNK, ENTRY_PUT_CHECK_CHUNK_KEY_MATCH,
                     ENTRY_PUT_CHECK_CHUNK_TAG_MATCH, ENTRY_PUT_CHECK_CHUNK_SIGNATURE, ENTRY_PUT_DB],
    TYPE_QUERY_CHUNK_ADDR: [ENTRY_TOTAL_QUERY_CHUNK, ENTRY_TIME_FIND_VALUE],
    TYPE_QUERY_CHUNK_LOCAL: [ENTRY_TOTAL_LOCAL_QUERY, ENTRY_CHECK_TOKEN_VALID, ENTRY_FETCH_POLICY, ENTRY_GET_AND_CHECK,
                             ENTRY_GET_CHECK_ACCESS, ENTRY_GET_DB, ENTRY_GET_TAG_CHECK],
    TYPE_STORE_CHUNK_LOCAL: [ENTRY_TOTAL_STORE_LOCAL, ENTRY_TIME_WELCOME_NODE, ENTRY_FETCH_POLICY, ENTRY_STORE_CHECK,
                             ENTRY_PUT_CHECK_CHUNK, ENTRY_PUT_CHECK_CHUNK_KEY_MATCH, ENTRY_PUT_CHECK_CHUNK_SIGNATURE,
                             ENTRY_PUT_CHECK_CHUNK_TAG_MATCH, ENTRY_PUT_DB],
    TYPE_STORE_CHUNK_REMOTE: [ENTRY_STORE_ONE_NODE]
}

def extract_bench_lines(path_to_file):
    with open(path_to_file,'r') as to_read:
        return [line for line in to_read if BENCH_TAG in line]


def extract_entries(list_of_lines):
    result = []
    for line in list_of_lines:
        [_, split_bench] = line.split(BENCH_TAG)
        [type, entries] = split_bench.split(TIME_TAG)
        type = type.strip()
        if ',' in entries:
            entries_list = map(lambda x: x.strip(), entries.split(','))
        else:
            entries_list = [entries.strip()]
        tmp_lst = {}
        for entry in entries_list:
            patter_result = entry_pattern.match(entry)
            tmp_lst[patter_result.group(1)] = float(patter_result.group(2))
        result.append((type, tmp_lst))
    return result


def db_create_script():
    script = ""
    for type in types:
        script += "CREATE TABLE %s (node_id TEXT NOT NULL," % type
        for column in types_to_entries[type]:
            script += "%s REAL, " % column
        script = "%s);\n" % script[:-2]
    return script


def db_create_insert(type):
    insert_quest = (len(types_to_entries[type]) + 1) * "?, "
    return "INSERT INTO %s VALUES (%s);" % (type, insert_quest[:-2])


def create_value_tuple_from_dict(nodeid, type_op, dict_data):
    return tuple([nodeid] +
                 [dict_data[column] if column in dict_data else None for column in types_to_entries[type_op]])


def fill_db_with_data(conn, data, nodeid):
    c = conn.cursor()
    try:
        for type_op, dict_data in data:
            c.execute(db_create_insert(type_op), create_value_tuple_from_dict(nodeid, type_op, dict_data))
        conn.commit()
    finally:
        c.close()


def create_db(db_filename):
    if os.path.exists(db_filename):
        raise Exception("Database '%s' already exists" % db_filename)
    con = sqlite3.connect(db_filename, timeout=2 ** 30)
    script = db_create_script()
    lines = [l + ";" for l in script.split(";")]
    for line in lines:
        con.execute(line)
    return con


def connect_db(db_filename):
    if not os.path.exists(db_filename):
        raise Exception("Database '%s' does not exists" % db_filename)
    con = sqlite3.connect(db_filename, timeout=2 ** 30)
    return con

conn = create_db("./tmp.db")
entries = extract_entries(extract_bench_lines("./logs/mainlog.log"))
fill_db_with_data(conn, entries, "main")
for i in range(1, 100):
    entries = extract_entries(extract_bench_lines("./logs/node%d.log" % i))
    fill_db_with_data(conn, entries, "node%d" % i)


