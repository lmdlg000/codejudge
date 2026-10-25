# CodeJudge 设计规范（design-spec.md）

> Phase 2 视觉交付物。唯一视觉依据；`frontend/src/styles/tokens.css` 为唯一样式令牌来源（第 10 节为可直接落地的变量表）。
> 依据文件：`docs/site-spec.md`（页面/功能/契约）、`docs/content-plan.md`（逐页文案与素材清单）、`requirements.md` §七（判定表）。
> **G1 契约修正（设计按此执行）**：① 结果页路由为 `/submissions/:sid`（`/results/:id` 作废）；② 同步判题、提交后直达结果页，**无轮询、无进度条占位**。
> 文案一律用 content-plan 原文，本规范只定排版与样式；发现的文案/字段冲突见文末「需要用户拍板」。

---

## 1. 设计原则与气质

**一句话定位**：克制、工程师感、可信的本机判题台 —— 像把 VS Code 的输出面板搬进一张干净的工单表格。

**三个形容词 + 参照物**：克制（无营销装饰）、工程师感（等宽数据 + 深色代码面板）、可信（判定与数字不修饰）—— 参照物：**Linear 的信息密度 + VS Code 面板的代码呈现**。

**视觉原则（5 条，冲突时按序裁决）**：

1. **工具本体压倒一切**：首页 H1 区压缩至 ≤ 220px 高，题目列表必须在首屏内露出（≥ 2 行/卡）；任何区块不得把「能点的题/能交的码」推到第二屏。
2. **数字与代码一律等宽**：判定代码、耗时 ms、得分、通过 x/y、权重、提交 ID、文件名、build_log —— 全部 mono；正文（题面、提示语）用无衬线，可读性优先。
3. **颜色只做判读加速，不做唯一信道**：7 种判定色永远与判定代码文字（AC/PE/…）+ 中文全称（aria-label / 悬停）并存；色弱用户靠文字即可完成全部判读。
4. **信息密度高但不拥挤**：表格行高 40px、单元格内边距 10px 12px、区块间距 48–64px；密度来自紧凑的行与统一的 4px 间距刻度，不来自缩小字号。
5. **零营销感**：无渐变大标题、无阴影堆叠、无插画铺垫；圆角统一 6px（小件 4px），阴影只给「浮起/弹层」一层（`--shadow-1`），卡片默认只有 1px 边框。

---

## 2. 色彩系统

### 2.0 主题策略（已定）

**默认浅色 UI + 深色代码面板（"凡代码皆深色"）**。

- 浏览/判读面（题面、表格、横幅、历史）用浅色：判定徽章 7 色在浅底上对比度最稳，表格密度高时浅底不累眼。
- 代码面（编辑区、题面样例块、build_log、stderr、输出对比）统一深色面板 `--code-bg #0F172A`：形成「代码 = 终端」的语义映射，与 Logo 终端光标呼应。
- 全深色主题**不做**（理由：逐用例表 + 徽章 7 色 + 横幅数字在深底上要逐对重验对比度，收益低于成本；整站暗色是 P2 的 F15）。`tokens.css` 已按「语义 token 分层」书写，P2 加 `[data-theme="dark"]` 覆盖块即可，不推翻本期结构。
- `prefers-color-scheme: dark` 本期只降级处理：不自动切深色（避免半深半浅破版），仅在深色代码面板内保持不变。

### 2.1 语义 token（浅色）

| token | HEX | 用途 | 对比度（配对 / 比值） |
|---|---|---|---|
| `--bg-page` | `#F8FAFC` | 页面底 | — |
| `--bg-surface` | `#FFFFFF` | 卡片/表格/横幅底 | — |
| `--bg-subtle` | `#F1F5F9` | 表头底、标签底、区块间隔底 | — |
| `--bg-inset` | `#E2E8F0` | 分隔条、禁用底、进度槽 | — |
| `--text-primary` | `#1E293B` | 正文、标题 | on `#FFFFFF` ≈ 14.6:1 ✓ |
| `--text-secondary` | `#475569` | 次要文字、表头文字、caption | on `#FFFFFF` ≈ 7.6:1 ✓ |
| `--text-muted` | `#64748B` | 占位、辅助说明、disabled 文字（仍可读） | on `#FFFFFF` ≈ 4.8:1 ✓ |
| `--text-disabled` | `#94A3B8` | 纯 disabled 图形/线，**不承载正文** | on `#FFFFFF` ≈ 2.6:1（仅装饰/禁用态，不用于正文） |
| `--text-inverse` | `#FFFFFF` | 深色底/主按钮上的文字 | on `#2563EB` ≈ 5.2:1 ✓ |
| `--border` | `#E2E8F0` | 常规边框（卡片、表格分隔） | 与 `#FFFFFF` 相邻可辨（非文本，3:1 不适用；承担信息的边框用 `--border-strong`） |
| `--border-strong` | `#CBD5E1` | 输入框边框、表格外框 | on `#FFFFFF` ≈ 1.9:1 —— 输入框边框同时有 label 与内边距形状，不单独靠色 |
| `--primary` | `#2563EB` | 主按钮、链接、焦点环、当前导航项 | 与 white 双向 ≈ 5.2:1 ✓ |
| `--primary-hover` | `#1D4ED8` | 主按钮 hover | white on it ≈ 6.5:1 ✓ |
| `--primary-active` | `#1E40AF` | 主按钮 pressed | white on it ≈ 8.6:1 ✓ |
| `--primary-bg` | `#EFF6FF` | 浅强调底（选中行、当前 tab） | 文字用 `--primary` on `#EFF6FF` ≈ 4.7:1 ✓ |
| `--focus-ring` | `#2563EB` | 焦点环（2px 实心 + 2px offset 白） | 3:1 vs 邻近色 ✓ |

### 2.2 语义色（成功/警告/危险/信息）——提示条与表单错误用

| 语义 | 文字 token | HEX | 底色 token | HEX | 对比度 |
|---|---|---|---|---|---|
| 成功 success | `--success-text` | `#166534` | `--success-bg` | `#DCFCE7` | ≈ 6.5:1 ✓ |
| 警告 warning | `--warning-text` | `#92400E` | `--warning-bg` | `#FEF3C7` | ≈ 6.9:1 ✓ |
| 危险 danger | `--danger-text` | `#991B1B` | `--danger-bg` | `#FEE2E2` | ≈ 6.7:1 ✓ |
| 信息 info | `--info-text` | `#075985` | `--info-bg` | `#E0F2FE` | ≈ 6.2:1 ✓ |

危险按钮实底：`--danger-solid #B91C1C`，hover `#991B1B`，white 文字 ≈ 6.5:1 ✓。

### 2.3 判定 7 色（AC / PE / WA / TLE / RE / CE / SE）

**结构（7 色统一）**：徽章 = 10% 色调底 + 800 档深色文字 + 300 档细边框 + 左侧 3px 同色系深条。**徽章内必须显示判定代码文字（mono 700）**，`title` 与 `aria-label` 给中文全称（见 content-plan §4）。

| 判定 | 代码色 text | 底色 bg | 边框 | 中文全称 | 使用位置 | 对比度（text on bg） |
|---|---|---|---|---|---|---|
| AC | `#166534` green-800 | `#DCFCE7` | `#86EFAC` | 答案正确 | 徽章、横幅左条（全部通过时）、历史行 | ≈ 6.5:1 ✓ |
| PE | `#075985` sky-800 | `#E0F2FE` | `#7DD3FC` | 格式错误 | 徽章、用例行 | ≈ 6.2:1 ✓ |
| WA | `#991B1B` red-800 | `#FEE2E2` | `#FCA5A5` | 答案错误 | 徽章、用例行 | ≈ 6.7:1 ✓ |
| TLE | `#9A3412` orange-800 | `#FFEDD5` | `#FDBA74` | 超出时间限制 | 徽章、用例行 | ≈ 6.1:1 ✓ |
| RE | `#831843` pink-900 | `#FCE7F3` | `#F9A8D4` | 运行时错误 | 徽章、用例行、RE 面板标题条 | ≈ 8.0:1 ✓ |
| CE | `#6B21A8` purple-800 | `#F3E8FF` | `#D8B4FE` | 编译错误 | 徽章、CE 面板标题条、横幅左条 | ≈ 6.4:1 ✓ |
| SE | `#44403C` stone-700 | `#F5F5F4` | `#D6D3D1` | 系统错误 | 徽章、SE 空/错状态 | ≈ 7.3:1 ✓ |

**互相可区分 + 色弱设计**：

1. **文字主信道**：徽章 100% 显示 `AC`/`PE`/… 代码；横幅 H1 显示中文全称；表格行可展开「帮助文案」。灰度打印/全色盲下仍可判读。
2. **色相分离**：绿(AC) / 蓝(PE) / 红(WA) / 橙(TLE) / 玫红(RE) / 紫(CE) / 灰棕(SE)。红绿这对唯一的色弱冲突对，靠 **WA 偏正红 + AC 偏深绿 + 明度差（AC text L 更深）** 与文字代码双保险；不做「只红只绿」的纯色块表意。
3. **明度阶梯**：7 个 text 色均压在 L*≈30–40 深带，bg 均在 L*≈90+ 浅带，徽章内部对比一致；徽章之间的区分不依赖明度而依赖色相 + 文字。
4. **禁止**：只给色条不给文字；把 7 色当装饰色用在与判定无关的元素上（如普通标签）。

### 2.4 代码面板色（深色，独立一组）

| token | HEX | 用途 | 对比度 |
|---|---|---|---|
| `--code-bg` | `#0F172A` | 编辑器/代码块/build_log/stderr 底 | — |
| `--code-text` | `#E2E8F0` | 代码正文 | on `#0F172A` ≈ 14.5:1 ✓ |
| `--code-muted` | `#94A3B8` | 行号、注释、次要输出 | on `#0F172A` ≈ 6.4:1 ✓ |
| `--code-accent` | `#7DD3FC` | 高亮 token（可选，CodeMirror 皮肤） | on `#0F172A` ≈ 11:1 ✓ |
| `--code-error` | `#FCA5A5` | build_log 首条 `error:` 行文字 | on `#0F172A` ≈ 9.2:1 ✓ |
| `--code-error-bar` | `#EF4444` | 首条 error 行左侧 3px 色条 | 非文本 |
| `--code-border` | `#1E293B` | 代码面板内分隔 | 非文本 |

---

## 3. 字体阶梯

**字族（只有两族）**：

