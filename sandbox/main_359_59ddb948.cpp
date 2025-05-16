template<int N>
struct ErrorGenerator {
    static_assert(N < 0, "💥 Compilation Bomb Triggered 💥 - Printing lots of template instantiations...");
    using type = typename ErrorGenerator<N + 1>::type;
};

int main() {
    typename ErrorGenerator<0>::type t;
    return 0;
}