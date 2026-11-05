// P13 共同空闲 —— main.cpp：只负责输入解析与输出格式，区间运算全部交给 DayPlan
#include <iostream>
#include <string>
#include <vector>

#include "slot.h"

using namespace std;

// 去掉行尾的 \r 与空白：题目用整行读入，Windows 换行不能把 "-" 判成非空
static string trimTail(const string& s) {
    size_t end = s.size();
    while (end > 0 && (s[end - 1] == '\r' || s[end - 1] == ' ' || s[end - 1] == '\t')) --end;
    return s.substr(0, end);
}

// 把 "1-3,5-6" 这样的一行喂给日程；"-" 表示整天没有占用
static void feed(DayPlan& plan, const string& raw) {
    string line = trimTail(raw);
    if (line.empty() || line == "-") return;
    size_t start = 0;
    while (true) {
        size_t comma = line.find(',', start);
        string tok = (comma == string::npos) ? line.substr(start)
                                             : line.substr(start, comma - start);
        if (!tok.empty()) {
            size_t dash = tok.find('-');
            long long l = stoll(tok.substr(0, dash));
            long long r = stoll(tok.substr(dash + 1));
            plan.add(l, r);
        }
        if (comma == string::npos) break;
        start = comma + 1;
    }
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long day;
    if (!(cin >> day)) return 0;

    string line_a, line_b, junk;
    getline(cin, junk);  // 吃掉第一行剩下的换行
    getline(cin, line_a);
    getline(cin, line_b);

    DayPlan a, b;
    feed(a, line_a);
    feed(b, line_b);
    a.normalize();
    b.normalize();

    const vector<Slot> free_a = a.freeWithin(day);
    const vector<Slot> free_b = b.freeWithin(day);
    const vector<Slot> common = DayPlan::intersect(free_a, free_b);

    if (common.empty()) {
        cout << "NULL\n";
        return 0;
    }
    for (size_t i = 0; i < common.size(); ++i) {
        if (i) cout << ", ";
        cout << common[i].l << '-' << common[i].r;
    }
    cout << '\n';
    return 0;
}
