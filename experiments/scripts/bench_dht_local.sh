#!/bin/bash

LOCAL_PATH=$(cd -P -- "$(dirname -- "$0")" && pwd -P)
CUR_PATH=$(pwd)

PROJECT_PATH="talosblockchain/"
#NUM_NODES_LIST={16,32}
KVALUE=10
ALPHA=3
SECURE=1
ITERATIONS=100
LATENCY="10"

BENCHMARK_NAME="local_dht_benchmark_${ITERATIONS}_${KVALUE}_${ALPHA}"

cd $LOCAL_PATH
cd ../../$PROJECT_PATH

if hash python2.7 2>/dev/null; then
    cmd=python2.7
else
    cmd=python
fi

echo "Assumes bitcoin node runs"
#echo "Run virtualchain"
#./scripts/run_rest_vc.sh

if [ "$(uname)" == "Darwin" ]; then
	echo "latency not supportet with nete,"
else
	if [[ ! -z  $LATENCY ]]; then
		 sudo tc qdisc add dev lo root netem delay ${LATENCY}ms
	fi
   
fi


sleep 2


mkdir $BENCHMARK_NAME
echo "Experiment starts"
for NUM_NODES in {32,}
do
	echo "Run $NUM_NODES dht nodes"
	NUM_HELPER_NODES=$((NUM_NODES-1))
	./scripts/run_dht_nodes.sh 127.0.0.1 $NUM_HELPER_NODES $SECURE $KVALUE $ALPHA

	echo "DHT nodes run wait bootstrap..."
	sleep 10
	ROUND_NAME=${BENCHMARK_NAME}_${NUM_NODES}

	echo "Start benchmark"
	$cmd ./benchmark/benchmark_api.py --log_db "$BENCHMARK_NAME/$ROUND_NAME.db" --num_rounds $ITERATIONS

	echo "Extract data from logs"
	$cmd ./benchmark/logextraction.py --logpath ./dhtstorage/logs --dbname "$BENCHMARK_NAME/$ROUND_NAME.db"

	echo "Terminate Nodes"
	./scripts/terminate_dht_nodes.sh

	echo "Remove DHT Files"
	#rm -r ./dhtstorage
done
echo "Benchmark done move results"
mv $BENCHMARK_NAME $LOCAL_PATH/../data

if [ "$(uname)" == "Darwin" ]; then
	echo "latency not supportet with netem"
else
	if [[ ! -z  $LATENCY ]]; then
		sudo tc qdisc del dev lo root netem
	fi  
fi

cd $CUR_PATH

