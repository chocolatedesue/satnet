input = "/home/chenyuxuan/satnet/gs-sat/configs/gs-config.csv"
output = "/home/chenyuxuan/satnet/gs-sat/configs/gs-config.txt"

fin = open(input)
fout = open(output, "w")
for line in fin.readlines():
    x, y = line.strip().split(',')
    fout.write("{} {} {}\n".format(x, y, 0))
fout.close()