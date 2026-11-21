// P23 数组极差 —— 参考实现（改编自 C 题库 2021 编程题 fun）
// 第一行 n，第二行 n 个整数，输出最大值与最小值之差（极差）。
#include <stdio.h>
int main(void) {
    int n;
    if (scanf("%d", &n) != 1) return 0;
    int x;
    scanf("%d", &x);
    int mn = x, mx = x;
    for (int i = 1; i < n; ++i) {
        scanf("%d", &x);
        if (x < mn) mn = x;
        if (x > mx) mx = x;
    }
    printf("%d\n", mx - mn);
    return 0;
}
