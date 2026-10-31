#include "BigInt.h"
#include <cstring>

// 存储不变式（全题遵守）：
//   isZero == true ⇔ 值为 0；0 的表示两种都合法：len==0/s="" 或 len==1/s="0"（课件风格）；
//   isZero == false ⇒ len >= 1、s[0] != '0'（无前导零）、s[len] == '\0'、size >= len + 1；
//   s[0] 最高位、s[len-1] 最低位（高位在前）。

void BigInt::initFrom(const char* str) {
    isZero = true;
    len = 0;
    size = 1;
    s = new char[1];
    s[0] = '\0';
    if (str == nullptr) return;
    const char* p = str;
    while (*p == '0') ++p;
    const char* start = p;
    size_t n = 0;
    while (*p != '\0') {
        if (*p < '0' || *p > '9') {
            std::cerr << "invalid: " << str << std::endl;
            break;
        }
        ++n;
        ++p;
    }
    if (n == 0) return;
    delete[] s;
    size = n + 1;
    s = new char[size];
    std::memcpy(s, start, n);
    s[n] = '\0';
    isZero = false;
    len = n;
}

void BigInt::assign(const BigInt& o) {
    char* ns = new char[o.size];
    std::memcpy(ns, o.s, o.size);
    delete[] s;
    s = ns;
    len = o.len;
    size = o.size;
    isZero = o.isZero;
}

BigInt::BigInt(size_t v) {
    char tmp[24];
    size_t n = 0;
    do {
        tmp[n++] = char('0' + (v % 10));
        v /= 10;
    } while (v > 0);
    isZero = (n == 1 && tmp[0] == '0');
    len = isZero ? 0 : n;
    size = n + 1;
    s = new char[size];
    for (size_t i = 0; i < n; i++) s[i] = tmp[n - 1 - i];
    s[isZero ? 0 : n] = '\0';
}

BigInt::BigInt(const char* str) {
    initFrom(str);
}

BigInt::BigInt(const BigInt& o) {
    isZero = o.isZero;
    len = o.len;
    size = o.size;
    s = new char[o.size];
    std::memcpy(s, o.s, o.size);
}

BigInt& BigInt::operator=(const BigInt& o) {
    if (this == &o) return *this;
    assign(o);
    return *this;
}

BigInt::~BigInt() {
    delete[] s;
}

int BigInt::cmp(const BigInt& o) const {
    if (isZero && o.isZero) return 0;
    if (isZero) return -1;
    if (o.isZero) return 1;
    if (len != o.len) return len < o.len ? -1 : 1;
    return std::strcmp(s, o.s);
}

BigInt operator+(const BigInt& left, const BigInt& right) {
    BigInt temp = left;
    temp += right;
    return temp;
}

BigInt operator*(const BigInt& left, const BigInt& right) {
    BigInt temp = left;
    temp *= right;
    return temp;
}

BigInt& BigInt::operator+=(const BigInt& right) {
    // 8-step algorithm (Project7 spec): longer/shorter pointers + temp array + reverse assign.
    // Alias-safe: if (this == &right), longer==shorter==this; we read before writing.
    const BigInt* longer;
    const BigInt* shorter;
    if (len >= right.len) {
        longer = this;
        shorter = &right;
    } else {
        longer = &right;
        shorter = this;
    }
    // Handle zero cases: if either is zero, result is the other (already in *this or need copy).
    if (shorter->isZero) {
        // *this + 0 = *this (if shorter==this and longer==&right, then *this is 0 and right is nonzero)
        if (longer != this) {
            // this is zero, right is nonzero -> *this = right
            assign(*longer);
        }
        return *this;
    }
    if (longer->isZero) {
        // both zero (shorter->isZero handled above) -> nothing to do
        return *this;
    }

    // Step 3: temp buffer of length longer->len + 1 (for possible carry)
    size_t cap = longer->len + 1;
    char* temp = new char[cap + 1]; // extra for null terminator
    int carry = 0;
    size_t ti = cap; // fill from back (low-order end of temp)

    // Step 4: from shorter's tail forward, add to longer's corresponding digit
    size_t i = longer->len;
    size_t j = shorter->len;
    while (j > 0) {
        --i;
        --j;
        int sum = (longer->s[i] - '0') + (shorter->s[j] - '0') + carry;
        temp[--ti] = char('0' + (sum % 10));
        carry = sum / 10;
    }
    // Step 5: longer's remaining digits (may have carry)
    while (i > 0) {
        --i;
        int sum = (longer->s[i] - '0') + carry;
        temp[--ti] = char('0' + (sum % 10));
        carry = sum / 10;
    }
    // Step 6: final carry
    if (carry > 0) {
        temp[--ti] = char('0' + carry);
    }
    size_t finalLen = cap - ti;

    // Step 7: delete this->s, allocate new array, reverse-assign temp into it
    char* ns = new char[finalLen + 1];
    for (size_t k = 0; k < finalLen; k++) {
        ns[k] = temp[ti + k];
    }
    ns[finalLen] = '\0';
    delete[] s;
    s = ns;
    len = finalLen;
    size = finalLen + 1;
    isZero = false;
    delete[] temp;

    // Step 8: return *this
    return *this;
}

BigInt& BigInt::operator*=(const BigInt& o) {
    if (isZero || o.isZero) {
        // 结果为 0
        delete[] s;
        size = 1;
        s = new char[1];
        s[0] = '\0';
        len = 0;
        isZero = true;
        return *this;
    }
    size_t n = len + o.len;
    int* acc = new int[n]();
    for (size_t i = 0; i < len; i++) {
        int a = s[len - 1 - i] - '0';
        for (size_t j = 0; j < o.len; j++) {
            acc[i + j] += a * (o.s[o.len - 1 - j] - '0');
        }
    }
    int carry = 0;
    for (size_t k = 0; k < n; k++) {
        acc[k] += carry;
        carry = acc[k] / 10;
        acc[k] %= 10;
    }
    // 去除前导零（acc[n-1] 是最高位）
    size_t finalLen = n;
    while (finalLen > 1 && acc[finalLen - 1] == 0) --finalLen;
    char* r = new char[finalLen + 1];
    for (size_t k = 0; k < finalLen; k++) r[k] = char('0' + acc[finalLen - 1 - k]);
    r[finalLen] = '\0';
    delete[] acc;
    delete[] s;
    s = r;
    len = finalLen;
    size = finalLen + 1;
    isZero = false;
    return *this;
}

bool BigInt::operator==(const BigInt& o) const { return cmp(o) == 0; }
bool BigInt::operator!=(const BigInt& o) const { return cmp(o) != 0; }
bool BigInt::operator< (const BigInt& o) const { return cmp(o) < 0; }
bool BigInt::operator<=(const BigInt& o) const { return cmp(o) <= 0; }
bool BigInt::operator> (const BigInt& o) const { return cmp(o) > 0; }
bool BigInt::operator>=(const BigInt& o) const { return cmp(o) >= 0; }

std::ostream& operator<<(std::ostream& os, const BigInt& b) {
    if (b.isZero) {
        os << '0';
    } else {
        os.write(b.s, static_cast<std::streamsize>(b.len));
    }
    return os;
}
