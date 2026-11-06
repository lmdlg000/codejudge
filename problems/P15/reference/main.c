// P15 成绩单排版 —— 参考实现（gen 刷 .out 用）
// 全部输出靠 printf 的宽度/精度控制：%-8s 左对齐补空格、%4d 右对齐、%7.2f 保留两位、%% 输出一个百分号。
#include <stdio.h>

#define LINE_WIDTH 42

static void print_rule(void) {
    for (int i = 0; i < LINE_WIDTH; i++) putchar('-');
    putchar('\n');
}

int main() {
    int n;
    if (scanf("%d", &n) != 1) return 0;

    char id[16], name[16];
    int c1, c2, c3;
    int pass = 0;
    double total = 0.0;

    printf("%-8s %-10s %4s %4s %4s %7s\n", "ID", "NAME", "C1", "C2", "C3", "AVG");
    print_rule();

    for (int i = 0; i < n; i++) {
        if (scanf("%s %s %d %d %d", id, name, &c1, &c2, &c3) != 5) return 0;
        double avg = (c1 + c2 + c3) / 3.0;
        printf("%-8s %-10s %4d %4d %4d %7.2f\n", id, name, c1, c2, c3, avg);
        if (avg >= 60.0) pass++;
        total += avg;
    }

    print_rule();
    printf("PASS %d/%d (%.1f%%)\n", pass, n, pass * 100.0 / n);
    printf("CLASS AVG %.2f\n", total / n);
    return 0;
}
