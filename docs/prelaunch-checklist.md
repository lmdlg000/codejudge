# 上线前检查清单（Gate G3 · 本地运行交付）

> 项目：CodeJudge 在线代码评测台（G0｜工具站｜真实判题｜本地运行，不做公网部署）
> 执行人：deploy-seo-engineer（郝收录）｜执行时间：2026-10-24
> 环境：Windows 10 + Python 3.13.12 + g++ 16.2.0（MSYS2 ucrt64）+ make 4.4.1｜uvicorn 0.54 / fastapi 0.162
> 证据方式：curl（`--noproxy 127.0.0.1`）+ Python http（`ProxyHandler({})`）真实发请求、真实判题；无浏览器环境处用「源码断言 + 构建产物断言 + API 实测」三层证据，逐项标注证据边界。
> 红线遵守：未公网部署、未买域名、未改 DNS、未 git commit、未删除任何既有文件。代码修改仅限 4 个文件（见附录 A），全部在「补 SEO 技术项 / 集成挂载」授权范围内。

**结论先行：79 项检查 → 74 PASS / 0 FAIL / 5 N-A（N/A 均有 content-plan 明文依据，见 §9）。判定：可上线（本地交付）。**

---

## 0. 环境与构建

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| 0.1 | 依赖就绪（python/fastapi/uvicorn/g++/make） | PASS | `python -m uvicorn --version` 可启动；`GET /api/health` → `{"status":"ok","engine":"ready","version":"1.0.0","problem_count":6}` |
| 0.2 | 前端构建 `npm run build` | PASS | vite 6.4.5 构建成功：`✓ 160 modules transformed`，`✓ built in 3.5s`，产物 `frontend/dist/`（29 文件 / 323,525 B） |
| 0.3 | 构建无报错/无警告阻断 | PASS | 构建输出无 error；仅 Starlette 弃用告警出现在 testclient 导入（测试脚本，不影响服务） |
| 0.4 | 题库数据自检 | PASS | `python scripts/verify_tests.py` → `全部核对通过`（30 组题面样例 + 12 组隐藏用手算值 + 压力用例形态抽查） |

## 1. 单端口集成（FastAPI 托管 dist + SPA 回退）

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| 1.1 | `GET /` 返回 index.html 200 | PASS | `HTTP 200 text/html 737B`，`<title>CodeJudge 在线代码评测台 · P1–P6 题库</title>` |
| 1.2 | StaticFiles 托管 `/assets/*`、favicon | PASS | `GET /assets/index-Dfop5saq.js → 200 text/javascript 108997B`；`GET /favicon.svg → 200 image/svg+xml` |
| 1.3 | SPA history 回退（深链直达） | PASS | `/problems/P1`、`/problems/P2`…`/problems/P6`、`/submissions`、`/submissions/20261024-181039-P1-46f1`、`/about`、`/no-such-page` 全部 `200` 且含 `id="app"` 的 index.html |
| 1.4 | `/api/*` 优先于静态回退 | PASS | `GET /api/problems/P9 → 404 application/json {"error":{"code":"PROBLEM_NOT_FOUND",…}}`（不是 HTML）；`GET /api/nope → 404` JSON 统一错误体 |
| 1.5 | dist 缺失时服务不崩溃（备用提示页分支） | PASS（代码级） | `main.py` 有 `else` 分支返回「后端已就绪」HTML；本次 dist 存在未触发该分支（证据边界：代码审查，未实际删 dist 验证——红线禁删既有文件） |
| 1.6 | 启动一条命令可演示 | PASS | 项目根 `python -m uvicorn backend.app.main:app --port 8000` 单进程同时出页面与 API |

## 2. 五页可达与页面要素

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| 2.1 | 首页 `/` 渲染 6 题卡片 | PASS | `GET /api/problems` → `total: 6`（P1–P6）；`ProblemList.vue` 由该数据渲染卡片（源码断言）；页面 HTTP 200 |
| 2.2 | `/problems/:pid` 题面+样例+提交区 | PASS | `GET /api/problems/P1` → `statement_md` 570 字符、`samples: 5`、`limits`/`build` 齐全；6 题详情接口逐个实测 200（P6 `build.mode=make`） |
| 2.3 | `/submissions/:sid` 结果页（横幅+逐用例） | PASS | 横幅数据实测：`通过 8/8 · 通过率 100% · 得分 100/100`（`bannerSegments` 模板逐字 `通过 {passed}/{total} · 通过率 {rate}% · 得分 {score}/{max_score}`，源码断言 + API 数据双证） |
| 2.4 | `/submissions` 历史表（含 file_label 列） | PASS | `GET /api/submissions` → `total: 20`，首行 `20261024-181039-P1-46f1 / P1 / AC / file_label=main.cpp`；`HistoryTable.vue` 列头「时间｜题目｜提交文件｜判定｜通过｜得分｜操作」，`file_label` 缺失降级显示「—」（源码断言） |
| 2.5 | `/about` 判定表 | PASS | 判定含义表（7 行 AC/PE/WA/TLE/RE/CE/SE，含触发条件/看到什么/怎么修）；页面 200，锚点 `id="verdicts"` 在构建产物中确认 |
| 2.6 | 每页唯一 H1 | PASS | 6 个页面组件均恰 1 个 h1（404 页为本次补的 `sr-only` H1「页面不存在」，不改视觉） |
| 2.7 | 404 页「回到题目列表」入口 | PASS | `NotFound.vue`：`action-label="回到题目列表"` → `router.push('/')`；文案与 content-plan 一致；构建产物含「回到题目列表」 |

