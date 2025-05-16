#include <iostream>

// 编译期递归模板计算 Fibonacci 数
template<int N>
struct Fib {
    static const unsigned long long value = Fib<N - 1>::value + Fib<N - 2>::value;
};

template<>
struct Fib<1> {
    static const unsigned long long value = 1;
};

template<>
struct Fib<0> {
    static const unsigned long long value = 0;
};

int main() {
    constexpr int N = 4500;  // 👈 改成更大的值，比如 100 或 500 来测试编译性能
    std::cout << "Fib(" << N << ") = " << Fib<N>::value << std::endl;
    return 0;
}
