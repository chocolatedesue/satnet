# DijkstraPred 3003

# MinHopCount 5001

# DisCoRouteBase 1001

# LBP 5002

# DiffDomainBridge_10_3  9433

# config=configs/full-April.json
# 将读取到的第一个参数赋值给变量config
config=$1

# 如果没有传入参数，则报错
if [ -z "$config" ]; then
  echo "Usage: $0 <config_file>"
  exit 1
fi

# ./main configs/full.json 3003
# ./main configs/full.json 5001
# ./main configs/full.json 1001
# ./main configs/full.json 5002
# ./main configs/full.json 9433

# ./main $config 3003
# ./main $config 5001
# ./main $config 1001
# ./main $config 5002
# ./main $config 9433

for ((i = 1000; i <= 9999; i++))
do
    ./main  $config  $i 
done