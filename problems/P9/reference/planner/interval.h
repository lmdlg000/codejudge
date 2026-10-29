#ifndef INTERVAL_H
#define INTERVAL_H

#include <vector>

// 闭区间 [l, r]
struct Interval {
    long long l;
    long long r;
};

// 按右端点升序排序（右端点相同按左端点升序）
void sort_by_right(std::vector<Interval>& a);

// 最大两两不相交区间个数（共享端点算相交：[1,2] 与 [2,3] 不能同时选）
// 内部按右端点贪心，O(n log n)
int max_disjoint(std::vector<Interval> a);

#endif
