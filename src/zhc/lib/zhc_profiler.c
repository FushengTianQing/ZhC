/**
 * @file zhc_profiler.c
 * @brief ZhC 性能剖析器实现
 */

#include "zhc_profiler.h"
#include <assert.h>

/* 全局剖析器实例 */
ProfilerState g_profiler = {0};

/* ============================================================================
 * 时间工具函数
 * ============================================================================ */

uint64_t profiler_get_time_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

void profiler_format_time(uint64_t ns, char* buffer, size_t size) {
    if (ns < 1000ULL) {
        snprintf(buffer, size, "%llu ns", (unsigned long long)ns);
    } else if (ns < 1000000ULL) {
        snprintf(buffer, size, "%.2f us", ns / 1000.0);
    } else if (ns < 1000000000ULL) {
        snprintf(buffer, size, "%.2f ms", ns / 1000000.0);
    } else {
        snprintf(buffer, size, "%.3f s", ns / 1000000000.0);
    }
}

/* ============================================================================
 * 内部辅助函数
 * ============================================================================ */

/**
 * @brief 查找函数记录
 */
static FunctionProfile* find_function(const char* name) {
    FunctionProfile* profile = g_profiler.functions;
    while (profile) {
        if (strcmp(profile->name, name) == 0) {
            return profile;
        }
        profile = profile->next;
    }
    return NULL;
}

/**
 * @brief 创建新的函数记录
 */
static FunctionProfile* create_function(const char* name) {
    FunctionProfile* profile = (FunctionProfile*)malloc(sizeof(FunctionProfile));
    if (!profile) return NULL;
    
    profile->name = name;
    profile->call_count = 0;
    profile->total_time_ns = 0;
    profile->min_time_ns = UINT64_MAX;
    profile->max_time_ns = 0;
    profile->start_time_ns = 0;
    profile->call_depth = 0;
    profile->next = g_profiler.functions;
    g_profiler.functions = profile;
    
    g_profiler.stats.function_count++;
    return profile;
}

/**
 * @brief 查找调用关系
 */
static CallRelation* find_relation(const char* caller, const char* callee) {
    CallRelation* relation = g_profiler.relations;
    while (relation) {
        if (strcmp(relation->caller, caller) == 0 &&
            strcmp(relation->callee, callee) == 0) {
            return relation;
        }
        relation = relation->next;
    }
    return NULL;
}

/**
 * @brief 创建新的调用关系
 */
static CallRelation* create_relation(const char* caller, const char* callee) {
    CallRelation* relation = (CallRelation*)malloc(sizeof(CallRelation));
    if (!relation) return NULL;
    
    relation->caller = caller;
    relation->callee = callee;
    relation->call_count = 0;
    relation->total_time_ns = 0;
    relation->next = g_profiler.relations;
    g_profiler.relations = relation;
    
    g_profiler.stats.relation_count++;
    return relation;
}

/**
 * @brief 压入调用栈
 */
static void push_call_stack(const char* name, uint64_t start_time) {
    CallFrame* frame = (CallFrame*)malloc(sizeof(CallFrame));
    if (!frame) return;
    
    frame->function_name = name;
    frame->start_time_ns = start_time;
    frame->next = g_profiler.call_stack;
    g_profiler.call_stack = frame;
    g_profiler.call_depth++;
    
    if (g_profiler.call_depth > g_profiler.stats.max_depth) {
        g_profiler.stats.max_depth = g_profiler.call_depth;
    }
}

/**
 * @brief 弹出调用栈
 */
static CallFrame* pop_call_stack(void) {
    if (!g_profiler.call_stack) return NULL;
    
    CallFrame* frame = g_profiler.call_stack;
    g_profiler.call_stack = frame->next;
    g_profiler.call_depth--;
    return frame;
}

/* ============================================================================
 * 剖析器控制 API
 * ============================================================================ */

