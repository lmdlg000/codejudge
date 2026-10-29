#pragma once
#include <utility>
#include <vector>

// 有向依赖图：1..n 编号，邻接表 + 入度
struct TopoGraph {
    int n;
    std::vector<std::vector<int>> adj;
    std::vector<int> indeg;
};

// 由边表建图（u -> v 表示 u 完成后 v 才能开始）
TopoGraph build_graph(int n, const std::vector<std::pair<int, int> >& edges);

// 最小堆拓扑排序：就绪集每次取编号最小者；有环返回 false
bool topo_sort(const TopoGraph& g, std::vector<int>& order);
