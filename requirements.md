\# 在线评测系统（Online Judge）构建方案



\## 一、总体思路



```

提交源码 ──► builder（编译/构建） ──► runner（限时执行） ──► comparator（比对）──► scorer（计分）

&#x20;  │              │                        │                       │                  │

&#x20;  │              ▼                        ▼                       ▼                  ▼

&#x20;  │           CE（附编译器输出）      TLE / RE（信号翻译）    AC / PE / WA          per-case 结果

&#x20;  │                                                                                │

&#x20;  └──────────────► reporter：控制台表格 + reports/\*.json ◄────────────────────────┘

```



\*\*设计原则\*\*



1\. \*\*数据即配置\*\*：题目目录 → `problem.json` + `tests/\*.in|out`；单用例可选 `\*.json` 覆盖权重/时限。

2\. \*\*判定顺序固定\*\*：先 CE（构建失败则所有用例标 CE 并跳过）→ 再逐用例 TLE → RE → 比对（AC/PE/WA）。

3\. \*\*判题与计分解耦\*\*：ACM 与 OI 复用同一套逐用例结果，仅在 `scorer` 中合成最终判定与得分。

4\. \*\*三种入口等价\*\*：手放 `.in/.out`、`gen` 生成、`import-samples` 抽取，最终都落到 `problems/<id>/tests/`。

5\. \*\*跨平台降级\*\*：Linux/macOS 用 `resource.setrlimit` + `Popen.kill`；Windows 走超时 + `taskkill`，信号翻译降级为「进程非 0 退出码」。



\---



\## 二、项目结构



```

online-judge/

├── judge.py                      # CLI 入口（子命令：run / gen / import-samples / list / init）

├── config.toml                   # 全局默认（时限、内存、计分模式、报告目录）

├── core/

│   ├── \_\_init\_\_.py

│   ├── problem.py                # 题目加载 + 用例发现 + 单用例 json 覆盖

│   ├── builder.py                # 编译/构建（g++ / make）

│   ├── runner.py                 # 限时执行（stdin 注入、超时终止、资源限制）

│   ├── verdict.py                # Verdict 枚举 + 信号翻译表

│   ├── comparator.py             # 逐字符 + token 比对（AC/PE/WA + 首处差异行号）

│   ├── scorer.py                 # 汇总（ACM / OI）、权重折算、通过率

│   ├── reporter.py               # 控制台表格 + JSON 报告（latest.json 软链）

│   ├── generator.py              # gen：编译参考实现 → 重跑 .in 刷新 .out

│   └── importer.py               # import-samples：解析题面 markdown 提取样例

├── problems/

│   ├── P1/

│   │   ├── problem.json          # 元信息 + 构建方式 + 计分模式

│   │   ├── statement.md          # 题面（Markdown）

│   │   ├── reference/P1.cpp      # 参考实现（gen 用）

│   │   └── tests/

│   │       ├── 1.in  / 1.out

│   │       ├── 2.in  / 2.out

│   │       ├── 3.in  / 3.out  / 3.json      # {"weight":2,"time\_ms":1500,"note":"边界"}

│   │       └── hidden-1.in / hidden-1.out / hidden-1.json  # 加权隐藏用例

│   ├── P2/ … P5/

│   └── P6/                                  # make 多文件构建

│       ├── problem.json

│       ├── statement.md

│       └── tests/…

├── exercise/                     # 题面 Markdown（import-samples 的输入源）

│   ├── P1-shipping.md … P6-inspector.md

├── examples/                     # 判定路径演示提交

│   ├── P1\_ac.cpp  P1\_wa.cpp  P1\_ce.cpp

│   ├── P1\_tle.cpp P1\_re.cpp  P1\_pe.cpp

│   └── P1\_make/                  # make 构建链路 + 多文件

│       ├── Makefile

│       ├── inspector.cpp

│       └── util.h

├── reports/                      # 运行时生成

│   ├── 20250101-120000-P1.json

│   └── latest.json

└── README.md

```



\---



\## 三、核心模块



\### 1. `verdict.py` —— 判定 + 信号翻译



```python

from enum import Enum

class Verdict(str, Enum):

&#x20;   AC, PE, WA, TLE, RE, CE, SE = "AC","PE","WA","TLE","RE","CE","SE"



SIGNAL\_MSG = {

&#x20;   "SIGSEGV": "段错误（SIGSEGV）：非法内存访问——常见于空指针解引用或数组越界",

&#x20;   "SIGFPE" : "算术异常（SIGFPE）：除零或整数溢出",

&#x20;   "SIGABRT": "程序中止（SIGABRT）：assert 失败或显式 abort()",

&#x20;   "SIGBUS" : "总线错误（SIGBUS）：地址未对齐 / 非法映射",

&#x20;   "SIGKILL": "被强制终止（SIGKILL）：疑似内存超限或被系统回收",

&#x20;   "SIGXCPU": "CPU 时间超限（SIGXCPU）",

}

def translate\_signal(sig: int) -> str: ...

```



