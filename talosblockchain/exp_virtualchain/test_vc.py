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
#virtualchain.connect_bitcoind(conf)

engine = StateEngine(util.MAGIC_BYTES, util.OPCODES, None, impl=chain)

virtualchain.sync_virtualchain(conf, 1123, engine)