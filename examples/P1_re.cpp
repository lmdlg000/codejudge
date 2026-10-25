// examples/P1_re.cpp —— 预期判定：RE（写空指针 → 进程异常退出）
// Windows 下信号翻译降级为「进程非 0 退出码」文案
#include <bits/stdc++.h>
using namespace std;

int main() {
    long long w, d;
    cin >> w >> d;
    volatile int *p = nullptr;
    *p = 1;   // 写空地址：段错误 / 访问违例
    return 0;
}
