// P25 日期比较 —— 参考实现（改编自 C 题库 2022 秋程序设计题 dateComp）
// 输入两个日期（年 月 日），日期1早于日期2输出 1，相等输出 0，否则输出 -1。
#include <stdio.h>
int dateComp(int y1, int m1, int d1, int y2, int m2, int d2) {
    if (y1 != y2) return y1 < y2 ? 1 : -1;
    if (m1 != m2) return m1 < m2 ? 1 : -1;
    if (d1 != d2) return d1 < d2 ? 1 : -1;
    return 0;
}
int main(void) {
    int y1, m1, d1, y2, m2, d2;
    if (scanf("%d %d %d", &y1, &m1, &d1) != 3) return 0;
    scanf("%d %d %d", &y2, &m2, &d2);
    printf("%d\n", dateComp(y1, m1, d1, y2, m2, d2));
    return 0;
}
