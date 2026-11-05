// P13 共同空闲 —— slot.cpp：归并 / 求补（空闲段）/ 双指针求交
#include "slot.h"

#include <algorithm>

DayPlan::DayPlan() {}

void DayPlan::add(long long l, long long r) { busy_.push_back(Slot{l, r}); }

// 按左端点排序后一次扫描：能接上（下一段左端点 ≤ 当前右端点，含共享端点）就延长，
// 否则另起一段。被包含的段只会让当前右端点保持不动。
void DayPlan::normalize() {
    std::sort(busy_.begin(), busy_.end(),
              [](const Slot& x, const Slot& y) {
                  if (x.l != y.l) return x.l < y.l;
                  return x.r < y.r;
              });
    std::vector<Slot> merged;
    for (const Slot& s : busy_) {
        if (!merged.empty() && s.l <= merged.back().r) {
            if (s.r > merged.back().r) merged.back().r = s.r;
        } else {
            merged.push_back(s);
        }
    }
    busy_.swap(merged);
}

// 把 [0, day] 里没被占用的整数分钟整理成闭区间：占用到 r 之后，空闲从 r+1 开始。
std::vector<Slot> DayPlan::freeWithin(long long day) const {
    std::vector<Slot> free_slots;
    long long cursor = 0;
    for (const Slot& s : busy_) {
        if (s.l > cursor) free_slots.push_back(Slot{cursor, s.l - 1});
        if (s.r + 1 > cursor) cursor = s.r + 1;
    }
    if (cursor <= day) free_slots.push_back(Slot{cursor, day});
    return free_slots;
}

// 两组有序、互不相交的区间求交：谁的右端点更小就谁先走一步。
std::vector<Slot> DayPlan::intersect(const std::vector<Slot>& a,
                                    const std::vector<Slot>& b) {
    std::vector<Slot> out;
    std::size_t i = 0, j = 0;
    while (i < a.size() && j < b.size()) {
        long long l = std::max(a[i].l, b[j].l);
        long long r = std::min(a[i].r, b[j].r);
        if (l <= r) out.push_back(Slot{l, r});
        if (a[i].r < b[j].r) ++i;
        else ++j;
    }
    return out;
}
