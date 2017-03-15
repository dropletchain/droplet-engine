import logging
import virtualchain
from virtualchain import StateEngine
import test_chain as chain
import util
import sys


virtualchain.setup_virtualchain(impl=chain)

conf={"bitcoind_port":18332,
      "bitcoind_user":"talos",
      "bitcoind_passwd":"talos",
      "bitcoind_server":"127.0.0.1",
      "bitcoind_p2p_port":18444,
      "bitcoind_spv_path":"./tmp.dat"}

"""
conf={"bitcoind_port":13001,
      "bitcoind_user":"admin13000",
      "bitcoind_passwd":"13000",
      "bitcoind_server":"13.93.113.195",
      "bitcoind_p2p_port":13000,
      "bitcoind_spv_path":"./tmp.dat"}
"""
"""
conf={"bitcoind_port":8332,
      "bitcoind_user":"bitcoinrpc",
      "bitcoind_passwd":"7876aeeebedebbc156b7dd69f9865af0fd8db6bc2afa6dc9eb64061ce9af91cc",
      "bitcoind_server":"127.0.0.1",
      "bitcoind_p2p_port":8333,
      "bitcoind_spv_path":"./tmp.dat"}
"""
#virtualchain.connect_bitcoind(conf)

engine = StateEngine(util.MAGIC_BYTES, util.OPCODES, util.OPCODE_FIELDS, impl=chain)

virtualchain.sync_virtualchain(conf, 847, engine)