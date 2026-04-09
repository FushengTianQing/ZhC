/**
 * ZhC 覆盖率追踪实现
 */

#include "zhc_coverage.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

// 全局覆盖率数据
CoverageData g_coverage = {0};
int g_coverage_enabled = 0;

// 动态数组增长因子
#define GROWTH_FACTOR 2
#define INITIAL_CAPACITY 64

// 初始化覆盖率数据
void coverage_init(void) {
    if (g_coverage.line_hits != NULL) {
        return; // 已初始化
    }
    
    memset(&g_coverage, 0, sizeof(CoverageData));
    
    // 初始分配
    g_coverage.line_capacity = INITIAL_CAPACITY;
    g_coverage.branch_capacity = INITIAL_CAPACITY;
    g_coverage.function_capacity = INITIAL_CAPACITY;
    
    g_coverage.line_hits = (uint64_t*)calloc(g_coverage.line_capacity, sizeof(uint64_t));
    g_coverage.branch_hits = (uint64_t*)calloc(g_coverage.branch_capacity * 2, sizeof(uint64_t));
    g_coverage.function_hits = (uint64_t*)calloc(g_coverage.function_capacity, sizeof(uint64_t));
    
    g_coverage.line_files = (char**)calloc(g_coverage.line_capacity, sizeof(char*));
    g_coverage.function_names = (char**)calloc(g_coverage.function_capacity, sizeof(char*));
    
    g_coverage_enabled = 1;
}

// 关闭覆盖率追踪
void coverage_shutdown(void) {
    // 释放内存
    if (g_coverage.line_files) {
        for (int i = 0; i < g_coverage.line_count; i++) {
            if (g_coverage.line_files[i]) {
                free(g_coverage.line_files[i]);
            }
        }
        free(g_coverage.line_files);
    }
    
    if (g_coverage.function_names) {
        for (int i = 0; i < g_coverage.function_count; i++) {
            if (g_coverage.function_names[i]) {
                free(g_coverage.function_names[i]);
            }
        }
        free(g_coverage.function_names);
    }
    
    free(g_coverage.line_hits);
    free(g_coverage.branch_hits);
    free(g_coverage.function_hits);
    
    memset(&g_coverage, 0, sizeof(CoverageData));
    g_coverage_enabled = 0;
}

// 启用覆盖率追踪
void coverage_enable(void) {
    g_coverage_enabled = 1;
}

// 禁用覆盖率追踪
void coverage_disable(void) {
    g_coverage_enabled = 0;
}

// 注册行
void coverage_register_line(const char* file, int line) {
    if (g_coverage.line_count >= g_coverage.line_capacity) {
        // 扩展数组
        int new_capacity = g_coverage.line_capacity * GROWTH_FACTOR;
        
        uint64_t* new_hits = (uint64_t*)realloc(g_coverage.line_hits, 
                                                  new_capacity * sizeof(uint64_t));
        char** new_files = (char**)realloc(g_coverage.line_files, 
                                           new_capacity * sizeof(char*));
        
        if (new_hits && new_files) {
            // 初始化新增部分
            memset(new_hits + g_coverage.line_count, 0, 
                   (new_capacity - g_coverage.line_count) * sizeof(uint64_t));
            memset(new_files + g_coverage.line_count, 0, 
                   (new_capacity - g_coverage.line_count) * sizeof(char*));
            
            g_coverage.line_hits = new_hits;
            g_coverage.line_files = new_files;
            g_coverage.line_capacity = new_capacity;
        }
    }
    
    // 保存文件路径（简化：只保存文件名）
    const char* basename = strrchr(file, '/');
    if (basename) {
        basename++; // 跳过 '/'
    } else {
        basename = file;
    }
    
    g_coverage.line_files[g_coverage.line_count] = strdup(basename);
    g_coverage.line_count++;
}

// 记录行执行
void coverage_hit_line(const char* file, int line) {
    // 简化实现：使用行号作为索引
    // 实际实现需要更复杂的映射
    if (line > 0 && line <= g_coverage.line_count) {
        g_coverage.line_hits[line - 1]++;
    }
}

