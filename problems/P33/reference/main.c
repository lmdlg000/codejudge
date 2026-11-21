// P35 韩信点兵 —— 情境拓展（趣味数学 4.1 韩信点兵）
// 已知某数除以 3 余 a、除以 5 余 b、除以 7 余 c，求满足条件的最小正整数。
// 输入 a b c（0<=a<3, 0<=b<5, 0<=c<7），输出最小正整数解（1..105）。
#include <stdio.h>
int main(void) {
    int a, b, c;
    if (scanf("%d %d %d", &a, &b, &c) != 3) return 0;
    for (int x = 1; x <= 105; ++x) {
        if (x % 3 == a && x % 5 == b && x % 7 == c) {
            printf("%d\n", x);
            return 0;
        }
    }
    printf("0\n");
    return 0;
}
