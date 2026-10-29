#include "critical.h"

long long critical_path(const TopoGraph& g, const std::vector<long long>& d,
                        const std::vector<int>& order) {
    // finish[i] = 任务 i 的最早完工时刻
    std::vector<long long> finish(g.n + 1);
    for (int i = 1; i <= g.n; ++i) finish[i] = d[i];
    for (int u : order) {
        for (int v : g.adj[u]) {
            if (finish[v] < finish[u] + d[v]) finish[v] = finish[u] + d[v];
        }
    }
    long long ans = 0;
    for (int i = 1; i <= g.n; ++i) {
        if (ans < finish[i]) ans = finish[i];
    }
    return ans;
}
