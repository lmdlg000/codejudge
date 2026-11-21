// P32 猴子分桃 —— 情境拓展（趣味数学 4.8.1）
// n 只猴子依次分一堆桃子：每只来了都把当前桃子平均分成 n 份，多出 1 个，扔掉后拿走自己那份；
// n 只都这样做完后，剩下的桃子恰好能被 n 整除。求桃子总数最少是多少。
// 输入 n（2<=n<=9），输出最小正整数解。
#include <stdio.h>
int main(void) {
    int n;
    if (scanf("%d", &n) != 1) return 0;
    if (n <= 1) { printf("1\n"); return 0; }
    // 从「最后剩下的桃子」反推：它是 n 的倍数 n*k；每只猴子前一步 = 余数/(n-1)*n + 1
    for (long long k = 1; ; ++k) {
        long long x = n * k;
        int ok = 1;
        for (int i = 0; i < n; ++i) {
            if (x % (n - 1) != 0) { ok = 0; break; }
            x = x / (n - 1) * n + 1;
        }
        if (ok) { printf("%lld\n", x); return 0; }
    }
    return 0;
}