## 3. 判题动线 E2E（真提交真判题）

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| 3.1 | 提交 AC 代码 → 201 全量结果 | PASS | `POST /api/submissions {P1, examples/P1_ac.cpp}` → `201`，`submission_id=20261024-181039-P1-46f1`，`verdict=AC`，`summary={total:8, passed:8, pass_rate:1.0, score:100.0, max_score:100.0, partial_score:100.0}`，8 用例全 AC（逐用例含 name/verdict/time_ms/weight） |
| 3.2 | 结果页横幅数据正确 | PASS | 渲染数据 = `通过 8/8 · 通过率 100% · 得分 100/100`，与 CLI 输出同句式 |
| 3.3 | 历史表能看到该单 | PASS | `GET /api/submissions` 首行即新单，`file_label=main.cpp`，`mode=oi`（P1 默认），`created_at` 倒序正确 |
| 3.4 | 结果页 GET 与 POST 同构 | PASS | `GET /api/submissions/20261024-181039-P1-46f1` → 200，`verdict`/`summary` 与 POST 响应一致；`files` 回显 `[{name:main.cpp, content:319字符}]` |
| 3.5 | 「下载报告 JSON」可序列化 | PASS（源码级+数据级） | 按钮把 GET 响应 `JSON.stringify(data,null,2)` 打成 Blob（`SubmissionDetail.vue`）；响应经 `json.dumps/loads` 往返无损——行为等价于「下载该 JSON」 |
| 3.6 | 空源码 400 | PASS | `{"problem_id":"P1","source_code":""}` → `400 VALIDATION_ERROR「提交内容不合法，请检查后重试：源码为空」`；前端另有按钮禁用（`canSubmit = code.trim().length>0`） |
| 3.7 | source_code/files 二选一违规 400 | PASS | 只给 problem_id → `400「…source_code 与 files 必须恰好给其一」` |
| 3.8 | P6 在线提交 400 拒绝 | PASS（历史记录，**已被 Δ5 裁定取代**） | ~~`POST {P6}` → `400「本期暂不开放在线提交」`~~ 已裁定 (a)：P6 在线多文件提交已开放（证据：`test_multifile_scenarios.py`「多文件 make 提交 P6 → AC」）；单文件 / 缺 Makefile 仍 400 但文案已更新为「该题为多文件 make 构建，请用多文件提交…」/「多文件 make 构建缺少 Makefile…」 |
| 3.9 | P6 详情页禁用态 | PASS（历史记录，**已被 Δ5 裁定取代**） | ~~`isP6` 禁用按钮 + 「本期暂不开放」提示条~~ 已裁定 (a)：详情页改为多文件提交指引（切「多文件上传」交 Makefile 与源文件，P6_make 可一键载入）；单文件/缺 Makefile 拒绝路径见 `test_multifile_scenarios.py` 对应项 |
| 3.10 | 未知题目 404 + 出路 | PASS | `POST {P9}` 与 `GET /api/problems/P9` → `404 PROBLEM_NOT_FOUND「题目不存在：P9」`；前端 404/错误条有「回到题目列表」按钮 |
| 3.11 | 未知 sid 404 | PASS | `GET /api/submissions/not-a-real-sid` → `404 SUBMISSION_NOT_FOUND「找不到该次提交：not-a-real-sid」` |
| 3.12 | CLI 复跑（对照通道） | PASS | `python judge.py run P1 examples/P1_ac.cpp` → 逐用例表 8×AC + `通过 8/8 · 通过率 100% · 得分 100/100` + 报告写入 `reports/20261024-180355-P1-46f1.json`（返回码 0） |

## 4. 七接口与错误码

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| 4.1 | `GET /api/health` | PASS | 200 `{"status":"ok","engine":"ready","version":"1.0.0","problem_count":6}` |
| 4.2 | `GET /api/problems` | PASS | 200，`total=6`，列表字段含 id/title/contest_type/score/test_count 等 |
| 4.3 | `GET /api/problems/{pid}` ×6 | PASS | P1–P6 全 200；各 5 组 samples；P6 `build.mode=make` |
| 4.4 | `POST /api/submissions` | PASS | 201 同步全量结果（见 3.1）；CE 路径另有实测：`examples/P1_ce.cpp` → `verdict=CE`，8/8 用例 `verdict=CE`，`build_log` 15 行含 `error:` |
| 4.5 | `GET /api/submissions` | PASS | 200 `{items,total}`，支持 `problem_id/limit/offset`（smoke 覆盖非法 limit/offset → 400） |
| 4.6 | `GET /api/submissions/{sid}` | PASS | 200 同构（见 3.4） |
| 4.7 | `GET /api/examples?problem_id=` | PASS | P1 → 7 项（P1_ac/wa/pe/tle/re/ce.cpp + P1_make/）；缺参 → 400；P9 → 404 |
| 4.8 | 错误体统一 `{"error":{"code","message"}}` | PASS | 400/404/408/429 各路径实测均为该形状 |
| 4.9 | 契约测试 | PASS | `python backend/tests/test_contract.py` → `7/7 通过` |
| 4.10 | API 冒烟 | PASS | `python scripts/smoke_api.py` → `通过 47 项 / 失败 0 项`（含并发 429、报告落盘可回查） |

## 5. 并发 / 超时 / 限制

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| 5.1 | 单并发：第二单 429 | PASS | 双线程同时提交（间隔 0.15s）：A → `201`（3.5s 完成），B → `429 JUDGE_BUSY「判题进行中，请稍候重试」`（0.0s 立即拒绝） |
| 5.2 | 整单硬上限 408 | PASS | 用 `JUDGE_MAX_SUBMIT_SECONDS=2` 起 8001 验证实例，提交 `P1_tle.cpp`（正常需 ~12s）→ `408 JUDGE_TIMEOUT「判题超时，请检查死循环后重试」`（2.1s 触发）；与生产默认 120s 同一代码路径（`get_max_submit_seconds()`） |
| 5.3 | 413 体积限制（65536/262144/20 项） | PASS（部分实测+契约） | smoke 47 项覆盖提交拒绝路径；本轮实测空源码/二选一违规 400。413 全量三阈值由契约测试与 smoke 既有用例背书（证据边界：本轮未重复触发 413，避免大载荷） |

