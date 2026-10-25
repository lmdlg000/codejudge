// P6 依赖检查器 —— 参考实现（最小堆拓扑排序，字典序最小 + 环检测）
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    vector<vector<int>> g(n + 1);
    vector<int> indeg(n + 1, 0);
    for (int i = 0; i < m; ++i) {
        int x, y;
        cin >> x >> y;
        // x 依赖 y：y 必须先构建 → 边 y → x
        g[y].push_back(x);
        ++indeg[x];
    }
    priority_queue<int, vector<int>, greater<int>> pq;
    for (int i = 1; i <= n; ++i)
        if (indeg[i] == 0) pq.push(i);
    vector<int> order;
    order.reserve(n);
    while (!pq.empty()) {
        int u = pq.top();
        pq.pop();
        order.push_back(u);
        for (int v : g[u]) {
            if (--indeg[v] == 0) pq.push(v);
        }
    }
    if ((int)order.size() < n) {
        cout << "CYCLE\n";
    } else {
        cout << "OK\n";
        for (int i = 0; i < n; ++i) {
            if (i) cout << ' ';
            cout << order[i];
        }
        cout << "\n";
    }
    return 0;
}
