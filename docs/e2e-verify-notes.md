# E2E 验证记录（Gate G3 证据卷）

> 执行人：deploy-seo-engineer（郝收录）｜日期：2026-10-24
> 用途：`prelaunch-checklist.md` 各项结论的原始证据（命令 + 关键输出摘要），供交付汇编引用与事后复跑。
> 约定：所有 HTTP 请求均加 `--noproxy 127.0.0.1`（本机 HTTP 代理会劫持 127.0.0.1）；Python 侧用 `urllib.request.build_opener(ProxyHandler({}))` 绕过代理。

---

## 1. 复跑入口（任何人 5 分钟可重现）

```bash
# 0) 环境：Python 3.13 / g++ 在 PATH / make 在 PATH
cd D:/Storage/Projects/260717/codejudge

# 1) 构建前端（本轮共执行 2 次：基线 + SEO 修复后）
cd frontend && npm run build && cd ..

# 2) 起单端口服务
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# 3) 自测三件套
python scripts/verify_tests.py        # 题库数据核对
python backend/tests/test_contract.py # 契约 7 组（进程内，不依赖服务）
python scripts/smoke_api.py           # API 冒烟 47 项（需服务在 :8000）

# 4) CLI 对照
python judge.py run P1 examples/P1_ac.cpp
```

本轮实测结果：`verify_tests.py 全部核对通过`｜`test_contract.py 7/7 通过`｜`smoke_api.py 47 项/失败 0`。

---

## 2. 单端口集成验证

### 2.1 静态托管与 SPA 回退

```
GET /                       -> 200 text/html 737B   <title>CodeJudge 在线代码评测台 · P1–P6 题库</title>
GET /problems/P1            -> 200  (index.html, id="app")
GET /problems/P2..P6        -> 200  各页同上
GET /submissions            -> 200  (index.html)
GET /submissions/<sid>      -> 200  (index.html) 深链直达
GET /about                  -> 200  (index.html)
GET /no-such-page           -> 200  (index.html) → 前端路由显示 404 页
GET /assets/index-Dfop5saq.js -> 200 text/javascript 108997B
GET /favicon.svg            -> 200 image/svg+xml
```

### 2.2 /api 优先匹配（不会被静态回退吞掉）

```
GET /api/problems/P9 -> 404 application/json
  {"error":{"code":"PROBLEM_NOT_FOUND","message":"题目不存在：P9"}}
GET /api/nope        -> 404 application/json
  {"error":{"code":"PROBLEM_NOT_FOUND","message":"Not Found"}}
```

> 备注：`/api/nope` 这类「未知 API 路径」也归入 `PROBLEM_NOT_FOUND` 码，属统一 404 兜底实现；契约只冻结了各端点自己的 404 码，不构成违约（观察项，不阻塞）。

### 2.3 传输压缩与缓存头（本轮新增，优化前后对比的来源）

```
# 优化前（基线）
GET /assets/index-*.js           -> content-length: 108989，无 content-encoding，无 cache-control

# 优化后（GZipMiddleware + 资产缓存中间件）
GET /assets/index-*.js (Accept-Encoding: gzip)
  -> 200, content-encoding: gzip, cache-control: public, max-age=31536000, immutable
  -> 实际下载 42,855 B（明文 108,997 B，-60.7%）
GET /
  -> cache-control: no-cache
```

---

## 3. E2E 判题动线（真提交真判题）

### 3.1 AC 主线（复跑输出摘要）

```
POST /api/submissions  {"problem_id":"P1","source_code":<examples/P1_ac.cpp>,"filename":"main.cpp"}
-> 201
submission_id: 20261024-181039-P1-46f1
status: finished | verdict: AC | mode: oi
summary: {"total": 8, "passed": 8, "pass_rate": 1.0, "score": 100.0, "max_score": 100.0, "partial_score": 100.0}
cases: 1.in AC 256ms … 5.in AC 179ms / hidden-1..3 AC（8/8，权重各 1.0）
横幅数据: 通过 8/8 · 通过率 100% · 得分 100/100
files 回显: [("main.cpp", 319 字符)]
reports/20261024-181039-P1-46f1.json  -> 落盘存在
```

### 3.2 历史与回查

