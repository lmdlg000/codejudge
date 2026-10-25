/**
 * 判定元数据 —— content-plan 第 4 节逐字（中文全称 / 帮助文案 / 信号翻译）。
 * 徽章代码 = Verdict 枚举值；颜色由 tokens.css 的 verdict-* 变量承担。
 */

export const VERDICTS = ['AC', 'PE', 'WA', 'TLE', 'RE', 'CE', 'SE']

export const VERDICT_META = {
  AC: {
    code: 'AC',
    label: '答案正确',
    help: '输出与标准答案逐字符一致（trim 模式忽略末尾多余换行）。ACM 模式下全部用例 AC 才记满分；OI 模式按通过用例的权重折算得分。'
  },
  PE: {
    code: 'PE',
    label: '格式错误',
    help: '内容对了，空格或换行不对。对照样例检查行尾空格、行数，以及是否多打了空格。'
  },
  WA: {
    code: 'WA',
    label: '答案错误',
    help: '输出与标准答案不一致。看提示里的行号，用本地 diff 对比你的输出与样例输出。'
  },
  TLE: {
    code: 'TLE',
    label: '超出时间限制',
    help: '程序超过时限被强制终止。常见原因：算法复杂度过高、死循环、cin/cout 未关同步。'
  },
  RE: {
    code: 'RE',
    label: '运行时错误',
    help: '程序异常退出。按信号提示查空指针、越界、除零；Windows 下若只见「进程非 0 退出码」，看 stderr 末尾定位。'
  },
  CE: {
    code: 'CE',
    label: '编译错误',
    help: '编译没通过。展开「编译器输出（末 200 行）」，从第一条 error: 开始改。'
  },
  SE: {
    code: 'SE',
    label: '系统错误',
    help: '这不是代码的判定结果。检查 problems/<id>/ 目录与 tests/ 是否完整、reports/ 是否可写，修复后重新提交。'
  }
}

/** RE 信号翻译（content-plan 第 4 节，原文照用 verdict.py 的 SIGNAL_MSG） */
export const SIGNAL_MSG = {
  SIGSEGV: '段错误（SIGSEGV）：非法内存访问——常见于空指针解引用或数组越界',
  SIGFPE: '算术异常（SIGFPE）：除零或整数溢出',
  SIGABRT: '程序中止（SIGABRT）：assert 失败或显式 abort()',
  SIGBUS: '总线错误（SIGBUS）：地址未对齐 / 非法映射',
  SIGKILL: '被强制终止（SIGKILL）：疑似内存超限或被系统回收',
  SIGXCPU: 'CPU 时间超限（SIGXCPU）'
}

/**
 * @param {string} verdict
 * @returns {{code:string, label:string, help:string}}
 */
export function verdictMeta(verdict) {
  return VERDICT_META[verdict] || {
    code: verdict || 'SE',
    label: '未知判定',
    help: '未识别的判定代码，请查看使用说明。'
  }
}

/**
 * RE 面板正文：有信号用信号翻译；signal 为 null 用 Windows 降级文案。
 * @param {{signal:string|null, exit_code:number|null}} c
 */
export function reExplain(c) {
  if (c.signal && SIGNAL_MSG[c.signal]) return SIGNAL_MSG[c.signal]
  const n = c.exit_code == null ? '—' : c.exit_code
  return `进程非 0 退出码（exit code ${n}）：Windows 下不细分信号，请看 stderr 定位。`
}
