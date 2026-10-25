/**
 * 轻量 Toast（Δ2-1）：视口右下、2.4s 自动消失、aria-live=polite。
 */
import { ref } from 'vue'

const message = ref('')
const visible = ref(false)
let timer = null

export function useToast() {
  function show(msg, duration = 2400) {
    message.value = msg
    visible.value = true
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      visible.value = false
    }, duration)
  }

  function hide() {
    visible.value = false
    if (timer) clearTimeout(timer)
  }

  return { message, visible, show, hide }
}
