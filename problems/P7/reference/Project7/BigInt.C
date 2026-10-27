#include "BigInt.h"
#include <cstring>

// 存储不变式（全题遵守）：
//   isZero == true  ⇔ 值为 0，此时 len == 0、s[0] == '\0'、size >= 1；
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

BigInt BigInt::operator+(const BigInt& o) const {
    if (isZero) return o;
    if (o.isZero) return *this;
    size_t n = (len > o.len ? len : o.len) + 1;
    char* r = new char[n + 1];
    r[n] = '\0';
    size_t i = len, j = o.len, k = n;
    int carry = 0;
    while (k > 0) {
        int sum = carry;
        if (i > 0) sum += s[--i] - '0';
        if (j > 0) sum += o.s[--j] - '0';
        r[--k] = char('0' + sum % 10);
        carry = sum / 10;
    }
    BigInt res(r);
    delete[] r;
    return res;
}

BigInt BigInt::operator*(const BigInt& o) const {
    if (isZero || o.isZero) return BigInt(size_t(0));
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
    char* r = new char[n + 1];
    for (size_t k = 0; k < n; k++) r[k] = char('0' + acc[n - 1 - k]);
    r[n] = '\0';
    delete[] acc;
    BigInt res(r);
    delete[] r;
    return res;
}

BigInt& BigInt::operator+=(const BigInt& o) {
    BigInt tmp = *this + o;
    return *this = tmp;
}

BigInt& BigInt::operator*=(const BigInt& o) {
    BigInt tmp = *this * o;
    return *this = tmp;
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