```
GET /api/submissions -> 200 {"total": 20, items 倒序}
首行: 20261024-181039-P1-46f1 | P1 | AC | 通过8/8 得分100.0/100.0 | file_label=main.cpp | mode=oi | 2026-10-24T18:10:39
GET /api/submissions/20261024-181039-P1-46f1 -> 200 与 POST 响应同构（verdict/summary 一致）
GET /api/submissions/not-a-real-sid -> 404 SUBMISSION_NOT_FOUND「找不到该次提交：not-a-real-sid」
```

历史列契约核对：`SubmissionSummary` 含 `submission_id/problem_id/problem_title/file_label/created_at/mode/verdict/summary`，前端 `HistoryTable.vue` 列头「时间｜题目｜提交文件｜判定｜通过｜得分｜操作」逐列对上；`file_label` 缺失时显示「—」。

### 3.3 CLI 对照（与网页同句式）

```
$ python judge.py run P1 examples/P1_ac.cpp
（逐用例表 8 行全 AC）
通过 8/8 · 通过率 100% · 得分 100/100
报告已写入 D:\Storage\Projects\260717\codejudge\reports\20261024-180355-P1-46f1.json
# 返回码 0
```

### 3.4 错误与拒绝路径

| 场景 | 请求 | 响应 | 结论 |
|---|---|---|---|
| 空源码 | `source_code:""` | `400 VALIDATION_ERROR「提交内容不合法，请检查后重试：源码为空」` | PASS |
| source_code/files 都没给 | 仅 problem_id | `400「…source_code 与 files 必须恰好给其一」` | PASS |
| 字段名用错（探测） | `source`（非契约名） | `400「…必须恰好给其一」` | 契约名是 `source_code`，API 拒绝符合预期 |
| P6 在线提交 | `problem_id:"P6"` | `400 {"code":"VALIDATION_ERROR","message":"本期暂不开放在线提交"}` | PASS（message 逐字） |
| 未知题目提交 | `problem_id:"P9"` | `404 PROBLEM_NOT_FOUND「题目不存在：P9」` | PASS |
| 并发第二单 | 双线程同时 POST | A: `201`（3.5s）；B: `429 JUDGE_BUSY「判题进行中，请稍候重试」`（0.0s） | PASS |
| 整单硬上限 | 8001 实例 `JUDGE_MAX_SUBMIT_SECONDS=2` + P1_tle.cpp | `408 JUDGE_TIMEOUT「判题超时，请检查死循环后重试」`（2.1s） | PASS（与默认 120s 同代码路径） |
| examples 缺参 | `GET /api/examples` | `400 VALIDATION_ERROR「…problem_id 必填」` | PASS |
| examples 未知题 | `GET /api/examples?problem_id=P9` | `404 PROBLEM_NOT_FOUND` | PASS |

### 3.5 CE / RE 判定语义

```
POST examples/P1_ce.cpp -> 201 verdict=CE
  8/8 用例 verdict=CE（构建失败→全用例 CE 跳过执行，判定顺序冻结）
  build_log: 15 行，含 error: 首条

POST examples/P1_re.cpp -> 201 verdict=RE（sid 20261024-180735-P1-375d）
  1.in RE | signal: None | exit_code: 3221225477
  message: 进程非 0 退出码（exit code 3221225477）：Windows 下不细分信号，请看 stderr 定位。
  （与 backend-run-notes §6 Windows 降级文案逐字一致）
```

### 3.6 「下载报告 JSON」按钮

- 实现（`SubmissionDetail.vue`）：`downloadJson()` 把 `GET /api/submissions/:sid` 响应 `JSON.stringify(data, null, 2)` 封装为 `Blob`，`a.download = ${submission_id}.json`——不新增接口。
- 可验证性证据：响应体经 `json.dumps → json.loads` 往返无损（Python 实测），序列化路径与按钮一致；点击行为属浏览器事件，以源码断言为准（无浏览器环境）。

---

## 4. 死链与锚点矩阵

### 4.1 站内路由（HTTP 实测全 200）

| 链接位 | 目标 | 实测 |
|---|---|---|
| 页头 Logo / 导航「题目列表」 | `/` | 200 |
| 页头导航「提交历史」 | `/submissions` | 200 |
| 页头导航「关于」 | `/about` | 200 |
| 页脚「关于」「使用说明」 | `/about` | 200 |
| 首页 6 张题卡 | `/problems/P1`…`/problems/P6` | 各 200 |
| 历史行 / 结果页深链 | `/submissions/:sid` | 200 |
| 404 页「回到题目列表」 | `/`（router.push） | 200 |
| P6 提交区「查看 CLI 用法」 | `/about#cli` | 200 + 锚点存在 |

