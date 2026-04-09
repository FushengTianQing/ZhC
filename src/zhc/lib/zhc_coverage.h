/**
 * ZhC 覆盖率追踪头文件
 *
 * 提供代码覆盖率追踪功能
 */

#ifndef ZHC_COVERAGE_H
#define ZHC_COVERAGE_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

#ifdef __cplusplus
extern "C" {
#endif

// 覆盖率数据结构
typedef struct {
    uint64_t* line_hits;       // 行执行计数
    uint64_t* branch_hits;     // 分支执行计数 (true/false 各一个)
    uint64_t* function_hits;   // 函数调用计数
    char** line_files;         // 行对应的源文件
    char** function_names;     // 函数名
    int line_count;            // 行数
    int branch_count;          // 分支数
    int function_count;        // 函数数
    int line_capacity;         // 行数组容量
    int branch_capacity;       // 分支数组容量
    int function_capacity;     // 函数数组容量
} CoverageData;

// 全局覆盖率数据
extern CoverageData g_coverage;
extern int g_coverage_enabled;

// 初始化和关闭
void coverage_init(void);
void coverage_shutdown(void);
void coverage_enable(void);
void coverage_disable(void);

// 行覆盖率追踪
void coverage_register_line(const char* file, int line);
void coverage_hit_line(const char* file, int line);

// 分支覆盖率追踪
int coverage_register_branch(const char* file, int line);
void coverage_hit_branch(int branch_id, int taken);

// 函数覆盖率追踪
void coverage_register_function(const char* file, const char* func_name, 
                                int start_line, int end_line);
void coverage_hit_function(const char* func_name);

// 报告生成
void coverage_report(const char* output_file);
void coverage_print_summary(void);
void coverage_save_lcov(const char* output_file);

// 宏定义，用于插桩代码
#define COVERAGE_LINE(line_num) \
    do { \
        if (g_coverage_enabled) { \
            coverage_hit_line(__FILE__, line_num); \
        } \
    } while(0)

#define COVERAGE_BRANCH(branch_id, taken) \
    do { \
        if (g_coverage_enabled) { \
            coverage_hit_branch(branch_id, (taken)); \
        } \
    } while(0)

#define COVERAGE_FUNCTION(func_name) \
    do { \
        if (g_coverage_enabled) { \
            coverage_hit_function(func_name); \
        } \
    } while(0)

// 注册宏（通常在程序启动时调用）
#define REGISTER_LINE(file, line) coverage_register_line(file, line)
#define REGISTER_BRANCH(file, line) coverage_register_branch(file, line)
#define REGISTER_FUNCTION(file, func, start, end) \
    coverage_register_function(file, func, start, end)

#ifdef __cplusplus
}
#endif

#endif // ZHC_COVERAGE_H