## 6. 错误提示与 Windows 降级文案

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| 6.1 | RE Windows 降级文案逐字 | PASS | 提交 `examples/P1_re.cpp` → `verdict=RE`，`signal=null`，`exit_code=3221225477`（0xC0000005），message = `进程非 0 退出码（exit code 3221225477）：Windows 下不细分信号，请看 stderr 定位。`（与 backend-run-notes §6 逐字一致） |
| 6.2 | CE 全用例 CE + build_log | PASS | 见 4.4；判定顺序冻结（CE → TLE → RE → 比对）由引擎冒烟 45 用例 + smoke 47 项背书 |
| 6.3 | TLE 路径 | PASS | 既有历史记录含 `TLE` 单（`20261024-175234-P1-74e4`）；`P1_tle.cpp` 提交在 408 验证实例按硬上限截断（正常时限下 smoke 覆盖 TLE 判定） |
| 6.4 | 错误码表 8 枚举可对号 | PASS | 本轮实测触达：VALIDATION_ERROR(400)/PROBLEM_NOT_FOUND(404)/SUBMISSION_NOT_FOUND(404)/JUDGE_BUSY(429)/JUDGE_TIMEOUT(408)；smoke/contract 背书：PAYLOAD_TOO_LARGE(413)/ENGINE_UNAVAILABLE(503) 拒绝路径与 INTERNAL_ERROR(500) 兜底 |

## 7. 响应式抽查（证据边界：构建产物 + 断点样式，无真实浏览器渲染）

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| 7.1 | viewport meta | PASS | `index.html`：`<meta name="viewport" content="width=device-width, initial-scale=1.0">` |
| 7.2 | 断点样式存在 | PASS | 构建 CSS 含 7 条 `@media`：`max-width:1023px`、`max-width:640px`、`prefers-reduced-motion:reduce` |
| 7.3 | 横幅防破版 | PASS（源码级） | ScoreBanner 逐段 `nowrap` + `tabular-nums` + `overflow-x:auto`（design-spec 5.5 实现） |
| 7.4 | 三端真实渲染 | N-A | 本环境无浏览器/无 Playwright；按任务约定以 curl + HTML/源码断言模拟。公网部署前建议人工开一次 375/768/1280 三宽度目检（列入观察项） |

## 8. 无障碍抽查

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| 8.1 | 表格语义 | PASS | `th scope="col"`（HistoryTable/About 判定表），`caption.sr-only` 说明表义 |
| 8.2 | 图片/插画替代文本 | PASS | 空状态 SVG `role="img"` + `aria-label` + 内部 `<title>`；favicon 为装饰性 |
| 8.3 | 区域与地标 | PASS | `main.page` 包裹主内容；`section aria-labelledby` 关联标题；得分横幅 `aria-label="得分横幅"` |
| 8.4 | 键盘/焦点 | PASS（源码级） | 可交互元素均为 `button`/`router-link` 原生可聚焦元素；折叠面板用按钮开合 |
| 8.5 | 减少动效偏好 | PASS | `@media (prefers-reduced-motion:reduce)` 已内置 |
| 8.6 | 标题层级 | PASS | 每页唯一 H1；H2→H3 不跳级；样例块用真标题（h3）/figure 语义 |

## 9. SEO 技术项（本地交付口径：能看、能命名、可移植留底）

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| 9.1 | 逐页 TDK 与 content-plan 一致 | PASS | 5 页 title/description 逐字对齐 content-plan §2（tdk.js 实现）：首页（index.html 静态）/题面（`{题名} · 在线提交判题 \| CodeJudge`）/结果（`判定结果 · {题名} \| CodeJudge`）/历史（`提交历史 · 本地评测记录 \| CodeJudge`）/关于（`使用说明 · 判定规则与本地运行 \| CodeJudge`）。构建产物 grep 到全部字符串 |
| 9.2 | SPA title/meta 处理方式 | PASS（说明） | 静态页走 `router.afterEach → applyTdk`；动态页（题面/结果/404）页面内取数据后套用。**静态 HTML 仅含首页 TDK**（SPA 通性）——本地交付目标是「标签页可读」已达成；公网部署需按路由预渲染 head（列入留底项，不阻塞本地上线） |
| 9.3 | 语义 URL | PASS | `/`、`/problems/:pid`、`/submissions`、`/submissions/:sid`、`/about` 与 spec §2 站点地图一致，小写、history 模式、无多余尾斜杠（路由表冻结） |
| 9.4 | 锚点 `#verdicts` / `#cli` / `#privacy` | PASS | About 构建产物含 `id:"verdicts"` `id:"cli"` `id:"privacy"`（及对应 title id）；`/about#cli` 由 P6 提交区旁路按钮引用；`scrollBehavior` 支持 `to.hash` 定位。任务提及的 `#quickstart` 以 content-plan 冻结的 `#cli` 为准 |
| 9.5 | 404 页 | PASS | 含「回到题目列表」入口 + TDK + 唯一 H1（本次补 sr-only H1） |
| 9.6 | FAQPage JSON-LD（/about） | PASS（本次补上） | content-plan §7 要求的 7 条判定问答（问答取第 4 节帮助文案）已注入 `application/ld+json`（About chunk grep 到 `FAQPage`）；进入/离开 /about 注入/清理，避免串页残留 |
| 9.7 | WebApplication schema | N-A | content-plan §7 为「可加」（可选项），本地版不引入；公网部署时再补（留底） |
| 9.8 | canonical | N-A（留底） | content-plan §7「为可移植留底」；当前无域名、无绝对 URL 可写，硬造 `http://127.0.0.1:8000/...` canonical 反而有害。公网部署时按真实域名逐页补 |
| 9.9 | 样例块 figure/figcaption 语义 | PASS（本次加固） | `CodeBlock` 的标签位由 `span` 改为 `figcaption`（figure 内）；题面样例对块 `figure.samples__pair` + 真标题 h3（符合「真标题或 figure/figcaption」二选一约定） |
| 9.10 | sitemap / robots | N-A | content-plan §7 明文「本地版不做 sitemap/robots」。**公网部署时必须补**（留底清单见 e2e-verify-notes） |
| 9.11 | og / twitter card | N-A | content-plan §6/§7「本地部署可省，留规格」；og:image 未产出（留底） |
| 9.12 | 标题层级/图片 alt | PASS | 见 8.6/8.2；正文图形全部 CSS/内联 SVG（无外链图片） |