\### 2. `problem.py` —— 题目加载 + 用例发现



```python

@dataclass

class TestCase:

&#x20;   name: str; input\_path: Path; output\_path: Path

&#x20;   weight: float = 1.0

&#x20;   time\_limit\_ms: int | None = None

&#x20;   note: str = ""



@dataclass

class Problem:

&#x20;   id: str; root: Path; title: str

&#x20;   contest\_type: str               # "acm" | "oi"

&#x20;   build: dict                     # {"command":..., "src":..., "target":..., "output":...}

&#x20;   default\_time\_ms: int = 1000

&#x20;   default\_memory\_mb: int = 256

&#x20;   tests: list\[TestCase]



&#x20;   @classmethod

&#x20;   def load(cls, pid, problems\_dir): ...

```



\*\*用例发现规则\*\*：扫描 `tests/\*.in`，按同名找 `.out`；`<stem>.json` 若有则覆盖 `weight` / `time\_limit\_ms` / `note`。缺 `.out` 直接拒绝并给出清晰错误。



\### 3. `builder.py` —— 编译 / 构建



\- `g++` 模板：`g++ -O2 -std=c++17 -o {bin} {src}`（`{src}` 可为 `main.cpp` 或一组文件）。

\- `make` 模式：`{"command":"make", "target":"inspector", "output":"inspector"}`，执行 `make <target>`，产物 `<workdir>/<output>`。

\- 捕获 stdout+stderr 作为 CE 提示（末尾 200 行 + 首个 error 行高亮）。

\- 构建超时（默认 60s）判 CE。



\### 4. `runner.py` —— 限时执行



```python

@dataclass

class RunResult:

&#x20;   exit\_code: int; signal: int | None

&#x20;   time\_ms: float; timed\_out: bool

&#x20;   stdout: bytes; stderr: bytes; peak\_rss\_kb: int | None



def run(binary, input\_data, time\_ms, mem\_mb) -> RunResult:

&#x20;   # POSIX：preexec\_fn 中 setrlimit(RLIMIT\_CPU, RLIMIT\_AS, RLIMIT\_FSIZE)

&#x20;   # Popen(..., stdin=PIPE, stdout=PIPE, stderr=PIPE)

&#x20;   # communicate(input, timeout=time\_ms/1000)；TimeoutExpired → kill(SIGKILL)

&#x20;   # 时钟：time.perf\_counter() 墙钟；Linux 下用 resource.getrusage 取 CPU 时间

```



\- \*\*墙钟超时\*\*与 \*\*CPU 时间\*\*双阈：墙钟默认 = 时限 × 1.5，防止 IO 卡顿。

\- \*\*stderr 截断\*\*：只保留末尾 2KB，避免无限输出淹没报告。



\### 5. `comparator.py` —— 输出比对



```python

def compare(actual: str, expected: str) -> tuple\[Verdict, str]:

&#x20;   if actual == expected:                       # 逐字符（含行尾）一致

&#x20;       return Verdict.AC, ""

&#x20;   a\_tokens, e\_tokens = actual.split(), expected.split()

&#x20;   if a\_tokens == e\_tokens:                     # 只有空白差异

&#x20;       return Verdict.PE, "仅空白差异（PE）：内容相同但换行/空格不一致"

&#x20;   a\_lines = actual.rstrip("\\n").split("\\n")

&#x20;   e\_lines = expected.rstrip("\\n").split("\\n")

&#x20;   for i, (a, e) in enumerate(zip(a\_lines, e\_lines), 1):

&#x20;       if a != e:

&#x20;           return Verdict.WA, f"第 {i} 行不一致：期望 {e!r}，实际 {a!r}"

&#x20;   if len(a\_lines) != len(e\_lines):

&#x20;       return Verdict.WA, f"行数不一致：期望 {len(e\_lines)} 行，实际 {len(a\_lines)} 行"

```



> 约定：忽略行尾 `\\r\\n` 与末尾多余空行的处理由 `problem.json` 里的 `"compare\_mode": "exact|trim"` 控制，默认为 `trim`（末尾多余换行视为无害）。



\### 6. `scorer.py` —— 汇总与计分



