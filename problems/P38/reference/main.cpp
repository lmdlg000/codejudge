// P38 数字三角形取最大和 —— 情境拓展（趣味数学 5.3 巧妙建模）
// 输入 n，接下来 n 行第 i 行有 i 个整数，构成数字三角形。
// 从顶到底每次只能向左下或右下走一步，求路径上数字之和的最大值。
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    if (!(cin >> n)) return 0;
    vector<vector<long long>> a(n + 1);
    for (int i = 1; i <= n; ++i) {
        a[i].resize(i + 1);
        for (int j = 1; j <= i; ++j) cin >> a[i][j];
    }
    vector<long long> dp(n + 2, 0);
    for (int i = n; i >= 1; --i)
        for (int j = 1; j <= i; ++j)
            dp[j] = a[i][j] + max(dp[j], dp[j + 1]);
    cout << dp[1] << '\n';
    return 0;
}
