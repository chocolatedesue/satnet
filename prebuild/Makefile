main: main.cpp lib/*
	clang++ -stdlib=libc++ -fopenmp main.cpp -o main -std=c++17 -O2

init:
	sudo apt update && \
	sudo apt install libomp-dev clang libc++-dev libc++abi-dev llvm -y
