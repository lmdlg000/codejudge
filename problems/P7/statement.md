# P7 大整数类 BigInt（算术运算版）

> 难度：★★★★★ · 多文件 make 工程 · 构建：`make` → `Project7` · 提交：多文件（恰好 4 个文件，见下）

## 题目背景

上一版 `BigInt` 只能存、比、印——这一版要**会算**。请实现一个非负大整数类 `BigInt`（位数不受 `int`/`long long` 限制），在原有构造、比较、输出的基础上，支持加法 `+`、`+=`、乘法 `*`、`*=`，并保证全程**无内存泄漏、无 double free、无 use-after-free**。

与课件示例的区别：课件第 7 周的 `BigInt` 只做"存取与比较"，本题**必须实现算术**；与 P5 的 `Rational` 也不同——不是分数四则，而是**任意位数的非负整数**，用 `char*` 逐位手算（禁用 `std::string`/`to_string`）。工程骨架（目录 + `makefile`）与 P6 同款。课件要求：**Must store the highest order digit first!!!**（最高位必须存在最前，即 `s[0]` 是最高位）；文件必须放在 `Project7` 目录下。

## 提交要求（多文件 make 工程）

多文件提交**恰好包含这 4 个文件**：

| 文件 | 内容 |
| --- | --- |
| `BigInt.h` | `class BigInt` 的**声明** + 头文件保护宏 |
| `BigInt.C` | 全部成员与友元函数的**实现**，首行 `#include "BigInt.h"` |
| `main.C` | 题目给定，**不得修改**（一个字符都不改） |
| `makefile` | 构建规则（见下） |

**`BigInt`（放在 `BigInt.h`，签名不得改动）**：

```cpp
class BigInt {
    bool   isZero;   // true 表示值为 0
    size_t len;      // 存储的位数
    size_t size;     // s 的分配容量（>= len + 1）
    char*  s;        // 数字串：s[0] 为最高位，s[len-1] 为最低位，s[len] = '\0'
    // 可自行增加私有辅助函数（如加法/乘法的核心实现），但不得增删改下列接口
    // 上面 4 个私有数据成员的名字与类型固定，不得增删改
public:
    BigInt(size_t v = 0);
    BigInt(const char* str);
    BigInt(const BigInt& o);
    BigInt& operator=(const BigInt& o);
    ~BigInt();

    friend BigInt operator+(const BigInt& left, const BigInt& right);
    friend BigInt operator*(const BigInt& left, const BigInt& right);
    BigInt& operator+=(const BigInt& right);
    BigInt& operator*=(const BigInt& o);

    bool operator==(const BigInt& o) const;
    bool operator!=(const BigInt& o) const;
    bool operator< (const BigInt& o) const;
    bool operator<=(const BigInt& o) const;
    bool operator> (const BigInt& o) const;
    bool operator>=(const BigInt& o) const;

    friend std::ostream& operator<<(std::ostream& os, const BigInt& b);
};
```

- 四个私有数据成员的**名字、类型、个数都不得改**；public 接口一个都不能动；
- `BigInt(size_t v = 0)` 的**默认参数不能去掉**（无参构造 = 0）；
- 二元 `+`/`*` **不修改任何一方**，返回新对象；`+` 和 `*` 要么**都是友元函数**，要么**都是成员函数**（不能一个友元一个成员，见下文「实现提示」）；`+=`/`*=` 修改自身并返回 `*this`（供 `(x3 += x4)` 链式输出）；
- 所有比较与 `operator<<` 都是 `const`（或友元）。

**实现提示（推荐写法，签名以本节声明为准）**：

**推荐实现顺序**：先把 `+=` 做出来，`+` 直接调用 `+=`（见下）；同理再把 `*=` 做出来，`*` 直接调用 `*=`。这样 `+`/`*` 都不用重复实现竖式逻辑。

**形式一致性（硬性要求）**：`+` 和 `*` 要么**都是友元函数**，要么**都是成员函数**，不能一个友元一个成员。上文类声明给出的是推荐形式（两者均为友元）；若你两个都改成成员函数（`BigInt operator+(const BigInt& right) const;` + `BigInt operator*(const BigInt& right) const;`），只要**两者形式一致**且功能正确，同样算对。

`BigInt& operator+=(const BigInt& right)` 的推荐算法（课件 Project7 要求，8 步）：

