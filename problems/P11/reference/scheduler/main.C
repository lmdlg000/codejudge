#include "critical.h"
#include "topo.h"

#include <iostream>
#include <utility>
#include <vector>

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);

    int n, m;
    if (!(std::cin >> n >> m)) return 0;
    std::vector<long long> d(n + 1);
    for (int i = 1; i <= n; ++i) std::cin >> d[i];
    std::vector<std::pair<int, int> > edges;
    edges.reserve(m);
    for (int i = 0; i < m; ++i) {
        int u, v;
        std::cin >> u >> v;
        edges.push_back(std::make_pair(u, v));
    }

    TopoGraph g = build_graph(n, edges);
    std::vector<int> order;
    if (!topo_sort(g, order)) {
        std::cout << "-1\n";
        return 0;
    }
    std::cout << critical_path(g, d, order) << "\n";
    for (int i = 0; i < n; ++i) {
        if (i) std::cout << ' ';
        std::cout << order[i];
    }
    std::cout << "\n";
    return 0;
}
