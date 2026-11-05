/**
 * contenteditable 编辑区的「高亮刷新」工具。
 *
 * 为什么要单独抽出来：输入后要把纯文本重新高亮成 <span> 结构，必须整块替换 innerHTML；
 * 替换会清空浏览器选区。若只恢复一个「光标」位置，用户先打字再拖选、或先框选再触发
 * 防抖刷新时，选区会突然消失/跳到行首——看起来就像「选中块错位」。
 * 这里统一做三件事：
 *   1. 替换前把选区两端（anchor/focus）都换算成文本偏移量，恢复成完整 Range；
 *   2. 一并保存/恢复滚动位置，避免长文件刷新后跳回顶部；
 *   3. 刷新期间不夺焦（原本没聚焦的编辑区不会因为刷新而抢焦点）。
 */

/** 文本节点偏移量 → 该节点内的偏移（超过长度则落在末尾） */
function pointAt(root, target) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null)
  let acc = 0
  let node
  let last = null
  while ((node = walker.nextNode())) {
    const len = node.textContent.length
    if (target <= acc + len) return { node, offset: target - acc }
    acc += len
    last = node
  }
  if (last) return { node: last, offset: last.textContent.length }
  return { node: root, offset: 0 }
}

/** 选区端点 → 整个编辑区内的纯文本偏移量 */
function offsetOf(root, node, offset) {
  let acc = 0
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null)
  let current
  while ((current = walker.nextNode())) {
    if (current === node) return acc + offset
    acc += current.textContent.length
  }
  return acc
}

/**
 * 记录编辑区当前状态（选区两端 + 滚动位置 + 是否聚焦）。
 * 选区不在编辑区内时只记录滚动与聚焦，hasRange=false。
 */
export function captureEditableState(root) {
  if (!root) return null
  const state = {
    hasRange: false,
    start: 0,
    end: 0,
    focused: document.activeElement === root,
    scrollTop: root.scrollTop,
    scrollLeft: root.scrollLeft
  }
  const sel = window.getSelection()
  if (!sel || sel.rangeCount === 0) return state
  const range = sel.getRangeAt(0)
  if (!root.contains(range.startContainer) || !root.contains(range.endContainer)) return state
  state.hasRange = true
  state.start = offsetOf(root, range.startContainer, range.startOffset)
  state.end = offsetOf(root, range.endContainer, range.endOffset)
  return state
}

/** 用新的 HTML 替换内容，并把选区、滚动位置原样还回去 */
export function rehighlightEditable(root, html, state) {
  if (!root) return
  const saved = state || captureEditableState(root)
  root.innerHTML = html || ''
  if (!saved) return

  root.scrollTop = saved.scrollTop
  root.scrollLeft = saved.scrollLeft

  if (!saved.hasRange) return
  // 先夺回焦点再落选区：部分浏览器 focus() 会把光标重置到开头
  if (saved.focused && document.activeElement !== root) {
    root.focus({ preventScroll: true })
  }
  const start = pointAt(root, saved.start)
  const end = pointAt(root, saved.end)
  const range = document.createRange()
  range.setStart(start.node, start.offset)
  range.setEnd(end.node, end.offset)
  const sel = window.getSelection()
  if (sel) {
    sel.removeAllRanges()
    sel.addRange(range)
  }
}