### 4.2 锚点（构建产物断言）

| 锚点 | 落点元素 | 构建产物证据 |
|---|---|---|
| `/about#verdicts` | `<section id="verdicts">` 判定含义表 | `About-*.js` 含 `id:"verdicts"` |
| `/about#cli` | `<section id="cli">` CLI 常用命令 | `About-*.js` 含 `id:"cli"` |
| `/about#privacy` | `<section id="privacy">` 本地处理声明 | `About-*.js` 含 `id:"privacy"` |

> 任务书提到的 `#quickstart`：content-plan 冻结锚点为 `#cli`（区块 4），无 `#quickstart` 定义——按 content-plan 执行，`#cli` 即「快速上手/CLI」落点。router `scrollBehavior` 支持 `to.hash` 定位（`el: to.hash, top: 72`）。

结论：**全站内链与锚点无死链**。

---

## 5. 性能数字

### 5.1 构建产物

| 文件 | 原始 | gzip（vite 报告） |
|---|---|---|
| `index-*.js`（公共壳） | 108,997 B | 43.11 kB |
| `ProblemDetail-*.js`（最大 chunk） | 116,137 B | 51.84 kB |
| `SubmissionDetail-*.js` | 13,317 B | 4.93 kB |
| `About-*.js` | 13,456 B | 5.19 kB |
| `index-*.css` | 11,233 B | 3.16 kB |
| **dist 合计** | **323,525 B / 29 文件** | — |

- 最大 chunk 116 kB < 500 kB 阈值 → 无需拆分/缓解。
- 首屏请求 4 个：`index.html`(737B) + `index-*.css` + `index-*.js` + `favicon.svg`(293B)；题面/结果/历史/关于 chunk 路由懒加载。
- 无 >500kB 单 chunk、无阻塞第三方资源（零外链，离线可用）。

### 5.2 优化前后（本轮唯一优化动作：传输层）

| 指标 | 前 | 后 |
|---|---|---|
| index.js 传输 | 108,997 B 明文 | 42,855 B gzip（**-60.7%**） |
| 资产缓存头 | 无 | `public, max-age=31536000, immutable` |
| HTML 缓存头 | 无 | `no-cache` |

---

## 6. SEO 技术项核对

### 6.1 逐页 TDK（与 content-plan §2 逐字比对）

| 页 | title（tdk.js / index.html） | 与 content-plan |
|---|---|---|
| `/` | `CodeJudge 在线代码评测台 · P1–P6 题库` | 一致（静态写入 index.html） |
| `/problems/:pid` | `{题名} · 在线提交判题 \| CodeJudge`（`problemTdk()` 模板） | 一致 |
| `/submissions/:sid` | `判定结果 · {题名} \| CodeJudge`（`TDK_RESULT.title(name)`） | 一致 |
| `/submissions` | `提交历史 · 本地评测记录 \| CodeJudge` | 一致 |
| `/about` | `使用说明 · 判定规则与本地运行 \| CodeJudge` | 一致 |
| 404 | `页面不存在 \| CodeJudge` | content-plan 未冻结 404 title，自洽合理 |

description 五页逐字一致（对照 content-plan §2 表，tdk.js 逐条抄写，构建产物 grep 证实随包）。

**SPA 处理方式说明**：静态 TDK 经 `router.afterEach → applyTdk` 套用；动态页在数据到达后套用模板。服务端静态 HTML 仅带首页 TDK（SPA 通性）；本地交付目标（标签页可读、命名不打架）达成，公网收录需预渲染——留底。

### 6.2 结构化数据

- `FAQPage`（本次补）：`/about` 挂载时注入 `<script type="application/ld+json">`，`mainEntity` 7 条（AC/PE/WA/TLE/RE/CE/SE），问题 `「{code}」（{中文全称}）是什么意思？`，答案 = content-plan 第 4 节「帮助文案」逐字（`verdicts.js` 同源）；卸载时移除防串页。构建产物 `About-*.js` grep 到 `FAQPage` + `application/ld+json`。
- `WebApplication`：可选项，本地未加（N/A 留底）。
- canonical / og / twitter：无域名，N/A 留底（规格见 content-plan §7）。

### 6.3 语义与 404

