/**
 * @file zhc_memcheck.c
 * @brief ZhC 内存使用分析器实现
 */

#include "zhc_memcheck.h"
#include <time.h>
#include <assert.h>

/* 全局实例 */
MemcheckState g_memcheck = {0};

/* ============================================================================
 * 时间戳获取
 * ============================================================================ */

uint64_t memcheck_get_time_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

void memcheck_format_bytes(uint64_t bytes, char* buffer, size_t size) {
    if (bytes < 1024ULL) {
        snprintf(buffer, size, "%llu B", (unsigned long long)bytes);
    } else if (bytes < 1024ULL * 1024ULL) {
        snprintf(buffer, size, "%.2f KB", bytes / 1024.0);
    } else if (bytes < 1024ULL * 1024ULL * 1024ULL) {
        snprintf(buffer, size, "%.2f MB", bytes / (1024.0 * 1024.0));
    } else {
        snprintf(buffer, size, "%.2f GB", bytes / (1024.0 * 1024.0 * 1024.0));
    }
}

/* ============================================================================
 * 内部辅助函数
 * ============================================================================ */

/**
 * @brief 创建内存块记录
 */
static MemBlock* create_block(void* ptr, size_t size, const char* file,
                             int line, const char* func) {
    MemBlock* block = (MemBlock*)malloc(sizeof(MemBlock));
    if (!block) return NULL;
    
    block->ptr = ptr;
    block->size = size;
    block->file = file;
    block->line = line;
    block->func = func;
    block->alloc_time = memcheck_get_time_ns();
    block->alloc_id = ++g_memcheck.current_id;
    block->next = g_memcheck.blocks;
    g_memcheck.blocks = block;
    
    return block;
}

/**
 * @brief 查找内存块
 */
static MemBlock* find_block(void* ptr) {
    MemBlock* block = g_memcheck.blocks;
    while (block) {
        if (block->ptr == ptr) {
            return block;
        }
        block = block->next;
    }
    return NULL;
}

/**
 * @brief 移除内存块
 */
static MemBlock* remove_block(void* ptr) {
    MemBlock** pprev = &g_memcheck.blocks;
    MemBlock* block = g_memcheck.blocks;
    
    while (block) {
        if (block->ptr == ptr) {
            *pprev = block->next;
            return block;
        }
        pprev = &block->next;
        block = block->next;
    }
    return NULL;
}

/**
 * @brief 记录操作
 */
static void record_operation(MemOpType type, void* ptr, size_t size,
                            const char* file, int line, const char* func) {
    /* 检查历史记录限制 */
    if (g_memcheck.max_history > 0) {
        int count = 0;
        MemOpRecord* r = g_memcheck.operations;
        while (r) {
            count++;
            r = r->next;
        }
        if (count >= g_memcheck.max_history) {
            /* 移除最旧的记录 */
            MemOpRecord* oldest = g_memcheck.operations;
            g_memcheck.operations = oldest->next;
            free(oldest);
        }
    }
    
    MemOpRecord* record = (MemOpRecord*)malloc(sizeof(MemOpRecord));
    if (!record) return;
    
    record->type = type;
    record->ptr = ptr;
    record->size = size;
    record->file = file;
    record->line = line;
    record->func = func;
    record->alloc_id = 0;
    record->timestamp = memcheck_get_time_ns();
    record->next = g_memcheck.operations;
    g_memcheck.operations = record;
}

/**
 * @brief 查找或创建分配源统计
 */
static AllocSite* find_or_create_alloc_site(const char* file, int line, const char* func) {
    AllocSite* site = g_memcheck.alloc_sites;
    while (site) {
        if (site->file == file && site->line == line && site->func == func) {
            return site;
        }
        site = site->next;
    }
    
    /* 创建新的分配源 */
    site = (AllocSite*)malloc(sizeof(AllocSite));
    if (!site) return NULL;
    
    site->file = file;
    site->line = line;
    site->func = func;
    site->alloc_count = 0;
    site->total_bytes = 0;
    site->current_bytes = 0;
    site->next = g_memcheck.alloc_sites;
    g_memcheck.alloc_sites = site;
    
    return site;
}

