// P21 字符查找 —— 参考实现（改编自 C 题库 2015 编程题 strfind）
// 输入一行字符串 s 与一个字符 c，输出 c 在 s 中第一次出现的位置（从 1 开始）；
// 若未出现输出 0。
#include <stdio.h>
#include <string.h>
int main(void) {
    char s[256];
    char c;
    if (!fgets(s, sizeof s, stdin)) return 0;
    size_t n = strlen(s);
    if (n > 0 && s[n-1] == '\n') s[n-1] = '\0';
    c = (char)getchar();
    for (int i = 0; s[i]; ++i)
        if (s[i] == c) { printf("%d\n", i + 1); return 0; }
    printf("0\n");
    return 0;
}
