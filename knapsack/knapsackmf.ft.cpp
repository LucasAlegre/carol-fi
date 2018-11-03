// A Memory Functions based solution for 0-1 Knapsack problem

#include <cstdio>
#include <iostream>
#include <fstream>
#include <vector>
#include <sstream>
#include <string>

using namespace std;

int knapSack(int W, int n, vector<int>& values, vector<int>& weights, vector<vector<int>>& V);
int knapSackAuxRec(int i, int j, vector<int>& values, vector<int>& weights, vector<vector<int>>& V);


int knapSack(int W, int n, vector<int>& values, vector<int>& weights, vector<vector<int>>& V) {

    V = vector<vector<int>>(n + 1);

    for (int i = 0; i <= n; i++)
        V[i] = vector<int>(W + 1);

    for (int i = 0; i <= n; i++) {
        for (int w = 0; w <= W; w++) {
            if (i == 0 || w == 0) {
                V[i][w] = 0;
            } else {
                V[i][w] = -1;
            }
        }
    }

    V[n][W] = knapSackAuxRec(n, W, values, weights, V);

    return V[n][W];
}

int knapSackAuxRec(int i, int j, vector<int>& values, vector<int>& weights, vector<vector<int>>& V) { // i = n, j = w
    int value;
    if (V[i][j] < 0) { // meaning not already calculated

        if (j < weights[i]) {
            value = knapSackAuxRec(i - 1, j, values, weights, V);
        } else {
            value = max(knapSackAuxRec(i - 1, j, values, weights, V), values[i] + knapSackAuxRec(i - 1, j - weights[i], values, weights, V));
        }


        V[i][j] = value;// put valid value in the table for both cases
    }

    return V[i][j];
}

int executeAlgorithm() {
    int W;
    int n;
    vector<int> values;
    vector<int> weights;
    vector<vector<int>> V;

    ifstream file("/tmp/knapsack/instance.txt");

    file >> n;
    file >> W;

    for (int i = 0; i < n; i++) {
        int x, y;
        file >> x >> y;
        values.push_back(x);
        weights.push_back(y);
    }

    return knapSack(W, n, values, weights, V);
}

int main() {
    ofstream outfile("/tmp/knapsack/outputmf");

    int result;
    int result1 = executeAlgorithm();
    int result2 = executeAlgorithm();

    if(result1 == result2) {
        result = result1;
    } else {
        result = executeAlgorithm();
    }

    outfile << result;
    outfile.close();

    std::cout << "Result: " << result << "\n";

    return 0;
}
