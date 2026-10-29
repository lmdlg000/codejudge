#include "paths.h"

#include <queue>
#include <vector>

std::vector<long long> count_shortest_paths(const Graph& g, int src,
                                            const std::vector<long long>& dist) {
    int n = g.node_count();
    std::vector<long long> cnt(n + 1, 0);
    // 最短路 DAG：边 (u,v,w) 满足 dist[u] + w == dist[v]（u、v 均可达）
    // Kahn 拓扑序 DP，正确处理 0 权边（同 dist 层内也按拓扑序推进）
    std::vector<int> indeg(n + 1, 0);
    for (int u = 1; u <= n; ++u) {
        if (dist[u] >= Graph::INF_DIST) continue;
        for (size_t i = 0; i < g.out_edges(u).size(); ++i) {
            const Edge& e = g.out_edges(u)[i];
            if (dist[e.to] < Graph::INF_DIST && dist[u] + e.w == dist[e.to]) {
                ++indeg[e.to];
            }
        }
    }
    std::queue<int> q;
    for (int u = 1; u <= n; ++u) {
        if (dist[u] < Graph::INF_DIST && indeg[u] == 0) q.push(u);
    }
    cnt[src] = 1;
    while (!q.empty()) {
        int u = q.front();
        q.pop();
        for (size_t i = 0; i < g.out_edges(u).size(); ++i) {
            const Edge& e = g.out_edges(u)[i];
            if (dist[e.to] >= Graph::INF_DIST) continue;
            if (dist[u] + e.w != dist[e.to]) continue;
            cnt[e.to] = (cnt[e.to] + cnt[u]) % PATH_MOD;
            if (--indeg[e.to] == 0) q.push(e.to);
        }
    }
    return cnt;
}