```css
--font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
             "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans SC", sans-serif;
--font-mono: "JetBrains Mono", "Cascadia Code", "SF Mono", Consolas,
             "Cascadia Mono", Menlo, monospace;
```

**阶梯（桌面值；移动端不缩放字号，只降区块间距）**：

| 级别 | 字号 / 行高 | 字重 | 字距 | 字族 | 用途 |
|---|---|---|---|---|---|
| H1 | 32px / 1.25 | 700 | -0.02em | sans | 每页唯一（如「P1 运费计算」） |
| H2 | 24px / 1.35 | 700 | -0.01em | sans | 区块标题（题面正文、逐用例判定…） |
| H3 | 18px / 1.4 | 600 | 0 | sans | 子区块（样例输入、编译器输出…） |
| H4 | 16px / 1.5 | 600 | 0 | sans | 卡片标题、面板标题 |
| body-lg | 16px / 1.75 | 400 | 0 | sans | 题面正文、说明段落 |
| body | 15px / 1.7 | 400 | 0 | sans | 默认正文、列表、表格文字 |
| caption | 13px / 1.55 | 400 | 0 | sans | 表头、辅助说明、图注、横幅补充行 |
| micro | 12px / 1.4 | 500 | 0.02em | sans | 标签、页脚、时间戳旁注 |

**等宽角色（全部 `--font-mono`）**：

| 角色 | 字号 / 行高 | 字重 | 用途 |
|---|---|---|---|
| mono-code | 13px / 1.6 | 400 | 代码编辑区、代码块、build_log、stderr、输出对比 |
| mono-data | 13px / 1.4 | 500 | 表格耗时/权重/得分单元、提交 ID、文件名 |
| mono-badge | 12px / 1 | 700 | 判定徽章代码（AC/PE/…），字距 0.04em |
| mono-banner | 22px / 1.3 | 700 | 得分横幅主行（`--banner-size`，≤640px 降 15px） |
| mono-inline | 13px / 1.5 | 400 | 正文内联代码（`w`、`d`、`main.cpp` 等），浅色底 `--bg-subtle` + 4px 圆角 |

规则：正文不用 mono（除上表角色）；H1–H4 不用 mono（横幅除外，它是数据不是标题）。

---

## 4. 间距与栅格

**间距刻度（4px 基数）**：`4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48 / 64 / 80 / 96`（token：`--space-1 … --space-12`，见第 10 节）。

| 项 | 值 |
|---|---|
| 区块纵向间距（桌面） | 64px（同页区块间）；页级大间隔 80px（页脚前） |
| 区块纵向间距（≤640px） | 48px |
| 卡片内边距 | 20px 24px（≤640px 16px） |
| 表格单元格内边距 | 10px 12px |
| 表格行高 | 40px（表头 36px）；逐用例表紧凑行 36px |
| 控件高度 | 按钮 40px（主 CTA 44px）；输入/下拉 40px；小按钮 32px（不低于 32px，点击区用 padding 撑到 44px 触达） |
| 内容容器 | `--container` 1120px（列表/历史/关于）；`--container-wide` 1280px（题目详情双栏、结果页）；`--container-narrow` 880px（关于页纯文本段） |
| 容器两侧留白 | 24px（≤640px 16px） |
| 栅格 | 12 列，gutter 24px；题目详情 = 7/5 列（题面 7、编辑区 5），间隔 32px |
| 表格密度 | 默认密度（40px 行）；逐用例表可用 36px 行（`--table-row-compact`），两表不混用 |

---

## 5. 组件样式

> 通用：圆角 `--radius-sm 4px`（徽章/标签）、`--radius 6px`（按钮/输入/卡片）、`--radius-lg 10px`（面板/弹层）；边框 1px `--border`；阴影仅 `--shadow-1: 0 1px 2px rgba(15,23,42,.06), 0 4px 12px rgba(15,23,42,.08)`（卡片 hover / 抽屉 / 下拉）。
> 每个可交互组件四态齐全：default / hover / active / disabled；表单加 error；按钮加 loading。

### 5.1 按钮

**尺寸基准**：高 40px，padding 0 16px，圆角 6px，字号 14px/600，字距 0；主 CTA 高 44px、padding 0 20px、字号 15px/600。最小点击区 44×44px（小按钮用 `position:relative` + 伪元素扩点击区）。

| 角色 | default | hover | active | disabled / loading |
|---|---|---|---|---|
| **主按钮**（提交判题 / 改代码再交一次 / 从 P1 开始） | bg `--primary`，文字 `#FFFFFF`，无边框 | bg `--primary-hover` | bg `--primary-active`，translateY(1px) | bg `--border-strong`，文字 `--text-muted`，cursor not-allowed；**loading 时保持主色**，文案换「判题中…」+ 左侧 16px 旋转环（`--spinner`：2px 边 `rgba(255,255,255,.4)` + 白色四分之一弧，0.8s linear infinite），`disabled` + `aria-busy="true"`，不可重复点击 |
| **次按钮**（先看使用说明 / 看提交历史 / 上传 .cpp） | bg `--bg-surface`，文字 `--text-primary`，边框 `--border-strong` | bg `--bg-subtle`，边框 `--text-muted` | bg `--bg-inset` | 文字 `--text-disabled`，边框 `--border`，bg `--bg-subtle` |
| **危险按钮**（删除文件项等，预留） | bg `--danger-solid #B91C1C`，白字 | `#991B1B` | `#7F1D1D` | 同主按钮 disabled |
| **文字按钮**（复制样例 / 看输出对比 / 收起对比） | 文字 `--primary`，无边框，padding 0 8px，高 32px | 文字 `--primary-hover`，底 `--primary-bg` | 文字 `--primary-active` | `--text-disabled` |
| **图标按钮**（复制/下载/筛选，16px 图标） | 32×32px，图标 `--text-secondary`，圆角 4px | bg `--bg-subtle`，图标 `--text-primary` | bg `--bg-inset` | 图标 `--text-disabled` |

焦点态（全部按钮/链接/可点行）：`outline: 2px solid var(--focus-ring); outline-offset: 2px;`，**不得 `outline:none`**。
空源码时主按钮 disabled，`title="先写点代码再提交。空源码不会进入评测队列。"`（文案取自 content-plan）。

### 5.2 题目卡片（首页列表，行式卡片）

**形态定稿**：**单列行式卡片**（不是多列方卡）。理由：变长标签组（模式/时限/内存/满分/用例数）+ 可选的题型/难度副文案需要弹性横排；整行可点 + 右侧固定 CTA，兼得表格密度与卡片点击热区。

```
┌──────────────────────────────────────────────────────────────┐
│ P1  运费计算                    [OI][1000ms][256MB][4 用例]   │
│ 分支 / 分段计费 · 入门                    [ 去做 P1 ](主按钮小号) │
└──────────────────────────────────────────────────────────────┘
```

- 结构：左侧 `--mono-data` 题号（宽 48px，`--text-secondary`）→ 题名 H4 + 一行副文案（`topic`·`difficulty`，**字段可得即渲染，缺失优雅降级不渲染该单元格/片段**，两项都缺则该副文案行整行省略）→ 右侧标签组 + CTA。
- 默认：bg `--bg-surface`，边框 `--border`，圆角 6px，padding 16px 20px，行间距 12px。
- hover：边框 `--primary`（1px）+ `--shadow-1`，CTA 同步 hover；`cursor:pointer`。
- 焦点：整卡 `tabindex="0"` + focus-ring，Enter 触发跳转（卡片本体是 `<a>` 或包一层链接，保键盘可达）。
- 标签（Tag）：高 22px，padding 0 8px，圆角 4px，`caption` 字号，bg `--bg-subtle`，文字 `--text-secondary`；**模式标签（ACM/OI）用 `--primary-bg` + `--primary` 文字** 以示区分；数字类（时限/满分）用 mono 12px。

### 5.3 数据表格（逐用例表 + 历史表，共用骨架）

- 容器：bg `--bg-surface`，边框 1px `--border`，圆角 6px，`overflow:hidden`；表格 `width:100%`，`border-collapse:collapse`。
- 表头：bg `--bg-subtle`，文字 `--text-secondary`，`caption` 12px/600 大写字距 0.04em（中文不转大写，仅字距），高 36px，`th scope="col"`。
- 行：高 40px（逐用例 36px），分隔线 1px `--border`；hover 行 bg `--primary-bg`（可点行）+ cursor pointer；斑马纹**不做**（hover 已够，避免和徽章底色打架）。
- 数字列（耗时/权重/得分/通过）右对齐或居中、mono `--mono-data`；文本列左对齐。
- 空提示单元格统一 `—`（em dash，`--text-muted`）。

**逐用例表（结果页，列冻结）**：`用例 | 判定 | 耗时 | 权重 | 提示` + 展开行。
- 用例：mono 文件名（`1.in`）。
- 判定：VerdictBadge（见 5.4）。
- 耗时：mono，TLE 行显示 `1000ms`（限时值）时可加 `--warning-text` 色。
- 权重：mono 数字。
- 提示：`--text-secondary` 13px，超长截断 1 行 + `title` 全文；空显示 `—`。
- 展开：行首/行尾「看输出对比」文字按钮；展开后插入详情行（colspan=5），内部左右双栏「期望输出 / 实际输出」深色代码块（`--code-bg`，各 max-height 240px，`overflow:auto`），差异行背景 `rgba(239,68,68,.18)` + 左侧 2px `--code-error-bar`；按钮文字切「收起对比」。

**历史表（`/submissions`，列按 content-plan 全列 + G2 补字段裁定）**：`时间 | 题目 | 提交文件 | 判定 | 通过 | 得分 | 操作`。
- 时间 mono 13px `--text-secondary`；题目列「P1 运费计算」（id mono + 标题）；提交文件列 `file_label`（如 `main.cpp`，多文件取主文件名或「N 个文件」）mono 文件名、列宽 140px；判定徽章；通过 `4/4` mono；得分 `100/100` mono。
- **渲染规则（G2）**：`file_label` **字段可得即渲染，缺失优雅降级不渲染该单元格内容**；其余列不变。
- **整列缺失边界（微裁定，已定）**：当全部行都缺 `file_label` 时，**列头保留、缺失单元格统一显示 `—`，不整列隐藏**（表头对齐不跳变）。
- 操作列：文字按钮「看结果」「看 JSON」。
- 整行可点（= 看结果），行 `tabindex`，focus-ring。
- 表上方筛选条：题目下拉（全部/P1…P6）+ 判定下拉（全部/7 种）+ 统计行 `共 N 次评测 · AC a 次 · 通过率 p%`（caption，数字 mono）。

