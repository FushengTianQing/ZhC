/**
 * zhc_stdlib.h - 中文C编译器标准库
 *
 * 提供 stdlib 模块对应的所有函数实现。
 * 本头文件应在使用 stdlib 模块时通过 #include "zhc_stdlib.h" 引入。
 *
 * 版本: 1.0
 * 作者: ZHC编译器团队
 */

#ifndef ZHC_STDLIB_H
#define ZHC_STDLIB_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <ctype.h>
#include <math.h>

/* ============================================================
 * 内存管理
 * ============================================================ */

/**
 * zhc_malloc - 分配内存
 *
 * 封装 malloc，分配指定字节数的内存块。
 *
 * 参数:
 *   size - 要分配的内存字节数
 *
 * 返回值: 指向分配内存的指针，失败返回 NULL
 */
void* zhc_malloc(int size) {
    if (size <= 0) return NULL;
    return malloc((size_t)size);
}

/**
 * zhc_calloc - 分配并初始化内存
 *
 * 封装 calloc，分配内存并初始化为0。
 *
 * 参数:
 *   count - 元素数量
 *   size  - 每个元素的字节大小
 *
 * 返回值: 指向分配内存的指针，失败返回 NULL
 */
void* zhc_calloc(int count, int size) {
    if (count <= 0 || size <= 0) return NULL;
    return calloc((size_t)count, (size_t)size);
}

/**
 * zhc_realloc - 重新分配内存
 *
 * 封装 realloc，调整已分配内存的大小。
 *
 * 参数:
 *   ptr  - 原内存指针
 *   size - 新的内存字节数
 *
 * 返回值: 指向新内存的指针，失败返回 NULL（原内存不变）
 */
void* zhc_realloc(void *ptr, int size) {
    if (size <= 0) return NULL;
    return realloc(ptr, (size_t)size);
}

/**
 * zhc_free - 释放内存
 *
 * 封装 free，释放之前分配的内存。
 *
 * 参数:
 *   ptr - 要释放的内存指针
 */
void zhc_free(void *ptr) {
    if (ptr != NULL) {
        free(ptr);
    }
}

/* ============================================================
 * 类型转换
 * ============================================================ */

/**
 * zhc_atoi - 字符串转整数
 *
 * 封装 atoi，将字符串转换为整数。
 *
 * 参数:
 *   str - 要转换的字符串
 *
 * 返回值: 转换后的整数，失败返回 0
 */
int zhc_atoi(const char *str) {
    if (str == NULL) return 0;
    return atoi(str);
}

/**
 * zhc_atol - 字符串转长整数
 *
 * 封装 atol，将字符串转换为长整数。
 *
 * 参数:
 *   str - 要转换的字符串
 *
 * 返回值: 转换后的长整数，失败返回 0
 */
long zhc_atol(const char *str) {
    if (str == NULL) return 0L;
    return atol(str);
}

/**
 * zhc_atof - 字符串转浮点数
 *
 * 封装 atof，将字符串转换为浮点数。
 *
 * 参数:
 *   str - 要转换的字符串
 *
 * 返回值: 转换后的浮点数，失败返回 0.0
 */
double zhc_atof(const char *str) {
    if (str == NULL) return 0.0;
    return atof(str);
}

/**
 * zhc_itoa - 整数转字符串
 *
 * 将整数转换为字符串。
 *
 * 参数:
 *   num   - 要转换的整数
 *   buf   - 存储结果的字符串缓冲区
 *   size  - 缓冲区大小
 *
 * 返回值: 转换后的字符串指针（buf），失败返回 NULL
 */
char* zhc_itoa(int num, char *buf, int size) {
    if (buf == NULL || size <= 0) return NULL;
    snprintf(buf, (size_t)size, "%d", num);
    return buf;
}

/**
 * zhc_ftoa - 浮点数转字符串
 *
 * 将浮点数转换为字符串。
 *
 * 参数:
 *   num     - 要转换的浮点数
 *   buf     - 存储结果的字符串缓冲区
 *   size    - 缓冲区大小
 *   decimal - 小数点后的位数
 *
 * 返回值: 转换后的字符串指针（buf），失败返回 NULL
 */
char* zhc_ftoa(double num, char *buf, int size, int decimal) {
    if (buf == NULL || size <= 0) return NULL;
    if (decimal < 0) decimal = 0;
    if (decimal > 15) decimal = 15;
    
    snprintf(buf, (size_t)size, "%.*f", decimal, num);
    return buf;
}

