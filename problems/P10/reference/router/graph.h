#ifndef GRAPH_H
#define GRAPH_H

#include <vector>

// 有向带权图（1..n，w >= 0，无重边无自环）
struct Edge {
    int to;
    long long w;
};

class Graph {
public:
    static const long long INF_DIST;

    explicit Graph(int n);

    void add_edge(int u, int v, long long w);
    int node_count() const;
    const std::vector<Edge>& out_edges(int u) const;

    // Dijkstra（src 出发的单源最短路，不可达为 INF_DIST）
    void dijkstra(int src, std::vector<long long>& dist) const;

private:
    int n_;
    std::vector<std::vector<Edge> > adj_;
};

#endif
