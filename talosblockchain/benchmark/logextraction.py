TAG_BENCH = "[BENCH]"
TAG_TIMES = "Times:"

TYPE_STORE_LOCAL = "STORE NODE"
TYPE_CALL_RPC_STORE = "CALL RPC"
TYPE_FULL_STORE = "STORE TIME"
TYPE_FULL_QUERY = "QUERY CHUNK"

def extract_bench_lines(path_to_file):
    with open(path_to_file,'r') as to_read:
        return [line for line in to_read if TAG_BENCH in line]

lines = extract_bench_lines("./logs/mainlog.log")
for line in lines:
    print line