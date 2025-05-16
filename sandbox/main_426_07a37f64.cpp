constexpr int f(int x) {
    return x + x + x + x + x + x + x + x + x + x; // 嵌套千层
}

int main() {
    constexpr int x = f(f(f(f(f(f(f(f(f(f(f(f(f(f(f(1))))))))))))))));
}
