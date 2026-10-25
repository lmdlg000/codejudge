# 站点规格卡 —— CodeJudge 在线代码评测台

> 唯一施工图。前端 / 后端 / 内容 / 视觉均以此为准；**接口契约（第 5 节）冻结，字段名不得两边各自发挥**。
> G0 基线：工具站（在线代码评测台）｜真实判题引擎（Python，按 requirements.md 流水线）+ FastAPI 后端 + Vue 3 前端｜页面：题目列表 → 题目详情/在线提交 → 逐用例判定结果（ACM/OI 双模式）｜内置 P1–P6 题目数据与判题演示用例｜本地运行、不做公网部署。

---

## 1. 站点定位

- **类型**：工具站（六类之一）。红线适用：**工具本体放首屏，不做任何铺垫**；隐私声明必须写清（本项目为「本机判题、数据不出机」）。
- **目标访客**：在本机做算法练习 / 教学演示的编程学习者与讲师。场景：写一段 C++ 代码，想立刻看到「真实编译运行 + 逐用例判定」的反馈（AC/PE/WA/TLE/RE/CE），并按 ACM 或 OI 规则看到得分。
- **核心转化动作**（一个）：**完成一次代码提交并看到逐用例判定结果与得分横幅**。所有页面、功能都必须能回答「它服务这个动作吗」，答不上来的删。

## 2. 站点地图

```
/                          题目列表（首页 = 工具本体首屏）
├── /problems/:pid         题目详情 + 在线写代码 + 提交（pid = P1…P6）
├── /submissions           提交历史（本地）
│   └── /submissions/:sid  判题结果（得分横幅 + 逐用例表格，sid = 提交 ID）
└── /about                 使用说明 / 关于（判定含义、CLI 用法、本地处理声明）
```

共 5 页（G0 页面量级 4–6 页内）。URL 用 vue-router history 模式，路径即上表，不设别名。

## 3. 页面清单

| 页面 | URL | 用途 | 关键区块 | 需要后端数据 |
|---|---|---|---|---|
| 题目列表（首页） | `/` | 进入即见可做的题，一步进详情 | 页头（站名+导航）；题目卡片列表（id/标题/计分模式/满分/时限/用例数）；页脚（关于链接 + 本地处理声明一行） | `GET /api/problems` |
| 题目详情 + 在线提交 | `/problems/:pid` | 读题 → 写代码 → 提交（核心转化动作发生页） | 题面（Markdown 渲染）；样例块；限制摘要（时限/内存/计分模式/满分）；代码编辑区（等宽字体 textarea）；主 CTA「提交判题」；错误提示条 | `GET /api/problems/:pid`；`POST /api/submissions` |
| 判题结果 | `/submissions/:sid` | 看懂这次提交为什么对/错 | 得分横幅（`通过 4/4 · 通过率 100% · 得分 100/100`）；逐用例判定表格（用例/判定/耗时/权重/提示）；CE 时编译输出（build_log）；提交源码回显（可折叠）；CTA「返回题目改代码」 | `GET /api/submissions/:sid`（提交后由 POST 响应直达，刷新/分享链接时走 GET） |
| 提交历史 | `/submissions` | 回看历次判题，复盘改错 | 倒序列表行（时间/题目/判定/得分摘要）；点行进结果页；按题目筛选 | `GET /api/submissions` |
| 关于 / 使用说明 | `/about` | 会用、敢用（隐私）、知道还有 CLI | 判定含义表（AC/PE/WA/TLE/RE/CE/SE）；ACM/OI 计分说明；使用流程三步；CLI 常用命令；本地处理声明 | 无（静态内容） |

## 4. 功能清单

优先级：P0 必做 / P1 应该做 / P2 以后再说。每条含验收标准，验收以「可观察行为」为准。

### 后端

| # | 功能 | 所属 | 优先级 | 验收标准 |
|---|---|---|---|---|
| B1 | 题目列表接口 | API | P0 | `GET /api/problems` 返回 P1–P6 全部摘要，字段与契约逐名一致；`total` = 实际题数 |
| B2 | 题目详情接口 | API | P0 | `GET /api/problems/P1` 返回题面 markdown、样例数组、限制、构建方式、用例数；`GET /api/problems/P9` 返回 404 + 统一错误体 |
| B3 | 提交判题（同步流水线） | API | P0 | `POST /api/submissions` 一次请求内完成 编译→逐用例执行→比对→计分→报告；判定顺序固定 CE → 逐用例 TLE → RE → 比对（AC/PE/WA）；响应含 summary+cases；CE 时全部用例 verdict=CE 且 build_log 非空；**make 题（P6）已开放（G3 追认，实测 AC）：必须走 files[] 且包含 Makefile，单文件→400、缺 Makefile→400（见 §5.4）** |
| B4 | 判题结果查询 | API | P0 | `GET /api/submissions/:sid` 响应与 POST 响应同构；未知 sid 返回 404 + 统一错误体 |
| B5 | 提交历史列表 | API | P0 | 倒序（新→旧）；`limit`/`offset` 生效；`problem_id` 过滤生效；`total` 为过滤后总数 |
| B6 | 健康检查 | API | P0 | `GET /api/health` 引擎就绪返回 200；`g++`/`make` 缺失或引擎初始化失败返回 503 + `ENGINE_UNAVAILABLE` |
| B7 | 并发与超时控制 | API | P0 | 判题进行中收到第二个提交返回 429 `JUDGE_BUSY`；整单判题超 120s 返回 408 `JUDGE_TIMEOUT`；单用例时限与构建超时（60s）由引擎层生效 |
| B8 | 提交落盘与报告持久化 | 存储 | P0 | 每次提交写 `reports/<sid>.json`（含提交文件、summary、cases）；`reports/latest.json` 同步为最新一份；重启后历史可查 |
| B9 | 多文件提交 | API | P0（已交付） | `files[]` 落盘后走 `make` 构建成功（对照 `examples/P1_make/` 链路）；**P6 在线多文件提交已实现并实测 AC（G3 追认）**；强制规则：make 题必须包含 Makefile（见 §5.4） |
| B10 | 示例代码接口 | API | P1 | `GET /api/examples?problem_id=P1` 返回该题演示文件名与内容（`P1_ac/wa/ce/tle/re/pe.cpp` 等） |
| B11 | 文件名安全校验 | 安全 | P0 | 文件名白名单 `^[A-Za-z0-9_.-]{1,64}$`，拒绝 `..`、路径分隔符、绝对路径；命令模板 `{bin}`/`{src}` 不接用户输入，`shell=False` |

### 前端

