// P14 密文算式 —— 参考实现（gen 刷 .out 用）
// 三步：逐字符解密（字母 52 表 / 数字 10 表，位置 i 按整行字符计）→ 按 B 进制解释操作数
//       → 从右往左扫 token，遇到运算符取两个数算完放回，输出 6 位小数。
#include <bits/stdc++.h>
using namespace std;

static int num(char c) {
    if (c >= 'a' && c <= 'z') return c - 'a';
    return c - 'A' + 26;
}

static char letter(int v) { return v < 26 ? char('a' + v) : char('A' + v - 26); }

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    if (!(cin >> T)) return 0;

    while (T--) {
        int base;
        string key;
        cin >> base >> key;

        string cipher, junk;
        getline(cin, junk);   // 吃掉第一行剩下的换行
        getline(cin, cipher);

        const int L = (int)key.size();
        string plain;
        plain.reserve(cipher.size());
        for (size_t i = 0; i < cipher.size(); i++) {
            char c = cipher[i];
            int shift = num(key[i % L]);
            if (c >= 'a' && c <= 'z') {
                plain += letter((num(c) - shift + 52) % 52);
            } else if (c >= 'A' && c <= 'Z') {
                plain += letter((num(c) - shift + 52) % 52);
            } else if (c >= '0' && c <= '9') {
                int s10 = shift % 10;
                plain += char('0' + (c - '0' - s10 + 10) % 10);
            } else {
                plain += c;   // 空格、负号原样保留
            }
        }

        vector<string> token;
        {
            istringstream in(plain);
            string w;
            while (in >> w) token.push_back(w);
        }

        vector<double> st;
        for (int i = (int)token.size() - 1; i >= 0; i--) {
            const string& s = token[i];
            if (s.size() == 1 && (s[0] == 'A' || s[0] == 'S' || s[0] == 'M' || s[0] == 'D')) {
                double left = st.back(); st.pop_back();    // 先取到的是左操作数
                double right = st.back(); st.pop_back();
                double r = 0.0;
                if (s[0] == 'A') r = left + right;
                else if (s[0] == 'S') r = left - right;
                else if (s[0] == 'M') r = left * right;
                else r = left / right;
                st.push_back(r);
            } else {
                bool neg = false;
                size_t p = 0;
                if (s[0] == '-') { neg = true; p = 1; }
                long long v = 0;
                for (; p < s.size(); p++) v = v * base + (s[p] - '0');
                st.push_back(neg ? -double(v) : double(v));
            }
        }

        cout << fixed << setprecision(6) << st.back() << "\n";
    }
    return 0;
}
