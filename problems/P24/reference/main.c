// P26 对称方阵 —— 参考实现（改编自 C 题库 2022 秋完善题二维数组图案）
// 输入 n（1<=n<=20），输出 n 行 n 列方阵：两条对角线上为 1，其余为 0，元素间一个空格。
#include <stdio.h>
int main(void) {
    int n;
    if (scanf("%d", &n) != 1) return 0;
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            int v = (i == j || i + j == n - 1) ? 1 : 0;
            if (j) putchar(' ');
            printf("%d", v);
        }
        putchar('\n');
    }
    return 0;
}
