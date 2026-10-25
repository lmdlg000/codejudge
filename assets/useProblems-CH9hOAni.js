import{W as d,I as r,s as u,X as _}from"./index-DetVD6iU.js";const p=[{id:"P1",title:"运费计算",contest_type:"oi",score:100,compare_mode:"trim",limits:{time_ms:1e3,memory_mb:256},build:{mode:"g++",command:"g++ -O2 -std=c++17 -o {bin} {src}",src:"main.cpp",default_filename:"main.cpp"},topic:"分支/分段计费",difficulty:"入门",statement_md:`# P1 运费计算

## 题目背景

快递点按重量收运费：首重 1000 克及以内收 10 元；超出部分每 500 克加收 3 元，不足 500 克按 500 克算。另外按派送距离加收附加费：500 公里以内免收，500 公里以上至 1000 公里加收 5 元，超过 1000 公里加收 12 元。请根据包裹重量和派送距离算出总运费。

## 输入格式

一行两个整数 \`w\` 和 \`d\`，分别表示包裹重量（克）和派送距离（公里）。

## 输出格式

一行一个整数，表示总运费（元）。

## 样例输入

\`\`\`
800 300
\`\`\`

## 样例输出

\`\`\`
10
\`\`\`

## 样例输入 2

\`\`\`
1000 500
\`\`\`

## 样例输出 2

\`\`\`
10
\`\`\`

## 样例输入 3

\`\`\`
1500 800
\`\`\`

## 样例输出 3

\`\`\`
18
\`\`\`

## 样例输入 4

\`\`\`
2300 1200
\`\`\`

## 样例输出 4

\`\`\`
31
\`\`\`

## 样例输入 5

\`\`\`
5000 1000
\`\`\`

## 样例输出 5

\`\`\`
39
\`\`\`

## 数据范围

- \`1 ≤ w ≤ 100000\`
- \`1 ≤ d ≤ 3000\`
- 运费保证在 32 位有符号整数范围内。
`,samples:[{input:"800 300",output:"10"},{input:"1000 500",output:"10"},{input:"1500 800",output:"18"},{input:"2300 1200",output:"31"},{input:"5000 1000",output:"39"}],test_count:null},{id:"P2",title:"字符串压缩",contest_type:"oi",score:100,compare_mode:"trim",limits:{time_ms:1e3,memory_mb:256},build:{mode:"g++",command:"g++ -O2 -std=c++17 -o {bin} {src}",src:"main.cpp",default_filename:"main.cpp"},topic:"字符串处理",difficulty:"简单",statement_md:`# P2 字符串压缩

## 题目背景

日志系统里存着大量只含小写字母的字符串，很多字符连续重复。为了节省空间，需要把每个连续相同字符段压缩成「字符 + 段长」的形式。例如 \`aaabbc\` 压缩为 \`a3b2c1\`。段长为 1 时也要写上数字，保证输出格式唯一。

## 输入格式

一行一个只含小写字母的字符串 \`s\`。

## 输出格式

一行一个字符串，表示压缩结果：按从左到右的顺序，对每个连续相同字符段输出「字符 + 该段长度」。

## 样例输入

\`\`\`
aaabbc
\`\`\`

## 样例输出

\`\`\`
a3b2c1
\`\`\`

## 样例输入 2

\`\`\`
a
\`\`\`

## 样例输出 2

\`\`\`
a1
\`\`\`

## 样例输入 3

\`\`\`
zzzzzzzzzz
\`\`\`

## 样例输出 3

\`\`\`
z10
\`\`\`

## 样例输入 4

\`\`\`
abcabc
\`\`\`

## 样例输出 4

\`\`\`
a1b1c1a1b1c1
\`\`\`

## 样例输入 5

\`\`\`
aabbaa
\`\`\`

## 样例输出 5

\`\`\`
a2b2a2
\`\`\`

## 数据范围

- \`1 ≤ |s| ≤ 100000\`
- \`s\` 仅由小写字母 \`a\`–\`z\` 组成。
`,samples:[{input:"aaabbc",output:"a3b2c1"},{input:"a",output:"a1"},{input:"zzzzzzzzzz",output:"z10"},{input:"abcabc",output:"a1b1c1a1b1c1"},{input:"aabbaa",output:"a2b2a2"}],test_count:null},{id:"P3",title:"活动安排",contest_type:"acm",score:100,compare_mode:"trim",limits:{time_ms:1500,memory_mb:256},build:{mode:"g++",command:"g++ -O2 -std=c++17 -o {bin} {src}",src:"main.cpp",default_filename:"main.cpp"},topic:"排序/贪心",difficulty:"中等",statement_md:`# P3 活动安排

## 题目背景

场地本周收到了 n 个活动的预约，第 i 个活动占用半开区间 \`[s_i, t_i)\`——同一时刻场地只能办一个活动，但一个活动的结束时刻恰好等于另一个的开始时刻时，两场可以连着办。请问最多能安排多少个活动？

## 输入格式

第一行一个整数 \`n\`，表示活动数量。
接下来 \`n\` 行，每行两个整数 \`s_i\` 和 \`t_i\`，表示第 i 个活动的开始与结束时刻。

## 输出格式

一行一个整数，表示最多能安排的活动数量。

## 样例输入

\`\`\`
3
1 3
2 5
4 7
\`\`\`

## 样例输出

\`\`\`
2
\`\`\`

## 样例输入 2

\`\`\`
1
5 10
\`\`\`

## 样例输出 2

\`\`\`
1
\`\`\`

## 样例输入 3

\`\`\`
4
1 2
2 3
3 4
1 4
\`\`\`

## 样例输出 3

\`\`\`
3
\`\`\`

## 样例输入 4

\`\`\`
5
1 10
2 3
3 4
4 5
5 6
\`\`\`

## 样例输出 4

\`\`\`
4
\`\`\`

## 样例输入 5

\`\`\`
4
1 5
2 6
3 7
4 8
\`\`\`

## 样例输出 5

\`\`\`
1
\`\`\`

## 数据范围

- \`1 ≤ n ≤ 10^6\`
- \`0 ≤ s_i < t_i ≤ 10^9\`
- **存在隐藏加权用例**：\`n = 10^6\` 边界的用例权重 ×2，请保证算法复杂度为 \`O(n log n)\` 或更优。
`,samples:[{input:`3
1 3
2 5
4 7`,output:"2"},{input:`1
5 10`,output:"1"},{input:`4
1 2
2 3
3 4
1 4`,output:"3"},{input:`5
1 10
2 3
3 4
4 5
5 6`,output:"4"},{input:`4
1 5
2 6
3 7
4 8`,output:"1"}],test_count:null},{id:"P4",title:"日期推算",contest_type:"oi",score:100,compare_mode:"trim",limits:{time_ms:1e3,memory_mb:256},build:{mode:"g++",command:"g++ -O2 -std=c++17 -o {bin} {src}",src:"main.cpp",default_filename:"main.cpp"},topic:"日期模拟",difficulty:"中等",statement_md:`# P4 日期推算

## 题目背景

排班系统只知道一个起始日期和要往后推的天数。请算出推算后的日期。注意闰年：能被 4 整除且不能被 100 整除的年份是闰年，能被 400 整除的年份也是闰年；闰年的 2 月有 29 天。

## 输入格式

一行一个日期和一个整数，格式为 \`YYYY-MM-DD D\`，表示起始日期和要推算的天数。

## 输出格式

一行一个日期，格式为 \`YYYY-MM-DD\`，表示推算结果。注意月和日不足两位时补前导零。

## 样例输入

\`\`\`
2025-01-01 0
\`\`\`

## 样例输出

\`\`\`
2025-01-01
\`\`\`

## 样例输入 2

\`\`\`
2025-01-01 31
\`\`\`

## 样例输出 2

\`\`\`
2025-02-01
\`\`\`

## 样例输入 3

\`\`\`
2024-02-28 1
\`\`\`

## 样例输出 3

\`\`\`
2024-02-29
\`\`\`

## 样例输入 4

\`\`\`
2025-12-31 1
\`\`\`

## 样例输出 4

\`\`\`
2026-01-01
\`\`\`

## 样例输入 5

\`\`\`
2024-01-01 365
\`\`\`

## 样例输出 5

\`\`\`
2024-12-31
\`\`\`

## 数据范围

- \`1900-01-01 ≤ 起始日期 ≤ 2100-12-31\`
- \`0 ≤ D ≤ 1000000\`
- 起始日期与推算结果均保证合法。
`,samples:[{input:"2025-01-01 0",output:"2025-01-01"},{input:"2025-01-01 31",output:"2025-02-01"},{input:"2024-02-28 1",output:"2024-02-29"},{input:"2025-12-31 1",output:"2026-01-01"},{input:"2024-01-01 365",output:"2024-12-31"}],test_count:null},{id:"P5",title:"最短路径",contest_type:"acm",score:100,compare_mode:"trim",limits:{time_ms:2e3,memory_mb:256},build:{mode:"g++",command:"g++ -O2 -std=c++17 -o {bin} {src}",src:"main.cpp",default_filename:"main.cpp"},topic:"图论/最短路",difficulty:"较难",statement_md:`# P5 最短路径

## 题目背景

城市间有 n 个节点和 m 条单向道路，第 i 条道路从 u_i 通向 v_i，通行耗时为 w_i。可能存在重边。请算出从 1 号节点到 n 号节点的最短耗时；如果根本到不了，输出 -1。

## 输入格式

第一行两个整数 \`n\` 和 \`m\`。
接下来 \`m\` 行，每行三个整数 \`u_i\`、\`v_i\`、\`w_i\`，表示一条从 \`u_i\` 到 \`v_i\`、耗时为 \`w_i\` 的单向道路。

## 输出格式

一行一个整数：从 1 到 n 的最短耗时；不可达输出 \`-1\`。

## 样例输入

\`\`\`
4 4
1 2 1
2 3 2
1 3 5
3 4 1
\`\`\`

## 样例输出

\`\`\`
4
\`\`\`

## 样例输入 2

\`\`\`
2 0
\`\`\`

## 样例输出 2

\`\`\`
-1
\`\`\`

## 样例输入 3

\`\`\`
3 2
1 2 3
2 3 4
\`\`\`

## 样例输出 3

\`\`\`
7
\`\`\`

## 样例输入 4

\`\`\`
4 3
1 2 10
1 3 1
3 4 1
\`\`\`

## 样例输出 4

\`\`\`
2
\`\`\`

## 样例输入 5

\`\`\`
5 5
1 2 2
1 3 5
2 3 1
2 4 7
4 5 2
\`\`\`

## 样例输出 5

\`\`\`
11
\`\`\`

## 数据范围

- \`1 ≤ n ≤ 10^5\`
- \`0 ≤ m ≤ 2×10^5\`
- \`1 ≤ u_i, v_i ≤ n\`，允许重边，\`u_i = v_i\` 可能出现但不影响结果
- \`1 ≤ w_i ≤ 10^6\`
- **存在隐藏加权用例**：\`n = 10^5、m = 2×10^5\` 边界的用例权重 ×2，请使用堆优化 Dijkstra（\`O((n+m) log n)\`）。
`,samples:[{input:`4 4
1 2 1
2 3 2
1 3 5
3 4 1`,output:"4"},{input:"2 0",output:"-1"},{input:`3 2
1 2 3
2 3 4`,output:"7"},{input:`4 3
1 2 10
1 3 1
3 4 1`,output:"2"},{input:`5 5
1 2 2
1 3 5
2 3 1
2 4 7
4 5 2`,output:"11"}],test_count:null},{id:"P6",title:"依赖检查器",contest_type:"acm",score:100,compare_mode:"trim",limits:{time_ms:2e3,memory_mb:256},build:{mode:"make",command:"make",src:null,default_filename:null},topic:"拓扑排序/环检测",difficulty:"中等",statement_md:`# P6 依赖检查器

## 题目背景

构建系统 inspector 负责在编译前检查目标之间的依赖是否能成立。系统里有 n 个构建目标，编号 1 到 n；给定 m 条依赖关系「x 依赖 y」，意思是构建 x 之前必须先构建 y。若依赖关系存在循环，构建必然失败。请写一个检查器：判断能否完成构建；若能，给出一种总耗时最少的检查顺序——即字典序最小的合法构建顺序（每次挑出当前所有依赖已满足的编号最小的目标）。

## 输入格式

第一行两个整数 \`n\` 和 \`m\`。
接下来 \`m\` 行，每行两个整数 \`x\` 和 \`y\`，表示目标 \`x\` 依赖目标 \`y\`（\`y\` 必须先于 \`x\` 构建）。

## 输出格式

若存在循环依赖，输出一行 \`CYCLE\`。
否则输出两行：第一行 \`OK\`，第二行按构建先后顺序输出 n 个目标编号，以单个空格分隔，行末无多余空格。

## 样例输入

\`\`\`
3 2
1 2
1 3
\`\`\`

## 样例输出

\`\`\`
OK
2 3 1
\`\`\`

## 样例输入 2

\`\`\`
2 2
1 2
2 1
\`\`\`

## 样例输出 2

\`\`\`
CYCLE
\`\`\`

## 样例输入 3

\`\`\`
1 0
\`\`\`

## 样例输出 3

\`\`\`
OK
1
\`\`\`

## 样例输入 4

\`\`\`
4 3
2 1
3 2
4 1
\`\`\`

## 样例输出 4

\`\`\`
OK
1 2 3 4
\`\`\`

## 样例输入 5

\`\`\`
5 4
5 4
4 3
3 2
2 1
\`\`\`

## 样例输出 5

\`\`\`
OK
1 2 3 4 5
\`\`\`

## 数据范围

- \`1 ≤ n ≤ 10^5\`
- \`0 ≤ m ≤ 2×10^5\`
- \`1 ≤ x, y ≤ n\`，\`x ≠ y\`，同一条依赖关系可能重复给出
- **存在隐藏加权用例**：\`n = 10^5、m = 2×10^5\` 边界的用例权重 ×2，请使用 \`O(n + m)\` 的队列/堆拓扑排序。

> 本题为多文件 make 构建，请用多文件模式提交 Makefile 与源文件。
`,samples:[{input:`3 2
1 2
1 3`,output:`OK
2 3 1`},{input:`2 2
1 2
2 1`,output:"CYCLE"},{input:"1 0",output:`OK
1`},{input:`4 3
2 1
3 2
4 1`,output:`OK
1 2 3 4`},{input:`5 4
5 4
4 3
3 2
2 1`,output:`OK
1 2 3 4 5`}],test_count:null}],o=Array.isArray(p)?p:[];function b(){return{items:o.map(n=>({id:n.id,title:n.title,contest_type:n.contest_type,score:n.score,test_count:n.test_count,time_limit_ms:n.limits&&n.limits.time_ms,memory_limit_mb:n.limits&&n.limits.memory_mb,build_mode:n.build&&n.build.mode,topic:n.topic,difficulty:n.difficulty})),total:o.length}}function f(n){return o.find(t=>t.id===n)||null}let a=null;function v(){const n=u([]),t=u(0),e=u(!1),m=u(null);async function l(s=!1){if(a&&!s){n.value=a.items,t.value=a.total;return}e.value=!0,m.value=null;try{const i=await d();n.value=i.items||[],t.value=i.total!=null?i.total:n.value.length,a={items:n.value,total:t.value}}catch(i){if(o.length){const c=b();n.value=c.items,t.value=c.total,a={items:n.value,total:t.value}}else m.value=r(i)}finally{e.value=!1}}return{items:n,total:t,loading:e,error:m,load:l}}function z(){const n=u(null),t=u(!1),e=u(null);async function m(l){t.value=!0,e.value=null,n.value=null;try{n.value=await _(l)}catch(s){const i=f(l);i?n.value=i:e.value=r(s)}finally{t.value=!1}}return{problem:n,loading:t,error:e,load:m}}export{z as a,v as u};
