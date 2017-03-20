from talosvc.talosvirtualchain import sync_blockchain
import os



os.environ["BLOCKSTACK_TESTNET"] = "1"
os.environ["DEBUG"] = "1"
os.environ["VIRTUALCHAIN_WORKING_DIR"] = "."

conf={"bitcoind_port":18332,
      "bitcoind_user":"talos",
      "bitcoind_passwd":"talos",
      "bitcoind_server":"127.0.0.1",
      "bitcoind_p2p_port":18444,
      "bitcoind_spv_path":"./tmp.dat"}

sync_blockchain(conf)