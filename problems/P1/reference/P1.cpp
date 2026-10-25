// P1 运费计算 —— 参考实现（gen 刷 .out 用）
#include <bits/stdc++.h>
using namespace std;

int main() {
    long long w, d;
    cin >> w >> d;
    long long fee = 10;                       // 首重 1000 克及以内 10 元
    if (w > 1000) fee += 3 * ((w - 1000 + 499) / 500);  // 超出部分每 500 克 3 元，向上取整
    if (d > 1000) fee += 12;                  // 超过 1000 公里
    else if (d > 500) fee += 5;               // 500<d≤1000
    cout << fee << "\n";
    return 0;
}
