// 测试函数语法 v4.0

#include <stdio.h>

// 基础函数声明
int 求和(int a, int b) {
    return a + b;
}

// 无参数函数
void printf问候语() {
    printf("你好，世界！\n");
}

// 复杂参数类型
void 处理数组(int 数组[], int 长度) {
    for (int i = 0; i < 长度; i++) {
        printf("数组[%d] = %d\n", i, 数组[i]);
    }
}

// 使用中文类型
int 中文求和(int a, int b) {
    return a + b;
}

// struct参数
struct 点 {
    float x;
    float y;
};

float 计算距离(struct 点 p1, struct 点 p2) {
    float dx = p1.x - p2.x;
    float dy = p1.y - p2.y;
    return dx * dx + dy * dy;
}

// main
int main() {
    int 结果 = 求和(10, 20);
    printf("求和结果: %d\n", 结果);
    
    printf问候语();
    
    int 数组[5] = {1, 2, 3, 4, 5};
    处理数组(数组, 5);
    
    int 中文结果 = 中文求和(30, 40);
    printf("中文求和结果: %d\n", 中文结果);
    
    struct 点 点1 = {0.0, 0.0};
    struct 点 点2 = {3.0, 4.0};
    float 距离平方 = 计算距离(点1, 点2);
    printf("距离平方: %f\n", 距离平方);
    
    return 0;
}