/* ============================================================================
 * 初始化和控制 API
 * ============================================================================ */

void memcheck_init(int max_history) {
    if (g_memcheck.initialized) {
        memcheck_shutdown();
    }
    
    memset(&g_memcheck, 0, sizeof(MemcheckState));
    g_memcheck.max_history = max_history;
    g_memcheck.initialized = 1;
    g_memcheck.enabled = 1;
}

void memcheck_shutdown(void) {
    if (!g_memcheck.initialized) return;
    
    /* 释放内存块链表 */
    MemBlock* block = g_memcheck.blocks;
    while (block) {
        MemBlock* next = block->next;
        free(block);
        block = next;
    }
    
    /* 释放操作记录链表 */
    MemOpRecord* record = g_memcheck.operations;
    while (record) {
        MemOpRecord* next = record->next;
        free(record);
        record = next;
    }
    
    /* 释放分配源统计 */
    AllocSite* site = g_memcheck.alloc_sites;
    while (site) {
        AllocSite* next = site->next;
        free(site);
        site = next;
    }
    
    memset(&g_memcheck, 0, sizeof(MemcheckState));
}

void memcheck_enable(void) {
    g_memcheck.enabled = 1;
}

void memcheck_disable(void) {
    g_memcheck.enabled = 0;
}

int memcheck_is_enabled(void) {
    return g_memcheck.enabled;
}

void memcheck_reset(void) {
    memcheck_shutdown();
    memcheck_init(g_memcheck.max_history);
}

/* ============================================================================
 * 内存追踪 API
 * ============================================================================ */

void* memcheck_alloc(size_t size, const char* file, int line, const char* func) {
    if (size == 0) return NULL;
    
    /* 分配实际内存 */
    void* ptr = malloc(size);
    if (!ptr) return NULL;
    
    /* 记录分配 */
    MemBlock* block = create_block(ptr, size, file, line, func);
    if (!block) {
        free(ptr);
        return NULL;
    }
    
    /* 更新统计 */
    g_memcheck.stats.total_alloc_bytes += size;
    g_memcheck.stats.current_used_bytes += size;
    g_memcheck.stats.alloc_count++;
    
    if (g_memcheck.stats.current_used_bytes > g_memcheck.stats.peak_used_bytes) {
        g_memcheck.stats.peak_used_bytes = g_memcheck.stats.current_used_bytes;
    }
    
    /* 更新分配源统计 */
    AllocSite* site = find_or_create_alloc_site(file, line, func);
    if (site) {
        site->alloc_count++;
        site->total_bytes += size;
        site->current_bytes += size;
    }
    
    /* 记录操作 */
    if (g_memcheck.enabled) {
        record_operation(MEM_OP_ALLOC, ptr, size, file, line, func);
    }
    
    return ptr;
}

void memcheck_free(void* ptr, const char* file, int line) {
    if (!ptr) return;
    
    /* 查找内存块 */
    MemBlock* block = find_block(ptr);
    if (!block) {
        g_memcheck.stats.invalid_free_count++;
        fprintf(stderr, "[MEMCHECK] 错误: 尝试释放未分配的内存 %p (%s:%d)\n",
                ptr, file, line);
        return;
    }
    
    /* 更新统计 */
    g_memcheck.stats.total_free_bytes += block->size;
    g_memcheck.stats.current_used_bytes -= block->size;
    g_memcheck.stats.free_count++;
    
    /* 更新分配源统计 */
    AllocSite* site = find_or_create_alloc_site(block->file, block->line, block->func);
    if (site && site->current_bytes >= block->size) {
        site->current_bytes -= block->size;
    }
    
    /* 移除内存块 */
    remove_block(ptr);
    
    /* 释放内存 */
    free(ptr);
    
    /* 记录操作 */
    if (g_memcheck.enabled) {
        record_operation(MEM_OP_FREE, ptr, 0, file, line, "释放");
    }
}

