/**
 * @file zhc_profiler.h
 * @brief ZhC 性能剖析器 - 函数调用分析和性能测量工具
 *
 * 功能：
 * 1. 函数调用追踪
 * 2. 执行时间测量（纳秒精度）
 * 3. 调用次数统计
 * 4. 调用关系图生成
 * 5. 性能报告输出
 *
 * 使用方法：
 *   // 初始化剖析器
 *   profiler_init(1000);
 *   profiler_enable();
 *
 *   // 使用剖析宏
 *   void my_function() {
 *       PROFILE_FUNCTION();
 *       // ... 函数代码
 *   }
 *
 *   // 输出报告
 *   profiler_report();
 *   profiler_shutdown();
 */

#ifndef ZHC_PROFILER_H
#define ZHC_PROFILER_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ============================================================================
 * 数据结构定义
 * ============================================================================ */

/**
 * @brief 函数剖析记录
 */
typedef struct FunctionProfile {
    const char* name;           /* 函数名 */
    uint64_t call_count;        /* 调用次数 */
    uint64_t total_time_ns;     /* 总执行时间（纳秒） */
    uint64_t min_time_ns;       /* 最小执行时间 */
    uint64_t max_time_ns;       /* 最大执行时间 */
    uint64_t start_time_ns;     /* 当前调用开始时间 */
    int call_depth;             /* 调用深度 */
    struct FunctionProfile* next; /* 链表指针 */
} FunctionProfile;

/**
 * @brief 调用关系记录
 */
typedef struct CallRelation {
    const char* caller;         /* 调用者函数名 */
    const char* callee;         /* 被调用者函数名 */
    uint64_t call_count;        /* 调用次数 */
    uint64_t total_time_ns;     /* 总时间 */
    struct CallRelation* next;  /* 链表指针 */
} CallRelation;

/**
 * @brief 调用栈帧
 */
typedef struct CallFrame {
    const char* function_name;  /* 函数名 */
    uint64_t start_time_ns;     /* 开始时间 */
    struct CallFrame* next;     /* 下一帧 */
} CallFrame;

/**
 * @brief 剖析器统计信息
 */
typedef struct ProfilerStats {
    uint64_t total_calls;       /* 总调用次数 */
    uint64_t total_time_ns;     /* 总执行时间 */
    uint64_t function_count;    /* 记录的函数数量 */
    uint64_t relation_count;    /* 记录的调用关系数量 */
    int max_depth;              /* 最大调用深度 */
} ProfilerStats;

/**
 * @brief 剖析器配置
 */
typedef struct ProfilerConfig {
    int max_functions;          /* 最大函数数量 */
    int max_relations;          /* 最大调用关系数量 */
    int enabled;                /* 是否启用 */
    int track_call_graph;       /* 是否追踪调用图 */
    int track_memory;           /* 是否追踪内存 */
    FILE* output;               /* 输出文件 */
} ProfilerConfig;

/**
 * @brief 剖析器状态（全局实例）
 */
typedef struct ProfilerState {
    int initialized;            /* 是否已初始化 */
    int enabled;                /* 是否启用 */
    FunctionProfile* functions; /* 函数记录链表 */
    CallRelation* relations;    /* 调用关系链表 */
    CallFrame* call_stack;      /* 调用栈 */
    int call_depth;             /* 当前调用深度 */
    ProfilerStats stats;        /* 统计信息 */
    ProfilerConfig config;      /* 配置 */
} ProfilerState;

/* 全局剖析器实例 */
extern ProfilerState g_profiler;

/* ============================================================================
 * 剖析器控制 API
 * ============================================================================ */

/**
 * @brief 初始化剖析器
 * @param max_functions 最大函数数量
 * @return 0 成功，-1 失败
 */
int profiler_init(int max_functions);

/**
 * @brief 关闭剖析器
 */
void profiler_shutdown(void);

/**
 * @brief 启用剖析
 */
void profiler_enable(void);

/**
 * @brief 禁用剖析
 */
