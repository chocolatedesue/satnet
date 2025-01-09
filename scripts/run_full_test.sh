#!/bin/bash

make main
for ((i = 1000; i <= 9999; i++))
do
    ./main configs/full-test.json $i &
done