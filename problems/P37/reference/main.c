// P37 螺旋方阵 —— 情境拓展（趣味数学 8.x 数形结合·螺旋填数）
// 输入 n(1<=n<=20)，把 1..n*n 按顺时针螺旋填入 n 阶方阵（从左上角向右开始），
// 逐行输出，元素间一个空格。
#include <stdio.h>
int main(void) {
    int n;
    if (scanf("%d", &n) != 1) return 0;
    int a[20][20] = {0};
    int top = 0, bottom = n - 1, left = 0, right = n - 1, v = 1;
    while (top <= bottom && left <= right) {
        for (int j = left; j <= right; ++j) a[top][j] = v++;
        ++top;
        for (int i = top; i <= bottom; ++i) a[i][right] = v++;
        --right;
        if (top <= bottom) { for (int j = right; j >= left; --j) a[bottom][j] = v++; --bottom; }
        if (left <= right) { for (int i = bottom; i >= top; --i) a[i][left] = v++; ++left; }
    }
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            if (j) putchar(' ');
            printf("%d", a[i][j]);
        }
        putchar('\n');
    }
    return 0;
}
