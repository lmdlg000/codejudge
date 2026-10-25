// P3 活动安排 —— 参考实现（按结束时间贪心，O(n log n)）
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<pair<long long, long long>> a(n);
    for (int i = 0; i < n; ++i) cin >> a[i].first >> a[i].second;
    sort(a.begin(), a.end(), [](const auto &x, const auto &y) { return x.second < y.second; });
    int cnt = 0;
    long long last = LLONG_MIN;
    for (const auto &[s, t] : a) {
        if (s >= last) {   // 半开区间：结束时刻等于开始时刻可连办
            ++cnt;
            last = t;
        }
    }
    cout << cnt << "\n";
    return 0;
}
