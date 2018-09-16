// A Dynamic Programming based solution for 0-1 Knapsack problem
#include<cstdio>
#include<iostream>
#include<fstream>
#include<sstream>
#include<string>

using namespace std;

int knapSack(int W, int n, int *val, int *wt) {
    int **V;
    V = static_cast<int **>(malloc(sizeof(int *) * (n + 1)));

    for (int i = 0; i <= n; i++) {
        *(V + i) = static_cast<int *>(malloc(sizeof(int) * (W + 1)));
    }

    for (int i = 0; i <= n; i++) {
        for (int w = 0; w <= W; w++) {
            if (i == 0 || w == 0)
                *(*(V + i) + w) = 0;
            else if (w >= wt[i - 1]) {
                *(*(V + i) + w) = max(val[i - 1] + V[i - 1][w - wt[i - 1]], V[i - 1][w]);
            } else
                *(*(V + i) + w) = V[i - 1][w];
        }
    }

    return *(*(V + n) + W);
}

int main() {
    ifstream file("/tmp/knapsack/instance.txt");
    ofstream outfile("/tmp/knapsack/outputdp");

    int *val;
    int *wt;
    int n, W;
    file >> n;
    file >> W;

    val = static_cast<int *>(malloc(sizeof(int) * n));
    wt = static_cast<int *>(malloc(sizeof(int) * n));

    for (int i = 0; i < n; i++) {
        int x, y;
        file >> x >> y;
        *(val + i) = x;
        *(wt + i) = y;
    }

    outfile << knapSack(W, n, val, wt);
    outfile.close();
    return 0;
}