## 10. 性能

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| 10.1 | dist 体积与 chunk | PASS | 总计 323,525 B（29 文件）；最大 chunk `ProblemDetail` 116,137 B（gzip 51.8 kB）< 500 kB 阈值；次大 `index` 108,997 B（gzip 43.1 kB）。路由级懒加载，首屏只拉 4 个请求 |
| 10.2 | 首屏资源数 | PASS | `index.html` 737 B + `index-*.css` 11,233 B + `index-*.js` 108,997 B + `favicon.svg` 293 B = 4 请求（题面/结果/关于等 chunk 按路由异步） |
| 10.3 | 传输压缩 | PASS（本次开启） | 优化前：JS 明文 108,997 B 传输、无 content-encoding；优化后：`content-encoding: gzip`，传输 42,855 B（**-60.7%**）。`GZipMiddleware(minimum_size=1024)` |
| 10.4 | 缓存头 | PASS（本次开启） | 优化前：无 Cache-Control；优化后：`/assets/*` → `public, max-age=31536000, immutable`（文件名带内容哈希）；HTML → `no-cache`（发版即生效） |
| 10.5 | 本地首屏体验 | PASS | 127.0.0.1 回环下页面与 API 均为即时响应（health/静态/SPA 路由 curl 耗时毫秒级）；判题为同步长请求（实测 AC 单 ~3.5s），UI 有「判题中…」loading 文案（F3） |

**优化前后对比（本轮实测）**

| 指标 | 优化前 | 优化后 | 变化 |
|---|---|---|---|
| index.js 传输体积 | 108,997 B | 42,855 B | **-60.7%** |
| 静态资源缓存策略 | 无 Cache-Control | immutable 1 年 | 二访免下载 |
| HTML 缓存策略 | 无 | no-cache | 发版不失效 |
| 最大 chunk | 116,137 B | 116,137 B | 无需拆分（<500 kB） |

## 11. 报告落盘与数据

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| 11.1 | API 提交写报告 | PASS | `reports/20261024-181039-P1-46f1.json` 存在（与 submission_id 同名）；RE/CE 等各单均有同名报告 |
| 11.2 | CLI 写报告 + latest 副本 | PASS | `reports/20261024-180355-P1-46f1.json` + `reports/latest.json`（2,917 B）均在 |
| 11.3 | 历史可回查 | PASS | `GET /api/submissions` total=20（reports/ 即数据库）；`GET /api/submissions/{sid}` 可取回任一历史单 |

## 12. 安全边界（本地工具站）

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| 12.1 | 仅监听 127.0.0.1 | PASS | 启动命令 `--host 127.0.0.1`；默认 `JUDGE_HOST=127.0.0.1`（config.py） |
| 12.2 | 不暴露公网声明 | PASS | backend-run-notes §9 明文「无沙箱加固，绝不暴露公网」；本次未做任何公网部署/域名/DNS |
| 12.3 | 文件名白名单 | PASS（契约+冒烟背书） | `^[A-Za-z0-9_.-]{1,64}$`，拒绝 `.`/`..`/路径分隔符（smoke 覆盖非法名拒绝） |

---

## 遗留清单（无阻塞项，均为「留底 / P1 观察」）

| 级别 | 项 | 说明 | 谁来接 |
|---|---|---|---|
| 留底 | canonical / og / twitter card / og:image | 无域名，本地版按 content-plan 省；公网部署时按 §7 规格补 | 公网部署时 deploy-seo |
| 留底 | sitemap.xml / robots.txt | content-plan 明文本地不做；公网部署**必须**补 | 公网部署时 deploy-seo |
| 留底 | SPA 静态 head 只有首页 TDK | 公网收录需按路由预渲染 title/meta（或 SSR） | 公网部署时定方案 |
| P1 观察 | 三端真实渲染目检 | 本轮无浏览器，响应式以断点样式+viewport 断言；建议人工开 375/768/1280 过一眼 | 交付后人工抽查 |
| P1 观察 | 413 三阈值未在本轮重复触发 | 由 smoke 47 项 + 契约测试背书，避免本轮发大载荷 | 无需动作 |
| P1 观察 | WebApplication schema（可选项） | content-plan 标「可加」，本地未加 | 公网部署时可选 |

## 回滚方式

本轮代码改动仅 4 处（均在授权范围），回滚步骤：

