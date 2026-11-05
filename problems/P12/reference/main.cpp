// P12 货架巡检 —— 参考实现（gen 刷 .out 用）
// 回型遍历：四段 for 各扫一条边，每扫完一条就把该边收缩掉；
// 每段都带 cnt < T 的守卫，预算用尽立刻停。
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int R, C;
    long long T;
    if (!(cin >> R >> C >> T)) return 0;

    vector<vector<long long>> a(R, vector<long long>(C));
    for (int i = 0; i < R; i++)
        for (int j = 0; j < C; j++) cin >> a[i][j];

    long long cnt = 0, sum = 0;
    int top = 0, bottom = R - 1, left = 0, right = C - 1;

    while (top <= bottom && left <= right && cnt < T) {
        for (int j = left; j <= right && cnt < T; j++) { sum += a[top][j]; cnt++; }
        top++;
        for (int i = top; i <= bottom && cnt < T; i++) { sum += a[i][right]; cnt++; }
        right--;
        if (top <= bottom) {
            for (int j = right; j >= left && cnt < T; j--) { sum += a[bottom][j]; cnt++; }
            bottom--;
        }
        if (left <= right) {
            for (int i = bottom; i >= top && cnt < T; i--) { sum += a[i][left]; cnt++; }
            left++;
        }
    }

    cout << cnt << " " << sum << "\n";
    return 0;
}