1. 定义 `BigInt` 指针 `longer` 和 `shorter`；
2. 如果 `this` 的长度较长，`longer` 设为 `this`、`shorter` 设为 `&right`；否则相反；
3. 生成一个 `char` 指针 `temp` 指向新的 `char` 数组，长度为 `longer` 的长度 + 1；
4. 从 `shorter` 的尾部开始向前循环，与 `longer` 对应的数字相加（注意进位），结果存在 `temp` 对应位置；
5. `longer` 剩下的数字循环（因为前面循环可能有进位数字），结果存在 `temp` 对应位置；
6. 处理最后一个进位，如果有，存在 `temp` 对应位置，记录最终的长度；
7. 删除 `this` 的数组，生成一个新数组，把 `temp` 的数字**反向赋值**给这个数组，正确处理 `this` 的 `size` 和 `len`；
8. 返还 `*this`。

`operator+` 的推荐实现（3 步，直接调用 `+=`）：

1. `BigInt temp = left;`
2. `temp += right;`
3. 返还 `temp`。

`BigInt& operator*=(const BigInt& right)`：竖式乘法（结果位数最多 `len_a + len_b`，任何数乘 0 得 0），同样要防 `a *= a` 别名。

`operator*` 的推荐实现（同 `+`，直接调用 `*=`）：

1. `BigInt temp = left;`
2. `temp *= right;`
3. 返还 `temp`。

> 注意：`+=` 第 4~5 步必须从**低位（串尾）向高位**算起；第 7 步反向赋值是因为 `temp` 是从低位往高位填充的。课件强调 **Must store the highest order digit first!!!**（最高位必须存在最前），最终 `s[0]` 是最高位。

**`main.C`（题目给定，请原样粘贴，不得修改）**：

```cpp
#include <iostream>
#include "BigInt.h"
using namespace std;

int main() {
    BigInt x1("9999999999");
    BigInt x2("1");
    cout << x1 << "+" << x2 << " = " << (x1 + x2) << endl;
    BigInt x3("2100000000");
    BigInt x4("2100000000");
    cout << x3 << "+" << x4 << " = " << (x3 += x4) << endl;
    BigInt y1(99);
    BigInt y2("99");
    size_t v = 0;
    BigInt y3(v);
    cout << y1 << "*" << y2 << " = " << (y1 * y2) << endl;
    cout << y1 << "*" << y3 << " = " << (y1 * y3) << endl;
    BigInt y4("9999999999");
    BigInt y5("9999999999");
    cout << y4 << "*" << y5 << " = " << (y4 *= y5) << endl;
    return 0;
}
```

**`makefile`**（命令前必须是 Tab，不是空格；不许写死绝对路径）：

```makefile
CXX = g++
CXXFLAGS = -std=c++20 -O2 -w -Wall
OBJ = main.o BigInt.o
TARGET = Project7

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(OBJ)

main.o: main.C BigInt.h
	$(CXX) $(CXXFLAGS) -c main.C

BigInt.o: BigInt.C BigInt.h
	$(CXX) $(CXXFLAGS) -c BigInt.C

clean:
	rm -f $(OBJ) $(TARGET)

.PHONY: all clean
```

目标名、变量名可以自己起，但行为必须满足：`make` 生成 `Project7`、`make clean` 清干净 `.o` 与可执行文件、每个 `.o` 写清依赖的 `.h`。

## 输入格式

**无输入**。`main.C` 里所有数据都是写死的常量；隐藏用例会**替换 `main.C` 里的常量**后重新构建运行（`BigInt` 的接口签名保证替换后仍能链接，改动签名 = CE；`friend operator+` 与 `operator+=` 的签名以「提交要求」声明为准）。

## 输出格式

`main.C` 逐行打印五条等式，格式固定为 `左操作数` `运算符` `右操作数` ` = ` `结果`：

- 运算符左右**没有空格**，` = ` 前后各一个空格（`main.C` 已写好，你只要保证 `operator<<` 印出纯数字）；
- 数字一律**无前导零**（0 就印 `0`）；行末不要多余空格，末尾不要多余空行；
- `stderr` 评测忽略：非法数据诊断只许进 `cerr`。

## 样例输入

```text
```

（无输入，`main.C` 固定）

## 样例输出

```text
9999999999+1 = 10000000000
2100000000+2100000000 = 4200000000
99*99 = 9801
99*0 = 0
9999999999*9999999999 = 99999999980000000001
```

五条等式分别覆盖：**进位到更高一位**（结果要多留一位）、**`+=` 并返回 `*this`**（超过 32 位 `int` 上限，必须按位算）、**两位乘两位**、**乘零**（结果是规范 0）、**十位乘十位**（20 位结果，竖式乘法进位要收对）。

## 计算规则与约束

