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

vector<int> val;
vector<int> wt;
int n, W;

int rand_bit(){
    return rand() % 2;
}

float random01(){
   return static_cast <float> (rand()) / static_cast <float> (RAND_MAX);
}

int cost(vector<int> &solution){
    int peso=0, valor=0;
    for(int i=0; i < n; i++){
       peso += solution[i] * wt[i];
       valor += solution[i] * val[i];
    }
    if(peso > W)
       return 99999999;
    else
       return -valor;
}

int simulated_annealing() {
    vector<int> solution(n);
    for(int i = 0; i < n; i++)
       solution[i] = rand_bit();
    int best = cost(solution);
    int temp = 2000000;

    //int co=0;

    for(int t = 0; t < 1000000; t++){
         vector<int> s(solution);
         int i = rand() % n;
         s[i] = 1 - s[i];
         int c = cost(s);
         int delta = c - best;
         if(delta <= 0){
             solution = s;
             best = c;
         }
         else if (random01() <= exp(-delta/(float)(temp))){
             //cout << exp(-delta/(float)(temp)) << endl;
             //co++;

             solution = s;
             best = min(c, best);
         }
         temp *= 0.99999;
    }
    //cout << co << endl;
    
    return -best;
}
 
int main()
{
    ifstream file("/tmp/knapsack/instance.txt");
    ofstream outfile("/tmp/knapsack/outputsa");

    srand (42);
    file >> n; file >> W;
    
    for(int i = 0; i < n; i++){
        int x, y; file >> x >> y;
        val.push_back(x);
        wt.push_back(y);
    }

    outfile << simulated_annealing();
    outfile.close();

    return 0;
}
