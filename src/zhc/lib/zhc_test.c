/**
 * ZhC 测试框架实现
 */

#include "zhc_test.h"
#include <setjmp.h>

// 全局计数器
int _test_pass_count = 0;
int _test_fail_count = 0;
int _test_skip_count = 0;
int _test_current_line = 0;
const char* _test_current_file = NULL;

// 测试跳转缓冲区
jmp_buf _test_jmp_buf;

// 报告断言结果
void _zhc_report_assertion(const char* file, int line, int passed, const char* msg) {
    if (passed) {
        _test_pass_count++;
        printf("✅ ");
    } else {
        _test_fail_count++;
        printf("❌ ");
    }
    printf("%s\n", msg);
    if (!passed) {
        printf("   at %s:%d\n", file, line);
    }
}

// 测试套件开始
void _zhc_test_suite_start(void) {
    _test_pass_count = 0;
    _test_fail_count = 0;
    _test_skip_count = 0;
}

// 测试套件结束
void _zhc_test_suite_end(void) {
    // 可以在这里添加汇总输出
}

// 单个测试开始
void _zhc_test_start(const char* file, int line) {
    _test_current_file = file;
    _test_current_line = line;
}

// 单个测试结束
void _zhc_test_end(void) {
    // 可以在这里添加单个测试的汇总
}

// 跳过测试
void _zhc_test_skip(const char* reason) {
    _test_skip_count++;
    printf("⏭️  跳过: %s\n", reason ? reason : "无原因");
}

// 辅助函数实现
int _zhc_contains(const void* container, const void* element) {
    // 默认实现，实际使用时需要特化
    return 0;
}

int _zhc_isinstance(const void* obj, const char* type_name) {
    // 默认实现，实际使用时需要特化
    return 0;
}

int _zhc_length(const void* obj) {
    // 默认实现，实际使用时需要特化
    return 0;
}

void _zhc_try_catch_start(void) {
    // 异常处理支持
}

// 字符串后缀检查
int _zhc_str_ends_with(const char* str, const char* suffix) {
    if (!str || !suffix) return 0;
    size_t str_len = strlen(str);
    size_t suffix_len = strlen(suffix);
    if (suffix_len > str_len) return 0;
    return strcmp(str + str_len - suffix_len, suffix) == 0;
}
