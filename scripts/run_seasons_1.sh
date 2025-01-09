#!/bin/bash

make main
for i in 9531
do
    ./main configs/seasons/full-Jan.json $i &
    ./main configs/seasons/full-Apr.json $i &
    ./main configs/seasons/full-Jul.json $i &
    ./main configs/seasons/full-Oct.json $i &
done