from bitcoinrpc.authproxy import AuthServiceProxy

rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:18332" % ("talos", "talos"))
best_block_hash = rpc_connection.getbestblockhash()
print(rpc_connection.getblock(best_block_hash))

print rpc_connection.getinfo()
