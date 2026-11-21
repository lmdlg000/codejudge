// P28 完数判定 —— 情境拓展（趣味数学 1.5.1）
// 输入正整数 n（1<=n<=1e8），若 n 等于其所有真因子（含 1，不含自身）之和输出 YES，否则 NO。
#include <stdio.h>
int main(void) {
    long long n;
    if (scanf("%lld", &n) != 1) return 0;
    if (n <= 1) { printf("NO\n"); return 0; }
    long long sum = 1;
    for (long long d = 2; d * d <= n; ++d) {
        if (n % d == 0) {
            sum += d;
            long long other = n / d;
            if (other != d) sum += other;
        }
    }
    printf("%s\n", sum == n ? "YES" : "NO");
    return 0;
}
