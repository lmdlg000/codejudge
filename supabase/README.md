# Supabase 集成（UAPI 执行 + AI 语义评判 + 人工复核）

本目录承载 Supabase 侧交付物：数据库迁移、Edge Functions。前端经 `@supabase/supabase-js` 直连；评分链路**不依赖 FastAPI**（GitHub Pages + Supabase + UAPI 即可跑通）。

## 流程（等待时间与评分计算时间解耦 · 强制显式样例校验）

```text
用户提交 → judge 函数前置同步校验（UAPI 逐个跑显式样例）
           ├─ 任一失败 → 400「存在未通过的显式测试样例，不能提交」，不落库
           └─ 全部通过 → 插入 submissions（status='judging'），立即返回 202
↓ EdgeRuntime.waitUntil 后台任务
将「代码 + 题目 + 真实运行结果（校验产物，不重复执行省积分）」交给 AI 评分
↓
┌───────────┴───────────┐
conclusive 且分数达标      conclusive=false / 低分 / AI 失败
↓                         ↓
status = 'ai_scored'     status = 'pending_review'
Realtime 推送            写入 human_review_queue（priority: 分数<40 或 AI 失败=high）
用户收到 AI 初评          管理员通过 admin-review 裁决（pass | fail | bad_data）
                          → human_reviewed_pass / human_reviewed_fail
                            （bad_data：退回 pending_review 并高优先级重新入队）
                          Realtime 推送最终结果
```

**双层校验**：① 前端体验层——OneCompiler 嵌入式编辑器内「测此样例」（populateCode 注入 stdin + triggerRun）或「运行样例」（`judge` 的 `dry_run`），全部通过才启用提交按钮；② 后端安全层（核心）——`judge` 插入前强制复验，任一失败 400 不写库。

4. **Supabase 回跳配置**：Site URL = `https://lmdlg000.github.io/codejudge/`；Redirect URLs 追加 `https://lmdlg000.github.io/codejudge/*` + `http://localhost:5173/*`（**严禁写 `#/`**，OAuth 回跳靠 `detectSessionInUrl` 吸收令牌）。
   **邮箱验证链路**：signUp 带 `emailRedirectTo = <站点>/?verified=1` → 确认邮件的 ConfirmationURL 验证通过后 302 落回站点 → 自动转入 `/auth/verified`「邮箱验证成功」页（链接过期则显示失败态）；因此 Redirect URLs 必须包含 `https://lmdlg000.github.io/codejudge/*` 通配，否则 goTrue 会拒绝该回跳。

**备用通道（防卡死）**：样例测试累计 ≥10 次仍无法全部通过时，前端解锁「备用通道提交（转人工复核）」（`force_submit: true`）——AI 仅出参考分，**一律进入人工复核队列**，最终得分以人工裁决为准。

前端零轮询零刷新：结果页订阅 `postgres_changes`（表 `submissions`，RLS 生效）。

## UAPI 成本适配

- **接口**：`POST https://uapis.cn/api/v1/execution/run`，**4 积分/次**；`Authorization: Bearer {UAPI_ACCESS_TOKEN}`。
- **参数**：`{ language, code, stdin, timeout_ms, network: { mode: 'offline' } }`（默认断网沙盒）；返回完整 stdout/stderr 与状态。
- **状态判定**：HTTP 200 仅代表接收，必须看响应体 `status`：`success`（再比对 stdout 与期望输出得 Accepted/WA）/ `compile_error` / `runtime_error` / `timeout`。
- **积分预算**：一次真实提交 = 显式样例数次调用（≤3）；`dry_run` 自测按次另计；AI 评分复用校验运行结果**不重复执行**。按 4 积分/次：访客 1500 积分 ≈ 375 次、登录 3500 积分 ≈ 875 次，配合低价积分包可覆盖低频使用。
- **多文件**：UAPI 为单 `code` 模型——多文件提交自动内联合并（本地头文件去 `#include` 后拼接，Makefile 过滤），常见多文件/make 题可实跑。

## 部署步骤

1. **建表 / RLS / RPC**：Supabase → SQL Editor → 依次执行
   - `migrations/0001_*.sql`（profiles / submissions / RLS，见 `docs/site-spec.md` §13.2）
   - `migrations/0002_ai_review.sql`（状态机 + 复核队列 + reviewers + complete_review + Realtime 发布）
   - `migrations/0003_onecompiler.sql`（run_summary 运行数据列 + 复核裁决 human_reviewed_*）
   - `migrations/0004_uapi.sql`（language 列 + 队列 priority/human_verdict）
2. **部署 Edge Functions**：
   ```bash
   supabase functions deploy judge
   supabase functions deploy admin-review
   ```
