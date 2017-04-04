#!/bin/bash

LOCAL_PATH=$(cd -P -- "$(dirname -- "$0")" && pwd -P)
CUR_PATH=$(pwd)

cd $LOCAL_PATH
cd ..

python policyapi.py "$@"

cd $CUR_PATH