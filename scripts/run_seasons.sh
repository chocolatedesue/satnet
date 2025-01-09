#!/bin/bash

make main
for i in 1001 3003 5001 5002 9433
do
    ./main configs/seasons/full-Jan.json $i &
    ./main configs/seasons/full-Apr.json $i &
    ./main configs/seasons/full-Jul.json $i &
    ./main configs/seasons/full-Oct.json $i &
done