void profiler_disable(void);

/**
 * @brief 检查剖析器是否启用
 * @return 1 启用，0 禁用
 */
int profiler_is_enabled(void);

/**
 * @brief 重置剖析器状态
 */
void profiler_reset(void);

/* ============================================================================
 * 函数剖析 API
 * ============================================================================ */

/**
 * @brief 进入函数（开始计时）
 * @param func_name 函数名
 */
void profiler_enter(const char* func_name);

/**
 * @brief 退出函数（结束计时）
 * @param func_name 函数名
 */
void profiler_exit(const char* func_name);

/**
 * @brief 获取函数剖析记录
 * @param func_name 函数名
 * @return 函数记录，不存在返回 NULL
 */
FunctionProfile* profiler_get_function(const char* func_name);

/**
 * @brief 获取所有函数记录
 * @param count 输出函数数量
 * @return 函数记录数组
 */
FunctionProfile** profiler_get_all_functions(int* count);

/* ============================================================================
 * 调用关系 API
 * ============================================================================ */

/**
 * @brief 记录调用关系
 * @param caller 调用者
 * @param callee 被调用者
 */
void profiler_record_call(const char* caller, const char* callee);

/**
 * @brief 获取调用关系
 * @param count 输出关系数量
 * @return 调用关系数组
 */
CallRelation** profiler_get_call_relations(int* count);

/* ============================================================================
 * 报告生成 API
 * ============================================================================ */

/**
 * @brief 生成剖析报告
 */
void profiler_report(void);

/**
 * @brief 生成 JSON 格式报告
 * @param output 输出文件
 */
void profiler_report_json(FILE* output);

/**
 * @brief 生成调用图（DOT 格式）
 * @param output 输出文件
 */
void profiler_export_call_graph_dot(FILE* output);

/**
 * @brief 获取统计信息
 * @return 统计信息
 */
ProfilerStats profiler_get_stats(void);

/* ============================================================================
 * 便捷宏定义
 * ============================================================================ */

/**
 * @brief 自动剖析函数
 * 使用方法：
 *   void my_function() {
 *       PROFILE_FUNCTION();
 *       // ... 函数代码
 *   }
 */
#define PROFILE_FUNCTION() \
    ProfileAuto _profile_auto_##__LINE__ = profile_auto_init(__func__)

/**
 * @brief 剖析代码块
 * @param name 代码块名称
 */
#define PROFILE_SCOPE(name) \
    ProfileAuto _profile_auto_##__LINE__ = profile_auto_init(name)

/**
 * @brief 自动剖析辅助结构
 */
typedef struct ProfileAuto {
    const char* name;
} ProfileAuto;

/**
 * @brief 初始化自动剖析
 */
static inline ProfileAuto profile_auto_init(const char* name) {
    profiler_enter(name);
    ProfileAuto auto_profile = { .name = name };
    return auto_profile;
}

/**
 * @brief 清理自动剖析
 */
static inline void profile_auto_cleanup(ProfileAuto* auto_profile) {
    if (auto_profile && auto_profile->name) {
        profiler_exit(auto_profile->name);
    }
}

/* GCC/Clang 自动清理属性 */
#if defined(__GNUC__) || defined(__clang__)
#define PROFILE_AUTO_CLEANUP __attribute__((cleanup(profile_auto_cleanup)))
#else
#define PROFILE_AUTO_CLEANUP
#endif

/* ============================================================================
 * 时间工具函数
 * ============================================================================ */

/**
 * @brief 获取当前时间（纳秒）
 * @return 当前时间戳（纳秒）
 */
uint64_t profiler_get_time_ns(void);

/**
 * @brief 格式化时间
 * @param ns 纳秒
 * @param buffer 输出缓冲区
 * @param size 缓冲区大小
 */
void profiler_format_time(uint64_t ns, char* buffer, size_t size);

#ifdef __cplusplus
}
#endif

#endif /* ZHC_PROFILER_H */
