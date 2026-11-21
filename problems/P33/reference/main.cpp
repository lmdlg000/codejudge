// P33 哥德巴赫配对 —— 情境拓展（趣味数学 2.6.1 哥德巴赫猜想）
// 输入偶数 n(4<=n<=200000)，输出一对素数 p<=q 使 p+q=n，且 p 尽可能小；若无解输出 NO。
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    if (!(cin >> n)) return 0;
    vector<char> prime(n + 1, 1);
    prime[0] = prime[1] = 0;
    for (int i = 2; (long long)i * i <= n; ++i)
        if (prime[i])
            for (long long j = (long long)i * i; j <= n; j += i) prime[(int)j] = 0;
    for (int p = 2; p <= n / 2; ++p) {
        if (prime[p] && prime[n - p]) {
            cout << p << ' ' << n - p << '\n';
            return 0;
        }
    }
    cout << "NO\n";
    return 0;
}
