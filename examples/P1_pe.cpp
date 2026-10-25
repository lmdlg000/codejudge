// examples/P1_pe.cpp —— 预期判定：PE（数值正确，行尾多一个空格 → 仅空白差异）
#include <bits/stdc++.h>
using namespace std;

int main() {
    long long w, d;
    cin >> w >> d;
    long long fee = 10;
    if (w > 1000) fee += 3 * ((w - 1000 + 499) / 500);
    if (d > 1000) fee += 12;
    else if (d > 500) fee += 5;
    cout << fee << " \n";  // 错误：数字后多打了一个空格
    return 0;
}
