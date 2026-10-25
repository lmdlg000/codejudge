// P2 字符串压缩 —— 参考实现（gen 刷 .out 用）
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string s;
    cin >> s;
    string out;
    out.reserve(s.size() * 2);
    for (size_t i = 0; i < s.size();) {
        size_t j = i;
        while (j < s.size() && s[j] == s[i]) ++j;
        out += s[i];
        out += to_string(j - i);
        i = j;
    }
    cout << out << "\n";
    return 0;
}