| # | 功能 | 所属页面 | 优先级 | 验收标准 |
|---|---|---|---|---|
| F1 | 题目列表 | `/` | P0 | 6 题卡片含 标题/计分模式/满分/时限/用例数，**并显示题型 topic/难度 difficulty（字段为 null 时优雅降级不渲染该标签）**；点卡片进 `/problems/:pid`；加载与空态有文案 |
| F2 | 题面渲染 | `/problems/:pid` | P0 | statement.md 完整渲染（标题/列表/代码块）；样例输入输出块可辨识；限制摘要一行可见 |
| F3 | 代码编辑与提交 | `/problems/:pid` | P0 | 等宽编辑区；空代码时提交按钮禁用；提交中按钮进入 loading 且文案「判题中…」不可重复点击 |
| F4 | 结果页主呈现 | `/submissions/:sid` | P0 | 顶部得分横幅严格为 `通过 {passed}/{total} · 通过率 {rate}% · 得分 {score}/{max_score}`；逐用例表格列 = 用例/判定/耗时/权重/提示；判定以彩色徽章区分 |
| F5 | CE/RE 细节展示 | `/submissions/:sid` | P0 | CE 展示 build_log（末 200 行）；RE/TLE/PE/WA 的 message 中文直接可见；stderr_tail 折叠展示 |
| F6 | 提交历史 | `/submissions` | P0 | 倒序列表；行内显示 时间/题目/判定/`通过 x/y · 得分 s/m`，**含提交文件列（file_label；缺失时优雅降级不渲染该单元格）**；点行进结果页 |
| F7 | 错误提示 | 全站 | P0 | 第 5 节每个错误码都有对应中文可读提示，网络断开也有兜底文案 |
| F8 | 关于 / 使用说明 | `/about` | P0 | 含判定含义表、计分说明、三步使用流程、本地处理声明 |
| F9 | 示例代码一键填入 | `/problems/:pid` | P1 | 下拉选 `examples/` 演示文件后一键填入编辑器（走 B10） |
| F10 | 多文件编辑面板 | `/problems/:pid` | P0（已交付） | make 题（build.mode=make）可添加/删除文件项并提交 files[]（**已交付，G3 追认开放**；提交文件必须含 Makefile，缺则后端 400） |
| F11 | 语法高亮编辑器 | `/problems/:pid` | P1 | CodeMirror 6 C++ 高亮替换 textarea（不改变提交数据结构） |
| F12 | 历史筛选 | `/submissions` | P1 | 按题目下拉过滤，URL query 同步 |
| F13 | 响应式适配 | 全站 | P1 | ≥1280px 完整双栏/宽布局；768px 可完成完整动线（可不美观但不破版） |
| F14 | 判题进度流（SSE） | 提交后 | P2 | 编译中/运行用例 n/N 实时提示 |
| F15 | 暗色模式 | 全站 | P2 | 跟随系统或手动切换 |

**明确不做（删掉并说明）**：注册登录、排行榜、管理端、多语言题面切换、在线调试器——它们不服务「完成一次判题看结果」这个唯一转化动作，且 G0 已排除。

## 5. 接口契约（冻结）

- **Base**：`http://127.0.0.1:8000`，全部路径以 `/api` 开头；请求/响应均 `application/json; charset=utf-8`。
- **字段名一次定死**，前后端照此实现；类型写死（string / number / boolean / ISO 8601 日期字符串 / 对象 / 数组），不接受「字符串或数字」。
- **日期格式**：ISO 8601 本地时间、秒级，例 `2025-01-01T12:00:00`。
- **统一错误体**（所有非 2xx）：

```json
{ "error": { "code": "PROBLEM_NOT_FOUND", "message": "题目不存在：P9" } }
```

`code` 为下表枚举；`message` 为中文可读信息（前端可直接展示，或按 code 映射自有文案）。

### 5.1 API 总表

| 方法 | 路径 | 用途 | 成功码 | 错误码 |
|---|---|---|---|---|
| GET | `/api/health` | 健康检查 | 200 | 503 ENGINE_UNAVAILABLE |
| GET | `/api/problems` | 题目列表 | 200 | 500 INTERNAL_ERROR |
| GET | `/api/problems/{pid}` | 题目详情（题面/样例/限制） | 200 | 404 PROBLEM_NOT_FOUND / 500 INTERNAL_ERROR |
| POST | `/api/submissions` | 提交判题（同步触发流水线） | 201 | 400 VALIDATION_ERROR / 404 PROBLEM_NOT_FOUND / 413 PAYLOAD_TOO_LARGE / 408 JUDGE_TIMEOUT / 429 JUDGE_BUSY / 503 ENGINE_UNAVAILABLE / 500 INTERNAL_ERROR |
| GET | `/api/submissions` | 提交历史列表 | 200 | 400 VALIDATION_ERROR / 500 INTERNAL_ERROR |
| GET | `/api/submissions/{sid}` | 判题结果查询 | 200 | 404 SUBMISSION_NOT_FOUND / 500 INTERNAL_ERROR |
| GET | `/api/examples?problem_id={pid}` | 判题演示示例代码（P1） | 200 | 400 VALIDATION_ERROR / 404 PROBLEM_NOT_FOUND |

### 5.2 错误码表（全站枚举，冻结）

| code | HTTP | 触发场景 | 前端提示（必须准备） |
|---|---|---|---|
| VALIDATION_ERROR | 400 | 字段缺失/类型不符/`source_code` 与 `files` 未恰好给其一/文件名非法/make 题单文件提交或缺 Makefile（见 §5.4） | 提交内容不合法，请检查后重试 |
| PROBLEM_NOT_FOUND | 404 | `pid` 不在 P1–P6 | 题目不存在 |
| SUBMISSION_NOT_FOUND | 404 | `sid` 无对应报告 | 找不到该次提交 |
| PAYLOAD_TOO_LARGE | 413 | 单文件 > 65536 字符 或 files 总量 > 262144 字符 或 files > 20 项 | 代码太长，请精简后重试 |
| JUDGE_TIMEOUT | 408 | 整单判题超过 120s 硬上限 | 判题超时，请检查死循环后重试 |
| JUDGE_BUSY | 429 | 已有一次判题在执行 | 判题进行中，请稍候重试 |
| ENGINE_UNAVAILABLE | 503 | `g++`/`make` 不在 PATH 或引擎初始化失败 | 判题引擎不可用，请检查本机编译环境 |
| INTERNAL_ERROR | 500 | 其他未预期异常 | 服务异常，请重试 |

### 5.3 数据结构（组件类型，接口间复用）

**ProblemSummary**（列表项）

| 字段 | 类型 | 含义 |
|---|---|---|
| id | string | 题目 id，如 `"P1"` |
| title | string | 题目标题 |
| contest_type | string | `"acm"` \| `"oi"`，默认计分模式 |
| score | number | 满分（problem.json 的 score） |
| test_count | number | 用例数（tests/ 发现结果） |
| time_limit_ms | number | 单用例时限（limits.time_ms） |
| memory_limit_mb | number | 内存限制（limits.memory_mb） |
| build_mode | string | `"g++"` \| `"make"` |
| topic | string \| null | 题型（如「分支/分段计费」），来源 problem.json 可选键 `topic`；缺省 null |
| difficulty | string \| null | 难度（如「入门/简单/中等/较难」），来源 problem.json 可选键 `difficulty`；缺省 null |

**ProblemDetail**（详情）

| 字段 | 类型 | 含义 |
|---|---|---|
| id | string | 题目 id |
| title | string | 题目标题 |
| contest_type | string | `"acm"` \| `"oi"` |
| score | number | 满分 |
| compare_mode | string | `"exact"` \| `"trim"` |
| limits | object | `{ "time_ms": number, "memory_mb": number }` |
| build | object | `{ "mode": "g++"\|"make", "command": string, "src": string\|null, "default_filename": string\|null }` |
| statement_md | string | 题面 Markdown 原文 |
| samples | array | `[{ "input": string, "output": string }]`，按题面出现顺序 |
| test_count | number | 用例数 |

**CaseResult**（逐用例结果）

| 字段 | 类型 | 含义 |
|---|---|---|
| name | string | 用例名，如 `"1.in"` |
| verdict | string | `"AC"`\|`"PE"`\|`"WA"`\|`"TLE"`\|`"RE"`\|`"CE"`\|`"SE"` |
| time_ms | number | 实际耗时（毫秒） |
| exit_code | number \| null | 进程退出码；被信号终止时为 null |
| weight | number | 用例权重 |
| message | string | 判定提示（中文；AC 为 `""`） |
| signal | string \| null | 信号名，如 `"SIGSEGV"`；无则 null |
| timed_out | boolean | 是否超时终止 |
| stderr_tail | string \| null | stderr 末 2KB；无则 null |

