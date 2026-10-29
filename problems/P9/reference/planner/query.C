#include "query.h"

#include <algorithm>

void build_index(const std::vector<Interval>& a, QueryIndex& idx) {
    idx.lefts.clear();
    idx.rights.clear();
    idx.lefts.reserve(a.size());
    idx.rights.reserve(a.size());
    for (const auto& iv : a) {
        idx.lefts.push_back(iv.l);
        idx.rights.push_back(iv.r);
    }
    std::sort(idx.lefts.begin(), idx.lefts.end());
    std::sort(idx.rights.begin(), idx.rights.end());
}

long long count_covering(const QueryIndex& idx, long long x) {
    // #{l <= x}：第一个 > x 的位置之前
    long long le = std::upper_bound(idx.lefts.begin(), idx.lefts.end(), x) - idx.lefts.begin();
    // #{r < x}：第一个 >= x 的位置之前
    long long lt = std::lower_bound(idx.rights.begin(), idx.rights.end(), x) - idx.rights.begin();
    return le - lt;
}