- URL 全小写、history 模式、与 spec §2 站点地图一致。
- 样例块：`figure.samples__pair` + 真标题 h3；代码块 `figure > figcaption`（本次将 `span` 改 `figcaption`，content-plan §7「figure/figcaption 语义」）。
- 404 页：「回到题目列表」入口 ✓ + 唯一 H1（本次补 `sr-only`「页面不存在」）✓。
- sitemap/robots：content-plan 明文本地不做 → N/A（公网必须补）。

---

## 7. 响应式 / 无障碍抽查记录

- viewport meta ✓；`@media (max-width:1023px)` / `(max-width:640px)` / `(prefers-reduced-motion:reduce)` 共 7 条断点规则。
- 无障碍：`th[scope=col]`、`caption.sr-only`、SVG `role="img"`+`aria-label`+`<title>`、`section[aria-labelledby]`、横幅 `aria-label="得分横幅"`、按钮均为原生 `button`/`a`。
- 证据边界：本环境无浏览器，三端渲染未做像素级目检（列入用户侧可选步骤）。

---

## 8. 本轮改动清单（授权范围内，供回滚/审计）

| 文件 | 改动 | 授权依据 |
|---|---|---|
| `frontend/src/pages/About.vue` | 注入/清理 FAQPage JSON-LD（7 条判定问答） | 补 SEO 技术项（结构化数据） |
| `frontend/src/components/CodeBlock.vue` | 标签 `span` → `figcaption` | 补 SEO 技术项（figure/figcaption 语义） |
| `frontend/src/pages/NotFound.vue` | 增加 `sr-only` H1「页面不存在」 | 补 SEO 技术项（404） |
| `backend/app/main.py` | `GZipMiddleware` + `/assets/` immutable、HTML no-cache 中间件 | 集成挂载相关（静态资源服务） |

未触碰：core/、judge.py、problems/、reports/（只读消费）、契约与路由定义、任何删除操作、git。

---

## 9. G3 判定回执

- **判定：PASS（可上线，本地交付）**
- 清单统计：**74 PASS / 0 FAIL / 5 N-A**（N/A = 响应式三端真实渲染目检、WebApplication schema、canonical、sitemap/robots、og/twitter，共 5 项留底，详见 prelaunch-checklist §7/§9）
- 修复了什么：① `/about` FAQPage JSON-LD（content-plan §7 要求项）；② 404 页唯一 H1；③ 代码块 figcaption 语义；④ 静态资源 gzip（-60.7% 传输）与缓存头
- 遗留：均为留底/P1 观察（canonical、sitemap/robots、og 卡片、SPA head 预渲染、三端人工目检、413 阈值本轮未重复触发）——无阻塞项

---
---

# Δ4 验证记录（用户系统 + GH Pages · 独立复核证据卷）

> 执行人：deploy-seo-engineer（郝收录）｜日期：2026-10-24 晚｜对应 prelaunch-checklist「Δ4 上线前检查」
> 独立复核口径：四套回归与 E2E 全部本轮真跑，命令与关键输出如下；uvicorn 测完已停。

## 1. 复跑入口

```bash
cd D:/Storage/Projects/260717/codejudge
python backend/tests/test_contract.py        # 契约 7 组（进程内）
python backend/tests/test_supabase_flow.py   # Supabase 流程 18 项（mock 配置态）
# 起服务后：
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
python scripts/smoke_api.py                  # API 冒烟 50 项
python scripts/test_multifile_scenarios.py   # 多文件情景 18 项
cd frontend && npm run build                 # 默认（history）构建
# GH Pages 态：
VITE_ROUTER_MODE=hash VITE_API_BASE=https://judge.example.com npm run build
```

## 2. 四套回归输出摘要

