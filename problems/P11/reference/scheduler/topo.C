#include "topo.h"

#include <functional>
#include <queue>

TopoGraph build_graph(int n, const std::vector<std::pair<int, int> >& edges) {
    TopoGraph g;
    g.n = n;
    g.adj.assign(n + 1, {});
    g.indeg.assign(n + 1, 0);
    for (const auto& e : edges) {
        g.adj[e.first].push_back(e.second);
        ++g.indeg[e.second];
    }
    return g;
}

bool topo_sort(const TopoGraph& g, std::vector<int>& order) {
    order.clear();
    order.reserve(g.n);
    std::vector<int> deg = g.indeg;
    std::priority_queue<int, std::vector<int>, std::greater<int> > ready;
    for (int i = 1; i <= g.n; ++i) {
        if (deg[i] == 0) ready.push(i);
    }
    while (!ready.empty()) {
        int u = ready.top();
        ready.pop();
        order.push_back(u);
        for (int v : g.adj[u]) {
            if (--deg[v] == 0) ready.push(v);
        }
    }
    return (int)order.size() == g.n;
}
