// 无限递归触发 static_assert，每层都让编译器打印更多信息
template<int N>
struct ErrorGenerator {
    static_assert(N < 0, "💥 Compilation Bomb Triggered 💥 - Printing lots of template instantiations...");
    using type = typename ErrorGenerator<N + 1>::type;
};

int main() {
    typename ErrorGenerator<0>::type t;
    return 0;
}
