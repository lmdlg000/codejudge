// P20 区间素数计数 —— 参考实现（改编自 C++ 试卷素数相关考点）
// 输入 l r（0<=l<=r<=100000），统计闭区间 [l,r] 内素数的个数。
#include <bits/stdc++.h>
using namespace std;
int main() {
    int l, r;
    if (!(cin >> l >> r)) return 0;
    int hi = max(r, 1);
    vector<char> isPrime(hi + 1, 1);
    isPrime[0] = 0;
    if (hi >= 1) isPrime[1] = 0;
    for (int i = 2; (long long)i * i <= hi; ++i)
        if (isPrime[i])
            for (long long j = (long long)i * i; j <= hi; j += i) isPrime[(int)j] = 0;
    int cnt = 0;
    for (int i = max(l, 2); i <= r; ++i) if (isPrime[i]) ++cnt;
    cout << cnt << '\n';
    return 0;
}