3. **配置密钥**（Edge Function Secrets，绝不进前端）：
   ```bash
   supabase secrets set SUPABASE_SECRET_KEY=sb_secret_…
   supabase secrets set UAPI_ACCESS_TOKEN=…        # uapis.cn 控制台获取
   supabase secrets set AI_API_KEY=…
   # 可选
   supabase secrets set AI_API_URL=https://api.openai.com/v1/chat/completions
   supabase secrets set AI_MODEL=gpt-4o-mini
   supabase secrets set AI_SCORE_THRESHOLD=60      # 低于此分转人工
   supabase secrets set UAPI_LANGUAGE=cpp
   supabase secrets set UAPI_TIMEOUT_MS=5000
   ```
   前端仍只用 `sb_publishable_…`（`frontend/.env`）。
4. **指定复核人**（人工复核权限 = `reviewers` 表）：
   ```sql
   insert into public.reviewers (id) values ('<复核人的 auth.uid>');
   ```
5. **前端 env**（`frontend/.env`）：`VITE_SUPABASE_URL`、`VITE_SUPABASE_PUBLISHABLE_KEY`。GitHub Pages 构建时经 CI Secrets 注入。

## judge / admin-review 接口摘要

- `POST /functions/v1/judge`（用户 JWT）：
  - `{ ..., dry_run: true }` → 200 `{ dry_run, passed, samples:[{name,passed,status,expected,actual,stderr}] }`（前端体验层，不落库）
  - 正常提交 → 202 `{ submissionId, status: 'judging' }`；样例不过 → 400 `存在未通过的显式测试样例，不能提交（<状态>）` + `failed_sample/expected/actual/execution_status`
  - 无样例 → 400 `必须提供显式测试样例`；UAPI 未配置 → 503
  - **备用通道**：`force_submit: true`（前端测试 ≥10 次仍不过时解锁）→ 跳过样例 400 门禁照常入库，但 **AI 判分后一律强制转人工复核**（reason=`force_submit`，priority=high，最终以人工裁决为准）
- `POST /functions/v1/admin-review`（用户 JWT + reviewers 白名单）：
  - `{ submission_id, score, feedback, decision }`，`decision ∈ pass | fail | bad_data`
  - pass → `human_reviewed_pass`；fail → `human_reviewed_fail`；bad_data → 提交退回 `pending_review` 并以 `reason='bad_data'`、`priority='high'` 重新入队
  - 队列项带乐观锁（仅 `pending` 可裁决）
- SQL 侧备用：`complete_review(submission_id, score, feedback, decision)` RPC（security definer）。

## 人工复核（/admin-review）

- 入口：站内 `/admin-review`（旧路径 `/review` 重定向；仅 `reviewers` 名单内账号可读队列）。
- 卡片展示：AI 初评（分数/反馈）+ 入队原因与优先级（分数 <40 / AI 失败 = 高优先）+ UAPI 运行数据 + 源码回显。
- 裁决表单：最终得分 + 通过/未通过/数据问题（退回重审）+ 复核反馈。
- 入队原因（reason）：`low_score`（分数 < `AI_SCORE_THRESHOLD`）| `inconclusive`（AI 无法可靠判断）| `ai_failed` | `force_submit`（样例未全过备用通道提交，强制人工）| `bad_data`（重审入队）。

## submissions 状态机

| status | 含义 | 用户看到 |
|---|---|---|
| `judging` | 已接收，AI 评分进行中（样例已全过） | 「评分中…（已接收）」 |
| `ai_scored` | AI 初评完成（conclusive 且分数达标） | AI 得分 + 反馈 + 运行数据 |
| `pending_review` | 待人工确认 | 「AI 已评分，正在等待人工确认」 |
| `human_reviewed_pass` | 人工复核完成（通过） | 最终得分 + 复核反馈 |
| `human_reviewed_fail` | 人工复核完成（未通过） | 最终得分 + 复核反馈 |

（`human_reviewed` 为早期值，前端按 `human_reviewed*` 前缀兼容识别。）历史行含 `cases` 的行走经典逐用例视图。

## 安全边界

- `SUPABASE_SECRET_KEY` / `UAPI_ACCESS_TOKEN` / `AI_API_KEY` 只进 Edge Function secrets；泄露即轮换。
- RLS：`submissions` 本人只读 + reviewers 只读；队列仅 reviewers 只读；写入只走 secret（judge/admin-review 函数）。
- AI 评分入参（题面 + 样例）由前端随提交携带，属演示级信任模型；如需防篡改可把题库迁入 Supabase 表由 Edge Function 读取。
- 用户代码在 UAPI 断网沙盒执行，不在 Supabase 内执行。
