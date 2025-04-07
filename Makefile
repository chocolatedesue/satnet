main: main.cpp lib/*
	clang++ -fopenmp  main.cpp -o main -std=c++17 -O2