**Summary**（汇总，两种计分模式通用）

| 字段 | 类型 | 含义 |
|---|---|---|
| total | number | 用例总数 |
| passed | number | AC 用例数 |
| pass_rate | number | 通过率，0–1，保留 4 位小数（0.25 即 25%） |
| score | number | 最终得分：OI = 加权折算；ACM = 全 AC 得满分否则 0 |
| max_score | number | 满分 |
| partial_score | number | 加权部分分（两种模式都给；OI 时与 score 相同；ACM 时供参考展示） |

**SubmissionResult**（提交/查询响应体）

| 字段 | 类型 | 含义 |
|---|---|---|
| submission_id | string | 提交 id，格式 `YYYYMMDD-HHMMSS-<pid>-<4位hex>`，例 `20250101-120000-P1-a3f2` |
| problem_id | string | 题目 id |
| problem_title | string | 题目标题（冗余，便于历史列表） |
| mode | string | 本次生效计分模式 `"acm"` \| `"oi"` |
| created_at | string | 提交时间（ISO 8601） |
| status | string | `"finished"`（判题完成）\| `"failed"`（基础设施错误 SE） |
| verdict | string | 总判定：ACM 合成规则（全 AC→`"AC"`，否则首个非 AC 用例判定；CE→`"CE"`；流水线崩溃→`"SE"`） |
| summary | object | Summary |
| cases | array | `CaseResult[]`，顺序同用例发现顺序；status=failed 时为 `[]` |
| build_log | string \| null | 编译输出（末 200 行）；仅 CE 时非 null |
| files | array | `[{ "name": string, "content": string }]` 提交源码回显（单文件也包成 1 项） |
| message | string \| null | status=failed 时的失败原因；否则 null |

**SubmissionSummary**（历史列表项）

| 字段 | 类型 | 含义 |
|---|---|---|
| submission_id | string | 提交 id |
| problem_id | string | 题目 id |
| problem_title | string | 题目标题 |
| file_label | string | 提交文件显示名：单文件取文件名（如 `"main.cpp"`）；多文件取主文件名，无法判定主文件时取「N 个文件」（N 为文件数）。随 `reports/<sid>.json` 持久化 |
| created_at | string | 提交时间（ISO 8601） |
| mode | string | `"acm"` \| `"oi"` |
| verdict | string | 总判定 |
| summary | object | Summary |

### 5.4 接口逐条定义

#### GET `/api/health`

- 入参：无。
- 出参 200：

```json
{
  "status": "ok",
  "engine": "ready",
  "version": "1.0.0",
  "problem_count": 6
}
```

| 字段 | 类型 | 含义 |
|---|---|---|
| status | string | 固定 `"ok"` |
| engine | string | `"ready"` |
| version | string | 服务版本号 |
| problem_count | number | 已加载题目数 |

- 错误：503 `ENGINE_UNAVAILABLE`（g++/make 缺失等）。

#### GET `/api/problems`

- 入参：无。
- 出参 200：`{ "items": ProblemSummary[], "total": number }`
- 错误：500 `INTERNAL_ERROR`。

#### GET `/api/problems/{pid}`

- 入参：路径参数 `pid`：string 必填（如 `P1`）。
- 出参 200：ProblemDetail。
- 错误：404 `PROBLEM_NOT_FOUND`；500 `INTERNAL_ERROR`。

#### POST `/api/submissions`

- 入参（JSON body）：

| 字段 | 类型 | 必填 | 约束与含义 |
|---|---|---|---|
| problem_id | string | 必填 | P1–P6 之一 |
| source_code | string | 二选一 | 单文件源码，≤ 65536 字符；与 `files` 互斥，恰好给其一 |
| filename | string | 选填 | 默认 `build.default_filename`，缺省 `"main.cpp"`；白名单 `^[A-Za-z0-9_.-]{1,64}$` |
| files | array | 二选一 | 多文件：`[{ "name": string, "content": string }]`；≤ 20 项；每项 content ≤ 65536 字符；合计 ≤ 262144 字符；name 同上白名单；与 `source_code` 互斥 |
| mode | string | 选填 | `"acm"` \| `"oi"`，覆盖题目默认计分模式；缺省用 `contest_type` |

- 出参 201：SubmissionResult（status 固定 `"finished"` 或 `"failed"`，同步判题当场出全量结果）。
- **make 题（P6）提交规则（G3 追认开放）**：必须走 `files[]` 且包含 Makefile——单文件提交 → 400 `VALIDATION_ERROR`，`message` 固定为 `该题为多文件 make 构建，请用多文件提交（需包含 Makefile 与源文件）`；`files[]` 缺 Makefile → 400 `VALIDATION_ERROR`，`message` 固定为 `多文件 make 构建缺少 Makefile，请在提交文件中包含 Makefile`。CLI（`python judge.py run P6 …`）不受影响。
- 判定语义（与 requirements 对齐，冻结）：
  - 构建失败 → 全部用例 verdict=`"CE"`，`build_log` 非空，`summary.score=0`；
  - 逐用例判定顺序：TLE → RE → 比对（AC/PE/WA）；
  - `mode=oi`：score = Σ通过权重 / Σ总权重 × 满分；verdict 仍按 ACM 合成规则给出（便于列表徽章统一）；
  - `mode=acm`：全 AC → score=max_score，verdict=`"AC"`；否则 score=0，verdict=首个非 AC 用例判定，partial_score 供参考。
- 错误：见 5.2（400/404/413/408/429/503/500）。

#### GET `/api/submissions`

- 入参（query）：

| 字段 | 类型 | 必填 | 约束 |
|---|---|---|---|
| problem_id | string | 选填 | 只返回该题提交 |
| limit | number | 选填 | 默认 20，范围 1–100 |
| offset | number | 选填 | 默认 0，≥0 |

- 出参 200：`{ "items": SubmissionSummary[], "total": number }`（items 按 created_at 倒序；total 为过滤后总数）。
- 错误：400 `VALIDATION_ERROR`（limit/offset 非法）；500 `INTERNAL_ERROR`。

#### GET `/api/submissions/{sid}`

- 入参：路径参数 `sid`：string 必填。
- 出参 200：SubmissionResult（与 POST 响应同构）。
- 错误：404 `SUBMISSION_NOT_FOUND`；500 `INTERNAL_ERROR`。

#### GET `/api/examples`（P1，首发可做）

- 入参（query）：`problem_id`：string 必填。
- 出参 200：`{ "items": [{ "name": string, "content": string, "expect": string }] }`
  - `name` 如 `"P1_ac.cpp"`；`expect` 为演示预期判定 `"AC"`\|`"PE"`\|`"WA"`\|`"TLE"`\|`"RE"`\|`"CE"`\|`"make"`（`P1_make/` 多文件用 `"make"`）。
- 错误：400 `VALIDATION_ERROR`；404 `PROBLEM_NOT_FOUND`。

## 6. 技术栈与托管

