// P22 数组最大值 —— 参考实现（改编自 C 题库 2017 编程题 max）
// 第一行 n，第二行 n 个整数，输出其中的最大值。
#include <stdio.h>
int main(void) {
    int n;
    if (scanf("%d", &n) != 1) return 0;
    int m;
    scanf("%d", &m);
    for (int i = 1; i < n; ++i) {
        int x; scanf("%d", &x);
        if (x > m) m = x;
    }
    printf("%d\n", m);
    return 0;
}
