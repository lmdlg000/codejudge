#include <iostream>
#include "BigInt.h"
using namespace std;

int main() {
    BigInt a("123");
    a += a;
    cout << "a+=a: " << a << endl;
    BigInt b("99");
    b *= b;
    cout << "b*=b: " << b << endl;
    BigInt c("0000");
    cout << "c: " << c << endl;
    BigInt d("007");
    cout << "d: " << d << endl;
    BigInt e("500");
    BigInt zero;
    e += zero;
    cout << "e+=0: " << e << endl;
    BigInt f("0");
    cout << "f*f: " << (f * f) << endl;
    cout << "a<c: " << (a < c) << endl;
    cout << "d>=c: " << (d >= c) << endl;
    return 0;
}
