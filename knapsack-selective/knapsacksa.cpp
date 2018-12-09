#include<stdio.h>
#include<iostream>
#include<fstream>
#include<vector>
#include<sstream>
#include<string>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>
using namespace std;

int W, W2, n, n2;
vector<int> val;
vector<int> val2;
vector<int> wt;
vector<int> wt2;

// int getW() {
// 	if(W1 == W2 && W2 == W3) {
// 		return W1;
// 	} else if(W1 == W2) {
// 		W3 = W1;
// 	} else if(W2 == W3) {
// 		W1 = W2;
// 	} else if(W1 == W3) {
// 		W2 = W1;
// 	}
// 	return W1;
// }

// void setW(int newW) {
// 	W1 = W2 = W3 = newW;
// }

void exit_gracefully(){
    ofstream detection_log("/tmp/knapsack/sa-detection.log");
    detection_log << "Erro dectado!";
    detection_log.close();
    exit(0);
}

int rand_bit(){
    return rand() % 2;
}

float random01(){
    return static_cast <float> (rand()) / static_cast <float> (RAND_MAX);
}

int cost(vector<int> &solution){
    if(n != n2 || W != W2){
        exit_gracefully();
    }

    int peso=0, peso2=0, valor=0, valor2=0;
    for(int i=0; i < n; i++){
        peso += solution[i] * wt[i];
        valor += solution[i] * val[i];
    }
    for(int i=0; i < n; i++){
        peso2 += solution[i] * wt2[i];
        valor2 += solution[i] * val2[i];
    }
    if(peso != peso2 || valor != valor2){
        exit_gracefully();
    }

    if(peso > W){
        return 99999999;
    }
    else{
        return -valor;
    }
}

int simulated_annealing() {
    vector<int> solution(n);
    for(int i = 0; i < n; i++)
        solution[i] = rand_bit();
    int best = cost(solution);
    int best2 = cost(solution);
    int temp = 2000000;
    int temp2 = 2000000;

    //int co=0;

    for(int t = 0; t < 1000000; t++){
        vector<int> s(solution);
        int i = rand() % n;
        s[i] = 1 - s[i];
        int c = cost(s);
        if(best != best2){
            exit_gracefully();
        }
        int delta = c - best;
        if(delta <= 0){
            solution = s;
            best = c;
            best2 = c;
        }
        else{
            if(temp == temp2){
                if (random01() <= exp(-delta/(float)(temp))){
                    //cout << exp(-delta/(float)(temp)) << endl;
                    //co++;

                    solution = s;
                    if(best != best2){
                        exit_gracefully();
                    }
                    best = min(c, best);
                    best2 = min(c, best2);
                }
            }
            else{
                exit_gracefully();
            }
        } 
        temp *= 0.99999;
        temp2 *= 0.99999;
    }
    //cout << co << endl;
    if(best != best2){
        exit_gracefully();
    }
    return -best;
}

int main()
{
    ifstream file("/tmp/knapsack/instance.txt");
    ofstream outfile("/tmp/knapsack/outputsa");
	

    srand (42);
    file >> n; file >> W;
    n2 = n; W2 = W;

    for(int i = 0; i < n; i++){
        int x, y; file >> x >> y;
        val.push_back(x); val2.push_back(x);
        wt.push_back(y); wt2.push_back(y);
    }

    outfile << simulated_annealing();
    outfile.close();

    return 0;
}
