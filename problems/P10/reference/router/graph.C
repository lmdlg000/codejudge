#include "graph.h"

#include <queue>
#include <utility>

const long long Graph::INF_DIST = (1LL << 62);

Graph::Graph(int n) : n_(n), adj_(n + 1) {}

void Graph::add_edge(int u, int v, long long w) {
    adj_[u].push_back(Edge{v, w});
}

int Graph::node_count() const { return n_; }

const std::vector<Edge>& Graph::out_edges(int u) const { return adj_[u]; }

void Graph::dijkstra(int src, std::vector<long long>& dist) const {
    dist.assign(n_ + 1, INF_DIST);
    dist[src] = 0;
    typedef std::pair<long long, int> PLI;
    std::priority_queue<PLI, std::vector<PLI>, std::greater<PLI> > pq;
    pq.push(PLI(0, src));
    while (!pq.empty()) {
        long long d = pq.top().first;
        int u = pq.top().second;
        pq.pop();
        if (d != dist[u]) continue;
        for (size_t i = 0; i < adj_[u].size(); ++i) {
            const Edge& e = adj_[u][i];
            long long nd = d + e.w;
            if (nd < dist[e.to]) {
                dist[e.to] = nd;
                pq.push(PLI(nd, e.to));
            }
        }
    }
}
