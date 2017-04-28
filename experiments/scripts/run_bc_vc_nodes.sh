LOCAL_PATH=$(cd -P -- "$(dirname -- "$0")" && pwd -P)
CUR_PATH=$(pwd)

PROJECT_PATH="talosblockchain/"
BC_CHAIN_NAME="talos-chain"
BC_MAIN_NODE="46.101.113.112:13000"

cd $LOCAL_PATH
cd ../../$PROJECT_PATH



if [ ! -d "$BC_CHAIN_NAME" ]; then
	mkdir $BC_CHAIN_NAME
fi


echo "Run bitcoin test node"
bitcoind -deamon -regtest -dnsseed=0 -addnode=$BC_MAIN_NODE -datadir=./$BC_CHAIN_NAME -server -rpcuser="talos" -rpcpassword="talos" -debug -txindex

echo "Wait 10s....."
sleep 10

echo "Run virtualchain node"
cd scripts 
./run_rest_vc.sh >/dev/null 2>&1 

echo "Wait 5s....."
sleep 5

cd $CUR_PATH