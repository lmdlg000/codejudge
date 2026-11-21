// P30 勾股数计数 —— 情境拓展（趣味数学 1.4.1）
// 输入 n（1<=n<=500），统计满足 1<=a<b<c<=n 且 a*a+b*b==c*c 的整数三元组个数。
#include <stdio.h>
int main(void) {
    int n;
    if (scanf("%d", &n) != 1) return 0;
    int cnt = 0;
    for (int a = 1; a <= n; ++a) {
        for (int b = a + 1; b <= n; ++b) {
            long long s = (long long)a*a + (long long)b*b;
            long long c = 1;
            while (c * c < s) ++c;
            if (c * c == s && c <= n) ++cnt;
        }
    }
    printf("%d\n", cnt);
    return 0;
}