1. `frontend/src/pages/About.vue`：删掉 `injectFaqJsonLd/removeFaqJsonLd` 与 `onUnmounted` 调用（恢复仅 `onMounted(applyTdk)`）——回滚 FAQPage；
2. `frontend/src/components/CodeBlock.vue`：`<figcaption class="code-block__label caption">` 改回 `<span class="code-block__label caption">`——回滚 figcaption；
3. `frontend/src/pages/NotFound.vue`：删掉 `<h1 class="sr-only">页面不存在</h1>`——回滚 404 H1；
4. `backend/app/main.py`：删掉 `GZipMiddleware` 导入/挂载与 `_asset_cache_headers` 中间件——回滚压缩与缓存头；
5. `cd frontend && npm run build` 重新构建；
6. 重启服务：项目根 `python -m uvicorn backend.app.main:app --port 8000`。

注：未执行 git commit（红线），dist/ 为本轮重建产物；若需完全回到本轮之前状态，按上表逐项还原源码再 build 即可，`reports/` 判题历史不受影响。

---

## 我的判定（可上线 / 不可上线）

**可上线（本地交付）**。阻塞项：**无**（0 FAIL）。

### 需要用户自己完成的步骤清单

1. 本机启动演示：项目根执行 `python -m uvicorn backend.app.main:app --port 8000`，浏览器打开 `http://127.0.0.1:8000`（若要从别的机器访问需自行改 `JUDGE_HOST`，但**不建议**——无沙箱，仅限本机）。
2. （可选）人工过一眼 375 / 768 / 1280 三宽度的页面渲染——本轮无浏览器，响应式只做了断点样式与 viewport 断言。
3. （仅当未来公网部署时）在你的域名/托管平台完成：绑定域名 + HTTPS、`www`/非 `www` 301、补 sitemap.xml 与 robots.txt、逐页 canonical 与 og/twitter 卡片（og:image 需出 1200×630 图）、SPA 按路由预渲染 head；**并先做代码执行沙箱加固**（当前判题是本机真实编译执行，绝不可以现状暴露公网）。

### 上线后建议观察的 2–3 个指标

1. **判题成功率与判定分布**：`reports/` 中 `status=failed`（SE）单量应为 0；AC/CE/WA/TLE 分布是否符合预期（演示动线以 AC+CE+RE 为主）。
2. **提交等待体感**：同步判题整单实测 ~3.5s（P1 AC 8 用例）；若单并发 429 频繁出现，说明演示时连续提交过快，等第一单完成即可（属设计行为）。
3. **首屏传输**：浏览器 Network 里 `index-*.js` 应显示 gzip ~43 kB 且二次访问走 memory/disk cache（immutable）；若见明文 ~109 kB 说明压缩中间件未生效，检查是否用旧命令起的服务。

---
---

# Δ4 上线前检查（用户系统与 GH Pages · G3 独立复核）

> 执行人：deploy-seo-engineer（郝收录）｜执行时间：2026-10-24 晚｜范围：Δ1–Δ3 增量（Supabase 用户系统、多文件提交、终端风、GH Pages 就绪）
> 角色定位：第二层 QA——四套回归全部**独立真跑**，未照抄前端/后端自测结论；浏览器不可用处按任务约定以「源码断言 + 构建产物断言 + API 实测」三层证据。
> 红线遵守：未公网部署、未 git commit、未删文件；uvicorn 测试进程**测完已停**。

**Δ4 结论：28 PASS / 0 FAIL / 1 N-A（真实 Supabase 人工验收）。原 CONCERNS（P6 多文件契约漂移）已裁定 (a) 认可开放 + 四域回补完成，**G3 转 PASS**（收口记录见 §C）。Δ4 列表项全部通过，可进交付汇编。**

## A. 独立回归（四套真跑）

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| A.1 | `backend/tests/test_contract.py` | PASS | `== 7/7 通过 ==`（examples/health/problem_detail/problems/submission_ac/submission_list/submission_rejects 全 OK） |
| A.2 | `backend/tests/test_supabase_flow.py`（mock 配置态） | PASS | `== 通过 18 项 / 失败 0 项 ==`（A1–A4 未配置态 4 项 + B1–B14 已配置态 14 项：401 文案冻结、synced=true/false、ID 单一空间、写入失败不 500 等） |
| A.3 | `scripts/smoke_api.py` | PASS | `== 通过 50 项 / 失败 0 项 ==`（较 Δ0 的 47 项新增 synced/health 字段项；含并发 429、报告落盘） |
| A.4 | `scripts/test_multifile_scenarios.py` | PASS | `== 18/18 通过 ==`（单文件回归 AC、多文件 g++ AC、多文件 make P6 AC、P6 单文件 400、缺 Makefile 400、重名 400、路径穿越 400、21 文件 413、mode 覆盖、CE/WA 明细、示例 API 多文件结构） |
| A.5 | `cd frontend && npm run build` | PASS | vite 6.4.5 `✓ built in 3.6s`，29+ 产物文件；最大 chunk `ProblemDetail` 121.86 kB（gzip 53.7），主包 `index` 350.18 kB（gzip 106.7，含 supabase-js，Δ3 引入后 +241 kB——观察项，仍 <500 kB 阈值） |
| A.6 | 任一失败根因 | N-A | 四套 0 失败，无需根因分析 |

