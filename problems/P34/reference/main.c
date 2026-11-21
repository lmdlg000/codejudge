// P34 百钱百鸡 —— 情境拓展（趣味数学 4.2.1 百钱百鸡问题）
// 公鸡每只 5 钱、母鸡每只 3 钱、小鸡三只 1 钱。
// 输入总钱数 m 与总只数 n，输出所有购买方案（公鸡x、母鸡y、小鸡z），
// 第一行方案数，之后每行 x y z，按 x 从小到大、x 相同按 y 从小到大排列。
#include <stdio.h>
int main(void) {
    int m, n;
    if (scanf("%d %d", &m, &n) != 2) return 0;
    int sol[1000][3], cnt = 0;
    for (int x = 0; x <= n && x * 5 <= m; ++x) {
        for (int y = 0; x + y <= n && x * 5 + y * 3 <= m; ++y) {
            int z = n - x - y;
            if (z % 3 != 0) continue;
            if (x * 5 + y * 3 + z / 3 == m) {
                sol[cnt][0] = x; sol[cnt][1] = y; sol[cnt][2] = z;
                ++cnt;
            }
        }
    }
    printf("%d\n", cnt);
    for (int i = 0; i < cnt; ++i)
        printf("%d %d %d\n", sol[i][0], sol[i][1], sol[i][2]);
    return 0;
}
