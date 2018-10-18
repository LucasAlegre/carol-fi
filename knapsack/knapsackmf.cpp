// A Memory Functions based solution for 0-1 Knapsack problem

#include <cstdio>
#include <iostream>
#include <fstream>
#include <vector>
#include <sstream>
#include <string>

using namespace std;

int W;
int n;
vector<int> values;
vector<int> weights;
vector<vector<int>> V;

int knapSack();
int knapSackAuxRec(int i, int j);


int knapSack() {

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

    //V[n][W] = knapSackAuxRec(n, W);

    return V[n][W];
}

int knapSackAuxRec(int i, int j) { // i = n, j = w
    int value;
    if (V[i][j] < 0) { // meaning not already calculated

        if (j < weights[i]) {
            value = knapSackAuxRec(i - 1, j);
        } else {
            value = max(knapSackAuxRec(i - 1, j), values[i] + knapSackAuxRec(i - 1, j - weights[i]));
        }


        V[i][j] = value;// put valid value in the table for both cases
    }

    return V[i][j];
}

int main() {
    ifstream file("/tmp/knapsack/instance.txt");
    ofstream outfile("/tmp/knapsack/outputdp");

    file >> n;
    file >> W;

    for (int i = 0; i < n; i++) {
        int x, y;
        file >> x >> y;
        values.push_back(x);
        weights.push_back(y);
    }

    outfile << knapSack();
    outfile.close();

    return 0;
}