## B. GitHub Pages 构建链（双态构建对比）

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| B.1 | `VITE_ROUTER_MODE=hash VITE_API_BASE=https://judge.example.com npm run build` | PASS | 构建成功（State A 产物） |
| B.2 | ① index.html 资源引用为相对路径（`base:'./'`） | PASS | State A：`href="./favicon.svg"`、`src="./assets/index-jzCSEG2z.js"`、`href="./assets/index-CupvHf1p.css"`——全部 `./` 相对，任意子路径可托管 |
| B.3 | ② 产物路由确为 hash 模式（createWebHashHistory 烘焙） | PASS | State A 主包含 hash 工厂函数体：`location.pathname+location.search:"",t.includes("#")||(t+="#"),Pf(t)`（即 vue-router `createWebHashHistory` 实现，静态条件 `"hash"==="hash"` 常量折叠后保留）；State B（无 env）同一标记**被 tree-shake**（`includes("#")` 计数 2→1，仅剩路由字符串解析共用代码）——两态差异符合预期 |
| B.4 | ③ VITE_API_BASE 注入点存在（client.js 读取） | PASS | 源码 `api/client.js:10`：`((import.meta.env && import.meta.env.VITE_API_BASE) \|\| '') + '/api'`；State A 产物 grep 到 `https://judge.example.com` 烘焙值，`VITE_API_BASE` 变量名已消失（构建期替换正确） |
| B.5 | 无 env 构建对比（history 模式） | PASS | State B：无 `judge.example.com` 残留、`"/api"` 同源默认在主包；hash 工厂被摇掉（见 B.3）；index.html 相对路径不变。两态差异 = 仅路由模式与 API 源，符合设计 |
| B.6 | 观察项 | （记录） | ① supabase-js 进主包使 index 达 350 kB（gzip 107 kB）——如需再减可对 `@supabase/supabase-js` 做手动分包（非阻塞）；② hash 态 `siteRootUrl()` 在 URL 无尾斜杠时（如 `/repo`）会退化为站点根 `/`——GitHub Pages 规范 URL 带尾斜杠（`/repo/`）故实际不触发，留观察 |

## C. ✅ 已收口：P6 多文件契约漂移（原 CONCERNS → 已裁定 (a)，G3 转 PASS）

> **裁定与回补要点（一行）**：已裁定 (a) 认可 Δ3 开放 P6 在线多文件提交（G2「本期不开放」作废）；四域回补完成——site-spec 五处追认开放、content-plan 区块 5 + `problems/P6/statement.md` + exercise 镜像改多文件指引（0 残留）、backend-run-notes §7 同步、`ProblemDetail.vue` 陈旧注释清除；deploy-seo 独立复核「暂不开放/本期不开放/只开放题面」四域 grep **0 命中**，`test_multifile_scenarios.py`「多文件 make 提交 P6 → AC」为功能证据。

| 项 | 内容 |
|---|---|
| 现象 | Δ3 实现已**开放 P6 在线多文件提交**（实测 201 AC 8/8），但冻结契约与文案仍写「本期不开放」 |
| 实现侧（实测） | `judge_service.py`：make 题强制 `files[]` + 必含 Makefile（单文件 → 400「该题为多文件 make 构建，请用多文件提交…」）；`test_multifile_scenarios.py` 断言「P6 可在线交」；前端 `ProblemDetail.vue` 为 make 题开多文件面板（文件 tab + 添加文件） |
| 契约/文案侧（未同步） | ① `site-spec.md` B3/B9/F10、§5.4、§5.2 错误码表、§12 非目标：P6 → 400「本期暂不开放在线提交」；② `content-plan.md` 区块 5「本期 P6 只开放题面阅读」+ 禁用按钮文案；③ `problems/P6/statement.md:99` 本期提示「在线提交暂未开放，建议本地 CLI 评测」（**用户可见矛盾**：题面说不开放、界面却能交且判过）；④ `backend-run-notes.md` §7「P6 在线提交被拒」；⑤ `ProblemDetail.vue:6` 注释仍写「P6 提交区禁用态」（陈旧） |
| 影响 | 本地演示不受影响（功能可用且18/18 测过）；但交付汇编若引用旧契约文案会与实测行为互相打脸；错误信息也从冻结的「本期暂不开放在线提交」变成了新文案 |
| 裁定结果（收口） | **已裁定 (a)**：认可 Δ3 开放 P6 多文件在线提交。回补 4/4 闭环——① site-spec B3/B9/F10/§5.4/错误码表 五处追认开放（requirement-architect）；② content-plan 区块 5 + P6 题面 + exercise 镜像改多文件指引，「暂不开放」0 残留（content-strategist）；③ backend-run-notes §7 同步（backend-engineer）；④ `ProblemDetail.vue` 陈旧注释清除、build 过（frontend-engineer）。deploy-seo 独立 grep 复核四域 0 命中。功能证据：`test_multifile_scenarios.py`「多文件 make 提交 P6 → AC（P6 可在线交）」；单文件 / 缺 Makefile 仍 400（新文案） |

## D. OAuth 回跳契约核验（代码级断言）

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| D.1 | signInWithOAuth redirectTo **不含 `#/`** | PASS | `composables/useAuth.js:168-170`：`signInWithOAuth({ provider:'github', options:{ redirectTo: siteRootUrl() } })`；`siteRootUrl()` 函数体无任何 `#` 拼接（`api/supabase.js:33-43` 全文核对） |
| D.2 | hash 模式下 siteRootUrl() 保留部署子路径 | PASS | `if (VITE_ROUTER_MODE==='hash') { const p = location.pathname.replace(/[^/]*$/,''); return origin + p }`——`https://user.github.io/repo/#/problems/P1` → pathname `/repo/` → 返回 `https://user.github.io/repo/`（含子路径、无 `#/`）；history 模式取 `origin + BASE_URL` 同样无 hash |
| D.3 | detectSessionInUrl/persistSession 显式声明 | PASS | `api/supabase.js:20-26`：`createClient(…, { auth:{ autoRefreshToken:true, detectSessionInUrl:true, persistSession:true } })`（对齐 §13.1） |
| D.4 | Supabase Site URL / Redirect URLs 期望值与 §13.7 一致 | PASS | 期望值整理为下表（逐条抄 §13.7，标注控制台位置）；代码侧 redirectTo 语义与 Site URL 同形（站点根、无 `#/`）一致 |

### D.4 附：用户外部配置核对表（值抄 §13.7，共 11 条）

