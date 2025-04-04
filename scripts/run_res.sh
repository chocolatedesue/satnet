# DijkstraPred 3003

# MinHopCount 5001

# DisCoRouteBase 1001

# LBP 5002

# DiffDomainBridge_10_3  9433

config=configs/full-April.json

# ./main configs/full.json 3003
# ./main configs/full.json 5001
# ./main configs/full.json 1001
# ./main configs/full.json 5002
# ./main configs/full.json 9433

./main $config 3003
./main $config 5001
./main $config 1001
./main $config 5002
./main $config 9433