| 模式 | 逐用例计分 | 最终判定 | 得分 |

|---|---|---|---|

| `oi` | 通过则得权重分 | 显示总通过率 | `Σ 通过权重 / Σ 总权重 × 满分` |

| `acm` | 同上（仅统计） | 全 AC → `Accepted`，否则首个非 AC 判定 | 全 AC 得 `满分`，否则 `0`（同时展示部分得分供参考） |



`通过 4/4 · 通过率 100% · 得分 100/100` 是通用横幅格式，两种模式都输出。



\### 7. `reporter.py` —— 输出



\*\*控制台表格\*\*



```

┌──────┬──────┬───────┬──────┬──────────────────────────────────────┐

│ 用例 │ 判定 │ 耗时  │ 权重 │ 提示                                 │

├──────┼──────┼───────┼──────┼──────────────────────────────────────┤

│ 1.in │ AC   │  12ms │ 25   │                                      │

│ 2.in │ WA   │  15ms │ 25   │ 第 3 行不一致：期望 '42'，实际 '41'  │

│ 3.in │ TLE  │ 1000ms│ 25   │ 超时（限时 1000ms）                  │

│ 4.in │ RE   │   8ms │ 25   │ SIGSEGV 段错误（空指针/越界）        │

└──────┴──────┴───────┴──────┴──────────────────────────────────────┘

通过 1/4 · 通过率 25% · 得分 25/100

```



\*\*JSON 报告\*\*（`reports/<ts>-<pid>.json` 与 `latest.json`）



```json

{

&#x20; "problem\_id": "P1", "contest\_type": "oi",

&#x20; "submission": "examples/P1\_wa.cpp",

&#x20; "started\_at": "2025-01-01T12:00:00",

&#x20; "summary": {"total": 4, "passed": 1, "pass\_rate": 0.25, "score": 25, "max\_score": 100},

&#x20; "cases": \[

&#x20;   {"name":"1.in","verdict":"AC","time\_ms":12,"exit\_code":0,"weight":25,"message":""},

&#x20;   {"name":"2.in","verdict":"WA","time\_ms":15,"exit\_code":0,"weight":25,

&#x20;    "message":"第 3 行不一致：期望 '42'，实际 '41'"},

&#x20;   {"name":"3.in","verdict":"TLE","time\_ms":1000,"timed\_out":true,"weight":25,"message":"超时"},

&#x20;   {"name":"4.in","verdict":"RE","time\_ms":8,"signal":"SIGSEGV","weight":25,

&#x20;    "message":"SIGSEGV 段错误…","stderr\_tail":"..."}

&#x20; ]

}

```



\### 8. `generator.py` —— `gen` 子命令



```bash

python judge.py gen P1 --ref reference/P1.cpp

```



流程：编译参考实现 → 遍历每个 `.in` 限时运行 → 把 stdout 原样写入同名 `.out`（先写临时文件再原子替换，避免半截数据）→ 打印每个用例的耗时与判定，出错（参考实现 RE/TLE）则中止并保留旧 `.out`。



\### 9. `importer.py` —— `import-samples`



```bash

python judge.py import-samples exercise/P1-shipping.md \[--target problems/P1]

```



解析规则：

\- 匹配 `## 样例输入( \\d+)?` 与 `## 样例输出( \\d+)?` 标题下的 fenced code block；无标题则按「输入块 → 输出块」顺序配对；

\- 已有同名 `\*.in` 时自动后缀 `sample-1`、`sample-2` 避免覆盖；

\- 支持显式指定 `--target`，否则从文件名前缀 `Pn-\*` 推导题目。



\---



\## 四、数据格式



\### `problem.json`



```json

{

&#x20; "id": "P1",

&#x20; "title": "运费计算",

&#x20; "contest\_type": "oi",

&#x20; "build": {

&#x20;   "command": "g++ -O2 -std=c++17 -o {bin} {src}",

&#x20;   "src": "main.cpp"

&#x20; },

&#x20; "limits": { "time\_ms": 1000, "memory\_mb": 256 },

&#x20; "score": 100,

&#x20; "compare\_mode": "trim"

}

```



`P6` 的 make 构建：



```json

{

&#x20; "id": "P6",

&#x20; "build": { "command": "make", "target": "inspector", "output": "inspector" },

&#x20; "contest\_type": "acm"

}

```



\### 单用例 `3.json`（可选）



```json

{ "weight": 2, "time\_ms": 1500, "note": "n=1e6 边界，含隐藏加权" }

```



\---



\## 五、CLI 设计



| 子命令 | 作用 |

|---|---|

