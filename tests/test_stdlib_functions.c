// 测试标准库函数 v5.0

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <ctype.h>

// 测试各种标准库函数
int main() {
    // 内存管理测试
    int* 指针 = (int*)malloc(sizeof(int) * 10);
    if (指针 == NULL) {
        printf("内存申请失败\n");
        return 1;
    }
    
    memset(指针, 0, sizeof(int) * 10);
    
    for (int i = 0; i < 10; i++) {
        指针[i] = i * i;
    }
    
    printf("内存管理测试: ");
    for (int i = 0; i < 10; i++) {
        printf("%d ", 指针[i]);
    }
    printf("\n");
    
    free(指针);
    
    // 字符串操作测试
    char 字符串1[50] = "Hello, ";
    char 字符串2[] = "World!";
    
    strcat(字符串1, 字符串2);
    printf("字符串连接: %s\n", 字符串1);
    
    int 长度 = strlen(字符串1);
    printf("字符串长度: %d\n", 长度);
    
    // 数学函数测试
    double x = 16.0;
    double sqrt值 = sqrt(x);
    double 幂值 = pow(2.0, 3.0);
    double sin值 = sin(3.14159 / 6.0);  // sin(π/6) = 0.5
    
    printf("数学函数测试:\n");
    printf("  平方根(%.1f) = %.4f\n", x, sqrt值);
    printf("  2^3 = %.1f\n", 幂值);
    printf("  sin(π/6) = %.4f\n", sin值);
    
    // 字符处理测试
    char 字符 = 'A';
    char 小写字符 = tolower(字符);
    char 数字字符 = '7';
    
    printf("字符处理测试:\n");
    printf("  转小写('%c') = '%c'\n", 字符, 小写字符);
    printf("  '%c' 是数字? %s\n", 数字字符, isdigit(数字字符) ? "是" : "否");
    printf("  '%c' 是字母? %s\n", 字符, isalpha(字符) ? "是" : "否");
    
    // 时间函数测试
    time_t time值 = time(NULL);
    printf("当前时间戳: %ld\n", time值);
    
    clock_t 开始时间 = clock();
    
    // 做一些工作
    long 和 = 0;
    for (int i = 0; i < 1000000; i++) {
        和 += i;
    }
    
    clock_t 结束时间 = clock();
    double 耗时毫秒 = ((double)(结束时间 - 开始时间)) / CLOCKS_PER_SEC * 1000;
    printf("计算耗时: %.2f 毫秒\n", 耗时毫秒);
    
    // rand测试
    srand(time值);
    int 随机值 = rand() % 100;
    printf("随机数 (0-99): %d\n", 随机值);
    
    // 文件操作测试（简单演示）
    printf("所有测试完成！\n");
    
    return 0;
}