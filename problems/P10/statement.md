# P10 最短路计数

> 难度：提高 · 多文件 make 工程（恰好 6 个文件） · 构建：`make` → `router` · 时限 2000ms / 256MB

## 题目背景

给定 n 个结点的有向带权图（结点编号 1..n，边权 w ≥ 0，**无重边、无自环**）。求从结点 1 到结点 n 的：

1. **最短路长度 D**；
2. **最短路的条数**（对 1000000007 取模）。

两条路径不同 ⟺ **边序列不同**（走过相同边序列视为同一条路径；允许经过重复结点，只要边序列不同就算不同路径）。题目保证最短路条数有限（即不存在全部位于最短路上的 0 权环）。

注意边权可以为 **0**：0 权边会制造大量**等长**的最短路，计数必须把它们全部算上，并按拓扑次序在最短路 DAG 上递推——同 dist 层内若不按拓扑序推进会漏算。

- 若 1 不可达 n：输出 `-1 0`；
- 若 n = 1：输出 `0 1`（起点即终点，长度为 0 的平凡路径恰 1 条）。

n、m 最大 10 万、20 万，O(n·m) 的 Bellman-Ford 式迭代或 O(n²) 的朴素 Dijkstra 必超时，需要堆优化 Dijkstra + 最短路 DAG 上的 DP，整体 O(m log n) 量级。

本题考查：图论（Dijkstra 最短路）、最短路 DAG 上的动态规划计数、0 权边边界处理、取模运算、多文件工程组织（模块拆分 + makefile）。

## 输入格式

- 第 1 行两个整数 `n m`。
- 接下来 m 行，每行三个整数 `u v w`，表示一条 u → v、边权为 w 的有向边（无重边、无自环）。

## 输出格式

- 一行两个整数 `D cnt`：D 是 1 到 n 的最短路长度，cnt 是最短路条数对 1000000007 取模的结果。
- 1 不可达 n 时输出 `-1 0`；n = 1 时输出 `0 1`。

## 约束条件

- 1 ≤ n ≤ 100000，0 ≤ m ≤ 200000
- 1 ≤ u, v ≤ n，u ≠ v；无重边、无自环
- 0 ≤ w ≤ 10^9
- 最短路条数对 **1000000007** 取模
- 保证不存在全部位于最短路上的 0 权环（最短路条数有限）
- 时限 2000ms，内存 256MB；整体复杂度需 O(m log n) 量级，O(n·m) 或 O(n²) 必超时

## 提交要求（多文件 make 工程）

多文件提交**恰好包含这 6 个文件**（文件名固定）：

| 文件 | 内容 |
| --- | --- |
| `graph.h` / `graph.C` | 建图 + Dijkstra 最短路模块 |
| `paths.h` / `paths.C` | 最短路 DAG 上 DP 计数模块 |
| `main.C` | 主程序：读入、调用两个模块、按格式输出 |
| `makefile` | 构建规则（见下） |

- **`.h` 只放声明 + 头文件保护宏**（`#ifndef/#define/#endif`），实现全部放 `.C`；
- 每个 `.C` **首行 `#include` 对应的 `.h`**（如 `graph.C` 首行 `#include "graph.h"`）；
- 允许使用 STL 容器与 `<queue>`、`<algorithm>` 等（本题考算法组织而非裸字符处理）；
- `makefile` 要求：`TARGET = router`、`all` 生成 `router`、`clean` 删除 `.o` 与 `router`、`CXX = g++`、`CXXFLAGS = -std=c++20 -O2 -w -Wall`、每个 `.o` 写清依赖的 `.h`、**配方行以 Tab 缩进**（不是空格）、**不写死绝对路径**。参考模板（`$(CXX)`、`rm` 行前是 Tab）：

```makefile
CXX = g++
CXXFLAGS = -std=c++20 -O2 -w -Wall
OBJ = main.o graph.o paths.o
TARGET = router

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(OBJ)

main.o: main.C graph.h paths.h
	$(CXX) $(CXXFLAGS) -c main.C

graph.o: graph.C graph.h
	$(CXX) $(CXXFLAGS) -c graph.C

paths.o: paths.C paths.h graph.h
	$(CXX) $(CXXFLAGS) -c paths.C

clean:
	rm -f $(OBJ) $(TARGET)

.PHONY: all clean
```

变量名与 `.o` 列表可自行调整，但行为必须满足：`make` 生成 `router`、`make clean` 清干净 `.o` 与可执行文件、每个 `.o` 依赖写全对应的 `.h`。

## 样例输入

```text
4 5
1 2 2
2 4 2
1 3 1
3 4 3
1 4 10
```

## 样例输出

```text
4 2
```

## 样例说明

4 个结点 5 条边：

- 1→2→4 长度 2+2 = **4**；
- 1→3→4 长度 1+3 = **4**；
- 1→4 直达长度 10。

最短路长度 **D = 4**，等长最短路共 **2** 条（边序列分别为 (1→2, 2→4) 与 (1→3, 3→4)），故输出 `4 2`。
