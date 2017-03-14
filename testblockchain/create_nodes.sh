#!/bin/bash
LOCAL_PATH=$(cd -P -- "$(dirname -- "$0")" && pwd -P)
CUR_PATH=$(pwd)

if [ -z "$1" ]
  then
    echo "Check arguments: <num_nodes>"
fi

NUM_NODES=$1

port=13000
old_port=13002

cd $LOCAL_PATH
for ((c=1; c<=$NUM_NODES; c++))
do  
	mkdir "node$c"
	if [ "$c" -lt 2 ]
	then
		python create_config.py $port "./node$c"
	else
		python create_config.py $port $old_port "./node$c"
	fi
	old_port=$port
	port=$(($port + 2))
done

python create_makefile.py $NUM_NODES

cd $CUR_PATH