- **后端**：FastAPI + Uvicorn（Python 3.10+）。**理由**：判题引擎 `core/` 是纯 Python，FastAPI 与引擎同进程同语言直接函数调用，无需跨语言桥接/子进程转发 CLI，出参可直接复用报告 JSON 结构；Pydantic schema 即接口契约的代码级单一来源。
- **前端**：Vue 3 + Vite + vue-router（history 模式）。**理由**：交互集中在「编辑→提交→结果表格」一条动线，组件化（结果表格/徽章/横幅）收益明显；本地工具站不需要 SEO/SSG，CSR 足够；Vite 开发体验与构建速度适合 5 页规模。
- **状态管理**：不引 Pinia，用组合式函数（composables）+ 组件内状态。**理由**：无跨页共享的复杂状态，仅「当前题目 / 当前结果」两份临时数据，引状态库是过度设计。
- **样式**：原生 CSS + 设计令牌 `frontend/src/styles/tokens.css`（Phase 5 视觉规范的唯一样式来源）。**理由**：5 页规模不上原子类/预处理器，令牌先行保证视觉统一。
- **题面渲染**：`markdown-it`（或 marked）渲染 statement.md；代码块保留等宽样式。
- **代码编辑**：P0 用 `<textarea>` 等宽字体（零依赖、无障碍好）；P1 升级 CodeMirror 6 语法高亮（不改提交数据结构）。
- **数据库**：**不需要**。题目数据在 `problems/`（数据即配置，requirements 设计原则 1）；提交历史 = `reports/*.json` 文件。**理由**：本地单机演示，文件即存储，免去迁移与运维面。
- **判题执行**：同步判题（无队列/无 WebSocket）。阻塞流水线用 `asyncio.to_thread` 包进事件循环，全局 `asyncio.Semaphore(1)` 限并发（超出 429）。
- **托管与运行**：本地运行，不做公网部署，无域名无 HTTPS。
  - 开发联调：后端 `uvicorn backend.app.main:app --reload --port 8000`；前端 `npm run dev`（:5173），Vite proxy 将 `/api` 转发 `http://127.0.0.1:8000`。
  - 单端口演示：`cd frontend && npm run build` → `dist/` 由 FastAPI `StaticFiles` 挂载到 `/`（html=True + history 回退 index.html），`/api/*` 路由优先匹配。启动一条命令即可用。
- **环境变量约定**（代码只引用名，不写值）：

| 变量名 | 用途 | 在哪里配置 | 必填 |
|---|---|---|---|
| `JUDGE_HOST` | 服务监听地址，默认 127.0.0.1 | 启动脚本/终端 | 否 |
| `JUDGE_PORT` | 服务端口，默认 8000 | 启动脚本/终端 | 否 |
| `JUDGE_REPORTS_DIR` | 报告目录覆盖（默认 `reports/`） | 启动脚本/终端 | 否 |
| `JUDGE_MAX_SUBMIT_SECONDS` | 整单判题硬上限，默认 120 | 启动脚本/终端 | 否 |

## 7. 目录结构约定

```
codejudge/                        # 项目根（= 引擎根，CLI 照旧可用）
├── judge.py                      # CLI 入口（run/gen/import-samples/list/init）——引擎保留
├── config.toml                   # 全局默认（时限/内存/计分模式/报告目录）
├── core/                         # 判题引擎（requirements 定义，公开函数签名不改）
│   ├── problem.py  builder.py  runner.py  verdict.py
│   ├── comparator.py  scorer.py  reporter.py  generator.py  importer.py
├── problems/                     # P1–P6 题目数据（见第 9 节）
├── exercise/                     # 题面 Markdown 源（import-samples 输入）
├── examples/                     # 判定路径演示提交（P1_ac/wa/ce/tle/re/pe.cpp、P1_make/）
├── reports/                      # 运行时生成：判题报告 = 提交历史存储（git 忽略）
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI 入口：挂路由 + StaticFiles + 异常→统一错误体
│   │   ├── config.py             # 环境变量读取（上表 4 个）
│   │   ├── routers/
│   │   │   ├── health.py         # GET /api/health
│   │   │   ├── problems.py       # GET /api/problems(/{pid})
│   │   │   └── submissions.py    # POST/GET /api/submissions(/{sid})
│   │   ├── schemas/
│   │   │   └── api.py            # Pydantic 模型 = 第 5 节契约的唯一代码来源
│   │   └── services/
│   │       ├── judge_service.py  # 流水线编排（见第 8 节）
│   │       ├── problem_service.py# 题目加载/样例提取（复用 core.problem + core.importer）
│   │       └── submission_store.py # reports/ 读写、sid 生成、历史查询
│   ├── requirements.txt          # fastapi, uvicorn
│   └── tests/                    # 接口测试（对照契约逐字段断言）
├── frontend/
│   ├── src/
│   │   ├── pages/                # ProblemList.vue  ProblemDetail.vue  SubmissionList.vue  SubmissionDetail.vue  About.vue
│   │   ├── components/           # ScoreBanner.vue  CaseTable.vue  VerdictBadge.vue  CodeEditor.vue  MarkdownView.vue  ProblemCard.vue  ErrorBar.vue
│   │   ├── api/                  # client.js（fetch 封装+错误码映射）+ types.js（契约 TS/JSDoc 类型）
│   │   ├── composables/          # useProblems.js  useSubmission.js
│   │   ├── router/index.js       # 第 2 节 URL 表
│   │   ├── styles/               # tokens.css（视觉令牌唯一来源）+ global.css
│   │   └── assets/
│   ├── public/                   # favicon 等原样拷贝
│   ├── index.html
│   ├── vite.config.js            # dev proxy: /api → 127.0.0.1:8000
│   └── package.json
├── docs/
│   ├── site-spec.md              # 本文件
│   └── (后续：视觉规范、文案稿)
└── README.md
```

约定：**页面进 `pages/`，可复用区块进 `components/`，样式变量只写 `tokens.css`，API 调用只走 `api/client.js`**，任何组件不得裸写 fetch URL。

## 8. 判题引擎落位（core/ 如何被 FastAPI 复用）

### 8.1 模块职责与复用方式

| core 模块 | 职责 | 服务层调用点 |
|---|---|---|
| problem.py | 题目加载 + 用例发现 + 单用例 json 覆盖 | `problem_service`：列表/详情/提交时 `Problem.load(pid, problems_dir)` |
| builder.py | g++/make 编译构建，CE 输出捕获 | `judge_service` 步骤 4 |
| runner.py | 限时执行（stdin 注入、超时、资源限制） | `judge_service` 步骤 5（逐用例） |
| verdict.py | Verdict 枚举 + 信号翻译 | 全程；Windows 降级见第 10 节 |
| comparator.py | 逐字符 + token 比对（AC/PE/WA + 首差行号） | `judge_service` 步骤 5 每用例执行后 |
| scorer.py | ACM/OI 汇总、权重折算、通过率 | `judge_service` 步骤 6 → 产出 Summary |
| reporter.py | 控制台表格 + JSON 报告 + latest.json | `judge_service` 步骤 7；同时充当提交存储 |
| generator.py / importer.py | gen 刷 .out / 题面抽样例 | 不进请求路径；importer 的样例解析函数被 `problem_service` 复用以产出 `samples[]` |

### 8.2 提交流水线（POST /api/submissions 同步执行）

```
Pydantic 校验 → 文件名白名单 → 临时 workdir 落盘(files)
   → Problem.load(pid)（不存在 → 404）
   → builder.build(workdir)（超时 60s）
        └ 失败/超时 → 全用例 CE + build_log（末 200 行，高亮首条 error:）
   → for case in tests: runner.run(binary, case.input, case.time_limit_ms, mem_mb)
        → TLE（墙钟 > 1.5×时限 或 CPU > 时限）→ RE（非 0 退出/信号）→ comparator.compare（AC/PE/WA）
   → scorer.score(mode) → Summary
   → reporter 写 reports/<sid>.json + latest.json
   → 映射 SubmissionResult 返回 201
```