### 5.4 判定徽章（VerdictBadge）

- 尺寸：高 22px，min-width 48px，padding 0 8px，圆角 4px，左 3px 同系深色条（`border-left:3px solid`）。
- 文字：`mono-badge`（12px/700/0.04em），内容固定为 2–3 位代码（AC/PE/WA/TLE/RE/CE/SE），颜色 = 该判定 text 色，底 = bg 色，边框 = 该判定 border 色。
- 语义：`role="img"` 不必要；用 `<span class="badge badge--ac" title="答案正确">AC</span>` + `aria-label="判定：答案正确"`（或在相邻单元格已含中文时 aria-hidden 徽章、由 `th` 关联）。
- 总判定徽章（横幅/H1 旁）放大版：高 28px，min-width 64px，字号 14px/700，同一套色。
- 7 色速查：见 2.3 表（HEX 三件套）。

### 5.5 得分横幅（ScoreBanner，格式冻结）

- 位置：结果页 H1 之下、一切面板之上；满容器宽（`--container-wide`）。
- 外观：bg `--bg-surface`，边框 1px `--border`，圆角 6px，**左侧 4px 竖条颜色 = 总判定色**（AC 绿 / CE 紫 / …）；padding 20px 24px。
- 主行（**格式逐字冻结**）：`通过 4/4 · 通过率 100% · 得分 100/100`，`mono-banner`（22px/700），颜色 `--text-primary`。
  - **防换行破版**：主行 `white-space:nowrap`；结构上拆三个 `<span class="seg">通过 4/4</span><span class="sep">·</span>…`，`.seg{white-space:nowrap}`，`.sep{margin:0 10px;color:var(--text-muted)}`。容器 `overflow-x:auto`（≤640px 字号降 15px，一般不再溢出）；**禁止**在 sep 处折行后把 `·` 留在行首。
  - 数字部分（4/4、100%、100/100）可分别包 span 便于 tabular-nums（`font-variant-numeric:tabular-nums`）。
- 补充行（主行下 8px，caption 13px `--text-secondary`，三选一，文案取自 content-plan）：
  - OI：`OI 模式：按通过用例的权重折算得分。`
  - ACM 全 AC：`ACM 模式：全部用例通过，记满分。`
  - ACM 非全 AC：`ACM 模式：未全对记 0 分。加权部分得分 {X}，仅供参考。`
- 横幅右侧可放总判定徽章（放大版）与 `mono-data` 的 `submission_id`（小字，`--text-muted`）。

### 5.6 页头导航（Header）

- 高 56px，bg `--bg-surface`，底部 1px `--border`，`position:sticky;top:0;z-index:20`。
- 左：Logo 字标（高 32px，见 9.1）+ 站名旁不加副标（零营销）。
- 右（桌面 ≥1024px）：文字链接 `题目列表 / 提交历史 / 使用说明`（14px/500，间距 24px），当前页 `--primary` + 底部 2px `--primary` 下划线（offset 18px）；hover `--primary-hover`。
- 健康点：导航右侧一枚 8px 圆点 + 微文案 `本机评测`（`micro`，`--text-muted`）；引擎异常（health 503）时圆点转 `--warning-text` 并可点出提示条（见 5.10）。不放版本号（本地版页脚版本位亦不渲染，见 5.7）。
- 移动导航形态（<1024px）：**右侧抽屉**。汉堡按钮 44×44px（三线图标 16px），点击滑出宽 260px 全高面板（bg `--bg-surface`，左 1px 边框，`--shadow-1`，translateX 200ms ease-out；`prefers-reduced-motion` 时无动画直接显隐）。抽屉内链接单列、行高 48px、当前项 `--primary-bg` 底；遮罩 `rgba(15,23,42,.4)`，点遮罩/Esc 关闭，焦点锁在抽屉内。

### 5.7 页脚（Footer）

- 顶边 1px `--border`，bg `--bg-surface`，padding 24px 0 32px，文字 `caption`/`micro`，`--text-muted`。
- 单行三段式（不设多栏）：左 `CodeJudge` 字标（**版本号位不渲染**——本地版删行不留占位、不编造版本号，仓库外链同理）｜中 `关于` `使用说明` 链接（hover `--primary`）｜右 本地处理声明一行：`本机判题、数据不出机。源码与报告只写入本地 reports/ 目录，不联网。`（口径对齐 content-plan 隐私声明与 site-spec G0「本机判题、数据不出机」）。
- ≤640px：三段纵排、间距 8px、居左。

### 5.8 代码编辑区（CodeEditor）

- 容器：bg `--code-bg`，圆角 6px，1px `--code-border`，padding 0；顶部工具条高 36px（bg `#1E293B`）：左 mono 13px 文件名 `main.cpp`（`--code-muted`），右「上传 .cpp 文件」「载入 AC 演示」小按钮（深底描边样式：文字 `--code-text`，边框 `#334155`，hover bg `#334155`）。
- textarea（P0）：宽 100%，min-height 320px（题目详情页 420px），padding 12px 16px，`--mono-code` 13px/1.6，文字 `--code-text`，caret `#7DD3FC`，`resize:vertical`，`spellcheck=false`，`wrap="off"`（横向滚动保代码结构）；placeholder `把 main.cpp 的内容贴到这里`（色 `--code-muted`）。
- 焦点：容器 2px `--focus-ring` 外描边（`outline-offset:2px`）。
- CodeMirror 6 皮肤（P1，替换 textarea，提交数据结构不变）：同 `--code-bg/#1E293B/#E2E8F0` 三色；行号列宽 40px、行号 `--code-muted`；当前行底 `rgba(125,211,252,.06)`；选区 `rgba(37,99,235,.35)`；语法高亮四色封顶：关键字 `#7DD3FC`、字符串 `#86EFAC`、数字 `#FDBA74`、注释 `#94A3B8`（勿做成彩虹）。
- 多文件面板（P1，P6 make 题）：工具条下文件标签行（每文件一枚 tab：文件名 mono + 关闭 ×），「+ 添加文件」文字按钮；文件名输入用白名单校验错误态（见 5.9 error）。

### 5.9 表单控件（下拉/输入/文件名）

- 高 40px，bg `--bg-surface`，边框 1px `--border-strong`，圆角 6px，padding 0 12px，14px sans；label 上置、12px/600 `--text-secondary`、间距 6px；字段间距 16px。
- hover 边框 `--text-muted`；focus 2px `--focus-ring` outline + 边框 `--primary`；error 边框 `--danger-solid` + 下方 12px `--danger-text` 说明文字（图标 + 文字，不只靠红）。
- 下拉（语言选择 `C++17（g++ -O2）`、筛选器）：右侧 16px chevron 图标；禁用项 `--text-disabled` + 说明 `当前镜像仅内置 C++17`。

### 5.10 提示条（Alert，4 种）

- 结构：图标 16px + 标题（14px/600）+ 正文（13px/1.6），圆角 6px，padding 12px 16px，1px 边框同色系 300 档；左 3px 色条。
- 成功：`--success-bg` 底 + `--success-text` 文字；警告：`--warning-*`；错误/危险：`--danger-*`；信息：`--info-*`。
- 图标形状区分（色弱）：成功 ✓、警告 ▲、错误 ✕、信息 ℹ（内联 SVG，1.5 stroke）。
- 用法映射（8 个错误码 → 错误提示条，文案取 site-spec 5.2 前端提示列，逐字使用）：
  `VALIDATION_ERROR`→错误条；`PROBLEM_NOT_FOUND`/`SUBMISSION_NOT_FOUND`→错误条 + 出路按钮；`PAYLOAD_TOO_LARGE`→错误条；`JUDGE_TIMEOUT`/`JUDGE_BUSY`→警告条；`ENGINE_UNAVAILABLE`→警告条 + `查看使用说明`；`INTERNAL_ERROR`→错误条；网络断开兜底→错误条 `判题后端没启动。在项目根目录运行 uvicorn 后端入口后刷新本页。` + `刷新页面` 按钮。
- 空源码拦截提示（不进错误条，用 tooltip + 按钮 title）：`先写点代码再提交。空源码不会进入评测队列。`

### 5.11 空状态（EmptyState）

- 结构：240×160 SVG 插图（9.5–9.7）+ 一句话（body 15px `--text-secondary`）+ 一个主按钮出路；整体居中，padding 48px 24px。
- 三处文案（content-plan §5）逐字用：无提交历史 / 筛选无结果（按钮 `清除筛选`）/ 题目加载失败（按钮 `回到题目列表`）。

### 5.12 折叠面板（输出对比 / stderr / build_log / 源码回显）

- 触发器：文字按钮（5.1 文字按钮规格）+ 右侧 12px chevron（展开转 180°，160ms）；`aria-expanded` + `aria-controls` 必须有。
- 面板体：bg `--code-bg` 代码块规格（`--mono-code`，padding 12px 16px，圆角 6px，max-height 320px `overflow:auto`），或浅色容器内嵌深色块（stderr 复制按钮放块右上角）。
- 展开动画：`grid-template-rows 0fr→1fr` 或 max-height 过渡 160ms ease-out；`prefers-reduced-motion:reduce` 时无动画。
- **build_log 专用**：标题行 `编译器输出（末 200 行）`（H4）+ 说明行 caption；等宽滚动块 max-height 480px；**首条含 `error:` 的行**：左 3px `--code-error-bar` 竖条 + 文字 `--code-error` + 字重 700 + 行底 `rgba(239,68,68,.12)`；其余行 `--code-muted`。默认展开（CE 时），折叠按钮 `展开编译输出`/`收起编译输出`。
- **stderr 折叠**（RE 面板内）：信号翻译一句（body，`--text-primary`，图标用 RE 徽章色）+ `stderr 末 2KB` 深色块默认折叠，按钮 `复制 stderr`（复制成功瞬时切「已复制」1.2s）。
- **源码回显**：标题 `提交源码`（H3）+ 文件名 tab（多文件时），深色块，默认**折叠**，按钮 `展开源码`/`收起源码`；只读。

### 5.13 标签栏（题目限制摘要，TagBar）

- 位置：题目详情页题面之上、编辑区之上各一份（同内容）；一行 6 枚标签（content-plan 区块 2）：`题号 P1` `模式 OI` `时限 1000ms` `内存 256MB` `满分 100` `构建 g++ -O2 -std=c++17`。
- 形态：高 28px，padding 0 10px，圆角 4px，bg `--bg-subtle`，`caption` 12px；键名（题号/模式/时限…）`--text-muted`，值 mono 12px/500 `--text-primary`；标签间距 8px，`flex-wrap:wrap`。
- 模式值（ACM/OI）用 `--primary-bg` + `--primary` 文字。

