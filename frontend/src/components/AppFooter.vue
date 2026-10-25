<script setup>
/**
 * 页脚（design-spec 5.7，微裁定已定）。
 * 单行三段式：左 CodeJudge 字标（版本号位不渲染——本地版删行不留占位、不编造版本号，仓库外链同理）
 * ｜中 关于 / 使用说明 链接 ｜右 本地处理声明一行。
 * ≤640px：三段纵排、间距 8px、居左。
 */
</script>

<template>
  <footer class="footer">
    <div class="footer__inner container container--wide">
      <!-- 左：字标（无版本号、无仓库外链、不留占位） -->
      <span class="footer__brand">CodeJudge</span>

      <!-- 中：链接 -->
      <nav class="footer__links" aria-label="页脚导航">
        <router-link to="/about" class="footer__link">关于</router-link>
        <router-link to="/about" class="footer__link">使用说明</router-link>
      </nav>

      <!-- 右：本地处理声明一行（Δ1-6 双模式表述替换） -->
      <p class="footer__decl">本地模式数据不出机；云模式仅判题历史入你的账号。</p>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  border-top: 1px solid var(--border);
  background: var(--bg-surface);
  padding: 24px 0 32px;
}

.footer__inner {
  display: flex;
  align-items: center;
  gap: var(--space-6);
  font-size: var(--text-caption);
  color: var(--text-muted);
}

.footer__brand {
  flex: none;
  font-family: var(--font-mono);
  font-size: var(--text-caption);
  font-weight: 700;
  color: var(--text-secondary);
  /* 版本号位不渲染：删行不留占位 */
}

.footer__links {
  display: flex;
  gap: var(--space-4);
  flex: none;
}

.footer__link {
  color: var(--text-muted);
}

.footer__link:hover {
  color: var(--primary);
}

.footer__decl {
  margin-left: auto;
  color: var(--text-muted);
  font-size: var(--text-caption);
  text-align: right;
}

@media (max-width: 640px) {
  .footer__inner {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .footer__decl {
    margin-left: 0;
    text-align: left;
  }
}
</style>
