#include <iostream>
#include <string>
#include <vector>
#include <cctype>

using namespace std;

// 去掉首尾空白字符（空格、\t、\r 等）
static string trim(const string& s) {
    size_t b = 0, e = s.size();
    while (b < e && isspace(static_cast<unsigned char>(s[b]))) ++b;
    while (e > b && isspace(static_cast<unsigned char>(s[e - 1]))) --e;
    return s.substr(b, e - b);
}

int main() {
    int n, s, m;
    if (!(cin >> n >> s >> m)) return 0;
    cin.ignore(1000000, '\n');

    vector<string> name(n);
    for (int i = 0; i < n; ++i) {
        string line;
        getline(cin, line);
        name[i] = trim(line);
    }

    // circle[k] = 当前圈中第 k 个位置对应的人（0 基下标）
    vector<int> circle(n);
    for (int i = 0; i < n; ++i) circle[i] = i;

    int cur = s - 1;      // 报数起点：当前位置报 1
    int remaining = n;
    while (remaining > 0) {
        int pos = (cur + m - 1) % remaining;   // 报到 m 的人
        cout << name[circle[pos]] << "\n";
        circle.erase(circle.begin() + pos);
        --remaining;
        if (remaining > 0) cur = pos % remaining;  // 出圈者下一个人重新从 1 报
    }
    return 0;
}