- **同步语义**：请求线程内 `asyncio.to_thread(pipeline)`；完成即返回全量结果，前端提交后直接 `router.push('/submissions/'+sid)`。
- **并发限制**：全局 `Semaphore(1)`；拿不到锁立即返回 429 `JUDGE_BUSY`（不排队，本地单机不需要队列）。
- **超时分层**：单用例 = problem.json `limits.time_ms`（墙钟 1.5× 兜底）；构建 60s；**整单硬上限 120s**（`JUDGE_MAX_SUBMIT_SECONDS`），超时返回 408 `JUDGE_TIMEOUT`，报告标 `status=failed`。
- **判定顺序固定（冻结）**：CE → 逐用例 TLE → RE → 比对（AC/PE/WA）。

### 8.3 报告 JSON → API 响应映射

`reports/<sid>.json` 与 requirements 报告同构并扩展（新增字段仅 `submission_id` / `status` / `files` / `message` / `problem_title` / `mode`）：

| 报告字段 | API 字段 | 说明 |
|---|---|---|
| problem_id | problem_id | 直映 |
| contest_type | mode | 改名（`"acm"`/`"oi"`） |
| started_at | created_at | 改名 |
| summary | summary | 直映（total/passed/pass_rate/score/max_score）+ 补 partial_score |
| cases[] | cases[] | 直映（name/verdict/time_ms/exit_code/weight/message/signal/timed_out/stderr_tail） |
| （新增）submission_id / status / files / build_log / message | 同名 | 服务层写入 |
| （新增）file_label | SubmissionSummary.file_label | 服务层写入并随报告持久化；SubmissionResult 不重复暴露（源码在 files[]） |

`sid` 即报告文件名主干；`latest.json` 恒为最新一份副本（CLI 兼容）。

## 9. 题目数据规范（problems/P1–P6）

### 9.1 目录约定

```
problems/<pid>/
├── problem.json      # 元信息 + 构建方式 + 计分模式（必需）
├── statement.md      # 题面 Markdown（必需）
├── reference/<pid>.cpp  # 参考实现，gen 刷 .out 用（P6 可为多文件）
└── tests/
    ├── 1.in  1.out           # 用例：同名配对（必需）
    ├── 3.in  3.out  3.json   # 可选覆盖：weight / time_ms / note
    └── hidden-1.in  hidden-1.out  hidden-1.json
```

### 9.2 problem.json 字段（冻结）

| 字段 | 类型 | 必填 | 含义 |
|---|---|---|---|
| id | string | 必填 | 题目 id，与目录名一致（`P1`…`P6`） |
| title | string | 必填 | 题目标题 |
| contest_type | string | 必填 | `"acm"` \| `"oi"` |
| build | object | 必填 | g++：`{"command":"g++ -O2 -std=c++17 -o {bin} {src}","src":"main.cpp"}`；make：`{"command":"make","target":"inspector","output":"inspector"}` |
| limits | object | 选填 | `{"time_ms":1000,"memory_mb":256}`，缺省 1000/256 |
| score | number | 选填 | 满分，缺省 100 |
| compare_mode | string | 选填 | `"exact"` \| `"trim"`，缺省 `"trim"`（末尾多余换行无害） |
| topic | string | 选填 | 题型标签（如「分支/分段计费」），API `ProblemSummary.topic`；缺省 null 不渲染 |
| difficulty | string | 选填 | 难度（如「入门/简单/中等/较难」），API `ProblemSummary.difficulty`；缺省 null 不渲染 |

P1–P6 的 `topic`/`difficulty` 取值以 `docs/content-plan.md` 题面清单为准（当前基线：P1 分支/分段计费·入门；P2 字符串处理·简单；P3 排序/贪心·中等；P4 日期模拟·中等；P5 图论/最短路·较难；P6 拓扑排序/环检测·中等）。

### 9.3 tests 发现规则

1. 扫描 `tests/*.in`，按同名找 `.out`；**缺 `.out` 直接拒绝**并给出清晰错误（题目不可用，接口报 500 之前在加载层修复）。
2. `<stem>.json` 若存在则覆盖该用例 `weight` / `time_ms` / `note`（缺省 weight=1.0，time_ms 用 limits）。
3. 发现顺序 = 文件名字典序；API `cases[]` 顺序与此一致。
4. 三种来源（手放 / gen 生成 / import-samples 抽取）对发现规则无差别。

### 9.4 statement.md 格式（可被 importer 解析）

- 标准 Markdown；样例块规则（与 core/importer 一致）：
  - 匹配标题 `## 样例输入( \d+)?` 与 `## 样例输出( \d+)?` 下的 fenced code block 成对；
  - 无标题时按「输入块 → 输出块」顺序配对；
- API 的 `samples[]` 直接来自同一解析函数，题面渲染与样例结构化同源。

### 9.5 reference/ 与 examples/ 的用途

| 目录 | 用途 | 谁消费 |
|---|---|---|
| `reference/<pid>.cpp` | 参考实现；`python judge.py gen <pid> --ref …` 批量刷新 `.out` | 维护者 / CLI |
| `examples/P1_ac/wa/ce/tle/re/pe.cpp` | 六条判定路径演示提交（AC/WA/CE/TLE/RE/PE） | CLI 演示；前端「一键填入示例代码」（P1，走 GET /api/examples） |
| `examples/P1_make/`（Makefile + inspector.cpp + util.h） | make 多文件构建链路演示 | CLI 演示；P6 在线多文件提交的对照基准 |

## 10. 非目标与已知约束

**非目标（本期明确不做）**：用户系统（注册/登录/排行榜/管理端）；公网部署与域名 HTTPS；沙箱加固（cgroup v2 + seccomp + user namespace + nsjail，requirements §八的对外部署方案）；多语言提交（仅 C++，g++/make 两种构建）；在线调试器/IDE 能力（补全、单步）；报告清理策略；判题队列与分布式执行。

**已知约束（实现与验收时必须知悉）**：

1. **Windows 信号翻译降级**：本机开发在 Windows 时，`resource.setrlimit` 不可用、信号翻译降级为「进程非 0 退出码」→ RE 的 `signal` 可能为 null、`message` 用退出码描述；超时终止走 `taskkill`。RE/TLE 判定精度弱于 POSIX，演示脚本按此预期。
2. **同步单并发**：同时只判一单，第 2 单 429；整单 120s 硬上限。这是本地评测台的有意取舍（G0），不是缺陷。
3. **提交内容即本机代码执行**：无沙箱加固，仅 `setrlimit`（POSIX）+ 墙钟 + 输出上限（stdout/stderr 各 4MB、stderr 报告留末 2KB）。**只许本机自用**，绝不暴露公网。
4. **路径安全红线**（requirements §八）：用户文件名只走白名单；`{bin}`/`{src}` 模板值由服务端生成；禁止 `shell=True` 拼接用户输入。
5. **reports/ 即数据库**：历史查询按文件扫描，规模以本地演示（数百单）为限，不做索引。
6. **数据一致性**：题目增删改只动 `problems/` 目录（数据即配置），后端无题库管理接口。

## 11. 转化路径（访客从进入到完成一次判题）

```
落地 /（题目列表，工具本体首屏）
  → 点题目卡片 → /problems/:pid（读题 + 看样例 + 限制）
  → 写/粘贴代码 → 点「提交判题」（loading：判题中…）
  → 跳转 /submissions/:sid（得分横幅 + 逐用例表格）
  → 「返回题目改代码」改完再交 或 进 /submissions 复盘
```

**逐步摩擦点与削减建议**：

