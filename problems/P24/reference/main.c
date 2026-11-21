// P24 元素查找 —— 参考实现（改编自 C 题库 2016 编程题 find）
// 第一行 n，第二行 n 个整数，第三行目标值 x。x 在数组中输出 found，否则 not found。
#include <stdio.h>
int main(void) {
    int n;
    if (scanf("%d", &n) != 1) return 0;
    int a[1000];
    for (int i = 0; i < n; ++i) scanf("%d", &a[i]);
    int x;
    scanf("%d", &x);
    for (int i = 0; i < n; ++i)
        if (a[i] == x) { printf("found\n"); return 0; }
    printf("not found\n");
    return 0;
}