void* memcheck_realloc(void* ptr, size_t new_size, const char* file, int line) {
    if (!ptr) {
        return memcheck_alloc(new_size, file, line, "重新申请");
    }
    
    if (new_size == 0) {
        memcheck_free(ptr, file, line);
        return NULL;
    }
    
    /* 查找原内存块 */
    MemBlock* old_block = find_block(ptr);
    if (!old_block) {
        g_memcheck.stats.invalid_free_count++;
        fprintf(stderr, "[MEMCHECK] 错误: 尝试重新分配未知的内存 %p (%s:%d)\n",
                ptr, file, line);
        return NULL;
    }
    
    /* 重新分配 */
    void* new_ptr = realloc(ptr, new_size);
    if (!new_ptr) {
        return NULL;
    }
    
    /* 计算大小变化 */
    int64_t size_diff = (int64_t)new_size - (int64_t)old_block->size;
    
    /* 更新内存块 */
    if (new_ptr != ptr) {
        /* 指针改变，需要更新链表 */
        remove_block(ptr);
        create_block(new_ptr, new_size, old_block->file, old_block->line, old_block->func);
    } else {
        /* 指针不变，只需更新大小 */
        old_block->size = new_size;
    }
    
    /* 更新统计 */
    g_memcheck.stats.total_alloc_bytes += (size_diff > 0) ? size_diff : 0;
    g_memcheck.stats.total_free_bytes += (size_diff < 0) ? -size_diff : 0;
    g_memcheck.stats.current_used_bytes += size_diff;
    
    if (g_memcheck.stats.current_used_bytes > g_memcheck.stats.peak_used_bytes) {
        g_memcheck.stats.peak_used_bytes = g_memcheck.stats.current_used_bytes;
    }
    
    /* 更新分配源统计 */
    AllocSite* site = find_or_create_alloc_site(old_block->file, old_block->line, old_block->func);
    if (site) {
        site->total_bytes += (size_diff > 0) ? size_diff : 0;
        site->current_bytes += size_diff;
    }
    
    /* 记录操作 */
    if (g_memcheck.enabled) {
        record_operation(MEM_OP_REALLOC, new_ptr, new_size, file, line, "重新申请");
    }
    
    return new_ptr;
}

/* ============================================================================
 * 查询 API
 * ============================================================================ */

MemBlock* memcheck_get_block(void* ptr) {
    return find_block(ptr);
}

int memcheck_is_valid_ptr(void* ptr) {
    return find_block(ptr) != NULL;
}

uint64_t memcheck_current_used(void) {
    return g_memcheck.stats.current_used_bytes;
}

uint64_t memcheck_peak_used(void) {
    return g_memcheck.stats.peak_used_bytes;
}

MemStats memcheck_get_stats(void) {
    /* 更新泄漏统计 */
    g_memcheck.stats.leak_count = 0;
    g_memcheck.stats.leak_bytes = 0;
    
    MemBlock* block = g_memcheck.blocks;
    while (block) {
        g_memcheck.stats.leak_count++;
        g_memcheck.stats.leak_bytes += block->size;
        block = block->next;
    }
    
    return g_memcheck.stats;
}

int memcheck_has_leaks(void) {
    return g_memcheck.blocks != NULL;
}

uint64_t memcheck_get_leak_count(void) {
    uint64_t count = 0;
    MemBlock* block = g_memcheck.blocks;
    while (block) {
        count++;
        block = block->next;
    }
    return count;
}

uint64_t memcheck_get_leak_bytes(void) {
    uint64_t bytes = 0;
    MemBlock* block = g_memcheck.blocks;
    while (block) {
        bytes += block->size;
        block = block->next;
    }
    return bytes;
}

/* ============================================================================
 * 报告生成 API
 * ============================================================================ */

