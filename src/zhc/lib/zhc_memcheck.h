/**
 * @file zhc_memcheck.h
 * @brief ZhC 内存使用分析器 - 内存泄漏检测和内存使用分析
 *
 * 功能：
 * 1. 内存分配追踪
 * 2. 内存释放验证
 * 3. 泄漏检测
 * 4. 使用统计
 *
 * 使用方法：
 *   // 初始化内存检查器
 *   memcheck_init();
 *
 *   // 使用追踪分配函数
 *   void* ptr = memcheck_alloc(size, __FILE__, __LINE__, "分配函数名");
 *   memcheck_free(ptr, __FILE__, __LINE__);
 *
 *   // 输出报告
 *   memcheck_report();
 *   memcheck_shutdown();
 *
 * 中文语法：
 *   整数型 指针 = 申请(尺寸);
 *   释放(指针);
 */

#ifndef ZHC_MEMCHECK_H
#define ZHC_MEMCHECK_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ============================================================================
 * 数据结构定义
 * ============================================================================ */

/**
 * @brief 内存块信息
 */
typedef struct MemBlock {
    void* ptr;                  /* 内存指针 */
    size_t size;                /* 内存大小 */
    const char* file;           /* 分配文件名 */
    int line;                   /* 分配行号 */
    const char* func;           /* 分配函数名 */
    uint64_t alloc_time;        /* 分配时间戳 */
    uint64_t alloc_id;          /* 分配 ID */
    struct MemBlock* next;      /* 链表指针 */
} MemBlock;

/**
 * @brief 内存操作类型
 */
typedef enum MemOpType {
    MEM_OP_ALLOC = 0,           /* 分配 */
    MEM_OP_FREE = 1,            /* 释放 */
    MEM_OP_REALLOC = 2,         /* 重新分配 */
} MemOpType;

/**
 * @brief 内存操作记录
 */
typedef struct MemOpRecord {
    MemOpType type;             /* 操作类型 */
    void* ptr;                  /* 内存指针 */
    size_t size;                /* 大小 */
    const char* file;            /* 文件 */
    int line;                   /* 行号 */
    const char* func;           /* 函数 */
    uint64_t alloc_id;          /* 关联的分配 ID */
    uint64_t timestamp;         /* 时间戳 */
    struct MemOpRecord* next;   /* 链表指针 */
} MemOpRecord;

/**
 * @brief 内存统计信息
 */
typedef struct MemStats {
    uint64_t total_alloc_bytes;     /* 总分配字节数 */
    uint64_t total_free_bytes;      /* 总释放字节数 */
    uint64_t current_used_bytes;    /* 当前使用字节数 */
    uint64_t peak_used_bytes;        /* 峰值使用字节数 */
    uint64_t alloc_count;            /* 分配次数 */
    uint64_t free_count;             /* 释放次数 */
    uint64_t leak_count;             /* 泄漏次数 */
    uint64_t leak_bytes;             /* 泄漏字节数 */
    uint64_t double_free_count;      /* 重复释放次数 */
    uint64_t invalid_free_count;     /* 无效释放次数 */
} MemStats;

/**
 * @brief 分配源统计
 */
typedef struct AllocSite {
    const char* file;            /* 文件 */
    int line;                    /* 行号 */
    const char* func;            /* 函数 */
    uint64_t alloc_count;        /* 分配次数 */
    uint64_t total_bytes;        /* 总字节数 */
    uint64_t current_bytes;      /* 当前字节数 */
    struct AllocSite* next;      /* 链表指针 */
} AllocSite;

/**
 * @brief 内存检查器状态
 */
typedef struct MemcheckState {
    int initialized;             /* 是否已初始化 */
    int enabled;                 /* 是否启用 */
    MemBlock* blocks;            /* 内存块链表 */
    MemOpRecord* operations;     /* 操作记录链表 */
    AllocSite* alloc_sites;      /* 分配源统计 */
    MemStats stats;             /* 统计信息 */
    uint64_t current_id;         /* 当前分配 ID */
    int max_history;            /* 最大历史记录数 */
} MemcheckState;

/* 全局实例 */
extern MemcheckState g_memcheck;

/* ============================================================================
 * 初始化和控制 API
 * ============================================================================ */

/**
 * @brief 初始化内存检查器
 * @param max_history 最大历史记录数（0 表示不限制）
 */
void memcheck_init(int max_history);

/**
 * @brief 关闭内存检查器
 */
