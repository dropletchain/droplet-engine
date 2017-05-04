#!/bin/bash

LOCAL_PATH=$(cd -P -- "$(dirname -- "$0")" && pwd -P)
CUR_PATH=$(pwd)

PROJECT_PATH="talosblockchain/"
#NUM_NODES_LIST={16,32}
KVALUE=10
ALPHA=3
SECURE=1
ITERATIONS=110
NUM_THREADS=32
LATENCY=10
NUM_NODES=1024
NUM_ENTRIES=2419200

BENCHMARK_NAME="local_dht_benchmark_daily_fetch_k${KVALUE}_a${ALPHA}"

declare -a GRANULARITIES=(3600 21600 43200 86400 604800)
declare -a F_GRANULARITIES=(86400 86400 86400 86400 604800)

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

mkdir $BENCHMARK_NAME
echo "Experiment starts"

if [ "$(uname)" == "Darwin" ]; then
	echo "latency not supportet with netem"
else
	if [[ ! -z  $LATENCY ]]; then
		echo "Add latency ${LATENCY}ms"
		sudo tc qdisc add dev lo root netem delay ${LATENCY}ms
	fi
fi

SLEEP_TIME=10

arraylength=${#GRANULARITIES[@]}
for (( c=0; c<$arraylength; c++ ))
do
	echo "Run $NUM_NODES dht nodes"
	NUM_HELPER_NODES=$((NUM_NODES-1))
	./scripts/run_dht_nodes.sh 127.0.0.1 $NUM_HELPER_NODES $SECURE $KVALUE $ALPHA

	echo "DHT nodes run wait bootstrap ${SLEEP_TIME}s..."
	sleep $SLEEP_TIME
	ROUND_NAME=${BENCHMARK_NAME}_n${NUM_NODES}_l${LATENCY}_g${GRANULARITIES[c]}_fg${F_GRANULARITIES[c]}
	echo "Start benchmark"
	$cmd ./benchmark/benchmark_api_daily.py --log_db "$BENCHMARK_NAME/$ROUND_NAME.db" --datapath "../raw-data/EcoSmart" --num_rounds $ITERATIONS --num_entries $NUM_ENTRIES --granularity ${GRANULARITIES[c]} --fetch_granularity ${F_GRANULARITIES[c]} --num_threads $NUM_THREADS

	echo "Extract data from logs"
	$cmd ./benchmark/logextraction.py --logpath ./dhtstorage/logs --dbname "$BENCHMARK_NAME/$ROUND_NAME.db"

	echo "Terminate Nodes"
	./scripts/terminate_dht_nodes.sh

	echo "Remove DHT Files"
	rm -r ./dhtstorage

	#SLEEP_TIME=$((SLEEP_TIME*2))
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