int profiler_init(int max_functions) {
    if (g_profiler.initialized) {
        profiler_shutdown();
    }
    
    memset(&g_profiler, 0, sizeof(ProfilerState));
    
    g_profiler.config.max_functions = max_functions > 0 ? max_functions : 1000;
    g_profiler.config.max_relations = max_functions * 2;
    g_profiler.config.enabled = 0;
    g_profiler.config.track_call_graph = 1;
    g_profiler.config.track_memory = 0;
    g_profiler.config.output = stdout;
    
    g_profiler.initialized = 1;
    g_profiler.enabled = 0;
    
    return 0;
}

void profiler_shutdown(void) {
    if (!g_profiler.initialized) return;
    
    /* 释放函数记录 */
    FunctionProfile* func = g_profiler.functions;
    while (func) {
        FunctionProfile* next = func->next;
        free(func);
        func = next;
    }
    
    /* 释放调用关系 */
    CallRelation* rel = g_profiler.relations;
    while (rel) {
        CallRelation* next = rel->next;
        free(rel);
        rel = next;
    }
    
    /* 释放调用栈 */
    CallFrame* frame = g_profiler.call_stack;
    while (frame) {
        CallFrame* next = frame->next;
        free(frame);
        frame = next;
    }
    
    memset(&g_profiler, 0, sizeof(ProfilerState));
}

void profiler_enable(void) {
    g_profiler.enabled = 1;
}

void profiler_disable(void) {
    g_profiler.enabled = 0;
}

int profiler_is_enabled(void) {
    return g_profiler.enabled;
}

void profiler_reset(void) {
    /* 保留配置，只重置数据 */
    profiler_shutdown();
    profiler_init(g_profiler.config.max_functions);
}

/* ============================================================================
 * 函数剖析 API
 * ============================================================================ */

void profiler_enter(const char* func_name) {
    if (!g_profiler.enabled || !func_name) return;
    
    uint64_t now = profiler_get_time_ns();
    
    /* 查找或创建函数记录 */
    FunctionProfile* profile = find_function(func_name);
    if (!profile) {
        profile = create_function(func_name);
        if (!profile) return;
    }
    
    profile->call_count++;
    profile->start_time_ns = now;
    profile->call_depth = g_profiler.call_depth;
    
    g_profiler.stats.total_calls++;
    
    /* 压入调用栈 */
    push_call_stack(func_name, now);
    
    /* 记录调用关系 */
    if (g_profiler.config.track_call_graph && g_profiler.call_stack) {
        CallFrame* caller_frame = g_profiler.call_stack->next;
        if (caller_frame) {
            profiler_record_call(caller_frame->function_name, func_name);
        }
    }
}

void profiler_exit(const char* func_name) {
    if (!g_profiler.enabled || !func_name) return;
    
    uint64_t now = profiler_get_time_ns();
    
    /* 弹出调用栈 */
    CallFrame* frame = pop_call_stack();
    if (!frame) return;
    
    /* 计算执行时间 */
    uint64_t elapsed = now - frame->start_time_ns;
    free(frame);
    
    /* 更新函数统计 */
    FunctionProfile* profile = find_function(func_name);
    if (profile) {
        profile->total_time_ns += elapsed;
        if (elapsed < profile->min_time_ns) {
            profile->min_time_ns = elapsed;
        }
        if (elapsed > profile->max_time_ns) {
            profile->max_time_ns = elapsed;
        }
    }
    
    /* 更新调用关系时间 */
    if (g_profiler.config.track_call_graph && g_profiler.call_stack) {
        CallFrame* caller_frame = g_profiler.call_stack;
        if (caller_frame) {
            CallRelation* rel = find_relation(caller_frame->function_name, func_name);
            if (rel) {
                rel->total_time_ns += elapsed;
            }
        }
    }
    
    g_profiler.stats.total_time_ns += elapsed;
}

FunctionProfile* profiler_get_function(const char* func_name) {
    return find_function(func_name);
}

