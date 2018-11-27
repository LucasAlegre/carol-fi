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
#include <algorithm>
using namespace std;

vector<int> val;
vector<int> wt;
int n, W;
int pop_size = 40;

int rand_bit(){
    return rand() % 2;
}

int cost(vector<int> &solution){
    int peso=0, valor=0;
    for(int i=0; i < n; i++){
        peso += solution[i] * wt[i];
        valor += solution[i] * val[i];
    }

    if(peso > W){
        return 99999999;
    }
    else{
        return -valor;
    }
}

float random01(){
    return static_cast <float> (rand()) / static_cast <float> (RAND_MAX);
}

struct chromossome{
    vector<int> solution;
    int fitness;
    chromossome(int size){
        for(int i = 0; i < size; i++)
            solution.push_back(rand_bit());
        fitness = cost(solution);
    }
    chromossome(){};
};

bool operator<(const chromossome& a, const chromossome& b)
{
    return a.fitness < b.fitness;
}

vector<int> tournament(vector<chromossome> &pop){
    vector<chromossome> competitors;

    for(int i=0; i < 3; i++){
        int randIndex = rand() % pop_size;
        competitors.push_back(pop[randIndex]);
    }

    sort(competitors.begin(), competitors.end());
    vector<int> tournamentWinner = competitors[0].solution;
    return tournamentWinner;
}

void crossover(vector<int> &pai, vector<int> &mae, vector<int> &filho1, vector<int> &filho2){
    vector<int> mask(n);
    for(int i = 0; i < n; i++){
        mask[i] = rand_bit();
    }
    filho1 = pai;
    filho2 = mae;
    for(int i = 0; i < n; i++){
        if(mask[i]){
            swap(filho1[i], filho2[i]);
        }
    }
}

int genetic_algorithm() {
    srand (42);
    vector<chromossome> pop;
    for(int i = 0; i < pop_size; i++)
        pop.push_back(chromossome(n));

    sort(pop.begin(), pop.end());
    int best = pop[0].fitness;

    for(int g = 0; g < 10000; g++){
        vector<chromossome> new_pop;

        for(int i=0; i < 2; i++)
            new_pop.push_back(pop[i]);

        while(new_pop.size() != pop_size){
            vector<int> pai, mae, filho1, filho2;
            pai = tournament(pop);
            mae = tournament(pop);
            crossover(pai, mae, filho1, filho2);
            chromossome f1, f2; f1.solution = filho1; f2.solution = filho2;
            new_pop.push_back(f1);
            new_pop.push_back(f2);
        }
        for(int i=0; i < pop_size; i++){
            if(random01() < 0.5)
                swap(new_pop[i].solution[rand() % n], new_pop[i].solution[rand() % n]);
            new_pop[i].fitness = cost(new_pop[i].solution);
        }

        sort(new_pop.begin(), new_pop.end());
        best = new_pop[0].fitness;
        pop = new_pop;
        //cout << g << " " << -best << endl;
    }

    return -best;
}

void read_input(){
    ifstream file("/tmp/knapsack/instance.txt");
    val.clear(); wt.clear();
    file >> n; file >> W;
    for(int i = 0; i < n; i++){
        int x, y; file >> x >> y;
        val.push_back(x);
        wt.push_back(y);
    }
    file.close();
}

int main()
{
    
    ofstream outfile("/tmp/knapsack/outputga");
    read_input();
    int result1 = genetic_algorithm();
    read_input();
    int result2 = genetic_algorithm();
    
    if(result1 != result2) {
	ofstream detection_log("/tmp/knapsack/ga-detection.log");
        detection_log << result1 << " " << result2;
    	detection_log.close();
    }

    outfile << result1;
    outfile.close();
    cout << "Result: " << result1 << "\n";

    return 0;
}
