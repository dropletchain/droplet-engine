#!/bin/bash

LOCAL_PATH=$(cd -P -- "$(dirname -- "$0")" && pwd -P)
CUR_PATH=$(pwd)

cd $LOCAL_PATH
cd ..

if hash python2.7 2>/dev/null; then
    cmd=python2.7
else
    cmd=python
fi

$cmd policyapi.py "$@"

cd $CUR_PATH