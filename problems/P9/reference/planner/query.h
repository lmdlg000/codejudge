#ifndef QUERY_H
#define QUERY_H

#include <vector>

#include "interval.h"

// 查询索引：左端点、右端点分别升序
struct QueryIndex {
    std::vector<long long> lefts;
    std::vector<long long> rights;
};

// 用全体区间构建查询索引
void build_index(const std::vector<Interval>& a, QueryIndex& idx);

// 被 x 包含（l <= x <= r）的区间个数：#{l<=x} - #{r<x}，O(log n)
long long count_covering(const QueryIndex& idx, long long x);

#endif
