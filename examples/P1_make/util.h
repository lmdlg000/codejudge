// examples/P1_make/util.h —— 多文件演示：依赖图与最小堆拓扑排序
#pragma once

#include <queue>
#include <vector>

// 依赖图：edge y→x 表示「x 依赖 y」（y 必须先构建）
struct DependencyGraph {
    int n;
    std::vector<std::vector<int>> adj;
    std::vector<int> indeg;

    explicit DependencyGraph(int n_) : n(n_), adj(n_ + 1), indeg(n_ + 1, 0) {}

    void add_dependency(int x, int y) {
        adj[y].push_back(x);
        ++indeg[x];
    }

    // 字典序最小的合法构建顺序；存在环返回 false
    bool topo_order(std::vector<int> &order) const {
        std::priority_queue<int, std::vector<int>, std::greater<int>> pq;
        for (int i = 1; i <= n; ++i)
            if (indeg[i] == 0) pq.push(i);
        order.clear();
        order.reserve(n);
        std::vector<int> deg = indeg;
        while (!pq.empty()) {
            int u = pq.top();
            pq.pop();
            order.push_back(u);
            for (int v : adj[u]) {
                if (--deg[v] == 0) pq.push(v);
            }
        }
        return (int)order.size() == n;
    }
};
