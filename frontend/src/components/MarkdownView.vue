<script setup>
/**
 * 题面 Markdown 渲染（markdown-it，site-spec 技术栈约定）。
 * stripH1：statement.md 的 `# 题名` 与页面 H1 合并显示，渲染前去掉首个 H1。
 */
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import { highlightCode } from '../utils/hljs.js'

const props = defineProps({
  source: { type: String, default: '' },
  stripH1: { type: Boolean, default: true }
})

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: false,
  // 围栏语言命中注册表（cpp/makefile/bash/json/python…）→ token 高亮；
  // 未注册或 ```text → 返回 ''，markdown-it 回退纯文本转义（样例 I/O 保持素文本）
  highlight: (str, lang) => highlightCode(str, lang)
})

const html = computed(() => {
  let src = props.source || ''
  if (props.stripH1) {
    // 只去掉首个顶级 H1（题名），后续标题层级不动
    src = src.replace(/^\s*#\s+[^\n]*\n/, '')
  }
  return md.render(src)
})
</script>

<template>
  <!-- eslint-disable-next-line vue/no-v-html —— markdown-it 已关 html，输出可信 -->
  <div class="md-body" v-html="html"></div>
</template>