FunctionProfile** profiler_get_all_functions(int* count) {
    if (!count) return NULL;
    
    /* 计算数量 */
    int n = 0;
    FunctionProfile* func = g_profiler.functions;
    while (func) {
        n++;
        func = func->next;
    }
    
    *count = n;
    if (n == 0) return NULL;
    
    /* 分配数组 */
    FunctionProfile** array = (FunctionProfile**)malloc(n * sizeof(FunctionProfile*));
    if (!array) return NULL;
    
    /* 填充数组 */
    int i = 0;
    func = g_profiler.functions;
    while (func && i < n) {
        array[i++] = func;
        func = func->next;
    }
    
    return array;
}

/* ============================================================================
 * 调用关系 API
 * ============================================================================ */

void profiler_record_call(const char* caller, const char* callee) {
    if (!caller || !callee) return;
    
    CallRelation* relation = find_relation(caller, callee);
    if (!relation) {
        relation = create_relation(caller, callee);
        if (!relation) return;
    }
    
    relation->call_count++;
}

CallRelation** profiler_get_call_relations(int* count) {
    if (!count) return NULL;
    
    /* 计算数量 */
    int n = 0;
    CallRelation* rel = g_profiler.relations;
    while (rel) {
        n++;
        rel = rel->next;
    }
    
    *count = n;
    if (n == 0) return NULL;
    
    /* 分配数组 */
    CallRelation** array = (CallRelation**)malloc(n * sizeof(CallRelation*));
    if (!array) return NULL;
    
    /* 填充数组 */
    int i = 0;
    rel = g_profiler.relations;
    while (rel && i < n) {
        array[i++] = rel;
        rel = rel->next;
    }
    
    return array;
}

/* ============================================================================
 * 报告生成 API
 * ============================================================================ */

void profiler_report(void) {
    FILE* output = g_profiler.config.output ? g_profiler.config.output : stdout;
    
    fprintf(output, "\n");
    fprintf(output, "╔══════════════════════════════════════════════════════════════════════════════════╗\n");
    fprintf(output, "║                              性能剖析报告                                        ║\n");
    fprintf(output, "╚══════════════════════════════════════════════════════════════════════════════════╝\n");
    fprintf(output, "\n");
    
    /* 统计信息 */
    fprintf(output, "统计信息:\n");
    fprintf(output, "  总调用次数: %llu\n", (unsigned long long)g_profiler.stats.total_calls);
    
    char time_buf[64];
    profiler_format_time(g_profiler.stats.total_time_ns, time_buf, sizeof(time_buf));
    fprintf(output, "  总执行时间: %s\n", time_buf);
    fprintf(output, "  记录函数数: %llu\n", (unsigned long long)g_profiler.stats.function_count);
    fprintf(output, "  最大调用深度: %d\n", g_profiler.stats.max_depth);
    fprintf(output, "\n");
    
    /* 函数统计表 */
    fprintf(output, "%-35s %10s %15s %15s %15s %10s\n",
            "函数名", "调用次数", "总时间", "平均时间", "最大时间", "占比");
    fprintf(output, "────────────────────────────────────────────────────────────────────────────────────────\n");
    
    /* 收集并排序函数记录 */
    int count = 0;
    FunctionProfile** funcs = profiler_get_all_functions(&count);
    if (funcs && count > 0) {
        /* 按总时间排序 */
        for (int i = 0; i < count - 1; i++) {
            for (int j = i + 1; j < count; j++) {
                if (funcs[j]->total_time_ns > funcs[i]->total_time_ns) {
                    FunctionProfile* tmp = funcs[i];
                    funcs[i] = funcs[j];
                    funcs[j] = tmp;
                }
            }
        }
        
        /* 输出 */
        for (int i = 0; i < count; i++) {
            FunctionProfile* p = funcs[i];
            uint64_t avg = p->call_count > 0 ? p->total_time_ns / p->call_count : 0;
            double percentage = g_profiler.stats.total_time_ns > 0 ?
                (double)p->total_time_ns / g_profiler.stats.total_time_ns * 100.0 : 0.0;
            
            char total_buf[32], avg_buf[32], max_buf[32];
            profiler_format_time(p->total_time_ns, total_buf, sizeof(total_buf));
            profiler_format_time(avg, avg_buf, sizeof(avg_buf));
            profiler_format_time(p->max_time_ns, max_buf, sizeof(max_buf));
            
            fprintf(output, "%-35s %10llu %15s %15s %15s %9.2f%%\n",
                    p->name,
                    (unsigned long long)p->call_count,
                    total_buf,
                    avg_buf,
                    max_buf,
                    percentage);
        }
        
        free(funcs);
    }
    
    fprintf(output, "\n");
}

