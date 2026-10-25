// P5 最短路径 —— 参考实现（堆优化 Dijkstra，O((n+m) log n)）
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    vector<vector<pair<int, long long>>> g(n + 1);
    for (int i = 0; i < m; ++i) {
        int u, v;
        long long w;
        cin >> u >> v >> w;
        g[u].push_back({v, w});
    }
    const long long INF = LLONG_MAX / 4;
    vector<long long> dist(n + 1, INF);
    dist[1] = 0;
    priority_queue<pair<long long, int>, vector<pair<long long, int>>, greater<>> pq;
    pq.push({0, 1});
    while (!pq.empty()) {
        auto [d, u] = pq.top();
        pq.pop();
        if (d > dist[u]) continue;
        for (auto [v, w] : g[u]) {
            if (dist[v] > d + w) {
                dist[v] = d + w;
                pq.push({dist[v], v});
            }
        }
    }
    if (dist[n] >= INF) cout << -1 << "\n";
    else cout << dist[n] << "\n";
    return 0;
}
