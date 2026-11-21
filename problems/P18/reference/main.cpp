// P18 素数因子分解 —— 参考实现（改编自 C++ 试卷编程题）
// 输入整数 n(2<=n<=1e9)，从小到大输出它的所有不同素数因子，空格分隔。
#include <bits/stdc++.h>
using namespace std;
int main() {
    long long n;
    if (!(cin >> n)) return 0;
    bool first = true;
    for (long long d = 2; d * d <= n; ++d) {
        if (n % d == 0) {
            if (!first) cout << ' ';
            cout << d; first = false;
            while (n % d == 0) n /= d;
        }
    }
    if (n > 1) { if (!first) cout << ' '; cout << n; }
    cout << '\n';
    return 0;
}
