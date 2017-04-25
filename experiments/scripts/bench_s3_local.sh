#!/bin/bash

# !!!
# Assumes S3 credentials ar located in ~/.aws/credentials
# (see https://boto3.readthedocs.io/en/latest/guide/quickstart.html)

LOCAL_PATH=$(cd -P -- "$(dirname -- "$0")" && pwd -P)
CUR_PATH=$(pwd)

PROJECT_PATH="talosblockchain/"
#NUM_NODES_LIST={16,32}
ITERATIONS=10
NUM_FETCH_THREADS=2
NUM_ROUNDS_PAR_FETCH=10

BENCHMARK_NAME="local_s3_benchmark"

cd $LOCAL_PATH
cd ../../$PROJECT_PATH

if hash python2.7 2>/dev/null; then
    cmd=python2.7
else
    cmd=python
fi

echo "Assumes bitcoin + virtualchain node runs"
mkdir $BENCHMARK_NAME

$cmd ./benchmark/benchmarks3.py --log_db "$BENCHMARK_NAME/$BENCHMARK_NAME.db" --num_rounds $ITERATIONS --num_fetch_threads $NUM_FETCH_THREADS --num_rounds_par_fetch $NUM_ROUNDS_PAR_FETCH

mv $BENCHMARK_NAME $LOCAL_PATH/../data

cd $CUR_PATH