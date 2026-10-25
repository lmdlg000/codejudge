/**
 * 接口契约类型（site-spec 第 5 节 + G2 契约增补 v1）。
 * 字段名一次定死，前端不得自行改名；可选字段缺失时优雅降级。
 *
 * G2 增补：
 * - ProblemSummary 可选 topic / difficulty
 * - SubmissionSummary 可选 file_label
 */

/**
 * @typedef {Object} ProblemSummary
 * @property {string} id            题目 id，如 "P1"
 * @property {string} title         题目标题
 * @property {'acm'|'oi'} contest_type  默认计分模式
 * @property {number} score         满分
 * @property {number} test_count    用例数
 * @property {number} time_limit_ms 单用例时限
 * @property {number} memory_limit_mb 内存限制
 * @property {'g++'|'make'} build_mode 构建方式
 * @property {string} [topic]       题型（可选）
 * @property {string} [difficulty]  难度（可选）
 */

/**
 * @typedef {Object} ProblemDetail
 * @property {string} id
 * @property {string} title
 * @property {'acm'|'oi'} contest_type
 * @property {number} score
 * @property {'exact'|'trim'} compare_mode
 * @property {{time_ms:number, memory_mb:number}} limits
 * @property {{mode:'g++'|'make', command:string, src:string|null, default_filename:string|null}} build
 * @property {string} statement_md
 * @property {{input:string, output:string}[]} samples
 * @property {number} test_count
 * @property {string} [topic]
 * @property {string} [difficulty]
 */

/**
 * @typedef {Object} CaseResult
 * @property {string} name
 * @property {'AC'|'PE'|'WA'|'TLE'|'RE'|'CE'|'SE'} verdict
 * @property {number} time_ms
 * @property {number|null} exit_code
 * @property {number} weight
 * @property {string} message
 * @property {string|null} signal
 * @property {boolean} timed_out
 * @property {string|null} stderr_tail
 */

/**
 * @typedef {Object} Summary
 * @property {number} total
 * @property {number} passed
 * @property {number} pass_rate  0–1，保留 4 位小数
 * @property {number} score
 * @property {number} max_score
 * @property {number} partial_score
 */

/**
 * @typedef {Object} SubmissionResult
 * @property {string} submission_id
 * @property {string} problem_id
 * @property {string} problem_title
 * @property {'acm'|'oi'} mode
 * @property {string} created_at  ISO 8601
 * @property {'finished'|'failed'} status
 * @property {'AC'|'PE'|'WA'|'TLE'|'RE'|'CE'|'SE'} verdict
 * @property {Summary} summary
 * @property {CaseResult[]} cases
 * @property {string|null} build_log
 * @property {{name:string, content:string}[]} files
 * @property {string|null} message
 */

/**
 * @typedef {Object} SubmissionSummary
 * @property {string} submission_id
 * @property {string} problem_id
 * @property {string} problem_title
 * @property {string} created_at
 * @property {'acm'|'oi'} mode
 * @property {'AC'|'PE'|'WA'|'TLE'|'RE'|'CE'|'SE'} verdict
 * @property {Summary} summary
 * @property {string} [file_label]  提交文件显示名（G2 增补，可选）
 */

/**
 * @typedef {Object} ExampleItem
 * @property {string} name
 * @property {string} content
 * @property {'AC'|'PE'|'WA'|'TLE'|'RE'|'CE'|'make'} expect
 */

/**
 * @typedef {Object} HealthInfo
 * @property {string} status
 * @property {string} engine
 * @property {string} version
 * @property {number} problem_count
 */

export {}