| 步 | 摩擦点 | 削减建议 |
|---|---|---|
| 落地 | 首屏是介绍/铺垫，工具藏在第二屏 | **红线**：`/` 直接渲染题目列表，零营销区块 |
| 选题 | 卡片信息不足以判断难度/成本 | 卡片固定展示 计分模式/满分/时限/用例数 四要素 |
| 读题 | 样例与题面混排，要来回滚动 | 详情页限制摘要常驻编辑区上方；样例块独立样式 |
| 写码 | 空白编辑器不知道写什么 | P0 给 main 函数骨架模板；P1「一键填入示例代码」（六条判定路径可玩） |
| 提交 | 按钮找不到 / 重复点击 / 空代码可提交 | 主 CTA 固定编辑区底部；loading 态禁用；空代码禁用 |
| 等待 | 同步判题最长 120s，无反馈 | loading 文案「判题中…（最长约 2 分钟）」；P2 SSE 进度 |
| 看结果 | 判定字母看不懂 | 横幅大字 + 判定徽章颜色 + message 中文；CE 直接展开 build_log |
| 复盘 | 改完找不到回来的路 | 结果页常驻「返回题目改代码」；历史页可直达任一结果 |

**最短路径**：落地（1 次点击）→ 详情（粘贴代码 1 次点击提交）→ 结果。共 2 次点击 + 1 次粘贴，无注册、无弹窗、无多余表单。

## 12. 范围分层

| 层 | 内容 | 砍掉后果 |
|---|---|---|
| **首发必做（P0）** | 5 页框架；题目列表/详情（题面+样例+限制）；单文件编辑+提交；同步判题全流水线（AC/PE/WA/TLE/RE/CE 全判定）；结果页（横幅+逐用例表+CE 日志）；提交历史列表+详情回看；健康检查；全错误码中文提示；B7 并发超时；B8 落盘；多文件提交与 P6 在线判题（B9/F10，已交付） | ——（少任何一条即未完成核心转化动作） |
| **首发可做（P1）** | 示例代码一键填入（B10/F9）；CodeMirror 高亮（F11）；历史筛选（F12）；响应式（F13） | 砍掉**不影响上线**：核心动线（判题+结果）不受影响 |
| **上线后迭代（P2）** | SSE 判题进度（F14）；暗色模式（F15）；导出报告；快捷键 | 无感知缺失 |

**预算/时间不足时的砍法**：只保 P0。若 P0 还要再减，可降级「提交历史详情回看」（保留列表不可点入）与「关于页」（并入页脚一行链接），但**结果页与判定表格一毫米都不能少**——那是唯一转化动作的落点。

---

**范围建议（砍到哪层能上线）**：P0 即可上线；再紧就砍历史详情回看与关于页，结果页与逐用例表格不许动。

**最大风险（一句话）**：Windows 下 runner 的资源限制与信号翻译降级（taskkill + 非 0 退出码），RE/TLE 判定精度与演示稳定性弱于 POSIX。

**需要用户拍板的 1–3 个决策**：① ~~P6 多文件在线提交~~ 已由 G3 追认开放并实测 AC（files[] 必含 Makefile）；② 提交历史是否保存源码全文回显（默认保存，便于复盘）；③ 单并发 + 整单 120s 硬上限是否接受（默认接受）。

---
---

# Δ1 增补：用户系统（Supabase）

> 本节为 Δ1 契约增补，**第 1–12 节原文不动**；认证与用户数据域以本节为准。
> Δ1 G0 基线：CodeJudge + Supabase 用户系统｜新一代密钥体系（VITE_SUPABASE_PUBLISHABLE_KEY 前端 / SUPABASE_SECRET_KEY 仅后端）｜邮箱 + GitHub OAuth 注册登录｜提交历史入 Supabase（按用户 RLS 隔离）｜双模式：配置了 Supabase 则登录后判题且历史入库，未配置则本地匿名可用（现有行为不变）｜前端 @supabase/supabase-js（Vite/npm）+ .env 占位｜GitHub Pages 部署就绪（hash 路由 / VITE_API_BASE / VITE_ROUTER_MODE）｜判题 API 保留 FastAPI 自托管。

## 13. 用户系统（Supabase）

### 13.1 认证契约

前端经 **@supabase/supabase-js 直连 Supabase Auth**（不经过 FastAPI 中转认证）。动作与调用冻结如下：

| 动作 | supabase-js 调用 | 说明 |
|---|---|---|
| 注册（邮箱密码） | `supabase.auth.signUp({ email, password, options: { data: { username } } })` | username 选填，存入 `raw_user_meta_data` |
| 登录（邮箱密码） | `supabase.auth.signInWithPassword({ email, password })` | |
| 登录（GitHub） | `supabase.auth.signInWithOAuth({ provider: 'github', options: { redirectTo } })` | `redirectTo` = 当前站点根 URL，**不带 `#/`**（见 13.6） |
| 退出 | `supabase.auth.signOut()` | |
| 会话监听 | `supabase.auth.onAuthStateChange(cb)` | 事件：`SIGNED_IN` / `SIGNED_OUT` / `TOKEN_REFRESHED` |
| 启动恢复 | `supabase.auth.getSession()` | App boot 时恢复登录态 |

**会话存取约定**：

- `createClient(VITE_SUPABASE_URL, VITE_SUPABASE_PUBLISHABLE_KEY, { auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true } })`（均为 supabase-js 默认值，显式声明防漂移）。
- 会话持久化在 `localStorage`，键名 `sb-<project-ref>-auth-token`；会话 = `access_token`（JWT）+ `refresh_token` + `user`。
- `access_token` 仅在请求判题 API 时携带：`Authorization: Bearer <access_token>`（`api/client.js` 的 `createSubmission` 增加该头，其余 GET 不强制）。
- `profiles` 行由前端在首次 `SIGNED_IN` 后 upsert：`insert into profiles (id, username) values (:uid, :username) on conflict (id) do nothing`（RLS 限本人，见 13.2）。

**登录态如何影响提交流程**：

| 模式 | 提交行为 |
|---|---|
| local（未配置 Supabase） | 现状不变：匿名提交，结果写 `reports/`，不带任何认证头 |
| supabase（已配置） | **登录后才能判题**：未登录点「提交判题」→ 唤起登录（不判题）；已登录 → `POST /api/submissions` 带 `Authorization: Bearer <access_token>` → 后端校验 JWT → 判题 → 结果带 `user_id` 入库（见 13.5） |

**Δ1 新增错误码**（§5.2 原表不动，此处补枚举，前端 `ERROR_HINTS` 同步补一行）：

| code | HTTP | 触发场景 | 前端提示 |
|---|---|---|---|
| UNAUTHORIZED | 401 | supabase 模式下未登录 / JWT 无效或过期 | 请先登录（登录状态可能已过期） |

### 13.2 数据库 Schema（DDL + RLS）

**DDL（Supabase SQL Editor 执行，一次建齐）**：

```sql
-- 用户资料表
create table public.profiles (
  id          uuid primary key references auth.users (id) on delete cascade,
  username    text,
  created_at  timestamptz not null default now()
);

-- 提交历史表（id = §5.3 submission_id / sid，与 reports/<sid>.json 同名，单一 ID 空间）
create table public.submissions (
  id          text primary key,                -- sid：YYYYMMDD-HHMMSS-<pid>-<4位hex>
  user_id     uuid not null references auth.users (id) on delete cascade,
  problem_id  text not null,
  verdict     text not null check (verdict in ('AC','PE','WA','TLE','RE','CE','SE')),
  score       numeric not null,
  summary     jsonb not null,                  -- §5.3 Summary 对象
  cases       jsonb not null,                  -- §5.3 CaseResult[]
  files       jsonb not null,                  -- §5.3 FileItem[]
  created_at  timestamptz not null default now(),
  -- 【契约对齐补列】对齐 §5.3 SubmissionSummary / SubmissionResult，前端不二次派生
  mode        text not null default 'oi' check (mode in ('acm','oi')),
  file_label  text not null default '',
  build_log   text                             -- 仅 CE 非 null；AC 等为 null
);

create index submissions_user_created_idx on public.submissions (user_id, created_at desc);
create index submissions_problem_idx on public.submissions (problem_id);
```

