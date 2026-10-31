# P11 工程排程

> 难度：综合 · 多文件 make 工程（恰好 6 个文件） · 构建：`make` → `scheduler` · 时限 2000ms / 256MB

## 题目背景

某工程项目包含 n 个任务，任务 i 的工期为 d_i 天。任务之间存在 m 条依赖关系：依赖 u → v 表示任务 u 必须完成后，任务 v 才能开始。工地有无限多台并行机器，任意任务在其全部前驱任务完成的那一刻即可立即开工，不受其他未完成任务影响。

项目管理者需要评估两件事：

1. 整个工程的最短完工时间（即最后一个任务完成的最早时刻）；
2. 一种字典序最小的合法任务执行顺序（拓扑序），用于排班公示。

若依赖关系成环（任务互相等待），则工程无法完成。

## 输入格式

第一行两个整数 n 和 m，表示任务数与依赖关系数。

第二行 n 个正整数 d_1 d_2 … d_n，表示每个任务的工期。

接下来 m 行，每行两个整数 u v（1 ≤ u, v ≤ n），表示一条依赖：任务 u 完成后任务 v 才能开始。

## 输出格式

若依赖成环，输出一行 `-1`。

否则输出两行：

- 第一行一个整数，表示最短完工时间；
- 第二行 n 个整数，表示字典序最小的合法拓扑序，编号之间用一个空格分隔，行末无多余空格。


## 提交要求（多文件 make 工程）

多文件提交**恰好包含这 6 个文件**（文件名固定）：

| 文件 | 内容 |
| --- | --- |
| `topo.h` / `topo.C` | 建图、入度计算、最小堆拓扑排序（就绪集每次取编号最小者）、环检测 |
| `critical.h` / `critical.C` | 关键路径动态规划，求最短完工时间（最长加权路径） |
| `main.C` | 主程序：读入数据、调用上述模块、按格式输出 |
| `makefile` | 构建规则（见下） |

- **`.h` 只放声明 + 头文件保护宏**（`#ifndef/#define/#endif`），实现全部放 `.C`；
- 每个 `.C` **首行 `#include` 对应的 `.h`**（如 `topo.C` 首行 `#include "topo.h"`）；
- 允许使用 STL 容器与 `<queue>`、`<algorithm>` 等（本题考算法组织而非裸字符处理）；
- `makefile` 要求：`TARGET = scheduler`、`all` 生成 `scheduler`、`clean` 删除 `.o` 与 `scheduler`、`CXX = g++`、`CXXFLAGS = -std=c++20 -O2 -w -Wall`、每个 `.o` 写清依赖的 `.h`、**配方行以 Tab 缩进**（不是空格）、**不写死绝对路径**。参考模板（`$(CXX)`、`rm` 行前是 Tab）：

```makefile
CXX = g++
CXXFLAGS = -std=c++20 -O2 -w -Wall
OBJ = main.o topo.o critical.o
TARGET = scheduler

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(OBJ)

main.o: main.C topo.h critical.h
	$(CXX) $(CXXFLAGS) -c main.C

topo.o: topo.C topo.h
	$(CXX) $(CXXFLAGS) -c topo.C

critical.o: critical.C critical.h topo.h
	$(CXX) $(CXXFLAGS) -c critical.C

clean:
	rm -f $(OBJ) $(TARGET)

.PHONY: all clean
```

变量名与 `.o` 列表可自行调整，但行为必须满足：`make` 生成 `scheduler`、`make clean` 清干净 `.o` 与可执行文件、每个 `.o` 依赖写全对应的 `.h`。

算法复杂度需达到 O((n + m) log n)。

## 样例输入
```text
4 3
3 2 4 1
1 2
1 3
3 4
```

## 样例输出
```text
8
1 2 3 4
```

## 样例说明

任务 1 无前驱，工期 3，在 [0, 3] 执行；任务 2 依赖 1，在 [3, 5] 执行；任务 3 依赖 1，在 [3, 7] 执行；任务 4 依赖 3，在 [7, 8] 执行。工程在时刻 8 完工，故最短完工时间为 8。

就绪集每次取编号最小者得到的拓扑序为 1 2 3 4，是字典序最小的合法拓扑序。

## 数据范围

- 1 ≤ n ≤ 100000
- 0 ≤ m ≤ 200000
- 1 ≤ d_i ≤ 10^9
- 允许图不连通；输入无重边；可能有环
- 时间限制 2000 ms，内存限制 256 MB
