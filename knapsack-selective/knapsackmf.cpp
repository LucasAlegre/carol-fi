// A Memory Functions based solution for 0-1 Knapsack problem

#include <cstdio>
#include <iostream>
#include <fstream>
#include <vector>
#include <sstream>
#include <string>

using namespace std;

int W;
int W2;
int n;
int n2;
vector<int> values;
vector<int> values2;
vector<int> weights;
vector<int> weights2;
vector<vector<int>> V;

int knapSack();
int knapSackAuxRec(int i, int i2, int j, int j2);
void exit_gracefully();

void exit_gracefully(){
    ofstream detection_log("/tmp/knapsack/ga-detection.log");
    detection_log << "Erro dectado!";
    detection_log.close();
    exit(0);
}

int knapSack() {

    V = vector<vector<int>>(n + 1);

    for (int i = 0; i <= n; i++)
        V[i] = vector<int>(W + 1);

    int i = 0, i2 = 0;
    while (i <= n && i == i2) {
        int w = 0, w2 = 0;

        while(w <= W && w == w2) {
            if (i == 0 || w == 0) {
                V[i][w] = 0;
            } else {
                V[i][w] = -1;
            }
            w++; w2++;
        }

        if(w != w2) {
            exit_gracefully();
        }

        i++; i2++;
    }

    if(i != i2) {
        exit_gracefully();
    }

    V[n][W] = knapSackAuxRec(n, n2, W, W2);

    return V[n][W];
}

int knapSackAuxRec(int i, int i2, int j, int j2) { // i = n, j = w
    int value;

    if (V[i][j] < 0) { // meaning not already calculated

        if (j < weights[i]) {
            value = knapSackAuxRec(i - 1, i2 - 1, j, j2);
        } else {
            value = max(knapSackAuxRec(i - 1, i2 - 1, j, j2), values[i] + knapSackAuxRec(i - 1, i2 - 1, j - weights[i], j2 - weights[i]));
        }

        V[i][j] = value;// put valid value in the table for both cases
    }

    if(i != i2 || j != j2) {
        exit_gracefully();
    }

    return V[i][j];
}

int main() {
    ifstream file("/tmp/knapsack/instance.txt");
    ofstream outfile("/tmp/knapsack/outputmf");

    file >> n;
    n2 = n;
    file >> W;
    W2 = W;

    for (int i = 0; i < n; i++) {
        int x, y;
        file >> x >> y;
        values.push_back(x);
        values2.push_back(x);
        weights.push_back(y);
        weights2.push_back(y);
    }

	int result = knapSack();

    if(n != n2 || W != W2) {
        exit_gracefully();
    }

    for(int i = 0; i < values.size(); i++){
        if(values[i] != values2[i] || weights[i] != weights2[i]) {
            exit_gracefully();
        }
    }

    outfile << result;
    outfile.close();

	std::cout << "Result: " << result << "\n";

    return 0;
}
