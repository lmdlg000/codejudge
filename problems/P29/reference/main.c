// P29 回文素数 —— 情境拓展（趣味数学 2.3 对称素数）
// 输入区间 [a,b]（1<=a<=b<=10000），输出区间内所有既是素数又是回文数的整数，空格分隔。
#include <stdio.h>
#include <string.h>
static int isPrime(int n) {
    if (n < 2) return 0;
    for (int d = 2; d * d <= n; ++d) if (n % d == 0) return 0;
    return 1;
}
static int isPalin(int n) {
    char s[16];
    sprintf(s, "%d", n);
    int l = 0, r = (int)strlen(s) - 1;
    while (l < r) if (s[l++] != s[r--]) return 0;
    return 1;
}
int main(void) {
    int a, b;
    if (scanf("%d %d", &a, &b) != 2) return 0;
    int first = 1;
    for (int n = a; n <= b; ++n) {
        if (isPrime(n) && isPalin(n)) {
            if (!first) putchar(' ');
            printf("%d", n);
            first = 0;
        }
    }
    putchar('\n');
    return 0;
}