```
test_contract.py        == 7/7 通过 ==
test_supabase_flow.py   == 通过 18 项 / 失败 0 项 ==
  [OK] A1–A4  未配置态：health false / 匿名 201 / synced=false / 带 token 不 401
  [OK] B1–B14 已配置态：health true / 无效 token 401 / 401 文案冻结 / 非 Bearer 401 /
       校验层异常→401 / 有效 token synced=true / payload 字段 / id=sid 单一空间 /
       user_id 取自 JWT / 写入失败与写入异常均 201 synced=false / 匿名照常 / 回查同构
  （输出中「Supabase 写入异常：RuntimeError」为 B11/B12 故意触发分支的日志，非故障）
smoke_api.py            == 通过 50 项 / 失败 0 项 ==   （Δ0 为 47 项，Δ3 增补 synced/health 项）
test_multifile_scenarios.py == 18/18 通过 ==
  [PASS] 健康检查 / 回归单文件 P1 AC / 多文件 g++ P1 AC / 多文件 make P6 AC 8/8
  [PASS] P6 单文件 400（「请用多文件提交」）/ 缺 Makefile 400 / 文件重名 400 /
         路径穿越 400 / 空内容文件 400 / 21 文件 413 / 空源码 400 / source_code+files 同给 400
  [PASS] mode=acm 覆盖 / 多文件 CE+build_log / 多文件 WA 行号提示 /
         P6 示例 API（files=['Makefile','inspector.cpp','util.h']）/ 未知题 404 / 回显全部文件
frontend npm run build  ✓ built in 3.6s（最大 chunk ProblemDetail 121.86 kB gzip 53.7；
                      主包 index 350.18 kB gzip 106.7 —— 含 supabase-js，Δ3 引入 +241 kB）
```

## 3. GH Pages 双态构建对比

```
State A: VITE_ROUTER_MODE=hash VITE_API_BASE=https://judge.example.com
  index.html: href="./favicon.svg"  src="./assets/index-jzCSEG2z.js"  href="./assets/index-*.css"   ← 相对路径
  主包含 createWebHashHistory 工厂体: location.pathname+location.search:"",t.includes("#")||(t+="#"),Pf(t)
  烘焙值 https://judge.example.com 出现在主包；"VITE_API_BASE" 变量名消失（构建期替换）
  includes("#") 计数 = 2（hash 工厂 + 路由字符串解析共用码）

State B: npm run build（无 env → history）
  index.html: 同为 "./assets/…" 相对路径
  includes("#") 计数 = 1（hash 工厂被 tree-shake，仅剩共用码）
  无 judge.example.com 残留；"/api" 同源默认在主包

两态差异 = 路由模式（hash 工厂去留）+ API 源（绝对 URL vs /api），符合预期。
误判排除记录：location.hash / "hash" 字符串两态均存在——分别来自 supabase-js 的
_getSessionFromURL（清 window.location.hash）与 vue-router 共用的 ["params","query","hash"]，
不可作为 hash 路由判据；真正判据是 createWebHashHistory 工厂体 `t.includes("#")||(t+="#")` 的去留。
```

## 4. OAuth 回跳契约（代码级）

```
composables/useAuth.js:168-170
  supabase.auth.signInWithOAuth({ provider:'github', options:{ redirectTo: siteRootUrl() } })

api/supabase.js:33-43  siteRootUrl()
  base = ENV.BASE_URL || '/'
  https? 绝对 base → 直接用
  hash 态  → origin + location.pathname.replace(/[^/]*$/,'')   # 保留 /repo/ 子路径
  history  → origin + base
  全函数无 "#" 拼接 → redirectTo / Site URL 不会带 #/  ✅

api/supabase.js:19-27  createClient(..., { auth:{ autoRefreshToken:true, detectSessionInUrl:true, persistSession:true } })

观察项：hash 态若页面 URL 无尾斜杠（/repo），pathname 去文件名后退化为 "/"。
GitHub Pages 规范 URL 带尾斜杠（/repo/）故不触发；如自定义托管需注意。
```

## 5. 密钥边界扫描记录

```
$ grep -rln "sb_secret_"（排除 node_modules/__pycache__）
  backend/.env.example            ← 占位说明（3 处注释）
  backend/app/services/supabase_store.py  ← docstring 说明（「Bearer + apikey 均为 sb_secret_…」）
  backend/tests/test_supabase_flow.py     ← 测试假值 sb_secret_fake_for_tests_only_not_real
  docs/backend-run-notes.md / docs/site-spec.md  ← 红线文档
  frontend/.env.example           ← 「严禁混用」告示
  frontend/dist/assets/index-*.js ← supabase-js 库识别逻辑:
      fu=t=>t.startsWith("sb_publishable_")||t.startsWith("sb_secret_")   （key 格式分类器）

$ grep "sb_publishable_" → 双端 .env.example / docs / supabase.js 注释 / dist 同上库逻辑；无真实值
$ grep -o "eyJ[A-Za-z0-9_-]{40,}"（JWT 形态）→ dist 与全源码树 0 命中
$ ls backend/.env frontend/.env → 不存在（仓库仅 .env.example）
$ .gitignore → .env / .env.* / backend/.env / frontend/.env / frontend/.env.* 全覆盖，!.env.example 放行

结论：无真实形态密钥。dist 中 sb_secret_/sb_publishable_ 命中属「库自带前缀识别逻辑」（任务允许项）。
```

