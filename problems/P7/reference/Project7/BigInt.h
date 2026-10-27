#ifndef BIGINT_H
#define BIGINT_H

#include <iostream>

class BigInt {
    bool   isZero;
    size_t len;
    size_t size;
    char*  s;
    void initFrom(const char* str);
    void assign(const BigInt& o);
    int  cmp(const BigInt& o) const;
public:
    BigInt(size_t v = 0);
    BigInt(const char* str);
    BigInt(const BigInt& o);
    BigInt& operator=(const BigInt& o);
    ~BigInt();

    BigInt operator+(const BigInt& o) const;
    BigInt operator*(const BigInt& o) const;
    BigInt& operator+=(const BigInt& o);
    BigInt& operator*=(const BigInt& o);

    bool operator==(const BigInt& o) const;
    bool operator!=(const BigInt& o) const;
    bool operator< (const BigInt& o) const;
    bool operator<=(const BigInt& o) const;
    bool operator> (const BigInt& o) const;
    bool operator>=(const BigInt& o) const;

    friend std::ostream& operator<<(std::ostream& os, const BigInt& b);
};

#endif
