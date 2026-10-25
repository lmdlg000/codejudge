<script setup>
/**
 * 判题流水线图（design-spec 9.3，960×220 内联 SVG）。
 * 四节点：builder → runner → comparator → scorer；下方分支 CE / TLE·RE / AC·PE·WA / per-case。
 * 颜色一律引用 tokens 同值（SVG 内写死 token HEX，禁止另调色）。
 */
</script>

<template>
  <figure class="pipe">
    <svg
      viewBox="0 0 960 220"
      width="100%"
      height="auto"
      role="img"
      aria-label="判题流水线：builder 编译、runner 限时执行、comparator 比对、scorer 计分"
    >
      <title>判题流水线四步</title>

      <!-- 连接箭头 -->
      <defs>
        <marker id="pipe-arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0 0l6 3-6 3z" fill="#35513D" />
        </marker>
      </defs>
      <line x1="216" y1="56" x2="248" y2="56" stroke="#35513D" stroke-width="1.5" marker-end="url(#pipe-arrow)" />
      <line x1="456" y1="56" x2="488" y2="56" stroke="#35513D" stroke-width="1.5" marker-end="url(#pipe-arrow)" />
      <line x1="696" y1="56" x2="728" y2="56" stroke="#35513D" stroke-width="1.5" marker-end="url(#pipe-arrow)" />

      <!-- builder -->
      <rect x="36" y="28" width="180" height="56" rx="6" fill="#101611" stroke="#35513D" stroke-width="1" />
      <text x="126" y="52" text-anchor="middle" font-family="monospace" font-size="14" fill="#D6E8D8">builder</text>
      <text x="126" y="70" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#9DBBA3">编译/构建</text>

      <!-- runner -->
      <rect x="276" y="28" width="180" height="56" rx="6" fill="#101611" stroke="#35513D" stroke-width="1" />
      <text x="366" y="52" text-anchor="middle" font-family="monospace" font-size="14" fill="#D6E8D8">runner</text>
      <text x="366" y="70" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#9DBBA3">限时执行</text>

      <!-- comparator -->
      <rect x="516" y="28" width="180" height="56" rx="6" fill="#101611" stroke="#35513D" stroke-width="1" />
      <text x="606" y="52" text-anchor="middle" font-family="monospace" font-size="14" fill="#D6E8D8">comparator</text>
      <text x="606" y="70" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#9DBBA3">比对</text>

      <!-- scorer -->
      <rect x="756" y="28" width="168" height="56" rx="6" fill="#101611" stroke="#35513D" stroke-width="1" />
      <text x="840" y="52" text-anchor="middle" font-family="monospace" font-size="14" fill="#D6E8D8">scorer</text>
      <text x="840" y="70" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#9DBBA3">计分</text>

      <!-- 分支虚线 -->
      <line x1="126" y1="84" x2="126" y2="120" stroke="#35513D" stroke-width="1" stroke-dasharray="3 3" />
      <line x1="366" y1="84" x2="366" y2="120" stroke="#35513D" stroke-width="1" stroke-dasharray="3 3" />
      <line x1="606" y1="84" x2="606" y2="120" stroke="#35513D" stroke-width="1" stroke-dasharray="3 3" />
      <line x1="840" y1="84" x2="840" y2="120" stroke="#35513D" stroke-width="1" stroke-dasharray="3 3" />

      <!-- CE -->
      <circle cx="102" cy="136" r="4" fill="#C792EA" />
      <text x="114" y="141" font-family="monospace" font-size="12" fill="#C792EA">CE</text>

      <!-- TLE · RE -->
      <circle cx="326" cy="136" r="4" fill="#FFB000" />
      <text x="338" y="141" font-family="monospace" font-size="12" fill="#FFB000">TLE</text>
      <circle cx="386" cy="136" r="4" fill="#FF6BD6" />
      <text x="398" y="141" font-family="monospace" font-size="12" fill="#FF6BD6">RE</text>

      <!-- AC · PE · WA -->
      <circle cx="546" cy="136" r="4" fill="#3DFF7A" />
      <text x="558" y="141" font-family="monospace" font-size="12" fill="#3DFF7A">AC</text>
      <circle cx="606" cy="136" r="4" fill="#56D4E0" />
      <text x="618" y="141" font-family="monospace" font-size="12" fill="#56D4E0">PE</text>
      <circle cx="666" cy="136" r="4" fill="#FF5F56" />
      <text x="678" y="141" font-family="monospace" font-size="12" fill="#FF5F56">WA</text>

      <!-- per-case → Summary -->
      <text x="840" y="141" text-anchor="middle" font-family="monospace" font-size="12" fill="#9DBBA3">per-case → Summary</text>

      <!-- 底注 -->
      <text x="480" y="196" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#6E8A75">
        构建失败则全部用例标 CE 并跳过后面步骤；判定顺序固定 CE → TLE → RE → 比对
      </text>
    </svg>
  </figure>
</template>

<style scoped>
.pipe {
  margin: 0;
  background: var(--bg-surface);
  border: var(--border);
  border-radius: var(--radius);
  padding: var(--space-4);
  overflow-x: auto;
}

.pipe svg {
  min-width: 640px;
  display: block;
}
</style>