// 注册分支
int coverage_register_branch(const char* file, int line) {
    if (g_coverage.branch_count >= g_coverage.branch_capacity) {
        // 扩展数组
        int new_capacity = g_coverage.branch_capacity * GROWTH_FACTOR;
        uint64_t* new_hits = (uint64_t*)realloc(g_coverage.branch_hits, 
                                                  new_capacity * 2 * sizeof(uint64_t));
        
        if (new_hits) {
            memset(new_hits + g_coverage.branch_count * 2, 0, 
                   (new_capacity - g_coverage.branch_capacity) * 2 * sizeof(uint64_t));
            g_coverage.branch_hits = new_hits;
            g_coverage.branch_capacity = new_capacity;
        }
    }
    
    return g_coverage.branch_count++;
}

// 记录分支执行
void coverage_hit_branch(int branch_id, int taken) {
    if (branch_id >= 0 && branch_id < g_coverage.branch_count) {
        if (taken) {
            g_coverage.branch_hits[branch_id * 2]++;
        } else {
            g_coverage.branch_hits[branch_id * 2 + 1]++;
        }
    }
}

// 注册函数
void coverage_register_function(const char* file, const char* func_name, 
                                int start_line, int end_line) {
    if (g_coverage.function_count >= g_coverage.function_capacity) {
        // 扩展数组
        int new_capacity = g_coverage.function_capacity * GROWTH_FACTOR;
        
        uint64_t* new_hits = (uint64_t*)realloc(g_coverage.function_hits, 
                                                  new_capacity * sizeof(uint64_t));
        char** new_names = (char**)realloc(g_coverage.function_names, 
                                           new_capacity * sizeof(char*));
        
        if (new_hits && new_names) {
            memset(new_hits + g_coverage.function_count, 0, 
                   (new_capacity - g_coverage.function_count) * sizeof(uint64_t));
            memset(new_names + g_coverage.function_count, 0, 
                   (new_capacity - g_coverage.function_count) * sizeof(char*));
            
            g_coverage.function_hits = new_hits;
            g_coverage.function_names = new_names;
            g_coverage.function_capacity = new_capacity;
        }
    }
    
    g_coverage.function_names[g_coverage.function_count] = strdup(func_name);
    g_coverage.function_count++;
}

// 记录函数调用
void coverage_hit_function(const char* func_name) {
    for (int i = 0; i < g_coverage.function_count; i++) {
        if (g_coverage.function_names[i] && 
            strcmp(g_coverage.function_names[i], func_name) == 0) {
            g_coverage.function_hits[i]++;
            return;
        }
    }
}

// 打印覆盖率摘要
void coverage_print_summary(void) {
    // 计算行覆盖率
    uint64_t total_lines = 0;
    uint64_t covered_lines = 0;
    for (int i = 0; i < g_coverage.line_count; i++) {
        if (g_coverage.line_files[i]) {
            total_lines++;
            if (g_coverage.line_hits[i] > 0) {
                covered_lines++;
            }
        }
    }
    
    // 计算分支覆盖率
    uint64_t total_branches = g_coverage.branch_count * 2;
    uint64_t covered_branches = 0;
    for (int i = 0; i < g_coverage.branch_count; i++) {
        if (g_coverage.branch_hits[i * 2] > 0) covered_branches++;
        if (g_coverage.branch_hits[i * 2 + 1] > 0) covered_branches++;
    }
    
    // 计算函数覆盖率
    uint64_t total_functions = g_coverage.function_count;
    uint64_t covered_functions = 0;
    for (int i = 0; i < g_coverage.function_count; i++) {
        if (g_coverage.function_hits[i] > 0) {
            covered_functions++;
        }
    }
    
    // 打印报告
    printf("\n");
    printf("========================================\n");
    printf("覆盖率报告\n");
    printf("========================================\n");
    printf("\n");
    
    if (total_lines > 0) {
        double line_rate = (double)covered_lines / total_lines * 100;
        printf("行覆盖率:   %.1f%% (%llu/%llu)\n", 
               line_rate, covered_lines, total_lines);
    }
    
    if (total_branches > 0) {
        double branch_rate = (double)covered_branches / total_branches * 100;
        printf("分支覆盖率: %.1f%% (%llu/%llu)\n", 
               branch_rate, covered_branches, total_branches);
    }
    
    if (total_functions > 0) {
        double func_rate = (double)covered_functions / total_functions * 100;
        printf("函数覆盖率: %.1f%% (%llu/%llu)\n", 
               func_rate, covered_functions, total_functions);
    }
    
    printf("\n");
    printf("========================================\n");
}

