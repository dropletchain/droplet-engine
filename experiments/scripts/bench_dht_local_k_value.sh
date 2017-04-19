#!/bin/bash

LOCAL_PATH=$(cd -P -- "$(dirname -- "$0")" && pwd -P)
CUR_PATH=$(pwd)

PROJECT_PATH="talosblockchain/"
#NUM_NODES_LIST={16,32}
ALPHA=3
SECURE=1
ITERATIONS=1050
LATENCY=10

BENCHMARK_NAME="local_dht_benchmark_kvalue_l${LATENCY}_a${ALPHA}"

cd $LOCAL_PATH
cd ../../$PROJECT_PATH

if hash python2.7 2>/dev/null; then
    cmd=python2.7
else
    cmd=python
fi

echo "Assumes bitcoin + virtualchain node runs"
#echo "Run virtualchain"
#./scripts/run_rest_vc.sh


sleep 2

if [ "$(uname)" == "Darwin" ]; then
	echo "latency not supportet with netem"
else
	if [[ ! -z  $LATENCY ]]; then
		echo "Add latency ${LATENCY}ms"
		sudo tc qdisc add dev lo root netem delay ${LATENCY}ms
	fi
fi

mkdir $BENCHMARK_NAME
echo "Experiment starts"
TMP=0
for KVALUE in {20,30,40}
do
	
	SLEEP_TIME=10
	for NUM_NODES in {16,32,64,128,256,512}
	do
		if [ $NUM_NODES -lt $KVALUE ]; then
			echo "Adapt kvalue to num nodes"
			TMP=$KVALUE
			KVALUE=$NUM_NODES
		fi
		
		echo "Run $NUM_NODES dht nodes"
		NUM_HELPER_NODES=$((NUM_NODES-1))
		./scripts/run_dht_nodes.sh 127.0.0.1 $NUM_HELPER_NODES $SECURE $KVALUE $ALPHA

		echo "DHT nodes run wait bootstrap ${SLEEP_TIME}s..."
		sleep $SLEEP_TIME
		ROUND_NAME=${BENCHMARK_NAME}_n${NUM_NODES}_k${KVALUE}
		echo "Start benchmark kvalue: $KVALUE num_nodes: $NUM_NODES"
		$cmd ./benchmark/benchmark_api.py --log_db "$BENCHMARK_NAME/$ROUND_NAME.db" --num_rounds $ITERATIONS

		echo "Extract data from logs"
		$cmd ./benchmark/logextraction.py --logpath ./dhtstorage/logs --dbname "$BENCHMARK_NAME/$ROUND_NAME.db"

		echo "Terminate Nodes"
		./scripts/terminate_dht_nodes.sh

		echo "Remove DHT Files"
		rm -r ./dhtstorage

		if [ $NUM_NODES -lt $TMP ]; then
			KVALUE=$TMP
		fi
		#SLEEP_TIME=$((SLEEP_TIME*2))
	done

done

if [ "$(uname)" == "Darwin" ]; then
	echo "latency not supportet with netem"
else
	if [[ ! -z  $LATENCY ]]; then
		echo "Remove latency ${LATENCY}ms"
		sudo tc qdisc del dev lo root netem
	fi  
fi

echo "Benchmark done move results"
mv $BENCHMARK_NAME $LOCAL_PATH/../data

cd $CUR_PATH
