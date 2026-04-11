#include "zhc_dynamic_cast.h"
#include "zhc_type_check.h"
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

// =============================================================================
// 初始化
// =============================================================================

/**
 * 初始化动态转换运行时
 *
 * 确保类型层次表已初始化。
 */
void zhc_dynamic_cast_init(void) {
    // 类型层次表由 zhc_typecheck_init() 初始化
    // 这里只做运行时检查
    if (g_zhc_type_hierarchy.entries == NULL) {
        zhc_typecheck_init();
    }
}

// =============================================================================
// 安全转换
// =============================================================================

void* zhc_safe_cast(void* obj, const char* obj_type, const char* target_type) {
    if (!obj) return NULL;
    if (!obj_type || !target_type) return NULL;
    if (zhc_is_type(obj_type, target_type)) {
        return obj;
    }
    return NULL;
}

// =============================================================================
// 动态转换（扩展版）
// =============================================================================

/**
 * 填充转换路径
 *
 * 从 source_type 向上追溯，记录到 target_type 的路径。
 */
static int fill_cast_path(const char* source_type, const char* target_type,
                          const char** path, size_t max_path) {
    int length = 0;

    if (strcmp(source_type, target_type) == 0) {
        if (max_path > 0) path[length++] = source_type;
        return length;
    }

    // 收集祖先链
    const char* chain[64];
    int chain_len = 0;
    chain[chain_len++] = source_type;

    const char* current = source_type;
    ZhCTypeHierarchyEntry* entry;
    int depth = 0;

    while ((entry = zhc_typecheck_lookup(current)) != NULL &&
           entry->parent_name != NULL && depth < 64) {
        chain[chain_len++] = entry->parent_name;
        if (strcmp(entry->parent_name, target_type) == 0) {
            break;
        }
        current = entry->parent_name;
        depth++;
    }

    // 检查是否找到目标类型
    bool found = false;
    int found_idx = -1;
    for (int i = 0; i < chain_len; i++) {
        if (strcmp(chain[i], target_type) == 0) {
            found = true;
            found_idx = i;
            break;
        }
    }

    if (found) {
        int copy_len = found_idx + 1;
        if (copy_len > (int)max_path) copy_len = (int)max_path;
        for (int i = 0; i < copy_len; i++) {
            path[i] = chain[i];
        }
        length = copy_len;
    }

    return length;
}

/**
 * 填充祖先列表
 */
static int fill_ancestors(const char* type_name,
                          const char** ancestors, size_t max_count) {
    return (int)zhc_get_ancestors(type_name, ancestors, max_count);
}

void* zhc_dynamic_cast_ex(void* obj, const char* obj_type,
                          const char* target_type,
                          __zhc_dynamic_cast_result_t* result) {
    if (!result) return NULL;

    // 初始化结果
    memset(result, 0, sizeof(__zhc_dynamic_cast_result_t));
    result->source_type = obj_type;
    result->target_type = target_type;

    // 空源检查
    if (!obj) {
        result->status = ZHC_CAST_NULL_SOURCE;
        result->error_message = "源对象为空";
        return NULL;
    }

    if (!obj_type || !target_type) {
        result->status = ZHC_CAST_INVALID_CAST;
        result->error_message = "类型名为空";
        return NULL;
    }

    // 相同类型
    if (strcmp(obj_type, target_type) == 0) {
        result->status = ZHC_CAST_SUCCESS;
        result->result = obj;
        result->cast_path[0] = obj_type;
        result->cast_path_length = 1;
        return obj;
    }

    // 检查类型兼容性
    if (zhc_is_type(obj_type, target_type)) {
        result->status = ZHC_CAST_SUCCESS;
        result->result = obj;

        // 填充转换路径
        result->cast_path_length = fill_cast_path(
            obj_type, target_type, result->cast_path, 16);

        // 填充祖先列表
        result->ancestor_count = fill_ancestors(
            obj_type, result->ancestors, 16);

        return obj;
    }

    // 转换失败
    result->status = ZHC_CAST_NOT_SUBTYPE;

    // 构建错误消息
    static char error_buf[256];
    snprintf(error_buf, sizeof(error_buf),
             "无法将 %s 转换为 %s（不是子类型）", obj_type, target_type);
    result->error_message = error_buf;

    // 填充祖先列表用于建议
    result->ancestor_count = fill_ancestors(
        obj_type, result->ancestors, 16);

    return NULL;
}

// =============================================================================
// 类型检查
// =============================================================================

bool zhc_is_type(void* obj, const char* obj_type, const char* target_type) {
    (void)obj;  // 对象指针在类型检查时不使用
    if (!obj_type || !target_type) return false;
    return zhc_is_type(obj_type, target_type);
}

bool zhc_is_type_ex(void* obj, const char* obj_type, const char* target_type,
                    const char** ancestors, size_t max_ancestors) {
    (void)obj;
    if (!obj_type || !target_type) return false;

    bool result = zhc_is_type(obj_type, target_type);
    if (result && ancestors && max_ancestors > 0) {
        zhc_get_ancestors(obj_type, ancestors, max_ancestors);
    }
    return result;
}

// =============================================================================
// 转换路径
// =============================================================================

int zhc_get_cast_path(const char* source_type, const char* target_type,
                      const char** path, size_t max_path) {
    if (!source_type || !target_type || !path || max_path == 0) return 0;
    return fill_cast_path(source_type, target_type, path, max_path);
}

// =============================================================================
// try_cast
// =============================================================================

__zhc_dynamic_cast_result_t zhc_try_cast(void* obj, const char* obj_type,
                                         const char* target_type) {
    __zhc_dynamic_cast_result_t result;
    zhc_dynamic_cast_ex(obj, obj_type, target_type, &result);
    return result;
}