### 5.14 代码块（题面样例 / 命令块，CodeBlock）

- 样例块：外层 `<figure>`，顶部条高 32px（bg `#1E293B`）：左 caption `样例输入`/`样例输出`（`--code-muted`），右文字按钮 `复制样例`（深底样式）；主体 `--code-bg` + `--mono-code` + `--code-text`，padding 12px 16px，圆角 0 0 6px 6px，`overflow-x:auto`，`white-space:pre`。
- 输入/输出成对时两块间距 16px；多组样例以 H3「样例输入 2」分组。
- 命令块（/about 快速开始）：同规格，语言标 `bash`，按钮 `复制命令`。

---

## 6. 响应式断点策略

断点：**640 / 1024 / 1280**（px）；基准桌面优先。

| 断点 | 布局规则 |
|---|---|
| **≥1280（宽屏）** | 容器 `--container-wide` 1280px 居中（**封顶不拉伸**）；题目详情 7/5 双栏（题面/编辑区，gap 32px）；结果页横幅 + 表 + 面板单列宽版；首页题目行式卡片单列满宽；历史表全列 |
| **1024–1279（桌面）** | 容器 1120px；题目详情仍双栏但降 6/6（题面与编辑区各半，编辑区 min-height 360px）；标签栏可折行；导航仍横排 |
| **640–1023（平板）** | 导航转右抽屉（5.6）；题目详情**单列**：题面 → 标签栏 → 编辑区（编辑区 min-height 320px）；结果页逐用例表隐藏「权重」列（权重并入提示列前缀 `权重 25 ·`，或表格横向滚动 `overflow-x:auto` 保全列——**默认横向滚动保列**，列内容不删）；首页行式卡片降为两行堆叠（题号+题名一行，标签+CTA 一行） |
| **<640（移动）** | 容器留白 16px；H1 降至 24px/1.3（字号仅此一处降，正文不缩）；区块间距 48px；得分横幅 mono 15px 仍单行（必要时容器横向滚动）；**逐用例表转堆叠卡片**（每用例一张：首行 判定徽章+用例名，次行 耗时/权重 mono，提示全文换行，展开输出对比改全宽上下块）；历史表转堆叠卡片（时间/题目/判定/得分/操作）；编辑区 min-height 280px；CE build_log 仍深色横滚；页脚三段纵排 |

**移动端导航形态（硬性）**：右侧抽屉 260px + 遮罩，汉堡 44×44px，详见 5.6。

**逐用例表格降级顺序**（写死，防止前端各写各的）：≥1024 全列 → 640–1023 横向滚动保全列 → <640 堆叠卡片。

**代码编辑区降级顺序**：textarea 不缩字号（13px），高度 420→360→280px；`wrap="off"` 横向滚动；工具条按钮在 <640 时收进「⋯」溢出菜单（保留上传与载入演示两个最常用）。

---

## 7. 关键页面线框与视觉说明

> 路由以 site-spec §2 为准：`/`、`/problems/:pid`、`/submissions/:sid`、`/submissions`、`/about`。
> 阅读顺序 = 线框从上到下；「视觉重心」= 该页第一眼落点。

### 7.1 首页 `/`（题目列表）

```
┌────────────────────────────────────────────────────────┐
│ Header: [Logo CodeJudge]            题目列表 提交历史 使用说明 │  sticky 56px
├────────────────────────────────────────────────────────┤
│ H1  选一道题，提交代码，拿逐用例判定                       │  ≤220px 压缩区
│ 副标题（1–2 行，body-lg，--text-secondary，max-width 720px）│
│ [从 P1 运费计算开始](主)  [先看使用说明](次)                │
│ 信任条：7 种判定 · ACM/OI 双模式 · 6 道内置题 · 本地评测…   │  caption，4 格
├────────────────────────────────────────────────────────┤
│ 题目列表（工具本体，视觉重心）                             │
│ ┌ P1  运费计算  分支/分段计费·入门   [OI][1000ms][256MB][4 用例] [去做 P1]┐│
│ ┌ P2  字符串压缩 字符串处理·简单     …                                  ┐│  行式卡片 ×6
│ ┌ P3 … ┐ ┌ P4 … ┐ ┌ P5 … ┐ ┌ P6 … ┐                       │  间距 12px
├────────────────────────────────────────────────────────┤
│ 三步上手：选题 / 交码 / 看结果（3 列，≤640 纵排）           │  次要区
│ 判定速查：7 枚徽章一行 + 链接「使用说明 · 判定表」           │
│ 环境与隐私一行 + 「查看完整运行命令」链接                    │
├────────────────────────────────────────────────────────┤
│ Footer                                                    │
└────────────────────────────────────────────────────────┘
```

- **层级**：H1（32/700）→ 副标题（16/400 secondary）→ CTA 行（主 44px 高）→ 信任条（12px caption，格间 `·`）→ 题目列表（页面主体，留白上 32px）。
- **视觉重心**：题目列表区。首屏（768px 高）必须露出 H1 区 + 至少 2 张题目卡片 → H1 区整体压到 220px 内（副标题最多 2 行，溢出省略）。
- **区块视觉要点**：信任条四格用 1px 竖分隔或 `·` 分隔，数字（7/6）mono；三步上手用编号圆点（24px 圆，`--primary-bg` + `--primary` 数字）；判定速查徽章用 5.4 原尺寸。
- **间距**：H1 区 → 列表 32px；列表 → 三步上手 64px；三步上手 → 判定速查 48px；→ 环境隐私 48px；→ 页脚 80px。

### 7.2 题目详情 + 提交 `/problems/:pid`（核心转化页）

```
┌──────────────────────────────────────────────────────────────┐
│ Header                                                         │
├─────────────────────────────┬──────────────────────────────────┤
│ 面包屑 题目列表 / P1          │                                  │
│ H1 P1 运费计算                │  标签栏：题号|模式|时限|内存|满分|构建 │
│ 标签栏（同右，≤1280 可只留左） │──────────────────────────────────│
│ 题面正文（H2 分节渲染）        │  语言下拉 C++17（g++ -O2）          │
│  题目背景/输入格式/输出格式    │  ┌─ CodeEditor（深色，420px）────┐ │
│  样例输入/样例输出（figure）   │  │ main.cpp            上传/载入 │ │
│  数据范围                     │  │ textarea / CodeMirror          │ │
│  （7 列宽）                   │  └───────────────────────────────┘ │
│                               │  [提交判题](主 CTA 44px)           │
│                               │  [载入 AC 演示](次)                │
│                               │  （P1）判题演示条 7 枚              │
│                               │  （5 列宽）                        │
├─────────────────────────────┴──────────────────────────────────┤
│ Footer                                                          │
└────────────────────────────────────────────────────────────────┘
```

- **层级**：H1 → 标签栏（一屏 5–6 个事实）→ 左栏题面（body-lg 16/1.75）→ 右栏编辑器（视觉重心之二）→ 主 CTA。
- **视觉重心**：右栏编辑区 + 主 CTA（深色块在浅色页里自成焦点）；左栏题面服务「读得懂」。
- **区块视觉要点**：样例块用 5.14 深色 figure；限制摘要（标签栏）在 ≥1024 时右栏顶部常驻一份、左栏顶部一份可省（避免重复：**≥1024 只在右栏顶部放标签栏**，<1024 单列时放题面 H1 之下）；判题演示条（仅 P1）为一行 chip：`P1_ac.cpp → AC` 等，chip 高 28px、可点载入，预期判定用对应色徽章小号。
- **错误提示条**（提交失败/引擎不可用）插在主 CTA 正下方、判题演示条之上。
- **间距**：双栏 gap 32px；题面内 H2 间距 32px、段落 12px；编辑器到 CTA 16px；CTA 到演示条 24px。

### 7.3 判题结果 `/submissions/:sid`（重点页）

```
┌──────────────────────────────────────────────────────────────┐
│ Header                                                         │
├──────────────────────────────────────────────────────────────┤
│ 面包屑 提交历史 / 20250101-120000-P1-a3f2（mono）                │
│ H1 判定结果：答案正确          [徽章 AC 放大版]                  │
│ ┌─ 得分横幅（左 4px 判定色条）────────────────────────────────┐ │
│ │ 通过 4/4 · 通过率 100% · 得分 100/100        (mono 22px)     │ │  ← 视觉重心
│ │ OI 模式：按通过用例的权重折算得分。(caption)                  │ │
│ └────────────────────────────────────────────────────────────┘ │
│ ┌─ [CE 专属] 编译器输出（末 200 行）──────────────────────────┐ │
│ │ 说明行 caption；深色块 480px 滚动；首条 error: 红条+加粗      │ │  ← 仅 CE；置于表格之前
│ └────────────────────────────────────────────────────────────┘ │
│ ┌─ 逐用例表格 用例|判定|耗时|权重|提示 ────────────────────────┐ │
│ │ 1.in [AC] 12ms 25  —                    [看输出对比]          │ │
│ │ 2.in [WA] 15ms 25  第 3 行不一致…         [看输出对比]          │ │  ← 次重心
│ │   └ 展开行：期望输出 | 实际输出（双栏深色块，差异行高亮）        │ │
│ └────────────────────────────────────────────────────────────┘ │
│ ┌─ [RE 专属] 程序异常退出 ────────────────────────────────────┐ │
│ │ 信号翻译一句（RE 色条）；stderr 末 2KB 折叠 + 复制 stderr      │ │  ← 仅 RE（TLE/PE/WA 有 stderr 也用此折叠）
│ └────────────────────────────────────────────────────────────┘ │
│ ┌─ 提交源码（默认折叠）[展开源码] ────────────────────────────┐ │
│ └────────────────────────────────────────────────────────────┘ │
│ [改代码再交一次](主)  [看提交历史](次)  [下载报告 JSON](次)        │
├──────────────────────────────────────────────────────────────┤
│ Footer                                                          │
└──────────────────────────────────────────────────────────────┘
```