1. **数值域**：非负整数（0 或正）；位数不限，`9999999999 * 9999999999` 这种 20 位结果必须正确。构造串位数 ≤ 1000，运算结果 ≤ 2000 位。
2. **存储不变式（全题遵守）**：
   - `isZero == true` ⇔ 值为 0；0 的规范表示：`isZero == true`、`len == 0`、`s[0] == '\0'`（`size >= 1`）；
   - `isZero == false` 时 `len >= 1`，`s[0]` 不是 `'0'`（**无前导零**：`"007"` 规范化成 `7`，`"0000"` 规范化成 0）；
   - `s[0]` 是最高位、`s[len-1]` 是最低位（**高位在前**）；`s[len] == '\0'`；`size >= len + 1`；
   - 任何写入 `s`/`len` 的地方都要**同步维护 `isZero`**。
3. **构造**：
   - `BigInt(size_t v)`：十进制逐位填入；`v == 0` 得到规范 0；
   - `BigInt(const char* str)`：跳过前导 `'0'`；`str` 为 `nullptr` 或全是 `'0'` 或空串 → 规范 0；**遇到非数字字符**：`cerr << "invalid: " << str << endl;` 诊断后**取前缀数字部分**（全非法则为 0）——`stderr` 评测忽略；
   - `BigInt(const BigInt& o)`：**深拷贝**（绝不能让两个对象共用一块缓冲）。
4. **`operator=`**：自赋值安全（`this == &o` 直接返回）；先分配新的、再 `delete[]` 旧的；返回 `*this`。
5. **加法 `+`/`+=`**：`+=` 是原地修改成员函数（算法见上文「实现提示」8 步）；`+` 推荐直接调用 `+=`（`BigInt temp = left; temp += right; return temp;`）。逐位竖式从低位算起，进位最多 1，结果位数最多 `max(len_a, len_b) + 1`；最高位进位要保留（`9999999999 + 1 = 10000000000`）。
6. **乘法 `*`/`*=`**：`*=` 是原地修改成员函数（竖式乘法）；`*` 推荐直接调用 `*=`（`BigInt temp = left; temp *= right; return temp;`）。第 `i` 位乘第 `j` 位累加到结果第 `i+j` 位；结果位数最多 `len_a + len_b`；任何数乘 0 得 0。
7. **`+=`/`*=` 的返回**：修改自身后返回 `*this` 引用；`operator+`/`operator*` 返回新对象（`BigInt temp = left; temp += right; return temp;` / `BigInt temp = left; temp *= right; return temp;`）。注意 `a += a`、`a *= a` **别名**情形（不能把源数据写坏）。
8. **比较**：六个比较运算符全部 `const`，用一个私有比较辅助统一实现（**先看 `isZero`** → 比位数 → 同位数从高位到低位逐字符比；高位在前，字典序即数值序）。
9. **`operator<<`**：`friend`、不修改对象；`isZero` 为真印 `"0"`，否则按 `s[0..len-1]` 顺序印（**不要反转**）。
10. **禁止**：`std::string`、`to_string`、`vector` 等 STL 容器与字符串设施；`auto`、范围 `for`、`lambda`、`template`、`<bits/stdc++.h>`、`rand`/`srand`/`time`。字符串处理只用 `<cstring>` 与手写循环。
11. **文件划分**：`.h` 只放类声明与保护宏，实现全部在 `BigInt.C`；`BigInt.C` 首行 `#include "BigInt.h"`。

## 健壮性要求

- **R1**：同一程序跑两次输出必须完全一致（不许 `static` 跨对象状态）。
- **R2**：`BigInt(const char*)` 遇非数字字符按第 3 条 `cerr` 诊断并取数字前缀，`stdout` 不受影响。
- **R3**：0、1、纯前导零串（`"0000"`、`"007"`）、最大 10 位数相乘、`+=`/`*=` 别名、乘 0 与加 0——任何路径都要保持 `isZero` 与 `len`/`s` 一致。
- **R4/R7**：`new char[]` ↔ `delete[]` 配对；拷贝构造/`operator=` 深拷贝；`+`/`*` 临时对象析构干净。自测用 valgrind 或 ASan，要求 0 errors、0 leaks。
- **R5**：析构 + 拷贝构造 + `operator=` 资源三件套齐全且正确。
- **R8**：`main.C` 原样粘贴，一个字符都不改；调试输出只能进 `cerr`，提交前删掉。
- **R9**：保护宏、`.h` 只声明、`makefile` 的 `all`/`clean` 可用、不写死绝对路径。

**边界保证**：构造串只含数字的用例之外，隐藏用例会构造非数字串考察 R2；位数不超过 1000 位；运算结果不超过 2000 位；不保证没有前导零与 0；不保证 `+=`/`*=` 的左右不是同一对象（但你必须自己防住）。