/* ============================================================
 * 随机数
 * ============================================================ */

/**
 * zhc_srand - 初始化随机数种子
 *
 * 封装 srand，设置随机数生成器的种子。
 *
 * 参数:
 *   seed - 随机数种子
 */
void zhc_srand(unsigned int seed) {
    srand(seed);
}

/**
 * zhc_rand - 生成随机数
 *
 * 封装 rand，生成伪随机数。
 *
 * 返回值: 随机整数（范围 0 到 RAND_MAX）
 */
int zhc_rand(void) {
    return rand();
}

/**
 * zhc_rand_range - 生成指定范围随机数
 *
 * 生成 [min, max] 范围内的随机数。
 *
 * 参数:
 *   min - 随机数最小值（包含）
 *   max - 随机数最大值（包含）
 *
 * 返回值: 范围内的随机整数
 */
int zhc_rand_range(int min, int max) {
    if (min > max) {
        int temp = min;
        min = max;
        max = temp;
    }
    return min + rand() % (max - min + 1);
}

/* ============================================================
 * 排序与搜索
 * ============================================================ */

/**
 * zhc_qsort - 快速排序
 *
 * 封装 qsort，对数组进行快速排序。
 *
 * 参数:
 *   base      - 要排序的数组
 *   count     - 数组元素个数
 *   size      - 每个元素的字节大小
 *   compare   - 比较两个元素的函数指针
 */
void zhc_qsort(void *base, int count, int size, 
               int (*compare)(const void*, const void*)) {
    if (base == NULL || count <= 0 || size <= 0 || compare == NULL) return;
    qsort(base, (size_t)count, (size_t)size, compare);
}

/**
 * zhc_bsearch - 二分查找
 *
 * 封装 bsearch，在已排序数组中二分查找。
 *
 * 参数:
 *   key     - 要查找的元素
 *   base    - 已排序的数组
 *   count   - 数组元素个数
 *   size    - 每个元素的字节大小
 *   compare - 比较两个元素的函数指针
 *
 * 返回值: 找到的元素指针，未找到返回 NULL
 */
void* zhc_bsearch(const void *key, const void *base, int count, int size,
                 int (*compare)(const void*, const void*)) {
    if (key == NULL || base == NULL || count <= 0 || size <= 0 || compare == NULL) {
        return NULL;
    }
    return bsearch(key, base, (size_t)count, (size_t)size, compare);
}

/* ============================================================
 * 系统功能
 * ============================================================ */

/**
 * zhc_exit - 退出程序
 *
 * 封装 exit，正常终止程序。
 *
 * 参数:
 *   status - 退出状态码
 */
void zhc_exit(int status) {
    exit(status);
}

/**
 * zhc_system - 执行系统命令
 *
 * 封装 system，执行系统命令。
 *
 * 参数:
 *   command - 要执行的系统命令字符串
 *
 * 返回值: 命令的退出状态码
 */
int zhc_system(const char *command) {
    if (command == NULL) {
        /* 检查shell是否可用 */
        return system(NULL);
    }
    return system(command);
}

/**
 * zhc_getenv - 获取环境变量
 *
 * 封装 getenv，获取环境变量的值。
 *
 * 参数:
 *   name - 环境变量名称
 *
 * 返回值: 环境变量的值字符串，不存在返回 NULL
 */
char* zhc_getenv(const char *name) {
    if (name == NULL) return NULL;
    return getenv(name);
}

/* ============================================================
 * 绝对值与类型范围
 * ============================================================ */

/**
 * zhc_abs - 整数绝对值
 *
 * 封装 abs，计算整数的绝对值。
 *
 * 参数:
 *   num - 整数值
 *
 * 返回值: 绝对值
 */
int zhc_abs(int num) {
    return (num < 0) ? -num : num;
}

/**
 * zhc_labs - 长整数绝对值
 *
 * 封装 labs，计算长整数的绝对值。
 *
 * 参数:
 *   num - 长整数值
 *
 * 返回值: 绝对值
 */
long zhc_labs(long num) {
    return (num < 0) ? -num : num;
}

/**
 * zhc_fabs - 浮点数绝对值
 *
 * 封装 fabs，计算浮点数的绝对值。
 *
 * 参数:
 *   num - 浮点数值
 *
 * 返回值: 绝对值
 */
double zhc_fabs(double num) {
    return fabs(num);
}

#endif /* ZHC_STDLIB_H */