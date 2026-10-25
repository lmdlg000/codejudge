// examples/P1_tle.cpp —— 预期判定：TLE（死循环，超时被终止）
#include <bits/stdc++.h>
using namespace std;

int main() {
    long long w, d;
    cin >> w >> d;
    volatile long long sink = 0;
    while (true) sink += 1;   // 死循环：墙钟超时被强制终止
    return 0;
}
