#include "interval.h"

#include <algorithm>

void sort_by_right(std::vector<Interval>& a) {
    std::sort(a.begin(), a.end(), [](const Interval& x, const Interval& y) {
        if (x.r != y.r) return x.r < y.r;
        return x.l < y.l;
    });
}

int max_disjoint(std::vector<Interval> a) {
    sort_by_right(a);
    int cnt = 0;
    long long last_r = -1;  // l >= 0，首区间必然满足 l > last_r
    for (const auto& iv : a) {
        if (iv.l > last_r) {  // 严格大于：共享端点算相交
            ++cnt;
            last_r = iv.r;
        }
    }
    return cnt;
}