| `python judge.py run P1 examples/P1\_ac.cpp` | 评测单个提交，输出表格 + 报告 |

| `python judge.py run P1 examples/P1\_ac.cpp --mode acm` | 覆盖比赛类型 |

| `python judge.py gen P1 --ref reference/P1.cpp` | 用参考实现刷新 `.out` |

| `python judge.py import-samples exercise/P1-shipping.md` | 从题面抽取样例 |

| `python judge.py list \[P1]` | 列出题目与用例（权重/时限/备注） |

| `python judge.py init P7 --type oi` | 创建题目骨架目录 |



返回码约定：`0` 全 AC；`1` 非 AC；`2` 基础设施错误（找不到题目/用例）。便于 CI 集成。



\---



\## 六、新增用例的三条路径（互不冲突）



1\. \*\*手工放置\*\*：`problems/Px/tests/42.in` + `42.out` → 下次 `run` 自动纳入；放 `42.json` 可覆盖权重/时限。

2\. \*\*参考实现批量生成\*\*：`python judge.py gen Px --ref reference/Px.cpp` → 遍历所有 `.in`，用参考实现输出覆盖 `.out`；适合题面样例扩充。

3\. \*\*从题面抽取\*\*：`python judge.py import-samples exercise/Px-\*.md` → 解析 markdown 样例块自动写入 `.in/.out`；已内置 P1\~P6 共 30 组题面样例。



三条路径最终都写入同一目录，`problem.py` 的用例发现对来源无差别。



\---



\## 七、判定细节与演示



| 判定 | 触发条件 | 提示内容 |

|---|---|---|

| \*\*CE\*\* | 构建非 0 退出 | 末 200 行编译器输出 + 首条 `error:` 高亮 |

| \*\*TLE\*\* | 墙钟 > 1.5×时限 或 CPU > 时限 | `超时（限时 Nms）` |

| \*\*RE\*\* | `exit\_code<0` 且信号可翻译 | `SIGSEGV 段错误…` + `stderr` 末 2KB |

| \*\*PE\*\* | token 相等但文本不等 | `仅空白差异（PE）` |

| \*\*WA\*\* | 首个不一致行 | `第 i 行不一致：期望 … 实际 …`，行数不一致单独提示 |

| \*\*AC\*\* | 逐字符相等（`trim` 模式去掉末尾空行） | 空 |



`judge/examples/` 六条判定路径的演示提交分别对应：`P1\_ac.cpp`、`P1\_wa.cpp`、`P1\_ce.cpp`、`P1\_tle.cpp`、`P1\_re.cpp`、`P1\_pe.cpp`，以及 `P1\_make/`（make 多文件构建 + `target=inspector`）。



\---



\## 八、安全与沙箱边界



\- \*\*本地开发 / 教学场景\*\*：`setrlimit`（CPU、AS、FSIZE）+ 墙钟超时 + 输出上限（stdout/stderr 各 4MB）即可。

\- \*\*对外部署\*\*：需在 `runner.py` 之上再套一层 \*\*cgroup v2 + seccomp + user namespace\*\*（禁止 `fork/exec/socket/open` 等），并使用独立低权用户 + `nsjail` 或 `isolate`。建议在 `runner.py` 抽象 `Sandbox` 接口，默认实现为 `NoopSandbox`（本地），生产切 `NsjailSandbox`。

\- \*\*绝对禁止\*\*：把 shell 拼接的用户路径直接交给 `subprocess.run(shell=True)`；`command` 模板中的 `{bin}`/`{src}` 必须做路径白名单校验。



\---



\## 九、实现顺序（建议里程碑）



1\. \*\*骨架\*\*：`problem.py` + `verdict.py` + CLI `run`（仅 AC/WA）—— 打通「编译 → 运行 → 比对 → 报告」。

2\. \*\*判定全覆盖\*\*：`runner.py` 资源限制 + 超时 + 信号翻译 → 补齐 CE/TLE/RE/PE。

3\. \*\*计分\*\*：`scorer.py`（ACM/OI 双模式）+ `reporter.py` 表格与 JSON。

4\. \*\*用例工具链\*\*：`generator.py`（`gen`）+ 单用例 `.json` 覆盖。

5\. \*\*题面工具链\*\*：`importer.py`（`import-samples`）+ `exercise/` 6 份题面，抽取 30 组样例。

6\. \*\*多文件构建\*\*：`builder.py` 支持 `make` + `P1\_make/` 用例。

7\. \*\*回归\*\*：`examples/` 六条判定路径 + `P1\~P6` 全量自测（含加权抽验：2/4 权重通过 → 50 分）。



