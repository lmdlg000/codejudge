-- 0002_ai_review.sql —— AI 初评 + 人工复核（异步 Realtime 流）
-- 承接 0001（profiles / submissions / RLS）。执行入口：Supabase → SQL Editor。
-- 状态机：judging → ai_scored | pending_review → human_reviewed

-- 1) submissions：生命周期状态 + AI 结果 + 复核结果
alter table public.submissions
  add column if not exists status text not null default 'ai_scored',
  add column if not exists ai_confidence numeric,
  add column if not exists ai_feedback text,
  add column if not exists reviewed_feedback text,
  add column if not exists reviewed_by uuid,
  add column if not exists reviewed_at timestamptz,
  add column if not exists scored_at timestamptz;

comment on column public.submissions.status is
  'judging | ai_scored | pending_review | human_reviewed（历史行默认 ai_scored 表示已完成）';

-- 2) 人工复核队列
create table if not exists public.human_review_queue (
  id uuid primary key default gen_random_uuid(),
  submission_id text not null unique references public.submissions (id) on delete cascade,
  reason text not null default 'low_confidence',   -- low_confidence | ai_failed
  ai_score numeric,
  ai_feedback text,
  ai_confidence numeric,
  status text not null default 'pending',          -- pending | done
  reviewed_by uuid,
  reviewed_score numeric,
  reviewed_feedback text,
  reviewed_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists human_review_queue_status_idx
  on public.human_review_queue (status, created_at desc);

-- 3) 复核人白名单（人工复核权限 = 在这张表里）
create table if not exists public.reviewers (
  id uuid primary key references auth.users (id) on delete cascade,
  created_at timestamptz not null default now()
);

-- 指定复核人（在 SQL Editor 执行，把 <auth-uid> 换成实际用户 id）：
--   insert into public.reviewers (id) values ('<auth-uid>');

-- 4) RLS
alter table public.human_review_queue enable row level security;
alter table public.reviewers enable row level security;

-- 复核人可读队列（前端 /review 页）；队列写入只走服务端 secret，不开 insert/update 策略
create policy "hrq_select_reviewer" on public.human_review_queue
  for select to authenticated
  using (exists (select 1 from public.reviewers r where r.id = auth.uid()));

create policy "reviewers_select_self" on public.reviewers
  for select to authenticated
  using (id = auth.uid());

-- 复核人可读任意被复核提交（否则复核页看不到源码与 AI 初评）
create policy "submissions_select_reviewer" on public.submissions
  for select to authenticated
  using (exists (select 1 from public.reviewers r where r.id = auth.uid()));

-- 5) 复核完成 RPC（security definer：复核人一次调用同时收队列 + 改状态）
create or replace function public.complete_review(
  p_submission_id text,
  p_score numeric,
  p_feedback text
) returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  if not exists (select 1 from public.reviewers where id = auth.uid()) then
    raise exception 'not a reviewer';
  end if;

  update public.human_review_queue
     set status = 'done',
         reviewed_by = auth.uid(),
         reviewed_score = p_score,
         reviewed_feedback = p_feedback,
         reviewed_at = now()
   where submission_id = p_submission_id
     and status = 'pending';

  update public.submissions
     set status = 'human_reviewed',
         score = p_score,
         reviewed_feedback = p_feedback,
         reviewed_at = now()
   where id = p_submission_id;
end $$;

revoke execute on function public.complete_review from public, anon;
grant execute on function public.complete_review to authenticated;

-- 6) Realtime：submissions 进发布（前端订阅状态变更，RLS 生效：只推本人/复核人可见行）
do $$
begin
  alter publication supabase_realtime add table public.submissions;
exception
  when duplicate_object then null;
  when others then null;
end $$;
