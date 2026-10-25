// P4 日期推算 —— 参考实现（逐月推进）
#include <bits/stdc++.h>
using namespace std;

static bool is_leap(int y) {
    return (y % 4 == 0 && y % 100 != 0) || (y % 400 == 0);
}

static int days_in_month(int y, int m) {
    static const int d[] = {0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
    if (m == 2 && is_leap(y)) return 29;
    return d[m];
}

int main() {
    int y, m, d, D;
    scanf("%d-%d-%d %d", &y, &m, &d, &D);
    while (D > 0) {
        int remain = days_in_month(y, m) - d + 1;  // 当月剩余天数（含今天）
        if (D < remain) {
            d += D;
            D = 0;
        } else {
            D -= remain;
            d = 1;
            ++m;
            if (m > 12) {
                m = 1;
                ++y;
            }
        }
    }
    printf("%04d-%02d-%02d\n", y, m, d);
    return 0;
}