## 6. 单端口 E2E（local 模式）实测

```
GET /api/health → {"status":"ok","engine":"ready","version":"1.0.0","problem_count":6,"supabase_configured":false}
GET /login      → 200 text/html（SPA 壳 id="app"）
TDK_LOGIN       → title「登录 / 注册 · CodeJudge」+ robots:'noindex'（applyTdk 写 meta[name=robots]，其余页恢复 index,follow）

POST /api/submissions（P1_ac.cpp，不带 Authorization）
  → 201 verdict=AC synced=false
  → summary {total:8, passed:8, pass_rate:1.0, score:100, max_score:100}
  → 横幅数据: 通过 8/8 · 通过率 100% · 得分 100/100
GET /api/submissions/{sid} → 200 同构（含 synced:false）
GET /api/submissions       → 首行 = 该 sid，file_label=main.cpp
POST（同代码 + Authorization: Bearer eyJfake…）
  → 201 synced=false（不 401）——交集降级规则实测通过

UI 字符串（构建产物 grep）：本地模式 ✅ 仅保存在本机 ✅ 登录 / 注册 ✅ noindex ✅
  登录成功。可以提交判题了。✅ 退出后本机浏览器清除登录状态 ✅
CORS 预检（local 无 env）：OPTIONS /api/submissions
  → access-control-allow-origin: *  allow-methods: …POST…  max-age: 600
```

## 7. RLS SQL 语法审查（无真实库，静态审查）

- §13.2 两个 SQL 块：DDL（profiles/submissions 建表 + verdict/mode check 约束 + jsonb 列 + 补列 mode/file_label/build_log + 2 索引）与 RLS（enable ×2 + 4 policy）。
- 谓词 `auth.uid() = id`（profiles）/ `auth.uid() = user_id`（submissions）与权限矩阵一致；submissions **有意不建写策略**（服务端 secret 绕过 RLS 代写）——语句完整、括号配平。
- 通过 SQL Editor 执行性仍以真实库为准（列入用户验收前置）。

## 8. 与双端自测不一致之处（发现 1 项 → **已收口**）

**P6 多文件契约漂移**（详见 prelaunch-checklist Δ4 §C）：
- Δ3 实现已开放 P6 在线多文件提交（我实测 201 AC 8/8；test_multifile_scenarios 断言「P6 可在线交」）；
- 但 site-spec B3/B9/F10/§5.4/错误码表/§12 非目标、content-plan 区块 5、`problems/P6/statement.md:99` 本期提示、backend-run-notes §7 均仍写「本期不开放在线提交 / 400 本期暂不开放在线提交」；
- 单文件 P6 的 400 文案也从冻结的「本期暂不开放在线提交」变为「该题为多文件 make 构建，请用多文件提交…」；
- 前端为 make 题开多文件面板（content-plan 区块 5 的禁用态文案不再出现），`ProblemDetail.vue:6` 注释仍写「P6 提交区禁用态」（陈旧）。
- 处置：属 requirement-architect / content-strategist / frontend-engineer 职责域，我仅报告未改文件。
- **收口（Δ5 回补 4/4）**：已裁定 (a) 认可开放。site-spec 五处追认开放｜content-plan 区块 5 + P6 题面 + exercise 镜像改多文件指引｜backend-run-notes §7 同步｜ProblemDetail 陈旧注释清除。deploy-seo 独立复核：「暂不开放/本期不开放/只开放题面」四域 grep **0 命中**（终验时间 2026-10-24 晚），`problems/P6/statement.md:99` 新文案「本题为多文件 make 构建，请用多文件模式提交 Makefile 与源文件。」已落。

## 9. Δ4 判定回执（收口后）

- **判定：G3 PASS**（Δ4 清单 28 PASS / 0 FAIL / 1 N-A；原 CONCERNS 已裁定 (a) + 四域回补完成，独立复核 0 残留）
- 独立回归逐套：contract 7/7｜supabase_flow 18/18｜smoke_api 50/50｜multifile_scenarios 18/18｜frontend build OK
- 用户人工验收清单：**6 步**（§13.7 第 11 条展开，见 prelaunch-checklist Δ4 §H；含第二账号交叉验证 RLS）
- 测试服务已停止（uvicorn 不驻留）
