// examples/P1_wa.cpp —— 预期判定：WA（首重费用算成 12 元，答案错误）
#include <bits/stdc++.h>
using namespace std;

int main() {
    long long w, d;
    cin >> w >> d;
    long long fee = 12;  // 错误：首重应为 10 元
    if (w > 1000) fee += 3 * ((w - 1000 + 499) / 500);
    if (d > 1000) fee += 12;
    else if (d > 500) fee += 5;
    cout << fee << "\n";
    return 0;
}
