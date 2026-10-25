# scripts/gen_test_inputs.py —— 生成 problems/P*/tests/*.in（样例 + 隐藏 + 加权压力）
# 一次性维护脚本：.in 落盘后由 `python judge.py gen` 用参考实现刷 .out
# 样例 .in 与题面（content-plan §3）逐字一致；隐藏小用例预期值写在注释里供人工核对
from __future__ import annotations

import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "problems"


def write(pid: str, name: str, content: str) -> None:
    p = TESTS / pid / "tests" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    if not content.endswith("\n"):
        content += "\n"
    p.write_text(content, encoding="utf-8")
    print(f"写入 {p.relative_to(ROOT)} ({len(content)} bytes)")


# ---------- P1 运费计算 ----------
# 样例 5 组（题面逐字）；hidden-1 期望 15；hidden-2 期望 18；hidden-3 期望 616
write("P1", "1.in", "800 300")
write("P1", "2.in", "1000 500")
write("P1", "3.in", "1500 800")
write("P1", "4.in", "2300 1200")
write("P1", "5.in", "5000 1000")
write("P1", "hidden-1.in", "1000 501")
write("P1", "hidden-2.in", "1001 1000")
write("P1", "hidden-3.in", "100000 3000")

# ---------- P2 字符串压缩 ----------
# hidden-1 期望 a1b1；hidden-2 期望 a100000（|s|=1e5 边界）
write("P2", "1.in", "aaabbc")
write("P2", "2.in", "a")
write("P2", "3.in", "zzzzzzzzzz")
write("P2", "4.in", "abcabc")
write("P2", "5.in", "aabbaa")
write("P2", "hidden-1.in", "ab")
write("P2", "hidden-2.in", "a" * 100000)

# ---------- P3 活动安排 ----------
# hidden-1 期望 3（贪心按结束时间）；hidden-2 为 n=1e6 加权压力（weight=2）
write("P3", "1.in", "3\n1 3\n2 5\n4 7")
write("P3", "2.in", "1\n5 10")
write("P3", "3.in", "4\n1 2\n2 3\n3 4\n1 4")
write("P3", "4.in", "5\n1 10\n2 3\n3 4\n4 5\n5 6")
write("P3", "5.in", "4\n1 5\n2 6\n3 7\n4 8")
write("P3", "hidden-1.in", "6\n1 4\n2 3\n3 6\n4 5\n5 8\n6 7")

rng = random.Random(20250101)
n = 1_000_000
lines = [str(n)]
for _ in range(n):
    s = rng.randrange(0, 500_000_000)
    t = s + 1 + rng.randrange(0, 1000)
    lines.append(f"{s} {t}")
write("P3", "hidden-2.in", "\n".join(lines))

# ---------- P4 日期推算 ----------
# hidden-1 期望 1900-01-01；hidden-2 期望 2000-02-29（%400 闰年）；hidden-3 期望 4737-07-14（脚本后核对）
write("P4", "1.in", "2025-01-01 0")
write("P4", "2.in", "2025-01-01 31")
write("P4", "3.in", "2024-02-28 1")
write("P4", "4.in", "2025-12-31 1")
write("P4", "5.in", "2024-01-01 365")
write("P4", "hidden-1.in", "1900-01-01 0")
write("P4", "hidden-2.in", "2000-02-28 1")
write("P4", "hidden-3.in", "2100-12-31 1000000")

# ---------- P5 最短路径 ----------
# hidden-1 期望 7（重边取最小 + 自环无影响）；hidden-2 为 n=1e5/m=2e5 加权压力（weight=2）
write("P5", "1.in", "4 4\n1 2 1\n2 3 2\n1 3 5\n3 4 1")
write("P5", "2.in", "2 0")
write("P5", "3.in", "3 2\n1 2 3\n2 3 4")
write("P5", "4.in", "4 3\n1 2 10\n1 3 1\n3 4 1")
write("P5", "5.in", "5 5\n1 2 2\n1 3 5\n2 3 1\n2 4 7\n4 5 2")
write("P5", "hidden-1.in", "3 4\n1 1 5\n1 2 9\n1 2 3\n2 3 4")

rng = random.Random(20250102)
n, m = 100_000, 200_000
lines = [f"{n} {m}"]
# 先铺一条 1→n 的链保证可达，再补随机边
for i in range(1, n):
    lines.append(f"{i} {i + 1} {1 + rng.randrange(0, 1000)}")
for _ in range(m - (n - 1)):
    u = rng.randrange(1, n + 1)
    v = rng.randrange(1, n + 1)
    w = rng.randrange(1, 1_000_001)
    lines.append(f"{u} {v} {w}")
write("P5", "hidden-2.in", "\n".join(lines))

# ---------- P6 依赖检查器 ----------
# hidden-1 期望 OK / 1 2 4 3（字典序陷阱：1、2 无依赖，4 先于 3）；hidden-2 期望 CYCLE
# hidden-3 为 n=1e5/m=2e5 加权压力（weight=2，DAG：y < x）
write("P6", "1.in", "3 2\n1 2\n1 3")
write("P6", "2.in", "2 2\n1 2\n2 1")
write("P6", "3.in", "1 0")
write("P6", "4.in", "4 3\n2 1\n3 2\n4 1")
write("P6", "5.in", "5 4\n5 4\n4 3\n3 2\n2 1")
write("P6", "hidden-1.in", "4 3\n4 1\n4 2\n3 4")
write("P6", "hidden-2.in", "5 5\n1 2\n2 3\n3 1\n4 5\n5 4")

rng = random.Random(20250103)
n, m = 100_000, 200_000
lines = [f"{n} {m}"]
for _ in range(m):
    y = rng.randrange(1, n)          # y < x → 边 y→x 前向，保证无环
    x = rng.randrange(y + 1, n + 1)
    lines.append(f"{x} {y}")
write("P6", "hidden-3.in", "\n".join(lines))

print("全部 .in 已生成。下一步：python judge.py gen <pid> --ref reference/<pid>.cpp 刷 .out")
