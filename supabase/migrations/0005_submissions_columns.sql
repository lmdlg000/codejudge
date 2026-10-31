-- 0005_submissions_columns.sql —— submissions 表全量列补齐（幂等）
-- 问题：初始表结构不完整，多个基础列从未创建，PostgREST 每次只报第一个缺失列
-- 执行入口：Supabase Dashboard → SQL Editor → 整段一次性执行
-- 所有 ADD COLUMN IF NOT EXISTS，已有列自动跳过，可反复执行

-- ===== 核心标识列 =====
alter table public.submissions
  add column if not exists id text primary key,
  add column if not exists user_id uuid not null default gen_random_uuid(),
  add column if not exists problem_id text not null default '';

-- ===== 判定结果列 =====
alter table public.submissions
  add column if not exists verdict text,
  add column if not exists score numeric,
  add column if not exists summary jsonb not null default '{}'::jsonb,
  add column if not exists cases jsonb not null default '[]'::jsonb;

-- ===== 提交内容列 =====
alter table public.submissions
  add column if not exists files jsonb not null default '[]'::jsonb,
  add column if not exists mode text,
  add column if not exists language text not null default 'cpp',
  add column if not exists file_label text not null default '',
  add column if not exists build_log text;

-- ===== 生命周期 / AI 评判列 =====
alter table public.submissions
  add column if not exists status text not null default 'ai_scored',
  add column if not exists run_summary jsonb,
  add column if not exists ai_confidence numeric,
  add column if not exists ai_feedback text;

-- ===== 人工复核列 =====
alter table public.submissions
  add column if not exists reviewed_feedback text,
  add column if not exists reviewed_by uuid,
  add column if not exists reviewed_at timestamptz,
  add column if not exists scored_at timestamptz;

-- ===== 时间列 =====
alter table public.submissions
  add column if not exists created_at timestamptz not null default now();

-- ===== 注释 =====
comment on column public.submissions.cases is
  '逐用例判定结果数组 [{case, verdict, time_ms, weight, message, ...}]';
comment on column public.submissions.summary is
  '判定汇总 {passed, total, rate, score, max_score}';
comment on column public.submissions.run_summary is
  'UAPI 执行器运行结果 {engine, skipped, all_accepted, cases:[...]}';
comment on column public.submissions.build_log is
  '构建/编译日志（CE 时展示编译器输出）';
comment on column public.submissions.status is
  'judging | ai_scored | pending_review | human_reviewed_pass | human_reviewed_fail';