- **位置关系（冻结）**：
  1. **得分横幅**永远第一（H1 之下）；格式逐字 `通过 a/b · 通过率 p% · 得分 s/m`，防换行规格见 5.5。
  2. **CE 面板**：`verdict===CE` 时**置于逐用例表格之前**并默认展开（全部用例都是 CE，表格参考价值低，编译输出是唯一有效信息）；非 CE 时不渲染。
  3. **逐用例表格**：CE 时在面板之后；其余情况紧随横幅。列固定 用例/判定/耗时/权重/提示 + 展开输出对比。
  4. **RE 面板**：表格之下；仅当存在 `signal`/`stderr_tail`/退出码信息时渲染（RE 主用；其他判定有 stderr 时同样折叠展示在对应位置，不新开面板）。
  5. **源码回显折叠**：RE/CE 面板之下、动作条之上，默认折叠。
  6. **动作条**：页尾固定顺序 主 `改代码再交一次` → 次 `看提交历史` → 次 `下载报告 JSON`。
- **视觉重心**：得分横幅（22px mono + 判定色左条 + 放大徽章）→ 逐用例表的判定列（7 色徽章列成一竖排，最易扫读）。
- **层级**：H1 中文全称（非 AC 时用对应中文，如「判定结果：答案错误」）；徽章仍显示代码字母。

### 7.4 提交历史 `/submissions`

```
┌────────────────────────────────────────────────────────┐
│ Header                                                    │
├────────────────────────────────────────────────────────┤
│ H1 这台机器上的每一次评测，都在这里                         │
│ 筛选条：[题目 ▾][判定 ▾]   共 N 次评测 · AC a 次 · 通过率 p% │  ← 统计行 mono 数字
│ ┌ 时间 | 题目 | 提交文件 | 判定 | 通过 | 得分 | 操作 ──────┐ │
│ │ 2025-01-01 12:00:00 | P1 运费计算 | P1_ac.cpp [AC] | 4/4 | 100/100 │ │  ← 视觉重心
│ │ 2025-01-01 12:05:10 | P1 运费计算 | P1_wa.cpp [WA] | 1/4 | 25/100  │ │
│ └────────────────────────────────────────────────────────┘ │
│ 分页/加载更多（limit 20，offset 翻页按钮「上一页/下一页」）    │
│ （空态：240×160 插图 + 文案 + [去做 P1]）                     │
├────────────────────────────────────────────────────────┤
│ Footer                                                    │
└────────────────────────────────────────────────────────┘
```

- **视觉重心**：表格的判定徽章列 + 得分列（mono）。
- **要点**：筛选条与表格间距 16px；统计行与筛选同行右对齐；整行可点 + 操作列文字按钮；hover 行 `--primary-bg`。
- **文案**：空态/筛选无结果用 content-plan §5 原文。

### 7.5 使用说明 `/about`

```
┌────────────────────────────────────────────────────────┐
│ Header                                                    │
├────────────────────────────────────────────────────────┤
│ H1 从跑起来到看懂每一种判定，一页讲完                        │
│ §快速开始：环境行 + 命令块（深色 figure + 复制命令）+ 预期输出 │
│ §判题流水线：四步一行 + 流水线图 960×220（9.3）              │
│ §判定表（#verdicts）：7 行表（判定|触发条件|看到什么|怎么修）   │  ← 视觉重心
│   判定列 = 徽章 + 中文全称；行可展开帮助文案                   │
│ §ACM 与 OI 差在哪：两栏对照（≤640 纵排）                      │
│ §用例从哪来：3 条路径（编号 + 命令 mono）                      │
│ §安全边界：正文 + 红线提醒（代码块/危险提示条样式）             │
│ [回题目列表做题](主)  [从 P1 运费计算开始](次)                 │
├────────────────────────────────────────────────────────┤
│ Footer（本地处理声明一行）                                   │
└────────────────────────────────────────────────────────┘
```

- **层级**：区块标题 H2 24px，间距 64px；判定表是全页重心（`#verdicts` 锚点，供首页链接跳转）。
- **要点**：命令块/红线提醒用深色代码面板；红线提醒可复用「错误提示条」视觉（danger 色条）但内容是代码块；不放沙箱示意图（8 号素材默认不画，见 9.8）。

---

## 8. 无障碍要点（前端必须满足的硬项）

1. **对比度**：正文与背景 ≥ 4.5:1（本规范 2.1–2.4 已逐对标注比值，最小可用组合 `--text-muted` on white = 4.8:1）；徽章/按钮/横幅文字均 ≥ 4.5:1；图标与信息性边框 ≥ 3:1（用 `--border-strong` 以上）。
2. **点击区**：所有可点元素 ≥ 44×44px 触达（视觉可 32px，热区用伪元素/padding 扩）；按钮、链接、行卡片、折叠触发器全覆盖。
3. **焦点可见**：统一 `:focus-visible{outline:2px solid var(--focus-ring);outline-offset:2px}`；禁止 `outline:none`；抽屉/弹层内焦点循环，Esc 可关。
4. **表格语义**：`<table><thead><th scope="col">`；逐用例表行的展开按钮放行内 `<button aria-expanded aria-controls>`；堆叠卡片降级时改用 `<ul><li>` 列表语义，不保留 table 壳。
5. **徽章 aria**：判定徽章 `aria-label="判定：答案正确"`（或表头 `判定` 已 scope 时徽章 `aria-hidden` + 单元格含视觉隐藏中文全称 `sr-only`，二选一，组件内写死一种）；颜色永不单独表意。
6. **键盘**：Tab 顺序 = 视觉顺序（Header → 主内容 → Footer）；行卡片 Enter/Space 可进入；折叠面板 Space/Enter 切换；「看输出对比」等文字按钮原生 `<button>`。
7. **表单**：编辑器 `<label for>`（可视觉隐藏「源码编辑区」）；上传输入有 label；错误提示同时有图标 + 文字 + `aria-live="polite"`。
8. **图片/图形**：内联 SVG 装饰件 `aria-hidden="true"`；有意义插图（空/错状态）`role="img"` + `<title>` 说明一句话。
9. **动效**：折叠/抽屉 160–200ms；`@media (prefers-reduced-motion:reduce)` 全部动画 0ms；loading 旋转环可用（非闪烁类）。
10. **标题层级**：每页唯一 H1；H1→H2→H3 不跳级（题面 markdown 的 `#` 渲染为 H2，见 content-plan 标题层级约定）。
11. **横幅可读**：得分横幅一行 nowrap，但需提供完整文本给读屏（三个 seg 内文本本就连续，读屏可读 `通过 4/4 通过率 100% 得分 100/100`）。

---

## 9. 素材绘制规格（对齐 content-plan §6 素材清单 9 项）

> 全部内联 SVG / CSS，无照片、无第三方图标库，离线可用。颜色一律引用第 10 节 token（SVG 内用 `currentColor` 或写死 token 同值 HEX，禁止另调色）。

### 9.1 Logo 字标（顶栏，高 32px）

- **形态**：`CodeJudge` 文字字标 + 末尾终端光标方块；SVG `viewBox="0 0 168 32"`，宽随字标自适应。
- **结构**：`<text>` 用 `--font-mono` 700 20px（或转 path 保字形一致），字色 `--text-primary`；`Judge` 部分可用 `--primary` 区分（两段色，不做渐变）；末尾 8×18px 光标方块 `--primary`，rx 1px，可选 1.2s 闪烁动画（`prefers-reduced-motion` 下不闪）。
- **配色**：`#1E293B` + `#2563EB`（token 值）。
- favicon：仅取光标方块 + `C` 字母，32×32。

### 9.2 判定徽章 ×7（约 48×22px）

- **形态**：CSS 为主（5.4 规格：tint 底 + 深色文字 + 300 边框 + 左 3px 深条）；若需导出 SVG（报告/分享用）：`<svg viewBox="0 0 48 22">`，`<rect width=48 height=22 rx=4 fill=bg>` + `<rect width=3 height=22 fill=text>` + `<text x=24 y=15 text-anchor=middle font-family=mono font-size=12 font-weight=700 fill=text>AC</text>`。
- **配色**：7 套 HEX 见 2.3 表（如 AC：bg `#DCFCE7` / text `#166534` / bar `#166534`）。

### 9.3 判题流水线图（960×220，`viewBox="0 0 960 220"`）

- **结构**（按 content-plan 描述重绘）：
  - 顶部四节点横排：`builder` → `runner` → `comparator` → `scorer`，每节点 180×56px 圆角矩形（rx 6），箭头连接（`--border-strong` 线 1.5px + 三角箭头）。
  - 节点填充 `--bg-surface` + 1px `--border`，标题 `--font-mono` 14px `--text-primary`，下方一行 caption 说明（如 `编译/构建`）。
  - 下方分支标签（从各节点垂直引出 1px 虚线）：builder ↓ `CE`（CE 色文字 + 4px 色点）；runner ↓ `TLE · RE`（TLE/RE 色）；comparator ↓ `AC · PE · WA`（三色点）；scorer ↓ `per-case → Summary`（`--text-secondary`）。
  - 分支色点 8px 圆 + 旁注 mono 12px 判定代码，颜色 = 对应判定 text 色。
- **配色**：`--bg-surface`、`--border`、`--text-primary`、`--text-secondary`、判定 7 色 text 档；无渐变无阴影。

### 9.4 图标组 16×16（stroke 1.5，线性，`viewBox="0 0 16 16"`）

- 五枚：时钟（时限）、内存/芯片（内存）、复制、下载、筛选（漏斗）。
- **结构**：统一 `fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"`；用 `currentColor` 由按钮/上下文取色（默认 `--text-secondary`）。
- 用法：标签栏/表格列头/图标按钮；整套一个 `<svg><symbol>` sprite，`<use href="#i-clock">`。

### 9.5 空状态图（240×160，提交历史空）

- **结构**：空收件箱/剪贴板 + 一个终端光标方块；`viewBox="0 0 240 160"`，主体线稿 stroke `#CBD5E1` 1.5–2px，光标方块 `#2563EB`，少量淡填充 `#F1F5F9`。
- `role="img"` + `<title>还没有评测记录的空收件箱示意</title>`。

### 9.6 错误状态图（240×160，题目加载失败）

- **结构**：断开的两块拼图 / 缺角文档；线稿 `#CBD5E1`，断口/缺角处 `#B91C1C` 2px 短线强调；右下角小 ✕ 圆标（`#FEE2E2` 底 + `#991B1B` 图标）。
- `role="img"` + `<title>题目数据缺失示意图</title>`。

### 9.7 错误状态图（240×160，SE 判题失败）

- **结构**：扳手 + 警告三角组合；扳手线稿 `#CBD5E1`，警告三角 `#FEF3C7` 填充 + `#92400E` 描边 2px + `!` 字符。
- `role="img"` + `<title>评测器自身异常示意</title>`。

