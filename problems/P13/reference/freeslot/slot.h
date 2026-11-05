// P13 共同空闲 —— slot.h：区间类型与日程类的声明
// 头文件只放声明；实现放在 slot.cpp（类的声明与实现分离，是本题的考点之一）。
#ifndef SLOT_H
#define SLOT_H

#include <vector>

// 闭区间 [l, r]，单位是"分钟"，两端都算被占用。
struct Slot {
    long long l;
    long long r;
};

// 某人一天的日程：busy_ 里是原始占用段，normalize() 之后才有序且互不相交。
class DayPlan {
public:
    DayPlan();

    void add(long long l, long long r);
    void normalize();
    std::vector<Slot> freeWithin(long long day) const;

    static std::vector<Slot> intersect(const std::vector<Slot>& a,
                                       const std::vector<Slot>& b);

private:
    std::vector<Slot> busy_;
};

#endif  // SLOT_H