void memcheck_report(void) {
    FILE* output = stdout;
    
    fprintf(output, "\n");
    fprintf(output, "╔══════════════════════════════════════════════════════════════════════════════════╗\n");
    fprintf(output, "║                              内存使用报告                                        ║\n");
    fprintf(output, "╚══════════════════════════════════════════════════════════════════════════════════╝\n");
    fprintf(output, "\n");
    
    /* 统计信息 */
    char buf[64];
    
    fprintf(output, "统计信息:\n");
    fprintf(output, "  总分配:       ");
    memcheck_format_bytes(g_memcheck.stats.total_alloc_bytes, buf, sizeof(buf));
    fprintf(output, "%s\n", buf);
    
    fprintf(output, "  总释放:       ");
    memcheck_format_bytes(g_memcheck.stats.total_free_bytes, buf, sizeof(buf));
    fprintf(output, "%s\n", buf);
    
    fprintf(output, "  当前使用:     ");
    memcheck_format_bytes(g_memcheck.stats.current_used_bytes, buf, sizeof(buf));
    fprintf(output, "%s\n", buf);
    
    fprintf(output, "  峰值使用:     ");
    memcheck_format_bytes(g_memcheck.stats.peak_used_bytes, buf, sizeof(buf));
    fprintf(output, "%s\n", buf);
    
    fprintf(output, "\n");
    fprintf(output, "  分配次数:     %llu\n", (unsigned long long)g_memcheck.stats.alloc_count);
    fprintf(output, "  释放次数:     %llu\n", (unsigned long long)g_memcheck.stats.free_count);
    fprintf(output, "  无效释放:     %llu\n", (unsigned long long)g_memcheck.stats.invalid_free_count);
    fprintf(output, "\n");
    
    /* 泄漏信息 */
    if (g_memcheck.blocks) {
        fprintf(output, "═══ 内存泄漏 ═══\n\n");
        
        MemBlock* block = g_memcheck.blocks;
        while (block) {
            fprintf(output, "  泄漏 #%llu:\n", (unsigned long long)block->alloc_id);
            fprintf(output, "    地址:   %p\n", block->ptr);
            memcheck_format_bytes(block->size, buf, sizeof(buf));
            fprintf(output, "    大小:   %s\n", buf);
            fprintf(output, "    位置:   %s:%d (%s)\n",
                    block->file, block->line, block->func);
            fprintf(output, "\n");
            block = block->next;
        }
        
        fprintf(output, "总计泄漏: %llu 处, ", (unsigned long long)memcheck_get_leak_count());
        memcheck_format_bytes(memcheck_get_leak_bytes(), buf, sizeof(buf));
        fprintf(output, "%s\n", buf);
    } else {
        fprintf(output, "✓ 未检测到内存泄漏\n");
    }
    
    fprintf(output, "\n");
}

void memcheck_report_json(FILE* output) {
    if (!output) output = stdout;
    
    MemStats stats = memcheck_get_stats();
    
    fprintf(output, "{\n");
    fprintf(output, "  \"stats\": {\n");
    fprintf(output, "    \"total_alloc_bytes\": %llu,\n", (unsigned long long)stats.total_alloc_bytes);
    fprintf(output, "    \"total_free_bytes\": %llu,\n", (unsigned long long)stats.total_free_bytes);
    fprintf(output, "    \"current_used_bytes\": %llu,\n", (unsigned long long)stats.current_used_bytes);
    fprintf(output, "    \"peak_used_bytes\": %llu,\n", (unsigned long long)stats.peak_used_bytes);
    fprintf(output, "    \"alloc_count\": %llu,\n", (unsigned long long)stats.alloc_count);
    fprintf(output, "    \"free_count\": %llu,\n", (unsigned long long)stats.free_count);
    fprintf(output, "    \"leak_count\": %llu,\n", (unsigned long long)stats.leak_count);
    fprintf(output, "    \"leak_bytes\": %llu,\n", (unsigned long long)stats.leak_bytes);
    fprintf(output, "    \"invalid_free_count\": %llu\n", (unsigned long long)stats.invalid_free_count);
    fprintf(output, "  },\n");
    
    fprintf(output, "  \"leaks\": [\n");
    
    MemBlock* block = g_memcheck.blocks;
    int first = 1;
    while (block) {
        if (!first) fprintf(output, ",\n");
        first = 0;
        
        fprintf(output, "    {\n");
        fprintf(output, "      \"id\": %llu,\n", (unsigned long long)block->alloc_id);
        fprintf(output, "      \"ptr\": \"%p\",\n", block->ptr);
        fprintf(output, "      \"size\": %zu,\n", block->size);
        fprintf(output, "      \"file\": \"%s\",\n", block->file);
        fprintf(output, "      \"line\": %d,\n", block->line);
        fprintf(output, "      \"func\": \"%s\"\n", block->func);
        fprintf(output, "    }");
        block = block->next;
    }
    
    fprintf(output, "\n  ]\n");
    fprintf(output, "}\n");
}

