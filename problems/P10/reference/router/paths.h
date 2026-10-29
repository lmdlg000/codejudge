#ifndef PATHS_H
#define PATHS_H

#include <vector>

#include "graph.h"

const long long PATH_MOD = 1000000007LL;

// 在最短路 DAG 上 DP 计数：cnt[v] = sum(cnt[u])（边 (u,v,w) 满足 dist[u]+w==dist[v]）。
// 前提：不存在位于最短路上的 0 权环（题目保证），故最短路 DAG 无环，计数有限。
// 返回 1-based 数组 cnt（已取模）；不可达点为 0。
std::vector<long long> count_shortest_paths(const Graph& g, int src,
                                            const std::vector<long long>& dist);

#endif
