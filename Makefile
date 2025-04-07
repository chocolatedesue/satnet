main: main.cpp lib/*
	clang++ -stdlib=libc++ -fopenmp main.cpp -o main -std=c++17 -O2