#!/bin/bash

make main
for i in 1001 3003 5001 5002 9433
do
    ./main configs/seasons/GW-A59-2-Jan.json $i &
    ./main configs/seasons/GW-A59-2-Apr.json $i &
    ./main configs/seasons/GW-A59-2-Jul.json $i &
    ./main configs/seasons/GW-A59-2-Oct.json $i &
done