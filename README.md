# CodeJudge 在线代码评测台

基于 `requirements.md` 实现的本地在线评测（Online Judge）工具站：**真实判题引擎**（编译 → 限时运行 → 比对 → 计分）+ Web 界面（**终端风格**）。内置 P1–P6 六道题、45 组测试用例，支持 ACM/OI 双计分模式与 AC/PE/WA/TLE/RE/CE/SE 七种判定，判题在本机执行、数据不出机。

**提交形态**：单文件源码提交 + **多源码文件上传提交评测**（可一次上传 Makefile / 多个 .cpp/.h，整套构建判题；P6 依赖检查器即 make 多文件题）。

**用户系统**：Supabase 认证（邮箱 + GitHub OAuth）与提交历史云同步（按账号 RLS 隔离），**双模式**——未配置云服务时本地匿名可用，配置后登录判题、历史随账号走。

**评分链路（supabase 模式）**：**UAPI 执行 + AI 语义评判 + 人工复核**异步流——**显式样例全部通过才可提交**（前端自测 + judge 前置强制校验），UAPI 真跑拿 stdout/stderr/状态，AI 基于运行数据评分；低分/无法可靠判断转人工复核，全程 **Supabase Realtime 推送**（零轮询零刷新）。

## 快速开始

### 环境要求
- Python 3.13+（后端与判题引擎）
- Node.js 18+（前端构建，实测 v22.22.2）
- g++（C++17）与 make（P6 多文件构建）；Windows 下为 MSYS2 工具链（本机实测 `D:\msys64\ucrt64\bin\g++.exe`、`D:\msys64\usr\bin\make.exe`）

### 启动（单端口演示）