void profiler_report_json(FILE* output) {
    if (!output) output = stdout;
    
    fprintf(output, "{\n");
    fprintf(output, "  \"stats\": {\n");
    fprintf(output, "    \"total_calls\": %llu,\n", (unsigned long long)g_profiler.stats.total_calls);
    fprintf(output, "    \"total_time_ns\": %llu,\n", (unsigned long long)g_profiler.stats.total_time_ns);
    fprintf(output, "    \"function_count\": %llu,\n", (unsigned long long)g_profiler.stats.function_count);
    fprintf(output, "    \"max_depth\": %d\n", g_profiler.stats.max_depth);
    fprintf(output, "  },\n");
    
    fprintf(output, "  \"functions\": [\n");
    
    int count = 0;
    FunctionProfile** funcs = profiler_get_all_functions(&count);
    if (funcs && count > 0) {
        for (int i = 0; i < count; i++) {
            FunctionProfile* p = funcs[i];
            uint64_t avg = p->call_count > 0 ? p->total_time_ns / p->call_count : 0;
            
            fprintf(output, "    {\n");
            fprintf(output, "      \"name\": \"%s\",\n", p->name);
            fprintf(output, "      \"call_count\": %llu,\n", (unsigned long long)p->call_count);
            fprintf(output, "      \"total_time_ns\": %llu,\n", (unsigned long long)p->total_time_ns);
            fprintf(output, "      \"avg_time_ns\": %llu,\n", (unsigned long long)avg);
            fprintf(output, "      \"min_time_ns\": %llu,\n", (unsigned long long)p->min_time_ns);
            fprintf(output, "      \"max_time_ns\": %llu\n", (unsigned long long)p->max_time_ns);
            fprintf(output, "    }%s\n", i < count - 1 ? "," : "");
        }
        free(funcs);
    }
    
    fprintf(output, "  ]\n");
    fprintf(output, "}\n");
}

void profiler_export_call_graph_dot(FILE* output) {
    if (!output) output = stdout;
    
    fprintf(output, "digraph CallGraph {\n");
    fprintf(output, "  rankdir=LR;\n");
    fprintf(output, "  node [shape=box, style=filled];\n");
    fprintf(output, "\n");
    
    int count = 0;
    CallRelation** rels = profiler_get_call_relations(&count);
    if (rels && count > 0) {
        for (int i = 0; i < count; i++) {
            CallRelation* r = rels[i];
            fprintf(output, "  \"%s\" -> \"%s\" [label=\"%llu calls\"];\n",
                    r->caller, r->callee, (unsigned long long)r->call_count);
        }
        free(rels);
    }
    
    fprintf(output, "}\n");
}

ProfilerStats profiler_get_stats(void) {
    return g_profiler.stats;
}

/* ============================================================================
 * 测试代码
 * ============================================================================ */

#ifdef ZHC_PROFILER_TEST

void test_function_a(void) {
    PROFILE_FUNCTION();
    for (volatile int i = 0; i < 1000000; i++);
}

void test_function_b(void) {
    PROFILE_FUNCTION();
    for (volatile int i = 0; i < 500000; i++);
    test_function_a();
}

int main(void) {
    profiler_init(100);
    profiler_enable();
    
    for (int i = 0; i < 10; i++) {
        test_function_b();
    }
    
    profiler_report();
    profiler_shutdown();
    
    return 0;
}

#endif /* ZHC_PROFILER_TEST */
