#!/bin/bash

LOCAL_PATH=$(cd -P -- "$(dirname -- "$0")" && pwd -P)
CUR_PATH=$(pwd)

cd $LOCAL_PATH
cd ..

export BLOCKSTACK_TESTNET=1
export VIRTUALCHAIN_WORKING_DIR=$LOCAL_PATH
export BLOCKSTACK_DEBUG=1

python restvcapi.py $* 2>&1 | tee $LOCAL_PATH/vc.log

cd $CUR_PATH