| # | 配置项 | 期望值 | 在哪个控制台操作 |
|---|---|---|---|
| 1 | 创建 Supabase 项目 | 记下 `project-ref`（URL 中随机串）与数据库密码 | supabase.com → New project |
| 2 | 建表 DDL | 执行 §13.2 全部（profiles / submissions / 索引 / RLS 策略 4 条） | Supabase → SQL Editor |
| 3 | 开启 Email 认证 | Enabled（演示可关 Confirm email） | Supabase → Authentication → Providers → Email |
| 4 | 创建 GitHub OAuth App | **Callback URL = `https://<project-ref>.supabase.co/auth/v1/callback`**；拿 Client ID / Client Secret | GitHub → Settings → Developer settings → OAuth Apps → New OAuth App |
| 5 | 开启 GitHub Provider | Enabled + 第 4 步的 Client ID / Secret | Supabase → Authentication → Providers → GitHub |
| 6 | 回跳白名单 | **Site URL = `https://<user>.github.io/<repo>/`**；Redirect URLs += Site URL 本身、`http://localhost:5173`、`http://127.0.0.1:5173`；**严禁写 `#/`** | Supabase → Authentication → URL Configuration |
| 7 | 取新一代密钥 | `sb_publishable_…`（前端）与 `sb_secret_…`（后端）；禁用旧 anon/service_role JWT | Supabase → Project Settings → API Keys |
| 8 | 前端 env | `frontend/.env`（照抄 .env.example）4 个 `VITE_*`；GH Pages 场景配进 repo Secrets 注入 Actions build step | 本地文件 / GitHub repo → Settings → Secrets and variables → Actions |
| 9 | 后端 env | `backend/.env`：`SUPABASE_URL`、`SUPABASE_SECRET_KEY`、`JUDGE_CORS_ORIGINS`（含 `https://<user>.github.io`、`http://localhost:5173`、`http://127.0.0.1:5173`） | 自托管后端主机 |
| 10 | 开启 GitHub Pages | 部署来源（Actions 工作流或分支）；确认 build 命令与 `dist/` 产物上传 | GitHub repo → Settings → Pages |
| 11 | 验收链路 | 见 §H 人工验收清单（6 步） | Supabase Table Editor + 浏览器 |

## E. 密钥边界终检

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| E.1 | `sb_secret_` 全项目 + dist 扫描 | PASS | 允许命中仅 7 处且全部合规：`backend/.env.example`（占位说明×3）、`backend/app/services/supabase_store.py`（docstring 说明）、`backend/tests/test_supabase_flow.py`（假值 `sb_secret_fake_for_tests_only_not_real`）、`docs/backend-run-notes.md`+`docs/site-spec.md`（红线说明）、`frontend/.env.example`（禁用告示）、**dist 中为 supabase-js 库自带前缀识别逻辑** `fu=t=>t.startsWith("sb_publishable_")\|\|t.startsWith("sb_secret_")`（key 格式分类器，非密钥值）。**无任何真实形态密钥** |
| E.2 | `sb_publishable_` 扫描 | PASS | 命中：双端 .env.example 占位、docs 说明、`frontend/src/api/supabase.js` 注释、dist 同一处库识别逻辑。**无真实 key 值**（State A 构建 env 未注入任何 Supabase key） |
| E.3 | `eyJ` 长串（JWT 形态）扫描 | PASS | `eyJ[A-Za-z0-9_-]{40,}` 在 dist 与全源码树 **0 命中**；`{20,}` 松扫描亦 0 唯一命中（此前粗扫的巨量输出系 dist 单行 350 kB 被整行打印的噪声，非真实命中） |
| E.4 | `.gitignore` 覆盖两端 `.env` | PASS | 覆盖 `.env`、`.env.*`、`backend/.env`、`frontend/.env`、`frontend/.env.*`，例外放行 `!.env.example` / `!frontend/.env.example`；当前仓库**不存在真实 .env 文件**（仅 .env.example） |
| E.5 | secret 不进日志/报错/reports | PASS（代码级） | 报错文案实测为固定中文（401「请先登录（登录状态可能已过期）」等）；`test_supabase_flow` B3/B5 断言 401 文案冻结、校验层异常→401 不 500；服务日志仅路由与状态码（run-notes §9） |

## F. 单端口集成 E2E（local 模式，真跑）

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| F.1 | `/login` 可达 | PASS | `GET /login → 200 text/html`，SPA 壳含 `id="app"` |
| F.2 | noindex 生效 | PASS（SPA 口径） | `TDK_LOGIN = { title:'登录 / 注册 · CodeJudge', …, robots:'noindex' }`（tdk.js:49-55）由 LoginPage `applyTdk` 套用；`applyTdk` 写 `<meta name="robots">` 且**其余页恢复 `index, follow`**（防泄漏）；构建产物 grep 到 `noindex`。证据边界：robots meta 为 JS 运行时套用（SPA 通性），静态 HTML 不含——公网抓取前建议服务端补静态 meta（沿用 Δ0 留底项「SPA head 预渲染」） |
| F.3 | local 模式完整提交动线（P1 单文件 AC） | PASS | `POST /api/submissions`（examples/P1_ac.cpp）→ `201`，`verdict=AC`，`summary={total:8,passed:8,pass_rate:1.0,score:100,max_score:100}`，横幅数据「通过 8/8 · 通过率 100% · 得分 100/100」；`GET /api/submissions/{sid}` 同构含 `synced`；历史首行=file_label `main.cpp` + 该 sid |
| F.4 | 响应 `synced` 字段 | PASS | local 模式实测 `synced: false`（POST 与 GET 回查一致）——与 §10.2 口径一致 |
| F.5 | 页头「本地模式」标签 | PASS（源码+产物级） | `AppHeader.vue`：`v-if="isLocalMode"` → `<span class="header__local micro">本地模式</span>`；构建产物含「本地模式」字符串；`isLocalMode = !authMode \|\| !effectiveAuthMode`（env 未配即真） |
| F.6 | 未配置时无登录入口 | PASS（源码+产物级） | 同一分支逻辑：local 模式渲染灰字「本地模式」，「登录 / 注册」链接只在 `v-else`（supabase+未登录）出现；产物含「登录 / 注册」但运行时受 `authMode=false` 控制不渲染 |
| F.7 | 结果页「仅保存在本机」徽章 | PASS（源码+产物级） | `SyncBadge.vue` 三态：synced→「已同步到你的账号」/ 同步失败→「同步失败，仅保存在本机」/ 未带 token→「仅保存在本机」（SE 灰）；local 模式 `synced=false` 且未带 token → 第三态；产物含「仅保存在本机」 |
| F.8 | local + 假 token 不 401（交集降级） | PASS | 实测 `Authorization: Bearer eyJfake…` + local 模式 → `201 synced:false`（不 401、照常判题），符合 §13.4/§10.2「后端未配置取交集」规则 |