补列说明：`mode`（提交可覆盖计分模式，无法从 problem_id 推导）、`file_label`（后端计算一次，与本地 reports 同值）、`build_log`（CE 明细，结果页 F5 需要）。`status`/`message` 不存——**仅 `status=finished` 的结果入库**，云端行恒映射 `status="finished"`、`message=null`。

**RLS 策略（逐表，冻结）**：

```sql
alter table public.profiles    enable row level security;
alter table public.submissions enable row level security;

-- profiles：本人读写自己的（读 / 新建 / 改名）
create policy "profiles_select_own" on public.profiles
  for select to authenticated using (auth.uid() = id);
create policy "profiles_insert_own" on public.profiles
  for insert to authenticated with check (auth.uid() = id);
create policy "profiles_update_own" on public.profiles
  for update to authenticated using (auth.uid() = id) with check (auth.uid() = id);

-- submissions：本人只读自己的；写入仅服务端（SUPABASE_SECRET_KEY 管理端，绕过 RLS）
create policy "submissions_select_own" on public.submissions
  for select to authenticated using (auth.uid() = user_id);
-- 有意不建 insert/update/delete 策略：anon 与 authenticated 直写一律拒绝
```

| 表 | 匿名（无 JWT） | 本人 | 他人 | 服务端（secret key） |
|---|---|---|---|---|
| profiles | 0 权限 | 读 + 写自己的行 | 0 权限 | 管理端全权（不走 RLS） |
| submissions | 0 权限 | 只读自己的行 | 0 权限 | 插入判题结果（不走 RLS） |

**历史页数据源切换（双模式）**：

| 状态 | `/submissions` 数据源 | 结果详情 `/submissions/:sid` |
|---|---|---|
| local 模式 | `GET /api/submissions`（reports/ 文件） | `GET /api/submissions/{sid}` |
| supabase 模式 + 未登录 | 空态 + 登录 CTA（不发请求） | 同左（不发请求） |
| supabase 模式 + 已登录 | supabase-js：`from('submissions').select('*').eq('user_id', user.id).order('created_at', { ascending: false })`（RLS 兜底再过滤一次） | supabase-js：`from('submissions').select('*').eq('id', sid).maybeSingle()` |

Supabase 行 → 现契约视图模型映射（渲染组件复用，字段名不改）：

| §5.3 字段 | submissions 列 | 备注 |
|---|---|---|
| submission_id | id | 即 sid，与 reports 同一 ID 空间 |
| problem_id | problem_id | |
| problem_title | （不存） | 前端用 `GET /api/problems` 静态映射 |
| file_label | file_label | 直取 |
| created_at | created_at | timestamptz → 前端格式化为 ISO 8601 本地秒级 |
| mode | mode | |
| verdict | verdict | |
| summary | summary jsonb | |
| cases / files / build_log | cases / files / build_log | 详情页用 |
| status / message | （不存） | 恒 `"finished"` / null |

### 13.3 密钥边界（新一代 publishable / secret 体系）

| 变量名 | 位置 | 可否进前端产物 | 用途 |
|---|---|---|---|
| `VITE_SUPABASE_URL` | frontend/.env 或构建 env | **可**（VITE_ 烘焙进 dist） | Supabase 项目 URL（`https://<project-ref>.supabase.co`） |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | frontend/.env 或构建 env | **可** | supabase-js 初始化 + publishable/anon 级请求；形如 `sb_publishable_…` |
| `SUPABASE_SECRET_KEY` | **仅 backend/.env** | **绝不**（不进前端/不进仓库/不进日志） | 服务端校验 JWT（admin `auth.get_user`）+ 代写 submissions（admin 客户端绕过 RLS）；形如 `sb_secret_…` |
| `SUPABASE_URL` | backend/.env | 不进前端 | 后端 admin 客户端的项目 URL（与 VITE_ 值同源，但后端环境独立读取） |
| `JUDGE_CORS_ORIGINS` | backend/.env | 不进前端 | 逗号分隔的 CORS 白名单（含 GH Pages origin 与 localhost:5173） |

- **新一代密钥体系**：`sb_publishable_…` 取代旧 anon key、`sb_secret_…` 取代旧 service_role JWT；新旧不混用，Supabase → Project Settings → API Keys 页面只取新一代两把。
- **.env.example 清单**（仓库只提交占位文件，真实 .env 一律 gitignore）：

`frontend/.env.example`：

```bash
# Supabase（留空 = local 模式，全站保持匿名本地行为）
VITE_SUPABASE_URL=
VITE_SUPABASE_PUBLISHABLE_KEY=
# 判题 API 源：留空 = 同源（本地/单端口模式）；GitHub Pages 填自托管后端 HTTPS 源
VITE_API_BASE=
# 路由模式：hash = GitHub Pages 等静态托管；留空 = history 模式
VITE_ROUTER_MODE=hash
```

`backend/.env.example`：

```bash
# Supabase（留空 = local 模式，不校验 JWT、不写云端）
SUPABASE_URL=
SUPABASE_SECRET_KEY=
# CORS 白名单（逗号分隔），如 https://<user>.github.io,http://localhost:5173
JUDGE_CORS_ORIGINS=
JUDGE_HOST=127.0.0.1
JUDGE_PORT=8000
JUDGE_REPORTS_DIR=reports
JUDGE_MAX_SUBMIT_SECONDS=120
```

### 13.4 双模式判定（authMode）

| 端 | 检测逻辑 | 取值 |
|---|---|---|
| 前端 | `import.meta.env.VITE_SUPABASE_URL && import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY` 均非空 | `authMode = 'supabase'`，初始化 supabase-js；否则 `'local'`，**不初始化** supabase-js |
| 后端 | `SUPABASE_URL && SUPABASE_SECRET_KEY` 均非空 | `supabase_configured = true/false` |

**健康接口附加字段**（§5.3 HealthResponse 原字段不动，附加 1 个向后兼容字段，旧客户端忽略）：

```json
{ "status": "ok", "engine": "ready", "version": "1.0.0", "problem_count": 6, "supabase_configured": true }
```

**两端不一致的降级规则**：以「实际可用能力」取交集——后端 `supabase_configured=false` 时，即使前端带 JWT 也照旧匿名判题不入库；前端启动时拉 `GET /api/health`，若 `supabase_configured=false` 而自身 env 已配，**降级为 local 行为**并在关于页提示配置不一致。

**未配置时**：全站行为 = 第 1–12 节现状（匿名本地、历史走 reports/、无登录 UI）。

**已配置时的差异点清单**：

1. 页头显示登录态（用户名/邮箱 + 退出按钮）；未登录显示「登录」入口。
2. 「提交判题」要求登录：未登录点击 → 唤起登录面板（不判题、不丢代码）。
3. 提交请求带 `Authorization: Bearer <access_token>`；401 → 提示重新登录。
4. 判题结果在后端代写入 Supabase `submissions`（仍双写 `reports/`，便于 CLI/排障）。
5. 历史页与结果详情页数据源切换为 Supabase（RLS 按用户隔离，他人/匿名不可见）。
6. 新增登录页（**路由 `/login`**，合一 tab 切换登录/注册，content-plan 既定方案；Δ2/Δ3 范围：终端风，邮箱密码 + GitHub 两按钮）。