### 9.8 沙箱/隐私示意（320×180，可选）

- **决定：不画**（content-plan 亦注明「或直接不放，纯文字已够」）；/about 安全边界区块用正文 + 红线提醒代码块呈现。若后续要画：笔记本 + 本机闭环箭头 + 「不联网」标注，线稿 `#CBD5E1` + `#166534` 闭环箭头。

### 9.9 社交分享卡 `og:image`（1200×630，本地版可省）

- **留规格不产出**：深底 `#0F172A` + CodeJudge 字标（白色 mono 72px）+ 一行 `在线代码评测台`（`#94A3B8` 32px）；日后对外部署时导出 PNG。

---

## 10. `tokens.css` 变量草案（`:root` 完整表，前端可直接落地）

```css
/* frontend/src/styles/tokens.css —— 视觉令牌唯一来源 */
:root {
  /* —— 字族 —— */
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
               "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans SC", sans-serif;
  --font-mono: "JetBrains Mono", "Cascadia Code", "SF Mono", Consolas,
               "Cascadia Mono", Menlo, monospace;

  /* —— 字号 / 行高 —— */
  --text-h1: 32px;        --lh-h1: 1.25;   --fw-h1: 700;
  --text-h2: 24px;        --lh-h2: 1.35;   --fw-h2: 700;
  --text-h3: 18px;        --lh-h3: 1.4;    --fw-h3: 600;
  --text-h4: 16px;        --lh-h4: 1.5;    --fw-h4: 600;
  --text-body-lg: 16px;   --lh-body-lg: 1.75;
  --text-body: 15px;      --lh-body: 1.7;
  --text-caption: 13px;   --lh-caption: 1.55;
  --text-micro: 12px;     --lh-micro: 1.4;
  --text-mono-code: 13px; --lh-mono-code: 1.6;
  --text-mono-data: 13px;
  --text-mono-badge: 12px;
  --text-banner: 22px;    /* ≤640px 降 15px */

  /* —— 间距刻度（4 基数）—— */
  --space-1: 4px;  --space-2: 8px;  --space-3: 12px; --space-4: 16px;
  --space-5: 20px; --space-6: 24px; --space-8: 32px; --space-10: 40px;
  --space-12: 48px; --space-16: 64px; --space-20: 80px; --space-24: 96px;

  /* —— 容器与栅格 —— */
  --container: 1120px;
  --container-wide: 1280px;
  --container-narrow: 880px;
  --gutter: 24px;
  --page-pad: 24px;          /* ≤640px: 16px */
  --section-gap: 64px;       /* ≤640px: 48px */

  /* —— 圆角 / 阴影 / 边框 —— */
  --radius-sm: 4px;
  --radius: 6px;
  --radius-lg: 10px;
  --shadow-1: 0 1px 2px rgba(15, 23, 42, 0.06), 0 4px 12px rgba(15, 23, 42, 0.08);
  --border: 1px solid #E2E8F0;
  --border-strong: 1px solid #CBD5E1;

  /* —— 中性色阶 —— */
  --neutral-50: #F8FAFC;  --neutral-100: #F1F5F9; --neutral-200: #E2E8F0;
  --neutral-300: #CBD5E1; --neutral-400: #94A3B8; --neutral-500: #64748B;
  --neutral-600: #475569; --neutral-700: #334155; --neutral-800: #1E293B;
  --neutral-900: #0F172A;

  /* —— 语义表面 / 文字 / 边框 —— */
  --bg-page: #F8FAFC;
  --bg-surface: #FFFFFF;
  --bg-subtle: #F1F5F9;
  --bg-inset: #E2E8F0;
  --text-primary: #1E293B;
  --text-secondary: #475569;
  --text-muted: #64748B;
  --text-disabled: #94A3B8;
  --text-inverse: #FFFFFF;

  /* —— 主色 —— */
  --primary: #2563EB;
  --primary-hover: #1D4ED8;
  --primary-active: #1E40AF;
  --primary-bg: #EFF6FF;
  --focus-ring: #2563EB;

  /* —— 语义色（提示条/表单）—— */
  --success-text: #166534; --success-bg: #DCFCE7; --success-border: #86EFAC;
  --warning-text: #92400E; --warning-bg: #FEF3C7; --warning-border: #FCD34D;
  --danger-text: #991B1B;  --danger-bg: #FEE2E2;  --danger-border: #FCA5A5;
  --danger-solid: #B91C1C; --danger-solid-hover: #991B1B;
  --info-text: #075985;    --info-bg: #E0F2FE;    --info-border: #7DD3FC;

  /* —— 判定 7 色（verdict）—— */
  --verdict-ac-text: #166534; --verdict-ac-bg: #DCFCE7; --verdict-ac-border: #86EFAC;
  --verdict-pe-text: #075985; --verdict-pe-bg: #E0F2FE; --verdict-pe-border: #7DD3FC;
  --verdict-wa-text: #991B1B; --verdict-wa-bg: #FEE2E2; --verdict-wa-border: #FCA5A5;
  --verdict-tle-text: #9A3412; --verdict-tle-bg: #FFEDD5; --verdict-tle-border: #FDBA74;
  --verdict-re-text: #831843; --verdict-re-bg: #FCE7F3; --verdict-re-border: #F9A8D4;
  --verdict-ce-text: #6B21A8; --verdict-ce-bg: #F3E8FF; --verdict-ce-border: #D8B4FE;
  --verdict-se-text: #44403C; --verdict-se-bg: #F5F5F4; --verdict-se-border: #D6D3D1;

  /* —— 代码面板（深色）—— */
  --code-bg: #0F172A;
  --code-bar-bg: #1E293B;
  --code-text: #E2E8F0;
  --code-muted: #94A3B8;
  --code-accent: #7DD3FC;
  --code-string: #86EFAC;
  --code-number: #FDBA74;
  --code-comment: #94A3B8;
  --code-error: #FCA5A5;
  --code-error-bar: #EF4444;
  --code-border: #1E293B;

  /* —— 控件尺寸 —— */
  --control-h: 40px;
  --control-h-lg: 44px;
  --control-h-sm: 32px;
  --header-h: 56px;
  --table-row-h: 40px;
  --table-row-compact-h: 36px;
  --table-head-h: 36px;
  --badge-h: 22px;
  --badge-h-lg: 28px;

  /* —— 动效 —— */
  --dur-fast: 160ms;
  --dur-base: 200ms;
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);

  /* —— 层级 —— */
  --z-header: 20;
  --z-drawer: 40;
  --z-toast: 60;
}

@media (max-width: 640px) {
  :root {
    --text-h1: 24px;
    --text-banner: 15px;
    --page-pad: 16px;
    --section-gap: 48px;
  }
}

@media (prefers-reduced-motion: reduce) {
  :root {
    --dur-fast: 0ms;
    --dur-base: 0ms;
  }
}
```

---

## 关键取舍

1. **浅色 UI + 深色代码面板，不做全深色**：7 色判定徽章在浅底上对比度最稳、表格密度不累眼；代码一律深色以立「代码 = 终端」的语义映射。整站暗色留 P2（F15），token 分层已为 `[data-theme="dark"]` 留好接口。
2. **判定色「文字主信道 + 色相辅信道」**：徽章永远带 AC/PE/… 代码文字与中文全称，颜色只做扫读加速；WA/AC 红绿冲突对靠明度差 + 文字兜底，7 色 text 统一压在深带（L* 30–40）保证徽章内部对比一致。
3. **首页题目列表用「行式卡片」而非多列方卡/纯表格**：变长标签组（含 G2 补充的可选 `topic`/`difficulty`）需要弹性横排，整行可点 + 固定 CTA，密度接近表格；同时把 H1 区压到 220px 内，保「工具本体首屏可见」红线。
4. **CE 时编译输出面板提到逐用例表之前**：CE 场景下全表皆 CE、零信息量，编译器输出是唯一有效信息，层级让位比固定模板更重要（其余判定仍 横幅→表→细节面板→源码折叠）。

## 前端最容易做走样的 2 个点

1. **得分横幅换行破版**：`通过 4/4 · 通过率 100% · 得分 100/100` 长度随数字变化，必须按 5.5 拆 `.seg/.sep` 逐段 `nowrap` + `tabular-nums`，禁止整段普通文本任其折行，禁止改字/改分隔符。
2. **判定色走样成「纯色块表意」**：徽章省掉代码文字、或把 7 色当装饰色乱用、或把 text 色调浅（对比度掉到 4.5 以下）。必须整套搬 2.3 的 HEX 三件套 + 左 3px 深条 + aria-label 中文全称。

## 需要用户拍板的 1–2 个决策

设计侧决策已全部闭环（G2 裁定 + 微裁定）：① 主 CTA 全站「提交判题」（loading「判题中…」）；② `ProblemSummary` 补可选 `topic`/`difficulty`、`SubmissionSummary` 补 `file_label`，字段可得即渲染、缺失优雅降级；③ 页脚版本号/仓库外链本地版删行不留占位；④ 历史表 `file_label` 全列缺失时列头保留 + 单元格 `—`。

**当前无待用户拍板事项。** 唯一遗留输入项：页脚版本号若日后开源需用户给出真实值（届时补行即可，本地版按③不渲染）。

---
---

# Δ2 用户系统组件（终端风）

> **主题切换声明（节首必读）**：站点整体已重绘为**终端风格**（CRT 终端：全站等宽、荧光绿 `#3DFF7A` 主色、ANSI 判定七色、直角、按钮 `[ ]` 括钮、页头 `$` 提示符 + 闪烁光标、扫描线）。**`frontend/src/styles/tokens.css` 现值是唯一事实来源**；本节所有色值/字号/间距一律引用该文件 token，不另立色板。上文第 1–10 节的浅色方案**仅作结构参考**（组件清单、栅格、对比度方法、无障碍硬项仍有效），凡与 tokens.css 现值冲突处以 tokens.css 为准。
> 文案事实来源：`content-plan.md`「Δ1 用户系统文案」节；契约事实来源：`site-spec.md` §13。文案逐字使用，本节只定排版与组件样式。
> 组件语言基线（已读现值）：`AppButton.vue`（`[ ]` 括钮 + 44px 热区伪元素 + loading 旋转环）、`AppHeader.vue`（`$` 提示符 + 闪烁光标块 + 260px 右抽屉）、`FileListEditor.vue`（`--code-bar-bg` 输入框 + 分段工具条）。Δ2 全部在此体系内延伸。

## Δ2-0 组件扩展总表（先看这张）

