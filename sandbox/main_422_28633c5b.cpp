#include <iostream>

// 定义一个单元素的类型
struct Chunk {
    char data[1024];  // 1KB 大小
};

// 使用模板创建一个数组状嵌套结构
template<int N>
struct BigObject {
    Chunk chunk;
    BigObject<N - 1> next;
};

template<>
struct BigObject<0> {};

// 在 main 中构造一个 ~100MB 的模板对象
int main() {
    BigObject<102400> obj;  // 102400 * 1KB = 100MB
    std::cout << "Done\n";  // 永远不会执行，但编译器必须构造整个类型结构
}
