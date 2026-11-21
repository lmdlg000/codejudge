// P19 绝对值降序前列 —— 参考实现（改编自 C++ 试卷编程题 Array 类）
// 输入 n m，再输入 n 个整数；按绝对值从大到小排序，绝对值相等时数值小的在前，
// 输出前 m 个元素，空格分隔。
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n, m;
    if (!(cin >> n >> m)) return 0;
    vector<long long> a(n);
    for (auto &x : a) cin >> x;
    sort(a.begin(), a.end(), [](long long x, long long y) {
        long long ax = llabs(x), ay = llabs(y);
        if (ax != ay) return ax > ay;
        return x < y;
    });
    for (int i = 0; i < m && i < n; ++i) { if (i) cout << ' '; cout << a[i]; }
    cout << '\n';
    return 0;
}
