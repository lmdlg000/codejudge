#include <cstdio>
#include <vector>

#include "graph.h"
#include "paths.h"

int main() {
    int n, m;
    if (scanf("%d %d", &n, &m) != 2) return 0;
    Graph g(n);
    for (int i = 0; i < m; ++i) {
        int u, v;
        long long w;
        scanf("%d %d %lld", &u, &v, &w);
        g.add_edge(u, v, w);
    }
    std::vector<long long> dist;
    g.dijkstra(1, dist);
    if (n == 1) {
        printf("0 1\n");
        return 0;
    }
    if (dist[n] >= Graph::INF_DIST) {
        printf("-1 0\n");
        return 0;
    }
    std::vector<long long> cnt = count_shortest_paths(g, 1, dist);
    printf("%lld %lld\n", dist[n], cnt[n]);
    return 0;
}
