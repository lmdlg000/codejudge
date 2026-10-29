# P9 区间规划器

> 难度：进阶 · 多文件 make 工程（恰好 4 个文件） · 构建：`make` → `planner` · 时限 2000ms / 256MB

## 题目背景

给定 n 个闭区间 [l, r] 与 q 个查询点 x，请在同一个程序里完成两件事：

1. 计算**最大两两不相交区间个数**（区间调度贪心：按右端点升序安排）。注意：**两区间共享端点即算相交**——[1,2] 与 [2,3] 不能同时选，[1,2] 与 [3,4] 可以同时选。
2. 对每个查询点 x，回答**有多少个区间包含 x**（l ≤ x ≤ r，端点算包含）。

n、q 最大 20 万，逐区间逐查询的 O(n·q) 扫描或 O(n²) 枚举都会超时，需要排序 + 二分把整体做到 O((n+q) log n) 量级。

本题考查：枚举与贪心（区间调度）、排序、二分检索、多文件工程组织（模块拆分 + makefile）。

## 输入格式

- 第 1 行两个整数 `n q`。
- 接下来 n 行，每行两个整数 `l r`，表示一个闭区间 [l, r]（0 ≤ l ≤ r ≤ 10^9）。
- 再接下来 q 行，每行一个整数 x（0 ≤ x ≤ 10^9）。

## 输出格式

- 第 1 行一个整数：最大两两不相交区间个数。
- 接下来 q 行，每行一个整数：第 j 行是第 j 个查询点 x_j 被多少个区间包含。

## 约束条件

- 1 ≤ n ≤ 200000，1 ≤ q ≤ 200000
- 0 ≤ l ≤ r ≤ 10^9，0 ≤ x ≤ 10^9
- 共享端点即算相交：[1,2] 与 [2,3] 不能同时选
- 包含判据：l ≤ x ≤ r（闭区间，端点值算包含）
- 时限 2000ms，内存 256MB；整体复杂度需 O((n+q) log n) 量级，O(n²) 必超时

## 提交要求（多文件 make 工程）

多文件提交**恰好包含这 4 个文件**（文件名固定）：

| 文件 | 内容 |
| --- | --- |
| `interval.h` / `interval.C` | 区间排序与贪心（最大不相交区间数）模块 |
| `query.h` / `query.C` | 二分查询（查询点被包含计数）模块 |
| `main.C` | 主程序：读入、调用两个模块、按格式输出 |
| `makefile` | 构建规则（见下） |

- **`.h` 只放声明 + 头文件保护宏**（`#ifndef/#define/#endif`），实现全部放 `.C`；
- 每个 `.C` **首行 `#include` 对应的 `.h`**（如 `interval.C` 首行 `#include "interval.h"`）；
- 允许使用 STL 容器与 `<algorithm>`（本题考算法组织而非裸字符处理）；
- `makefile` 要求：`TARGET = planner`、`all` 生成 `planner`、`clean` 删除 `.o` 与 `planner`、`CXX = g++`、`CXXFLAGS = -std=c++20 -O2 -w -Wall`、每个 `.o` 写清依赖的 `.h`、**配方行以 Tab 缩进**（不是空格）、**不写死绝对路径**。参考模板（`$(CXX)`、`rm` 行前是 Tab）：

```makefile
CXX = g++
CXXFLAGS = -std=c++20 -O2 -w -Wall
OBJ = main.o interval.o query.o
TARGET = planner

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(OBJ)

main.o: main.C interval.h query.h
	$(CXX) $(CXXFLAGS) -c main.C

interval.o: interval.C interval.h
	$(CXX) $(CXXFLAGS) -c interval.C

query.o: query.C query.h interval.h
	$(CXX) $(CXXFLAGS) -c query.C

clean:
	rm -f $(OBJ) $(TARGET)

.PHONY: all clean
```

变量名与 `.o` 列表可自行调整，但行为必须满足：`make` 生成 `planner`、`make clean` 清干净 `.o` 与可执行文件、每个 `.o` 依赖写全对应的 `.h`。

## 样例输入

```text
4 3
1 3
2 5
4 6
7 8
2
4
7
```

## 样例输出

```text
3
2
2
1
```

## 样例说明

4 个区间 [1,3]、[2,5]、[4,6]、[7,8]，3 个查询点 2、4、7：

- 最大不相交：选 [1,3]、[4,6]、[7,8] 共 **3** 个（[2,5] 与 [1,3] 相交，与 [4,6] 也相交，不能选）；
- x=2：被 [1,3]、[2,5] 包含 → **2**；
- x=4：被 [2,5]、[4,6] 包含 → **2**；
- x=7：被 [7,8] 包含 → **1**。
