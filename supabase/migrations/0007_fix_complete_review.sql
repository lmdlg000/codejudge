-- 0007_fix_complete_review.sql —— 修复 complete_review 函数重名冲突
-- 根因：0002 和 0003 各定义了一次 complete_review（3 参数 vs 4 参数），
--       REVOKE/GRANT 不带参数签名导致 PostgreSQL 无法消歧
-- 执行入口：Supabase Dashboard → SQL Editor → 整段执行

-- 1) 删掉所有旧重载
DROP FUNCTION IF EXISTS public.complete_review(text, numeric, text);
DROP FUNCTION IF EXISTS public.complete_review(text, numeric, text, text);

-- 2) 只保留一个版本（4 参数，p_decision 有默认值）
CREATE OR REPLACE FUNCTION public.complete_review(
  p_submission_id text,
  p_score numeric,
  p_feedback text,
  p_decision text DEFAULT 'pass'
) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
AS $$
DECLARE
  v_decision text := CASE WHEN p_decision = 'fail' THEN 'fail' ELSE 'pass' END;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM public.reviewers WHERE id = auth.uid()) THEN
    RAISE EXCEPTION 'not a reviewer';
  END IF;

  UPDATE public.human_review_queue
     SET status = 'done',
         reviewed_by = auth.uid(),
         reviewed_score = p_score,
         reviewed_feedback = p_feedback,
         reviewed_at = now()
   WHERE submission_id = p_submission_id
     AND status = 'pending';

  UPDATE public.submissions
     SET status = 'human_reviewed_' || v_decision,
         score = p_score,
         reviewed_feedback = p_feedback,
         reviewed_at = now()
   WHERE id = p_submission_id;
END $$;

-- 3) 带完整签名的 REVOKE/GRANT（消除歧义）
REVOKE EXECUTE ON FUNCTION public.complete_review(text, numeric, text, text) FROM public, anon;
GRANT EXECUTE ON FUNCTION public.complete_review(text, numeric, text, text) TO authenticated;
