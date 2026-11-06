// P16 机柜状态 —— 参考实现（gen 刷 .out 用）
// 位运算：置 1 用 |、清 0 用 &= ~、翻转用 ^=、交换高低 16 位用 (x<<16)|(x>>16)。
// 统计：所有修改做完后再算一遍"每柜亮灯数"的前缀和，查询 O(1)。
#include <stdio.h>

#define MAXN 200005

static unsigned int state[MAXN];
static long long prefix[MAXN];

// 二进制里 1 的个数（Brian Kernighan 法：每轮清掉最低位的 1）
static int popcount32(unsigned int x) {
    int c = 0;
    while (x) {
        x &= x - 1u;
        ++c;
    }
    return c;
}

int main() {
    int n, m, q;
    while (scanf("%d %d %d", &n, &m, &q) == 3) {
        for (int i = 1; i <= n; i++) scanf("%x", &state[i]);

        for (int k = 0; k < m; k++) {
            char op[4];
            int idx, bit;
            scanf("%s", op);
            if (op[0] == 'W') {
                scanf("%d", &idx);
                state[idx] = (state[idx] << 16) | (state[idx] >> 16);
            } else {
                scanf("%d %d", &idx, &bit);
                if (op[0] == 'S') state[idx] |= (1u << bit);
                else if (op[0] == 'C') state[idx] &= ~(1u << bit);
                else state[idx] ^= (1u << bit);
            }
        }

        prefix[0] = 0;
        for (int i = 1; i <= n; i++) prefix[i] = prefix[i - 1] + popcount32(state[i]);

        for (int k = 0; k < q; k++) {
            int l, r;
            scanf("%d %d", &l, &r);
            printf("%lld\n", prefix[r] - prefix[l - 1]);
        }
    }
    return 0;
}
