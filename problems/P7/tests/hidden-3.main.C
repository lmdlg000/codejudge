#include <iostream>
#include "BigInt.h"
using namespace std;

int main() {
    BigInt a("12a34");
    cout << "a: " << a << endl;
    BigInt b("abc");
    cout << "b: " << b << endl;
    BigInt c("00042");
    BigInt d(42);
    cout << "c==d: " << (c == d) << endl;
    cout << "c<d: " << (c < d) << endl;
    cout << "c>d: " << (c > d) << endl;
    cout << "c!=d: " << (c != d) << endl;
    BigInt e("100");
    BigInt f("99");
    cout << "e>f: " << (e > f) << endl;
    cout << "f<=e: " << (f <= e) << endl;
    return 0;
}
