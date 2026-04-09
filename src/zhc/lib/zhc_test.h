/**
 * ZhC 测试框架头文件
 *
 * 提供测试断言和报告功能
 */

#ifndef ZHC_TEST_H
#define ZHC_TEST_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

// 编译器指令
#ifdef __cplusplus
extern "C" {
#endif

// 全局计数器
extern int _test_pass_count;
extern int _test_fail_count;
extern int _test_skip_count;
extern int _test_current_line;
extern const char* _test_current_file;

// 测试状态
typedef enum {
    TEST_PASS,
    TEST_FAIL,
    TEST_SKIP,
    TEST_ERROR
} TestStatus;

// 报告断言结果
void _zhc_report_assertion(const char* file, int line, int passed, const char* msg);

// 测试套件开始/结束
void _zhc_test_suite_start(void);
void _zhc_test_suite_end(void);

// 单个测试开始/结束
void _zhc_test_start(const char* file, int line);
void _zhc_test_end(void);

// 跳过测试
void _zhc_test_skip(const char* reason);

// 断言宏定义
#define 断言等于(a, b, ...) \
    _zhc_report_assertion(__FILE__, __LINE__, (a) == (b), #a " == " #b)

#define 断言不等于(a, b, ...) \
    _zhc_report_assertion(__FILE__, __LINE__, (a) != (b), #a " != " #b)

#define 断言为真(条件, ...) \
    _zhc_report_assertion(__FILE__, __LINE__, (条件), #条件)

#define 断言为假(条件, ...) \
    _zhc_report_assertion(__FILE__, __LINE__, !(条件), "!(" #条件 ")")

#define 断言为空(指针, ...) \
    _zhc_report_assertion(__FILE__, __LINE__, (指针) == NULL, #指针 " == NULL")

#define 断言非空(指针, ...) \
    _zhc_report_assertion(__FILE__, __LINE__, (指针) != NULL, #指针 " != NULL")

#define 断言浮点等于(a, b, epsilon, ...) \
    _zhc_report_assertion(__FILE__, __LINE__, fabs((a) - (b)) < (epsilon), #a " ≈ " #b)

#define 断言字符串等于(a, b, ...) \
    _zhc_report_assertion(__FILE__, __LINE__, strcmp((a), (b)) == 0, #a " == " #b)

#define 断言大于(a, b, ...) \
    _zhc_report_assertion(__FILE__, __LINE__, (a) > (b), #a " > " #b)

#define 断言小于(a, b, ...) \
    _zhc_report_assertion(__FILE__, __LINE__, (a) < (b), #a " < " #b)

#define 断言大于等于(a, b, ...) \
    _zhc_report_assertion(__FILE__, __LINE__, (a) >= (b), #a " >= " #b)

#define 断言小于等于(a, b, ...) \
    _zhc_report_assertion(__FILE__, __LINE__, (a) <= (b), #a " <= " #b)

#define 断言包含(容器, 元素, ...) \
    _zhc_report_assertion(__FILE__, __LINE__, _zhc_contains(容器, 元素), #元素 " in " #容器)

#define 断言不包含(容器, 元素, ...) \
    _zhc_report_assertion(__FILE__, __LINE__, !_zhc_contains(容器, 元素), #元素 " not in " #容器)

#define 断言类型(对象, 类型, ...) \
    _zhc_report_assertion(__FILE__, __LINE__, _zhc_isinstance(对象, #类型), "isinstance(" #对象 ", " #类型 ")")

#define 断言长度(对象, 长度, ...) \
    _zhc_report_assertion(__FILE__, __LINE__, _zhc_length(对象) == (长度), "len(" #对象 ") == " #长度)

#define 断言为空集合(对象, ...) \
    _zhc_report_assertion(__FILE__, __LINE__, _zhc_length(对象) == 0, "len(" #对象 ") == 0")

#define 断言不为空集合(对象, ...) \
    _zhc_report_assertion(__FILE__, __LINE__, _zhc_length(对象) > 0, "len(" #对象 ") > 0")

#define 断言数组相等(a, b, n, ...) \
    _zhc_report_assertion(__FILE__, __LINE__, memcmp((a), (b), (n)) == 0, #a " == " #b " (memcmp)")

#define 断言字符串包含(字符串, 子串, ...) \
    _zhc_report_assertion(__FILE__, __LINE__, strstr((字符串), (子串)) != NULL, #子串 " in " #字符串)

#define 断言字符串以(字符串, 前缀, ...) \
    _zhc_report_assertion(__FILE__, __LINE__, strncmp((字符串), (前缀), strlen(前缀)) == 0, #字符串 " starts with " #前缀)

#define 断言字符串以结尾(字符串, 后缀, ...) \
    _zhc_report_assertion(__FILE__, __LINE__, _zhc_str_ends_with((字符串), (后缀)), #字符串 " ends with " #后缀)

#define 断言抛出异常(表达式, 异常类型, ...) \
    do { \
        int _caught = 0; \
        const char* _exception_msg = NULL; \
        if (setjmp(_test_jmp_buf) == 0) { \
            _zhc_try_catch_start(); \
            { \
                异常类型 _ex; \
                表达式; \
            } \
        } else { \
            _caught = 1; \
        } \
        _zhc_report_assertion(__FILE__, __LINE__, _caught, "抛出 " #异常类型); \
    } while(0)

// 辅助函数声明
int _zhc_contains(const void* container, const void* element);
int _zhc_isinstance(const void* obj, const char* type_name);
int _zhc_length(const void* obj);
int _zhc_str_ends_with(const char* str, const char* suffix);

// 测试跳转缓冲区
extern jmp_buf _test_jmp_buf;
void _zhc_try_catch_start(void);

#ifdef __cplusplus
}
#endif

#endif // ZHC_TEST_H