| # | 组件 | 复用/新建 | 规格见 |
|---|---|---|---|
| 1 | `/login` 表单卡片（终端对话框） | 新建 `AuthCard.vue` | Δ2-1 |
| 2 | 登录/注册合一 tab | **统一组件** `AppTabs.vue`（从 ProblemDetail `mode-tabs` 抽出，历史页双 tab 共用） | Δ2-1 / Δ2-4 |
| 3 | 终端风 input（邮箱/密码/确认密码） | 新建 `TermInput.vue`（吸收 FileListEditor `mfile__input` 语言） | Δ2-1 |
| 4 | GitHub 按钮 | `AppButton` 加 `oauth` 变体（深底 + GitHub 标，**不加括钮**） | Δ2-1 |
| 5 | 页头用户菜单（链接态/下拉/本地模式标签） | 扩展 `AppHeader.vue` | Δ2-2 |
| 6 | 同步徽章三态 | 新建 `SyncBadge.vue`（徽章语法同 VerdictBadge） | Δ2-3 |
| 7 | 历史双 tab + 三种空状态 | `AppTabs` + `EmptyState.vue` 重着色 | Δ2-4 |
| 8 | 提交拦截提示条 | 复用 `AlertBar.vue`（补自定义 action 文案能力） | Δ2-5 |
| 9 | 登录成功 toast | 新建轻量 `Toast.vue`（`--z-toast`） | Δ2-1 |
| 10 | 退出二次确认 | 复用终端对话框壳（同 AuthCard 标题条） | Δ2-2 |

## Δ2-1 `/login` 登录 / 注册页（合一，页内切换）

**路由**：`/login` 单页双态（登录 ↔ 注册 页内 tab 切换），不设 `/register`（G1 已定）。TDK 与 noindex 按 content-plan Δ1-8（`noindex` 建议加，不进 sitemap）。

### 线框

```
┌────────────────────────────────────────────────────────────┐
│ Header：$ CodeJudge ▮          题目 提交历史 关于   [本机评测] │
├────────────────────────────────────────────────────────────┤
│                                                            │
│          H1  登录后提交判题，历史随账号走                     │
│          副标题一行（--text-secondary，max-width 640px）      │
│                                                            │
│          ┌─ auth ────────────────────────────┐              │
│          │ [ 登录 ] │ 注册        ← AppTabs   │              │
│          │ ─────────────────────────────────  │              │
│          │ $ 邮箱                              │              │
│          │ ┌──────────────────────────────┐   │              │
│          │ │ you@example.com              │   │              │
│          │ └──────────────────────────────┘   │              │
│          │ $ 密码                              │              │
│          │ ┌──────────────────────────────┐   │              │
│          │ │ 你的密码                     │   │              │
│          │ └──────────────────────────────┘   │              │
│          │ （注册态追加：$ 确认密码 一行）      │              │
│          │                                    │              │
│          │          [ 登录 ]  ← 主 CTA block  │              │
│          │                                    │              │
│          │ ───────────  或  ───────────        │              │
│          │   [ ◉ 使用 GitHub 登录 ] ← oauth   │              │
│          │                                    │              │
│          │  没有账号，去注册  ← 切换链接       │              │
│          │  继续即表示：本地模式不收集任何数据…  │              │
│          └────────────────────────────────────┘              │
│                                                            │
├────────────────────────────────────────────────────────────┤
│ Footer                                                      │
└────────────────────────────────────────────────────────────┘
```

阅读顺序 = 线框从上到下：方式（tab）→ 字段 → 动作（主按钮）→ 或 → GitHub → 切换链接 → 底部说明。视觉重心 = 表单卡片（页面唯一实体块，H1 区留白衬托）。

### 表单卡片（AuthCard，类终端对话框）

- 外壳：宽 `min(440px, 100%)` 居中；bg `--bg-surface`，border `var(--border-strong)`（1px），radius `var(--radius)`，box-shadow `var(--shadow-1)`。
- 标题条（仿 FileListEditor `mfile__bar` / 代码面板顶条）：高 36px，bg `--code-bar-bg`，左侧 mono `--text-mono-micro`（11px）`--code-accent` 文字 `auth · login`（注册态切 `auth · signup`）；右侧可放 8px 绿点（`--success-text`，装饰，`aria-hidden`）。
- 标题条下 1px `--code-border` 分隔；内边距 `var(--space-5) var(--space-5) var(--space-6)`。
- 卡片顶部可放 `$` 提示符行（装饰，复用 AppHeader 的 `$` 语言）：`$ auth --login` / `$ auth --signup`，mono 13px，`--code-muted`，行末 8×16px 闪烁光标块（`--primary`，1.2s step-end 闪烁，`prefers-reduced-motion` 下不闪）。
- **H1 在卡片外**（页面级唯一 H1），副标题 = content-plan 原文：`邮箱注册登录，或用 GitHub 一键登录。未配置云服务时站点按本地匿名模式运行，此页不出现在导航里。`（caption 12px，`--text-secondary`，max-width 640px）。

### 合一 tab（AppTabs，登录 | 注册）

- **统一组件**（本页与历史页双 tab 共用）：外框 `border: var(--border-strong)`，radius `var(--radius)`，overflow hidden，两格等分（`flex:1`），格高 36px，字号 `--text-caption`/600——结构即 ProblemDetail `mode-tabs` 现值，抽出为 `AppTabs.vue`。
- 选中态：bg `--primary-bg` + 文字 `--primary`，文字前缀 `> `（终端提示符语义，纯 CSS `::before`）；未选中：bg `--bg-surface` + `--text-secondary`，hover `--bg-subtle`。
- 语义：`role="tablist"` / `role="tab"` + `aria-selected`；默认选中 `登录`；切换即时换表单字段与按钮文案，不发请求。
- 键盘：每个 tab 是原生 `<button>`，Tab 可达；左右方向键在两 tab 间移动焦点（`tabindex` roving，选中项 0，未选中 -1）。

### 字段（TermInput：邮箱 / 密码 / 确认密码）

- 标签行（真 `<label for>`，不可省）：mono 12px `--text-secondary`，格式 `$ 邮箱` / `$ 密码` / `$ 确认密码`（`$` 用 `--primary`，字段名中文；注册态密码标签 `$ 密码（至少 8 位）` 可与 placeholder 二选一，文案以 content-plan 为准）。
- 输入框：高 `--control-h`（40px），bg `--code-bar-bg`，border `1px solid var(--code-border)`，radius `--radius-sm`，padding `0 var(--space-3)`，文字 `--code-text`，caret `--code-accent`（同 FileListEditor 输入语言）。
- placeholder `--code-muted`，逐字用 content-plan：邮箱 `you@example.com`；密码 登录态 `你的密码` / 注册态 `至少 8 位`；确认密码 `再输入一次`。
- **聚焦绿描边**：`:focus` 时 `border-color: var(--primary)`；`:focus-visible` 全局 2px `--focus-ring` outline + 2px offset 照常生效（双保险）。
- 错误态：`border-color: var(--danger-text)` + 下方 12px `--danger-text` 错误语（见下表），`aria-invalid="true"` + `aria-describedby` 关联。
- 密码字段 `type="password"`；注册态确认密码仅在注册 tab 渲染（登录态 DOM 中不存在，不用隐藏）。

### 校验错误语（6 条，输入框下方红字；提交被拒时同时走错误条）

| 场景 | 提示语 | 附加 |
|---|---|---|
| 邮箱格式 | `邮箱格式不正确` | — |
| 密码不足 8 位 | `密码至少 8 位` | — |
| 两次密码不一致 | `两次输入的密码不一致` | — |
| 邮箱已注册 | `该邮箱已注册，请直接登录` | 尾附链接 `去登录` |
| 密码错误 | `邮箱或密码不正确` | 补充行 `请检查大小写后重试` |
| 尝试次数过多 | `尝试次数过多，请稍后再试` | 补充行 `10 分钟后再试一次` |

### 按钮与动作

- **主按钮**：登录态文案 `登录`、注册态 `创建账号`；`AppButton variant="primary"`（`[ ]` 括钮 + 44px 热区），`block` 撑满卡片宽；loading 时文案切 `登录中…` / `创建中…` + 旋转环（复用 AppButton loading 机制；括钮在 loading 时保留）。
- **分隔线「或」**：左右各 1px `--border` 横线 + 中间 mono 12px `--text-muted` `或`（flex 三段，线 flex:1）。
- **GitHub 按钮**：`AppButton variant="oauth"`（新变体）——宽 block，高 `--control-h-lg`，bg `--bg-inset`（深色底），border `1px solid var(--border-strong)`，文字 `--text-primary` 15px/600，**不加 `[ ]` 括钮**（括钮留给动作动词）；左侧 16px GitHub 标（octocat 线标，`fill: currentColor`）+ 文案 `使用 GitHub 登录`；hover：border `--primary` + 文字 `--primary`（绿描边）；active：bg `--primary-bg`；disabled：`--text-disabled`。
- **切换链接**：登录态底部 `没有账号，去注册`；注册态 `已有账号，去登录`；`a` 文字链接 `--primary`，hover `--primary-hover` + 下划线；居中，字号 `--text-body`；点击只切 tab 不跳路由。
- **底部说明行**：`继续即表示：本地模式不收集任何数据；开启云同步后，判题历史存入你的账号并按账号隔离。`（micro 11px，`--text-muted`，max-width 36em 换行，卡片内底部）。

### 登录成功

- toast：`登录成功。可以提交判题了。` —— 新建轻量 `Toast.vue`：bg `--bg-surface`，border `1px solid var(--success-border)`，border-left `3px solid var(--success-text)`，文字 `--success-text`，位置视口右下（`--z-toast`），2.4s 自动消失（`aria-live="polite"`）。
- 行为（文案归 content-plan，此处只定视觉）：自动回跳来源页；来源为被拦截题目页时编辑器内容保留。无来源回 `/`。

### 认证错误条（10 条 + UNAUTHORIZED）

- 走 `AlertBar`（tone=error / warning 视 code 而定），文案逐字用 content-plan Δ1-7 表；`ERROR_HINTS` 扩 11 行（10 条 auth code + API 的 `UNAUTHORIZED`，后者提示 `请先登录（登录状态可能已过期）` + 动作 `去登录`）。
- 错误条插入位置：tab 下方、字段上方（表单内），role=alert。

## Δ2-2 页头用户菜单（扩展 AppHeader.vue）

三态（content-plan Δ1-2 逐字）：