// 生成 LCOV 格式报告
void coverage_save_lcov(const char* output_file) {
    FILE* f = fopen(output_file, "w");
    if (!f) {
        fprintf(stderr, "无法打开文件: %s\n", output_file);
        return;
    }
    
    // 当前文件
    const char* current_file = "unknown.c";
    
    fprintf(f, "TN:\n");
    fprintf(f, "SF:%s\n", current_file);
    
    // 函数信息
    for (int i = 0; i < g_coverage.function_count; i++) {
        if (g_coverage.function_names[i]) {
            fprintf(f, "FN:0,%s\n", g_coverage.function_names[i]);
        }
    }
    
    for (int i = 0; i < g_coverage.function_count; i++) {
        if (g_coverage.function_names[i]) {
            fprintf(f, "FNDA:%llu,%s\n", 
                   (unsigned long long)g_coverage.function_hits[i],
                   g_coverage.function_names[i]);
        }
    }
    
    fprintf(f, "FNF:%d\n", g_coverage.function_count);
    
    uint64_t covered_funcs = 0;
    for (int i = 0; i < g_coverage.function_count; i++) {
        if (g_coverage.function_hits[i] > 0) covered_funcs++;
    }
    fprintf(f, "FNH:%llu\n", (unsigned long long)covered_funcs);
    
    // 行信息
    for (int i = 0; i < g_coverage.line_count; i++) {
        if (g_coverage.line_files[i]) {
            fprintf(f, "DA:%d,%llu\n", i + 1, 
                   (unsigned long long)g_coverage.line_hits[i]);
        }
    }
    
    uint64_t total_lines = 0;
    uint64_t covered_lines = 0;
    for (int i = 0; i < g_coverage.line_count; i++) {
        if (g_coverage.line_files[i]) {
            total_lines++;
            if (g_coverage.line_hits[i] > 0) covered_lines++;
        }
    }
    
    fprintf(f, "LF:%llu\n", (unsigned long long)total_lines);
    fprintf(f, "LH:%llu\n", (unsigned long long)covered_lines);
    
    // 分支信息
    for (int i = 0; i < g_coverage.branch_count; i++) {
        fprintf(f, "BRDA:%d,0,%d,0\n", i, 0);  // 简化
    }
    
    fprintf(f, "BRF:%llu\n", (unsigned long long)(g_coverage.branch_count * 2));
    
    uint64_t covered_branches = 0;
    for (int i = 0; i < g_coverage.branch_count; i++) {
        if (g_coverage.branch_hits[i * 2] > 0) covered_branches++;
        if (g_coverage.branch_hits[i * 2 + 1] > 0) covered_branches++;
    }
    fprintf(f, "BRH:%llu\n", (unsigned long long)covered_branches);
    
    fprintf(f, "end_of_record\n");
    
    fclose(f);
}

// 生成覆盖率报告
void coverage_report(const char* output_file) {
    if (output_file) {
        // 根据扩展名选择格式
        const char* ext = strrchr(output_file, '.');
        if (ext && strcmp(ext, ".lcov") == 0) {
            coverage_save_lcov(output_file);
            return;
        }
    }
    
    // 默认输出到文件
    FILE* f = fopen(output_file, "w");
    if (!f) {
        fprintf(stderr, "无法打开文件: %s\n", output_file);
        coverage_print_summary();
        return;
    }
    
    fprintf(f, "覆盖率报告\n");
    fprintf(f, "==========\n\n");
    
    // 计算覆盖率
    uint64_t total_lines = 0, covered_lines = 0;
    for (int i = 0; i < g_coverage.line_count; i++) {
        if (g_coverage.line_files[i]) {
            total_lines++;
            if (g_coverage.line_hits[i] > 0) covered_lines++;
        }
    }
    
    if (total_lines > 0) {
        double line_rate = (double)covered_lines / total_lines * 100;
        fprintf(f, "行覆盖率: %.1f%% (%llu/%llu)\n", 
               line_rate, covered_lines, total_lines);
    }
    
    fclose(f);
}
