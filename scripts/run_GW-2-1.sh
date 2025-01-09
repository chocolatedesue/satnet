#!/bin/bash

make main
for i in 1001 3003 5001 5002 9423
do
    ./main configs/seasons/GW-2-1-Jan.json $i &
    ./main configs/seasons/GW-2-1-Apr.json $i &
    ./main configs/seasons/GW-2-1-Jul.json $i &
    ./main configs/seasons/GW-2-1-Oct.json $i &
done