| 状态 | 页头显示 | 动作 |
|---|---|---|
| supabase 模式 + 未登录 | 文字链接 `登录 / 注册`（`--primary`，hover 下划线；**不用括钮**，避免与主导航争重） | → `/login` |
| 已登录 | `{邮箱 或 GitHub 用户名}` mono 13px `--text-secondary` + 12px 下箭头（`▾`） | 下拉：灰字一行当前邮箱 + `退出登录` |
| local 模式（未配置 Supabase） | 灰字标签 `本地模式`（micro 11px，`--text-muted`，无交互） | 不显示登录入口 |

- **下拉面板（桌面）**：宽 240px，右对齐触发器；bg `--bg-surface`，border `var(--border)`，radius `--radius`，shadow `--shadow-1`；顶行 = 当前邮箱（mono 12px `--text-muted`，超长省略 + `title` 全文）；1px `--border` 分隔；`退出登录` 行（高 40px，hover `--danger-bg` + `--danger-text`）。展开动画 160ms（`--dur-fast`），Esc / 点外关闭，焦点进面板首项。
- **移动端（<1024px）**：不独立下拉，**复用现有右侧抽屉**（260px + 遮罩 + 焦点锁，AppHeader 现值）：抽屉顶部加用户信息区（邮箱灰字 / `本地模式` 标签 / `登录 / 注册` 链接），`退出登录` 作为抽屉底部一条（danger 色）。
- **退出二次确认**（防误触）：终端对话框壳（同 AuthCard 标题条，`auth · signout`）；正文 `退出后本机浏览器清除登录状态，云端历史仍保留。`；按钮 `确认退出`（`AppButton danger`）+ `取消`（`secondary`）。弹层居中，遮罩 `rgba(11,15,12,.55)`（透明度 token，见 Δ2-7），Esc=取消。

## Δ2-3 判题结果页同步徽章三态（SyncBadge.vue）

- **位置**：提交信息行（结果页区块 0）右侧，**不占得分横幅**（横幅格式冻结不受影响）。
- **徽章语法**（同 VerdictBadge）：高 22px，padding `0 var(--space-2)`，radius `--radius-sm`，左 3px 色条，mono 12px/700，亮字 + 暗底 + 深边（ANSI 三件套）。

| 状态 | 文案（逐字） | 色映射（token，不新增色相） | 补充 |
|---|---|---|---|
| 已入库 | `已同步到你的账号` | success 三件套：`--success-text` / `--success-bg` / `--success-border`（= AC 绿） | — |
| 本地模式 / 未启用云同步 | `仅保存在本机` | SE 灰三件套：`--verdict-se-text` / `--verdict-se-bg` / `--verdict-se-border` | — |
| 入库失败 | `同步失败，仅保存在本机` | warning 三件套：`--warning-text` / `--warning-bg` / `--warning-border`（= TLE 琥珀） | 旁附文字按钮 `重试同步`（`AppButton text`，hover 亮绿）；补充行 `云端暂不可用，本次结果已存本机 reports/。`（caption，`--text-secondary`，徽章下一行） |

- 无障碍：徽章带 `aria-label`（如 `同步状态：已同步到你的账号`）；颜色 + 文字双信道，灰/绿/琥珀形状无差，文字即判据；`重试同步` 为真按钮，loading 时切 `同步中…` + 禁点。
- 徽章右缘与提交信息行基线对齐；窄屏（<640px）换行到信息行下一行左对齐，不挤时间戳。

## Δ2-4 历史页双 tab 与三种空状态

### 双 tab（AppTabs 复用）

- 文案逐字：`云端 · 按账号隔离` | `本机 · reports/`；默认 tab：已登录 → 云端；未登录 / local 模式 → 本机（content-plan Δ1-4）。
- 选中态沿用 AppTabs 统一样式（`> ` 前缀 + `--primary-bg`/`--primary`），外框与逐用例表容器同宽；tab 行右侧可放当前数据源计数（mono 12px `--text-muted`，如 `6 条`）。
- 行内标签徽章：云端行 `云端 · 按账号隔离`（info 三件套：`--info-text`/`--info-bg`/`--info-border`）；本机行 `本机`（SE 灰三件套）——列位在「提交文件」列右侧或题目列尾随，尺寸同 SyncBadge 22px。
- 历史表其余列结构不变（时间 | 题目 | 提交文件 | 判定 | 通过 | 得分 | 操作，file_label 降级规则照旧）。

### 三种空状态（EmptyState.vue，插图终端色重着色）

插图沿用现有 240×160 SVG 语言（线稿 + 单点缀色），重着色规则：线稿 stroke `--text-disabled`（原 `#CBD5E1`），点缀/强调用 `--primary`（绿光标方块）或 `--warning-text`（警示件），填充 `--bg-subtle`；`role="img"` + `<title>` 说明照旧。

| 场景 | 插图 | 文案（逐字） | 按钮 |
|---|---|---|---|
| 未登录查看云端 tab | 登录锁 + 空收件箱（绿光标方块） | `登录后可查看云端历史。云端历史按账号隔离。` | `去登录`（primary 括钮）→ `/login` |
| 已登录、云端无记录 | 空收件箱 + 光标方块（沿用 9.5 构图） | `云端还没有评测记录。提交一份代码后，这里会出现每一次的判定与得分。` | `去做 P1` |
| 本机 tab 无记录 | 同上（本机构图） | `还没有评测记录。提交一份代码后，这里会出现每一次的判定与得分。` | `去做 P1` |

- 插图高 160px 容器内居中，整体块 padding `var(--space-12) var(--space-6)`；文案 body 14px `--text-secondary`；按钮 `AppButton primary`。

## Δ2-5 提交拦截与双模式提示条（AlertBar 复用）

| 场景 | 文案（逐字） | tone | 按钮 |
|---|---|---|---|
| 未配置 Supabase（全站提示条，可关闭） | `本地匿名模式：未配置云服务。判题照常，历史只存本机。` | info | `知道了`（关闭） |
| 已配置但未登录，点「提交判题」 | `登录后可提交判题并云同步历史。` | info | `去登录` → `/login`（回跳保留编辑器内容） |
| 登录成功回跳题目页 | `登录成功。可以提交判题了。` | success | —（toast，见 Δ2-1） |

- 样式 = `AlertBar.vue` 现值（图标形状区分 + 3px 左色条 + `--*-bg` 底）零改动；**唯一扩展**：`actionLabel` 支持外部自定义文案（现值仅认 `ERROR_HINTS` 内置动作），以容纳 `去登录` / `知道了`。
- 拦截条插入位置：题目详情页主 CTA 正下方（原「错误提示条」位）；全站 local 模式条插在页头之下、页内容之上，可关闭（关闭态记 localStorage，不再出）。
- 401 `UNAUTHORIZED` 错误条同款，动作 `去登录`。

## Δ2-6 响应式与无障碍

**响应式**：

| 断点 | `/login` | 用户菜单 | 历史双 tab |
|---|---|---|---|
| ≥1024 | 卡片 440px 居中，H1 区与卡片纵向居中（页 min-height `100vh - header`） | 下拉浮层 240px | tab 行 + 表格同行宽 |
| 640–1023 | 同上（卡片仍 440px，页边距 24px） | <1024 并入右抽屉 | 同上 |
| <640 | **单列**：H1 降 22px（tokens 现值），卡片宽 100%、内边距 16px；主按钮/GitHub 按钮 block 撡满；分隔线照旧 | 抽屉内用户区 | tab 等分照旧；表格降级沿用既有堆叠卡片规则 |

**无障碍硬项**：

1. 表单：每个输入真 `<label for>`；错误语 `aria-describedby` + `aria-invalid`；错误条 `role="alert"`。
2. 热区：全部按钮沿用 AppButton 44px 伪元素热区；tab 格高 36px 但点击区撑满 44px（padding 补足）；切换链接行高 ≥44px。
3. 焦点：全局 `:focus-visible` 2px `--focus-ring` + 2px offset 照常；输入聚焦绿描边不替代 outline。
4. 键盘：tab（登录/注册、云端/本机）方向键 roving + Tab 进入；下拉 Esc 关闭 + 焦点回归触发器；弹层（退出确认）焦点锁 + Esc=取消。
5. 不靠颜色单独表意：同步徽章三态、空状态、错误条均有文字；GitHub 按钮的图标 `aria-hidden` + 文字自明。
6. `prefers-reduced-motion`：闪烁光标/下拉/弹层动画全关（tokens 现值已把 `--dur-*` 归零）。
7. `/login` 的 `noindex` 由文档头 `meta` 落（Δ1-8），不在组件内。

## Δ2-7 tokens 变更（无新增色相）

**不新增任何色相**。同步徽章三态、GitHub 按钮、表单聚焦、弹层遮罩全部由现有 token 组合而成：

- 绿/灰/琥珀 三态 = `--success-*` / `--verdict-se-*` / `--warning-*`（已有）。
- GitHub 按钮深底 = `--bg-inset` + `--border-strong`（已有）。
- 表单输入 = `--code-bar-bg` / `--code-border` / `--code-text` / `--code-muted` / `--code-accent`（已有，同 FileListEditor）。

仅允许补**透明度 / 间距** token（至多 1 个透明度）：

```css
:root {
  /* Δ2 补：弹层遮罩（统一 AppHeader 现用 rgba 与退出确认弹层） */
  --overlay: rgba(11, 15, 12, 0.55);
}
```

（AppHeader 现值 `rgba(15,23,42,0.4)` 建议一并改引 `--overlay`，属同值迁移，不属新色相。）间距全部复用 `--space-*` 刻度。

## Δ2 取舍与风险

1. **合一 tab 不拆路由**：登录/注册共用卡片与错误条，动线最短（G1 已定）；代价是注册态字段在 tab 切换时重挂载，表单内容不跨 tab 保留——有意为之（防误填混用）。
2. **AppTabs 统一组件**：login 的 登录|注册 与历史页 云端|本机 同构抽出，避免两套 tab 各写各的；ProblemDetail `mode-tabs` 迁移为引用（视觉不变）。
3. **风险**：① GitHub OAuth 回跳在 hash 路由下依赖 `detectSessionInUrl`（契约已定，视觉无涉，但登录成功 toast 时机要跟 `SIGNED_IN` 事件而非路由跳转）；② AlertBar 扩自定义 action 是唯一对现组件的破坏性小改，前端注意别把 `ERROR_HINTS` 内置动作路径改坏；③ 邮箱 mono 长文（GitHub 用户名/email）在 240px 下拉里必须省略 + title，否则破版。
