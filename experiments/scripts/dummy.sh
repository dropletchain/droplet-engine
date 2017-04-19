TMP=0
for KVALUE in {10,20,30,40}
do
	
	SLEEP_TIME=10

	for NUM_NODES in {16,32,64,128,256,512}
	do
		if [ $NUM_NODES -lt $KVALUE ]; then
			echo "Adapt kvalue to num nodes"
			TMP=$KVALUE
			KVALUE=$NUM_NODES
		fi
		echo "$KVALUE $NUM_NODES"
		if [ $NUM_NODES -lt $TMP ]; then
			KVALUE=$TMP
		fi
	done

done