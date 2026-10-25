# 后端运行说明（供 README 汇编 · backend-engineer 交付）

> 适用环境：Windows（本机实测 win32 + MSYS2）；POSIX 分支已保留但未在本机验证。
> 范围：判题引擎 `core/` + CLI `judge.py` + FastAPI 服务 `backend/`。前端部分见前端交付。

## 1. 环境要求

| 依赖 | 版本要求 | 本机实测 | 说明 |
|---|---|---|---|
| Python | 3.10+（用到 `tomllib` 则 3.11+，实测 3.13 无碍） | 3.13.14 | 引擎与服务同进程 |
| g++ | 支持 `-std=c++17` | MSYS2 g++ 16.2.0（`D:\msys64\ucrt64\bin`） | 必须在 PATH（`where g++` 能查到） |
| make | GNU Make | 4.4.1（`D:\msys64\usr\bin`） | P6/多文件 make 构建需要；在 PATH |
| fastapi / uvicorn / pydantic | 见 `backend/requirements.txt` | fastapi 0.162 / uvicorn 0.54 / pydantic 2.14 | 仅后端需要；引擎纯标准库 |

```bash
# 项目根目录执行
python -m pip install -r backend/requirements.txt
```

## 2. 启动

```bash
# 开发联调（后端 :8000；前端 npm run dev :5173 会把 /api 代理过来）
python -m uvicorn backend.app.main:app --reload --port 8000

# 单端口演示（先构建前端，dist/ 由 FastAPI 托管 + history 回退）
cd frontend && npm run build && cd ..
python -m uvicorn backend.app.main:app --port 8000
# 打开 http://127.0.0.1:8000
```

- **必须从项目根 `codejudge/` 启动**（`backend.app.main`、`core`、`judge` 均按项目根导入）。
- `frontend/dist` 不存在时服务不崩溃：非 `/api` 路径返回「后端已就绪」提示页。
- 健康检查：`GET http://127.0.0.1:8000/api/health` → `{"status":"ok","engine":"ready",...}`。

## 3. 环境变量（均可省略）

| 变量名 | 用途 | 默认 |
|---|---|---|
| `JUDGE_HOST` | 监听地址 | `127.0.0.1` |
| `JUDGE_PORT` | 监听端口 | `8000` |
| `JUDGE_REPORTS_DIR` | 报告目录（相对项目根或绝对路径） | `reports/` |
| `JUDGE_MAX_SUBMIT_SECONDS` | 整单判题硬上限（超时 → 408） | `120` |

## 4. CLI（不依赖 FastAPI）

```bash
python judge.py list                    # 题目与用例（权重/时限/备注）
python judge.py run P1 examples/P1_ac.cpp        # 评测单文件提交
python judge.py run P6 examples/P1_make          # 多文件 make 工程（target=inspector）
python judge.py run P3 solution.cpp --mode oi    # 覆盖计分模式
python judge.py gen P1 --ref reference/P1.cpp    # 用参考实现刷 .out（原子写）
python judge.py import-samples exercise/P1-shipping.md --target problems/P1
python judge.py init P7 --type oi                # 新题骨架
```

返回码：`0` 全 AC；`1` 非 AC；`2` 基础设施错误。报告写入 `reports/<sid>.json`，`reports/latest.json` 恒为最新副本。

## 5. 判题语义（前后端/CLI 一致）

- 判定顺序冻结：**CE（构建失败→全用例 CE 跳过执行）→ 逐用例 TLE → RE → 比对（AC/PE/WA）**。
- 计分：`OI = Σ通过权重/Σ总权重×满分`；`ACM = 全 AC 满分否则 0`（`partial_score` 两种模式都给）。
- 总判定统一按 ACM 合成规则（全 AC→AC，否则首个非 AC；CE→CE；流水线崩→SE）。
- 同步判题：POST 一次请求内跑完全流水线；全局单并发，第 2 单立即 429 `JUDGE_BUSY`；整单 120s 硬上限 → 408 `JUDGE_TIMEOUT`。
- compare_mode 默认 `trim`（`\r\n` 归一 + 末尾多余换行无害）；PE = token 相等但文本不等。

## 6. Windows 降级（已知差异，非缺陷）

- **RE 判定**：不细分信号，`signal=null`，文案为「进程非 0 退出码（exit code N）：Windows 下不细分信号，请看 stderr 定位。」（访问违例常见 exit code 3221225477 = 0xC0000005）。
- **超时终止**：`taskkill /F /T`（进程树）+ `Popen.kill`；墙钟超时 = 时限 ×1.5；`resource.setrlimit` 仅 POSIX 生效（CPU/AS/FSIZE）。
- 构建产物可能带 `.exe` 后缀，引擎已兼容查找。

## 7. 常见问题

