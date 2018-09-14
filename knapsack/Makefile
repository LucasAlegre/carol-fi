# C compiler
CC = g++ -g
CC_FLAGS = -std=c++11

destDir = /tmp/knapsack

all: gen_bin mv_bin

gen_bin: knapsackdp.cpp knapsacksa.cpp knapsackga.cpp 
	$(CC) $(CC_FLAGS) knapsackdp.cpp -o dp
	$(CC) $(CC_FLAGS) knapsacksa.cpp -o sa 
	$(CC) $(CC_FLAGS) knapsackga.cpp -o ga 

mv_bin: 
	mkdir -p $(destDir)
	cp instance.txt dp sa ga golddp goldsa goldga $(destDir)
	@echo "All Done, executables should be in the $(destDir)"


