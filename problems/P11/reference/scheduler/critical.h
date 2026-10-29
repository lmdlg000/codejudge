#pragma once
#include "topo.h"

#include <vector>

// 关键路径 DP：返回最短完工时间（最长加权路径长度，可能超过 32 位）。
// d 为 1..n 的工期，order 为合法拓扑序。
long long critical_path(const TopoGraph& g, const std::vector<long long>& d,
                        const std::vector<int>& order);