void memcheck_report_leaks(FILE* output) {
    if (!output) output = stdout;
    
    fprintf(output, "Memory Leaks Report\n");
    fprintf(output, "===================\n\n");
    
    if (!g_memcheck.blocks) {
        fprintf(output, "No memory leaks detected.\n");
        return;
    }
    
    MemBlock* block = g_memcheck.blocks;
    int i = 1;
    while (block) {
        fprintf(output, "Leak #%d:\n", i++);
        fprintf(output, "  Address: %p\n", block->ptr);
        fprintf(output, "  Size: %zu bytes\n", block->size);
        fprintf(output, "  Location: %s:%d in %s()\n",
                block->file, block->line, block->func);
        fprintf(output, "\n");
        block = block->next;
    }
    
    fprintf(output, "Total: %llu leaks, %llu bytes\n",
            (unsigned long long)memcheck_get_leak_count(),
            (unsigned long long)memcheck_get_leak_bytes());
}

void memcheck_report_alloc_sites(FILE* output) {
    if (!output) output = stdout;
    
    fprintf(output, "Allocation Sites Report\n");
    fprintf(output, "=======================\n\n");
    
    if (!g_memcheck.alloc_sites) {
        fprintf(output, "No allocation sites recorded.\n");
        return;
    }
    
    /* 收集并排序 */
    int count = 0;
    AllocSite** sites = NULL;
    AllocSite* site = g_memcheck.alloc_sites;
    while (site) {
        count++;
        site = site->next;
    }
    
    if (count > 0) {
        sites = (AllocSite**)malloc(count * sizeof(AllocSite*));
        int i = 0;
        site = g_memcheck.alloc_sites;
        while (site && i < count) {
            sites[i++] = site;
            site = site->next;
        }
        
        /* 按当前字节数排序 */
        for (int j = 0; j < count - 1; j++) {
            for (int k = j + 1; k < count; k++) {
                if (sites[k]->current_bytes > sites[j]->current_bytes) {
                    AllocSite* tmp = sites[j];
                    sites[j] = sites[k];
                    sites[k] = tmp;
                }
            }
        }
        
        /* 输出 */
        fprintf(output, "%-50s %10s %12s %12s\n",
                "Location", "Count", "Total", "Current");
        fprintf(output, "---------------------------------------------------"
                        "---------------------------------------------------\n");
        
        char buf[64];
        for (int j = 0; j < count; j++) {
            site = sites[j];
            fprintf(output, "%s:%d %-30s ", site->file, site->line, site->func);
            fprintf(output, "%10llu ", (unsigned long long)site->alloc_count);
            memcheck_format_bytes(site->total_bytes, buf, sizeof(buf));
            fprintf(output, "%12s ", buf);
            memcheck_format_bytes(site->current_bytes, buf, sizeof(buf));
            fprintf(output, "%12s\n", buf);
        }
        
        free(sites);
    }
    
    fprintf(output, "\n");
}

/* ============================================================================
 * 测试代码
 * ============================================================================ */

#ifdef ZHC_MEMCHECK_TEST

int main(void) {
    memcheck_init(1000);
    
    printf("=== 内存检查测试 ===\n\n");
    
    /* 测试基本分配 */
    void* p1 = 申请(100);
    void* p2 = 申请(200);
    void* p3 = 申请(300);
    
    /* 泄漏 p3 */
    释放(p1);
    释放(p2);
    
    /* 测试 realloc */
    void* p4 = 申请(50);
    p4 = 重新申请(p4, 100);
    释放(p4);
    
    /* 测试 double free */
    void* p5 = 申请(64);
    释放(p5);
    /* 释放(p5);  // 取消注释以测试无效释放 */
    
    /* 输出报告 */
    memcheck_report();
    
    /* 测试分配源 */
    memcheck_report_alloc_sites(stdout);
    
    memcheck_shutdown();
    return 0;
}

#endif /* ZHC_MEMCHECK_TEST */
