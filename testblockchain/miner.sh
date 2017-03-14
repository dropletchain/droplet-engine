#!/bin/bash
for (( c=1; c<=$1; c++ )); 
do
	echo "Mining round $c";
	make generate
	sleep $2
done