### 13.5 提交流程变更

- **`POST /api/submissions` 的路径、请求体、响应体全部不变**（§5.4 冻结字段不动）；判题仍走 FastAPI 同步流水线（§8.2 不动）。
- 新增可选请求头：`Authorization: Bearer <supabase_access_token>`。
- **supabase 模式流程**：前端带 JWT → 后端用 `SUPABASE_SECRET_KEY` admin 客户端校验（`auth.get_user(jwt)`，无效/缺失 → **401 UNAUTHORIZED**）→ 同步判题 → **判题完成后后端代写 Supabase `submissions`**（`user_id` 取自已校验 JWT，`id` = sid）→ 同时照旧写 `reports/<sid>.json` → 返回 SubmissionResult。
- **JWT 执行口径（裁定）**：请求带 `Authorization: Bearer <access_token>` 时后端校验（无效/过期 → 401 UNAUTHORIZED），校验通过 → 判题 + secret 代写入库；请求不带 Authorization → 匿名判题照常、不入库（保双模式与「两端不一致取交集」降级可用）；「登录后判题」的入口拦截由前端负责，服务端 401 仅兜底。
- **响应附加字段（裁定）**：SubmissionResult 增加 `synced: boolean`——`true` = 本次结果已由 secret 写入 Supabase `submissions`，`false` = 未入库（未登录/未配置/写入失败，判题本身不受影响）；前端结果页「已同步」徽章由此字段驱动。
- **结果入库路径二选一的裁定：经后端 secret 代写**（不做前端直写）。理由：
  1. **服务端权威**：score / verdict / cases 由判题引擎产出，客户端无法伪造入库，历史数据可信；
  2. **单点映射**：file_label / summary（§8.3）在后端一次算好，`reports/` 与 Supabase 行形态一致；
  3. **RLS 收紧**：submissions 对 authenticated 仅开 SELECT，攻击面最小（前端零写权限）；
  4. **密钥边界干净**：secret 只在后端，前端只有 publishable key。
- **入库范围**：仅 `status=finished`；`failed`（SE）不入 Supabase（`reports/` 仍有，便于排障）。
- **ID 单一空间**：Supabase `submissions.id`（text）= sid = `reports/<sid>.json` 文件名主干 = 响应 `submission_id`，三处同值。
- **local 模式**：流程与存储完全保持现状（`reports/` + `GET /api/submissions`）。

### 13.6 GitHub Pages 部署契约

- **构建 env 注入**：`VITE_*` 是**构建期变量**，`npm run build` 时烘焙进 `dist/`，运行时不可切换。
  - 本地构建：`frontend/.env.production` 或 shell 环境变量；
  - GitHub Actions：repo **Secrets / Variables** 注入 build step 的 `env`（`VITE_SUPABASE_URL` / `VITE_SUPABASE_PUBLISHABLE_KEY` / `VITE_API_BASE` / `VITE_ROUTER_MODE`）。
- **hash 路由约定**：`VITE_ROUTER_MODE=hash` → `createWebHashHistory`（`frontend/src/router/index.js` 现状已支持）；对外 URL 形如 `https://<user>.github.io/<repo>/#/problems/P1`；`vite.config.js` 的 `base: './'` 已设，任意子路径可托管。本地开发留空走 history 模式（现状）。
- **VITE_API_BASE**：GitHub Pages 场景必须填自托管 FastAPI 的 HTTPS 源（如 `https://judge.example.com`）；留空 = 同源（本地单端口模式）。
- **后端 CORS**：`JUDGE_CORS_ORIGINS` 白名单须含 GH Pages origin（`https://<user>.github.io`）与本地联调 origin（`http://localhost:5173`、`http://127.0.0.1:5173`）；判题 API 保留 FastAPI 自托管不变。
- **Supabase Auth 配置值**：
  - Site URL = `https://<user>.github.io/<repo>/`
  - Redirect URLs = Site URL + `http://localhost:5173` + `http://127.0.0.1:5173`
- **OAuth 回跳与 hash 路由的冲突规避**：`signInWithOAuth` 的 `redirectTo` 传站点根 URL（**不带 `#/`**）；GitHub 回跳落在 `#access_token=…` 片段，supabase-js（`detectSessionInUrl: true`）吸收令牌并清理 hash，前端在 `onAuthStateChange('SIGNED_IN')` 后 `router.replace('/')` 恢复应用路由。**禁止**把 `#/` 写进 redirectTo / Site URL。

### 13.7 外部配置清单（用户在平台逐条照做，共 11 条）

1. **创建 Supabase 项目**：supabase.com → New project → 记下 `project-ref`（项目 URL 里的随机串）与数据库密码。
2. **建表**：Supabase → SQL Editor → 执行 13.2 全部 DDL（profiles / submissions / 索引 / RLS 策略）。
3. **开启 Email 认证**：Authentication → Providers → Email → Enabled（演示可关闭 `Confirm email`，免邮箱验证步骤）。
4. **创建 GitHub OAuth App**：GitHub → Settings → Developer settings → OAuth Apps → New OAuth App → **Callback URL = `https://<project-ref>.supabase.co/auth/v1/callback`** → 拿到 **Client ID** 与 **Client Secret**。
5. **开启 GitHub Provider**：Supabase → Authentication → Providers → GitHub → Enabled → 填入第 4 步的 Client ID / Client Secret。
6. **配置回跳白名单**：Supabase → Authentication → URL Configuration → **Site URL = `https://<user>.github.io/<repo>/`**；Redirect URLs 添加：Site URL 本身、`http://localhost:5173`、`http://127.0.0.1:5173`。
7. **取新一代密钥**：Supabase → Project Settings → API Keys → 复制 `sb_publishable_…`（前端）与 `sb_secret_…`（后端）。
8. **配置前端 env**：本地 `frontend/.env`（照抄 `.env.example` 填值）；GitHub Pages 场景把 4 个 `VITE_*` 配进 repo Secrets 并注入 Actions build step。
9. **配置后端 env**：`backend/.env` 填 `SUPABASE_URL`、`SUPABASE_SECRET_KEY`、`JUDGE_CORS_ORIGINS`（含 GH Pages origin）。
10. **开启 GitHub Pages**：仓库 → Settings → Pages → 选择部署来源（Actions 工作流或分支）；Actions 场景确认 build 命令与 `dist/` 产物上传。
11. **验收链路**：注册邮箱账号 → GitHub 登录回跳成功 → 提交一次判题 → Supabase → Table Editor 看到 `submissions` 行（user_id 正确）→ 退出登录后历史页不可见该记录（RLS 生效）→ 清空前端 env 后回退 local 模式可用。

### 13.8 Δ1 非目标

- 不做角色/权限分级与管理后台（只有「本人数据」一档）。
- 不做手机/短信登录、微信等其他 OAuth provider（仅 邮箱密码 + GitHub）。
- 不做密码找回/邮箱验证流程的自定义（用 Supabase 默认邮件流）。
- **secret 不进前端、不进仓库、不进日志**（CI 日志同样禁止打印）。
- 不做两模式历史互通迁移（本地 `reports/` 与云端 `submissions` 互不导入、互不同步）。
- 不做用户主页 / 排行榜 / 关注 / 组织多租户。
- 不在 Supabase 跑判题（判题永远在自托管 FastAPI，Supabase 只做认证与历史存储）。
- 不做 Supabase Edge Functions / 触发器同步（入库只有后端代写一条路径）。

