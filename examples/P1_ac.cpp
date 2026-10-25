// examples/P1_ac.cpp —— 预期判定：AC（正确解法）
#include <bits/stdc++.h>
using namespace std;

int main() {
    long long w, d;
    cin >> w >> d;
    long long fee = 10;
    if (w > 1000) fee += 3 * ((w - 1000 + 499) / 500);
    if (d > 1000) fee += 12;
    else if (d > 500) fee += 5;
    cout << fee << "\n";
    return 0;
}
