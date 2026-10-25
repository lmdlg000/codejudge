// examples/P1_make/inspector.cpp —— make 多文件构建链路演示（P6 依赖检查器实现）
#include "util.h"

#include <cstdio>
#include <iostream>

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n, m;
    if (!(std::cin >> n >> m)) return 0;
    DependencyGraph g(n);
    for (int i = 0; i < m; ++i) {
        int x, y;
        std::cin >> x >> y;
        g.add_dependency(x, y);
    }
    std::vector<int> order;
    if (!g.topo_order(order)) {
        std::cout << "CYCLE\n";
        return 0;
    }
    std::cout << "OK\n";
    for (size_t i = 0; i < order.size(); ++i) {
        if (i) std::cout << ' ';
        std::cout << order[i];
    }
    std::cout << "\n";
    return 0;
}
