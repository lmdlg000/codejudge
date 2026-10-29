#include <iostream>
#include <vector>

#include "interval.h"
#include "query.h"

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);

    int n, q;
    if (!(std::cin >> n >> q)) return 0;

    std::vector<Interval> a(n);
    for (int i = 0; i < n; ++i) std::cin >> a[i].l >> a[i].r;

    std::cout << max_disjoint(a) << "\n";

    QueryIndex idx;
    build_index(a, idx);
    for (int j = 0; j < q; ++j) {
        long long x;
        std::cin >> x;
        std::cout << count_covering(idx, x) << "\n";
    }
    return 0;
}