void memcheck_shutdown(void);

/**
 * @brief 启用内存追踪
 */
void memcheck_enable(void);

/**
 * @brief 禁用内存追踪
 */
void memcheck_disable(void);

/**
 * @brief 检查是否启用
 * @return 1 启用，0 禁用
 */
int memcheck_is_enabled(void);

/**
 * @brief 重置统计数据
 */
void memcheck_reset(void);

/* ============================================================================
 * 内存追踪 API
 * ============================================================================ */

/**
 * @brief 分配内存（追踪版本）
 * @param size 大小
 * @param file 文件名
 * @param line 行号
 * @param func 函数名
 * @return 分配的内存指针
 */
void* memcheck_alloc(size_t size, const char* file, int line, const char* func);

/**
 * @brief 释放内存（追踪版本）
 * @param ptr 内存指针
 * @param file 文件名
 * @param line 行号
 */
void memcheck_free(void* ptr, const char* file, int line);

/**
 * @brief 重新分配内存（追踪版本）
 * @param ptr 原指针
 * @param new_size 新大小
 * @param file 文件名
 * @param line 行号
 * @return 新指针
 */
void* memcheck_realloc(void* ptr, size_t new_size, const char* file, int line);

/* ============================================================================
 * 查询 API
 * ============================================================================ */

/**
 * @brief 获取内存块信息
 * @param ptr 内存指针
 * @return 内存块信息，不存在返回 NULL
 */
MemBlock* memcheck_get_block(void* ptr);

/**
 * @brief 检查指针是否有效
 * @param ptr 内存指针
 * @return 1 有效，0 无效
 */
int memcheck_is_valid_ptr(void* ptr);

/**
 * @brief 获取当前使用的内存字节数
 * @return 字节数
 */
uint64_t memcheck_current_used(void);

/**
 * @brief 获取峰值使用内存字节数
 * @return 字节数
 */
uint64_t memcheck_peak_used(void);

/**
 * @brief 获取统计信息
 * @return 统计信息
 */
MemStats memcheck_get_stats(void);

/* ============================================================================
 * 报告生成 API
 * ============================================================================ */

/**
 * @brief 生成内存使用报告
 */
void memcheck_report(void);

/**
 * @brief 生成 JSON 格式报告
 * @param output 输出文件
 */
void memcheck_report_json(FILE* output);

/**
 * @brief 生成泄漏详情报告
 * @param output 输出文件
 */
void memcheck_report_leaks(FILE* output);

/**
 * @brief 生成分配源报告
 * @param output 输出文件
 */
void memcheck_report_alloc_sites(FILE* output);

/**
 * @brief 检查是否有泄漏
 * @return 1 有泄漏，0 无泄漏
 */
int memcheck_has_leaks(void);

/**
 * @brief 获取泄漏数量
 * @return 泄漏数量
 */
uint64_t memcheck_get_leak_count(void);

/**
 * @brief 获取泄漏字节数
 * @return 泄漏字节数
 */
uint64_t memcheck_get_leak_bytes(void);

/* ============================================================================
 * 便捷宏定义（中文语法支持）
 * ============================================================================ */

/**
 * @brief 追踪分配宏
 * @param size 大小
 */
#define 申请(size) memcheck_alloc(size, __FILE__, __LINE__, "申请")

/**
 * @brief 追踪释放宏
 * @param ptr 指针
 */
#define 释放(ptr) memcheck_free(ptr, __FILE__, __LINE__)

/**
 * @brief 追踪重新分配宏
 * @param ptr 原指针
 * @param size 新大小
 */
#define 重新申请(ptr, size) memcheck_realloc(ptr, size, __FILE__, __LINE__)

/**
 * @brief 标准分配宏（自动追踪）
 * @param type 类型
 * @param size 大小
 */
#define 新建(type, size) (type*)memcheck_alloc(size, __FILE__, __LINE__, "新建")

/* ============================================================================
 * 时间戳获取
 * ============================================================================ */

/**
 * @brief 获取当前时间戳（纳秒）
 * @return 时间戳
 */
uint64_t memcheck_get_time_ns(void);

/**
 * @brief 格式化字节数
 * @param bytes 字节数
 * @param buffer 输出缓冲区
 * @param size 缓冲区大小
 */
void memcheck_format_bytes(uint64_t bytes, char* buffer, size_t size);

#ifdef __cplusplus
}
#endif

#endif /* ZHC_MEMCHECK_H */
