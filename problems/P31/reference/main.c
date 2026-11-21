// P31 卡普雷卡尔操作 —— 情境拓展（趣味数学 3.9.1 卡普雷卡尔方式）
// 输入一个 4 位、各位不全相同的正整数 n，反复：把 4 位数字降序排成最大数、升序排成最小数，
// 大数减小数，直到得到 6174。输出进行的操作次数。
#include <stdio.h>
#include <stdlib.h>
static int cmp_int(const void *a, const void *b) {
    int x = *(const int*)a, y = *(const int*)b;
    return (x > y) - (x < y);
}
int main(void) {
    int n;
    if (scanf("%d", &n) != 1) return 0;
    int steps = 0;
    while (n != 6174) {
        int d[4];
        for (int i = 0; i < 4; ++i) { d[i] = n % 10; n /= 10; }
        qsort(d, 4, sizeof(int), cmp_int);
        int desc = 0, asc = 0;
        for (int i = 3; i >= 0; --i) desc = desc * 10 + d[i];
        for (int i = 0; i < 4; ++i) asc = asc * 10 + d[i];
        n = desc - asc;
        ++steps;
    }
    printf("%d\n", steps);
    return 0;
}
