// P27 水仙花数 —— 情境拓展（趣味数学 1.1.1）
// 输入区间 [a,b]（1<=a<=b<=100000），输出区间内所有三位水仙花数（各位数字立方和等于自身），
// 空格分隔；若没有则输出一个空行。
#include <stdio.h>
int main(void) {
    int a, b;
    if (scanf("%d %d", &a, &b) != 2) return 0;
    int first = 1;
    for (int n = a; n <= b && n <= 999; ++n) {
        if (n < 100) continue;
        int x = n, s = 0;
        while (x) { int d = x % 10; s += d*d*d; x /= 10; }
        if (s == n) {
            if (!first) putchar(' ');
            printf("%d", n);
            first = 0;
        }
    }
    putchar('\n');
    return 0;
}