```bash
# 1. 后端依赖
pip install -r backend/requirements.txt

# 2. 前端构建（首次或前端改动后）
cd frontend && npm install && npm run build && cd ..

# 3. 启动服务（frontend/dist 由 FastAPI 托管，SPA history 回退）
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

打开 <http://127.0.0.1:8000> 即为完整站点（单端口：页面 + `/api/*` 同源）。

**开发联调**：后端加 `--reload`；另开 `cd frontend && npm run dev`（:5173，`/api` 已代理到 :8000）。

> 本机若有 HTTP 代理，curl 自测请加 `--noproxy 127.0.0.1`。

### 环境变量

| 变量 | 默认 | 说明 |
|---|---|---|
| `JUDGE_HOST` | `127.0.0.1` | 监听地址 |
| `JUDGE_PORT` | `8000` | 端口 |
| `JUDGE_REPORTS_DIR` | `reports/` | 报告与提交历史目录 |
| `JUDGE_MAX_SUBMIT_SECONDS` | `120` | 整单判题硬上限（超时返回 408） |

## 判题 CLI

```bash
python judge.py list                          # 题目与用例一览
python judge.py run P1 examples/P1_ac.cpp     # 评测单个提交
python judge.py run P1 examples/P1_ac.cpp --mode acm   # 覆盖计分模式
python judge.py gen P1 --ref reference/P1.cpp # 参考实现刷新 .out
python judge.py import-samples exercise/P1-shipping.md # 题面抽样例
python judge.py init P7 --type oi             # 新题骨架
```

退出码：`0` 全 AC / `1` 非 AC / `2` 基础设施错误（便于 CI）。

## 站点地图

| 路由 | 用途 |
|---|---|
| `/` | 题目列表（P1–P6） |
| `/problems/:pid` | 题面 + 在线写代码（单文件 / **多文件上传**）+ 提交判题 |
| `/submissions/:sid` | 判题结果（得分横幅 + 逐用例表格 + CE/RE 面板 + 源码回显） |
| `/submissions` | 提交历史（倒序，可按题目筛选） |
| `/about` | 使用说明（判定含义表、ACM/OI 计分、CLI、本地处理声明） |

## 多文件提交评测

- **单文件**（原有能力）：textarea 编辑或上传单个 .cpp，按 `source_code` 提交。
- **多文件**（新增）：题目详情页切「多文件上传」标签——多选上传 / 新建文件 / 逐个编辑 / 删除，按 `files[]` 整套提交。g++ 题会把所有 `.cpp` 一并编译（`.h` 走 `#include`）；make 题（如 P6）执行 `make <target>` 构建。
- **make 题规则**：必须多文件提交且包含 `Makefile`（单文件提交会返回 400 并提示）；P6 可用「示例代码」一键载入 `P6_make`（Makefile + inspector.cpp + util.h，预期 AC）。
- **限制**：最多 20 个文件、单文件 64K 字符、合计 256K 字符；文件名仅限字母、数字、`_ . -`（拒绝路径穿越）。

## AI 评分 + 人工复核（异步流）

supabase 模式的提交走 **Edge Function 异步评分**（本地模式仍为 FastAPI 同步真判）：

```text
用户提交 → judge 函数前置同步校验（UAPI 逐个跑显式样例）
           ├─ 任一失败 → 400，不落库（「存在未通过的显式测试样例，不能提交」）
           └─ 全部通过 → 插入 judging 记录，立即返回 202
↓ (EdgeRuntime.waitUntil，后台异步)
「代码 + 题目 + 真实运行结果」交给 AI 评分（conclusive 语义）
├─ conclusive 且分数达标 → status='ai_scored'（Realtime 推送 AI 得分与反馈）
└─ conclusive=false / 低分 / AI 失败 → 入 human_review_queue，status='pending_review'
        ↓ 管理员经 admin-review 裁决（pass | fail | bad_data）
   status='human_reviewed_pass | human_reviewed_fail'（bad_data 退回重审）
```

- **双层校验**：OneCompiler 嵌入式编辑器内逐样例测试（注入 stdin 触发运行）/「运行样例」自测（全部通过才启用提交按钮）+ judge 后端强制复验（任一失败 400 不落库）。
- **备用通道**：样例测试 ≥10 次仍不过 → 解锁「备用通道提交」（`force_submit`），AI 参考评分 + **强制人工复核**，防止用户卡死在样例门禁。
- **三层分工**：UAPI 出确定性执行结果（4 积分/次，断网沙盒），AI 基于真实运行数据做语义评判，人工只在低分/无法可靠判断/坏数据时介入。
- **前端零轮询**：结果页订阅 `postgres_changes`（RLS 生效）；结果页含「真实运行数据（UAPI）」表。
- **状态机**：`judging → ai_scored | pending_review → human_reviewed_*`（历史列表显示状态徽章）。
- **人工复核**：`/admin-review`（reviewers 白名单），队列带优先级（分数 <40 / AI 失败 / 备用通道 = 高优先），裁决支持「数据问题（退回重审）」。
- **配置**（Edge Function secrets）：`UAPI_ACCESS_TOKEN`（uapis.cn）、`AI_API_KEY`/`AI_API_URL`/`AI_MODEL`（OpenAI 兼容）、`AI_SCORE_THRESHOLD`（默认 60）。多文件提交自动内联合并后实跑。
- **部署与迁移**：见 `supabase/README.md`（迁移 0002–0004、`supabase functions deploy judge admin-review`、密钥与复核人配置）。

## 用户系统（Supabase）

邮箱 + GitHub OAuth 注册/登录，判题历史入 Supabase（按账号 RLS 隔离，换机可查）。**双模式**：不配置云服务时全站行为与旧版一致（本地匿名、历史存 `reports/`）；配置后登录判题、历史入账号。

### 密钥体系（新一代 publishable / secret）

| 变量 | 位置 | 说明 |
|---|---|---|
| `VITE_SUPABASE_URL` | `frontend/.env` | Supabase 项目 URL |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | `frontend/.env` | `sb_publishable_…`，可进前端产物 |
| `SUPABASE_URL` | `backend/.env` | 同上项目 URL |
| `SUPABASE_SECRET_KEY` | `backend/.env` | `sb_secret_…`，**仅后端**（校验 JWT + 管理端代写入库）。进产物/仓库 = 全库失守，泄露即轮换 |
| `JUDGE_CORS_ORIGINS` | `backend/.env` | 逗号分隔白名单；空=不限制（本地） |

两端均有 `.env.example` 占位模板；真实 `.env` 已被 `.gitignore`。不与旧 anon/service_role 密钥混用。

### 外部配置（11 步）与人工验收（6 步）

完整步骤见 `docs/site-spec.md` §13.7（Supabase 建项目 → SQL 建表（profiles/submissions + RLS）→ 开 Email → GitHub OAuth App（Callback=`https://<project-ref>.supabase.co/auth/v1/callback`）→ Supabase GitHub Provider → Site URL/Redirect URLs → 取两把密钥 → 配两端 `.env` → 开 GitHub Pages → 验收）。郝收录整理的控制台核对表在 `docs/prelaunch-checklist.md` Δ4 小节。

配置完成后按 6 步人工验收：①邮箱注册登录 ②GitHub 登录回跳 ③登录后提交 `synced:true` ④Supabase Table Editor 看到行且 user_id 正确 ⑤换第二账号验证 RLS 隔离 ⑥清 env 重建回退本地模式可用。

## GitHub Pages 部署

流水线已内置（`.github/workflows/deploy-pages.yml`）：push `main` 自动构建并发布。启用步骤：

1. **开启 Pages**：仓库 Settings → Pages → Build and deployment → Source 选 **GitHub Actions**（一次性）。
2. **配置 Secrets**：Settings → Secrets and variables → Actions，按需添加——
   | Secret | 必填 | 说明 |
   |---|---|---|
   | `VITE_SUPABASE_URL` | 云模式必填 | `https://<project-ref>.supabase.co` |
   | `VITE_SUPABASE_PUBLISHABLE_KEY` | 云模式必填 | `sb_publishable_…` |
   | `VITE_API_BASE` | 选填 | 自托管 FastAPI 源（不带 `/api` 后缀）；不配则纯 Supabase 模式 |
3. **推送触发**：`git push`（或 Actions 页手动 Run workflow）→ 站点发布到 `https://lmdlg000.github.io/codejudge/`。
4. **Supabase 回跳配置**：Site URL = `https://lmdlg000.github.io/codejudge/`，Redirect URLs 追加同值 + `http://localhost:5173`（**严禁写 `#/`**，OAuth 回跳靠 `detectSessionInUrl` 吸收令牌）。
5. **配套部署**（云模式完整能力）：按 `supabase/README.md` 部署 `judge` / `admin-review` Edge Functions 并配 `UAPI_ACCESS_TOKEN` 等 secrets。

构建内置保障：`base:'./'`（任意子路径可托管）、`VITE_ROUTER_MODE=hash`（静态托管无 history 回退）、题库静态打包（无 FastAPI 也能出题面）。未配 Supabase secrets 时站点降级为只读演示（题目可看，提交需云模式）。

## 判定与计分

| 判定 | 含义 | 判定 | 含义 |
|---|---|---|---|
| AC | 答案正确 | TLE | 超出时间限制 |
| PE | 仅空白差异 | RE | 运行时错误（Windows 下降级为「进程非 0 退出码」） |
| WA | 答案错误（提示首处差异行） | CE | 编译错误（附编译器输出） |
| SE | 系统错误（判题设施异常） | | |

- **OI**：按用例权重折算 `Σ 通过权重 / Σ 总权重 × 满分`
- **ACM**：全 AC 得满分，否则 0 分（附加权部分得分仅供参考）
- 得分横幅固定句式：`通过 x/y · 通过率 n% · 得分 s/m`

## 目录结构

```
codejudge/
├── judge.py            # CLI 入口（run/gen/import-samples/list/init）
├── core/               # 判题引擎九模块（problem/builder/runner/comparator/scorer/…）
├── backend/            # FastAPI 服务（7 个 /api 接口，契约见 docs/site-spec.md）
├── frontend/           # Vue 3 + Vite 前端（npm run build → dist/）
├── problems/P1–P6/     # 题库（problem.json + statement.md + tests/ + reference/）
├── examples/           # 六条判定路径演示提交（P1_ac/wa/pe/tle/re/ce + P1_make/）
├── exercise/           # 题面 Markdown 源（import-samples 输入）
├── reports/            # 判题报告 JSON（即提交历史存储）
├── scripts/            # 题库核对与接口冒烟脚本
└── docs/               # 规格卡、内容策划、设计规范、上线检查表
```

## 养护与更新说明

**新增题目**：`python judge.py init P7 --type oi` 建骨架 → 写 `statement.md`（样例块用 `## 样例输入` / `## 样例输出` + 代码围栏，importer 可解析）→ 手放 `tests/*.in/.out` → `python judge.py gen P7 --ref reference/P7.cpp` 校验/刷新期望输出。`problem.json` 可选 `topic` / `difficulty` 键（首页卡片显示）。

**新增用例**（三条路径等价，都落 `tests/`）：① 手放 `42.in` + `42.out`（可加 `42.json` 覆盖 weight/time_ms/note）；② `gen` 批量刷新；③ `import-samples` 从题面抽取。

**改文案**：以 `docs/content-plan.md` 为准改对应组件；**改视觉**：终端主题令牌在 `frontend/src/styles/tokens.css`（全站等宽 + 荧光绿主色 + ANSI 判定七色，按钮 `[ ]` 括号、扫描线在 `global.css`）；`docs/design-spec.md` 为旧版浅色规范，仅作组件结构参考；**改接口**：先改 `docs/site-spec.md` 契约（唯一事实来源），再同步 `backend/app/schemas/api.py` 与前端 `api/types.js`。

**历史与报告**：`reports/*.json` 即提交历史，删文件即删历史；`latest.json` 为最近一次报告副本。

**重新构建前端后**无需重启后端以外的额外配置，刷新页面即可（静态资源带一年 immutable 缓存，HTML no-cache）。

## 已知风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| Windows 下信号翻译降级 | RE 只报「进程非 0 退出码」，RE/TLE 精度弱于 POSIX | 文案已内置降级说明；POSIX 分支保留，Linux/macOS 部署时自动增强 |
| 无沙箱加固（cgroup/seccomp/nsjail） | 恶意代码可越界 | **仅限本机自用，严禁公网暴露**；公网部署须先补沙箱（见 requirements.md 第八节） |
| 单并发 + 120s 整单上限 | 第二单返回 429、长单 408 | 本地单机有意取舍；可调 `JUDGE_MAX_SUBMIT_SECONDS` |
| TLE 单用例墙钟约 2.2s | 耗时含终止开销 | 有意为之（1.5× 时限 + taskkill）；报文已是真实墙钟 |
| P6（make 多文件）单文件提交被拒 | 400 提示改用多文件 | 有意为之：make 构建必须有 Makefile；多文件提交已开放，`P6_make` 示例一键载入 |
| 「看输出对比」未提供 | 逐用例表无 diff 面板 | P1 遗留；WA 提示已含首处差异行，契约如增 expected/actual 字段可开 |
| 真实 Supabase/OAuth 未联调 | 云链路仅 mock 验证过 | 配好 11 步外部配置后按 6 步人工验收（见上「用户系统」节） |
| 云端入库 best-effort 单次写 | Supabase 抖动时该单 `synced:false` | 本地 `reports/` 恒有兜底；如需补传可后续加 CLI 对账 |
| supabase-js 进主包（+241kB） | 首屏包偏大（gzip ~107kB） | 未超阈值；后续可手动分包 |
| 两端 Supabase 配置不一致 | 「登录了却查不到历史」困惑 | 取交集自动降级 + 关于页/提示条说明；部署时两端 env 同配 |

## 文档索引

| 文档 | 内容 |
|---|---|
| `docs/site-spec.md` | 站点规格卡与接口契约（唯一事实来源） |
| `docs/content-plan.md` | 逐页文案、SEO、P1–P6 题面 |
| `docs/design-spec.md` | 设计规范与 tokens.css |
| `docs/prelaunch-checklist.md` | G3 上线前检查表（74 PASS / 0 FAIL / 5 N-A） |
| `docs/e2e-verify-notes.md` | 集成验证记录 |
| `docs/backend-run-notes.md` | 后端运行说明详版 |
