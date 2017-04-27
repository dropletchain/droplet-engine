#!/bin/bash

# !!!
# Assumes S3 credentials ar located in ~/.aws/credentials
# (see https://boto3.readthedocs.io/en/latest/guide/quickstart.html)

LOCAL_PATH=$(cd -P -- "$(dirname -- "$0")" && pwd -P)
CUR_PATH=$(pwd)

PROJECT_PATH="talosblockchain/"
ITERATIONS=10
CHUNK_SIZE=10000
TAG_SIZE=10

BENCHMARK_NAME="local_chunk_benchmark"

cd $LOCAL_PATH
cd ../../$PROJECT_PATH

if hash python2.7 2>/dev/null; then
    cmd=python2.7
else
    cmd=python
fi

mkdir $BENCHMARK_NAME

$cmd ./benchmark/benchmarkchunk.py --log_db "$BENCHMARK_NAME/$BENCHMARK_NAME.db" --num_rounds $ITERATIONS --chunk_size $CHUNK_SIZE --tag_size $TAG_SIZE

mv $BENCHMARK_NAME $LOCAL_PATH/../data

cd $CUR_PATH