| 现象 | 原因与处理 |
|---|---|
| `/api/health` 返回 503 `ENGINE_UNAVAILABLE` | `g++`/`make` 不在 PATH，或 `problems/` 数据损坏（缺 `.out`、problem.json 非法）。看 message 具体原因 |
| 提交返回 429 `JUDGE_BUSY` | 判题单并发，等当前单完成再交（整单最长约 2 分钟） |
| 提交返回 408 `JUDGE_TIMEOUT` | 程序死循环/过慢；`reports/` 里会有 `status=failed` 的记录 |
| 提交返回 413 | 单文件 >65536 字符 / files 合计 >262144 / files >20 项 |
| 全部用例 CE 但代码「看起来没错」 | 展开编译器输出（末 200 行）看首条 `error:`；确认提交文件名合法且 g++ 可编译该文件 |
| P6 在线提交被拒（400） | P6/make 题支持**在线多文件提交**（`files[]` 须含 `Makefile` + 源文件，实测 AC）；单文件提交 → 400「该题为多文件 make 构建，请用多文件提交（需包含 Makefile 与源文件）」；多文件缺 `Makefile` → 400「多文件 make 构建缺少 Makefile，请在提交文件中包含 Makefile」。CLI 路径不变：`python judge.py run P6 <目录>` |
| 本机有 HTTP 代理导致脚本连不上 127.0.0.1 | 给 curl 加 `--noproxy 127.0.0.1`，或 httpx 用 `trust_env=False`（自测脚本已内置） |
| 报告/历史在哪 | `reports/<sid>.json` 即数据库；删文件即删历史；`latest.json` 是最新副本 |

## 8. 自测入口（可复跑）

```bash
python scripts/verify_tests.py    # 题库数据核对（30 组样例对题面 + 12 组隐藏用手算值）
python scripts/smoke_api.py       # API 冒烟 50 项（需先启动 uvicorn :8000）
python scripts/test_multifile_scenarios.py  # 多文件/make 提交 18 情景（需先启动 uvicorn :8000）
python backend/tests/test_contract.py       # 契约测试 7 组（进程内 TestClient，无需启动）
python backend/tests/test_supabase_flow.py  # Supabase 集成流 18 项（mock HTTP，无需真实云）
```

## 9. 安全边界（本地工具站，仅限本机自用）

- 提交代码在本机真实编译执行：仅 墙钟超时 + 输出上限（stdout/stderr 各 4MB）+ POSIX setrlimit；**无沙箱加固，绝不暴露公网**。
- 文件名白名单 `^[A-Za-z0-9_.-]{1,64}$`（拒绝 `.`/`..`/路径分隔符）；构建命令 `shell=False`，`{bin}`/`{src}` 只代入服务端生成的白名单文件名。
- 本地模式无鉴权面：历史共享 `reports/`；启用 Supabase 后历史按用户 RLS 隔离（见第 10 节）。
- 敏感信息：源码只落 `reports/`（本机）；服务日志仅记录路由、状态码与错误类型（不记 token/密钥/源码）。

## 10. 用户系统（后端侧）（Δ3，Supabase）

> 详表见 `docs/site-spec.md` §13。本节只讲后端怎么开、密钥放哪。

### 10.1 开关与配置

- **local 模式（默认）**：`backend/.env` 不配 Supabase（或留空）→ 行为与 Δ 前完全一致；`GET /api/health` 返回 `supabase_configured: false`。
- **supabase 模式**：复制 `backend/.env.example` → `backend/.env`，填 `SUPABASE_URL` 与 `SUPABASE_SECRET_KEY`（均非空才算已配置）→ 重启后端，health 应显示 `supabase_configured: true`。
- 其余变量：`JUDGE_CORS_ORIGINS`（逗号分隔白名单，须含 GH Pages origin 与 `http://localhost:5173`；留空=不限制）。

### 10.2 提交语义（G1 执行口径）

| 请求 | 行为 |
|---|---|
| `POST /api/submissions` 不带 Authorization | 匿名判题照常，**不入库**，响应 `synced: false` |
| 带 `Authorization: Bearer <access_token>`，token 无效/过期/格式非法 | **401 UNAUTHORIZED**（统一错误体，message「请先登录（登录状态可能已过期）」） |
| 带有效 token | 后端校验（`GET {SUPABASE_URL}/auth/v1/user`，5s 超时）→ 判题 → secret 代写 `submissions` → 响应 `synced: true` |
| 入库失败（网络/RLS/超限） | **不影响判题**：仍 201，`synced: false`，仅服务端 warning 日志 |
| 后端未配置 Supabase 但前端带了 token | 降级为匿名判题（13.4 交集规则），`synced: false`，不 401 |

- **ID 单一空间**：响应 `submission_id` = `reports/<sid>.json` = Supabase `submissions.id`，三处同值。
- 响应新增字段 `synced: boolean`（SubmissionResult）；`GET /api/health` 新增 `supabase_configured: boolean`；均为向后兼容追加。
- 仅 `status=finished` 的结果入库；SE/超时失败单只在本地 `reports/`。

### 10.3 🔴 密钥安全红线

- **`sb_secret_…` 只能出现在 `backend/.env`（gitignore 已覆盖，绝不入库）**。泄漏 = Supabase 全库失守（管理端绕过 RLS），必须立刻去 Project Settings → API Keys 轮换。
- 前端只用 `sb_publishable_…`（`VITE_SUPABASE_PUBLISHABLE_KEY`），**可**进构建产物；两把钥匙严禁混用，也不要沿用旧体系的 `anon` / `service_role` JWT。
- secret 不进日志、不进报错文案、不进 reports/；自检：`grep -r "sb_secret_" --exclude-dir=node_modules --exclude-dir=.git .` 应只命中 `.env.example` 的占位说明与测试里的假值。
- `.env` 丢失无所谓（重配即可）；`.env` 泄漏很有所谓（先轮换再排查）。