## G. CORS / .env.example / RLS SQL

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| G.1 | CORS 实现 | PASS | `main.py` 挂 `CORSMiddleware`，`JUDGE_CORS_ORIGINS` 逗号分隔（`config.py:get_cors_origins`）；空 = 不限制。实测 OPTIONS 预检：`access-control-allow-origin: *` + `allow-methods: …POST…` + `max-age: 600`（local 现状预期） |
| G.2 | `.env.example` 双端齐备且与 §13.3 一致 | PASS | `frontend/.env.example`：VITE_SUPABASE_URL / VITE_SUPABASE_PUBLISHABLE_KEY（注释明示仅 publishable）/ VITE_API_BASE / VITE_ROUTER_MODE=hash，4 项齐；`backend/.env.example`：SUPABASE_URL / SUPABASE_SECRET_KEY（🔴红线注释）/ JUDGE_CORS_ORIGINS / JUDGE_* 4 项齐。与 §13.3 清单逐项对上 |
| G.3 | RLS SQL 可执行性（语法审查，无真实库） | PASS | §13.2 两个 SQL 块结构审查：`create table public.profiles`/`create table public.submissions`（含 verdict/mode check 约束、jsonb 列、补列 mode/file_label/build_log）、`create index` ×2、`enable row level security` ×2、4 条 policy（profiles 3 读写 + submissions_select_own）均在；括号配平、语句分号闭合（block1 末尾为注释行故启发式报 semi=FALSE，人工核对实际语句完整）；`auth.uid() = id` / `auth.uid() = user_id` 谓词正确；**有意不建 submissions 写策略**与 §13.2 权限矩阵一致 |
| G.4 | 健康接口附加字段 | PASS | `GET /api/health` → `{"status":"ok","engine":"ready","version":"1.0.0","problem_count":6,"supabase_configured":false}`（向后兼容追加，local 模式 false） |

## H. 真实 Supabase 验收（N/A · 用户配置后人工验收）

| # | 检查项 | 结果 | 原因与清单 |
|---|---|---|---|
| H.1 | OAuth 全流程 / 邮箱验证 / RLS 跨用户隔离 | **N-A** | 本环境无真实 Supabase 项目与 GitHub OAuth App（§13.7 第 1/4/5/7 条均为用户侧平台操作），mock 套件已覆盖后端分支；按任务要求列为**用户配置后人工验收清单**（对应 §13.7 第 11 条，共 6 步）：① 邮箱注册并登录成功；② GitHub 登录回跳成功（redirectTo 无 `#/`，detectSessionInUrl 吸收令牌）；③ 登录后提交一次判题，响应 `synced:true`；④ Supabase → Table Editor 看到 `submissions` 行且 `user_id` 正确；⑤ 退出登录后历史页不可见该记录（RLS 生效）、换账号亦不可见；⑥ 清空前端 env 重建后回退 local 模式可用。**通过前不算 supabase 模式验收完成** |

---

## Δ4 我的判定收尾

**我的判定：可上线（本地交付）——G3 PASS。** 阻塞项：无（0 FAIL）；原待裁定项（P6 多文件开放 vs G2 冻结文案）**已裁定 (a) 认可开放 + 四域回补完成**（见 §C 收口记录），旧条目 3.8/3.9 已标注被 Δ5 裁定取代。

### 需要用户自己完成的步骤清单（Δ4 增量）

1. 按 §D.4 核对表 11 条在 Supabase / GitHub / 仓库 Secrets / 自托管后端逐条配置（值见表，勿写 `#/` 进回跳白名单）。
2. 配置完成后执行 §H 人工验收 6 步；**第 ⑤ 步 RLS 隔离必须用第二个账号交叉验证**。
3. GH Pages 上线前在 repo Secrets 注入 4 个 `VITE_*` 并跑一次 Actions 构建，打开线上 `…/#/` 与 `…/#/login` 看 noindex 与回跳。
4. ~~（裁定后续）若采纳开放 P6…~~ 已闭环：P6 多文件在线提交已开放且四域文档/注释同步（§C），P6 可正常对外演示；单文件/缺 Makefile 的 400 新文案即用户引导。

### 上线后建议观察的 2–3 个指标（Δ4 增量）

1. **synced 率**：登录用户的提交 `synced:true` 占比应为 100%（false 频出 = Supabase 写入路径/RLS 配置问题）。
2. **401 UNAUTHORIZED 频次**：登录态过期时应只提示重新登录，不应出现 5xx；B5/B12 分支保证写入失败不影响判题。
3. **主包体积**：index-*.js 现 350 kB（gzip 107 kB）；若后续再引依赖，注意守住 <500 kB，必要时对 supabase-js 手动分包。
