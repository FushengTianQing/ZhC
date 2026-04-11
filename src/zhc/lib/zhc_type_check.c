#include "zhc_type_check.h"
#include <string.h>
#include <stdlib.h>

// =============================================================================
// 全局类型层次表
// =============================================================================

ZhCTypeHierarchyTable g_zhc_type_hierarchy = {NULL, 0, {NULL}, 0};

// =============================================================================
// 初始化
// =============================================================================

void zhc_typecheck_init(void) {
    g_zhc_type_hierarchy.entries = NULL;
    g_zhc_type_hierarchy.count = 0;
    g_zhc_type_hierarchy.primitive_count = 0;

    // 注册基本类型
    static const char* no_interfaces[] = {NULL};
    (void)no_interfaces;

    zhc_typecheck_register("int", NULL, NULL, 0, false, false, false, true);
    zhc_typecheck_register("char", NULL, NULL, 0, false, false, false, true);
    zhc_typecheck_register("float", NULL, NULL, 0, false, false, false, true);
    zhc_typecheck_register("double", NULL, NULL, 0, false, false, false, true);
    zhc_typecheck_register("_Bool", NULL, NULL, 0, false, false, false, true);
    zhc_typecheck_register("long", NULL, NULL, 0, false, false, false, true);
    zhc_typecheck_register("short", NULL, NULL, 0, false, false, false, true);
    zhc_typecheck_register("void", NULL, NULL, 0, false, false, false, true);

    // ZhC 中文类型名
    zhc_typecheck_register("整数型", NULL, NULL, 0, false, false, false, true);
    zhc_typecheck_register("字符型", NULL, NULL, 0, false, false, false, true);
    zhc_typecheck_register("浮点型", NULL, NULL, 0, false, false, false, true);
    zhc_typecheck_register("双精度浮点型", NULL, NULL, 0, false, false, false, true);
    zhc_typecheck_register("逻辑型", NULL, NULL, 0, false, false, false, true);
    zhc_typecheck_register("长整数型", NULL, NULL, 0, false, false, false, true);
    zhc_typecheck_register("短整数型", NULL, NULL, 0, false, false, false, true);
    zhc_typecheck_register("空型", NULL, NULL, 0, false, false, false, true);
    zhc_typecheck_register("字符串型", NULL, NULL, 0, false, false, false, true);
}

void zhc_typecheck_register(const char* type_name,
                           const char* parent_name,
                           const char** interfaces,
                           size_t interface_count,
                           bool is_class,
                           bool is_struct,
                           bool is_interface,
                           bool is_primitive) {
    ZhCTypeHierarchyEntry* entry = (ZhCTypeHierarchyEntry*)malloc(sizeof(ZhCTypeHierarchyEntry));
    if (!entry) return;

    entry->type_name = type_name;
    entry->parent_name = parent_name;
    entry->interfaces = (const char**)interfaces;
    entry->interface_count = interface_count;
    entry->is_class = is_class;
    entry->is_struct = is_struct;
    entry->is_interface = is_interface;
    entry->is_primitive = is_primitive;
    entry->next = NULL;

    // 追加到链表末尾
    if (g_zhc_type_hierarchy.entries == NULL) {
        g_zhc_type_hierarchy.entries = entry;
    } else {
        ZhCTypeHierarchyEntry* current = g_zhc_type_hierarchy.entries;
        while (current->next != NULL) {
            current = current->next;
        }
        current->next = entry;
    }
    g_zhc_type_hierarchy.count++;

    // 记录基本类型
    if (is_primitive && g_zhc_type_hierarchy.primitive_count < 16) {
        g_zhc_type_hierarchy.primitives[g_zhc_type_hierarchy.primitive_count++] = entry;
    }
}

// =============================================================================
// 内部查找
// =============================================================================

ZhCTypeHierarchyEntry* zhc_typecheck_lookup(const char* type_name) {
    if (!type_name) return NULL;

    ZhCTypeHierarchyEntry* current = g_zhc_type_hierarchy.entries;
    while (current != NULL) {
        if (strcmp(current->type_name, type_name) == 0) {
            return current;
        }
        current = current->next;
    }
    return NULL;
}

// =============================================================================
// 类型查询
// =============================================================================

bool zhc_is_type(const char* obj_type, const char* target_type) {
    if (!obj_type || !target_type) return false;

    // 相同类型
    if (strcmp(obj_type, target_type) == 0) return true;

    // 检查继承链
    ZhCTypeHierarchyEntry* entry = zhc_typecheck_lookup(obj_type);
    if (!entry) return false;

    // 向上追溯父类
    const char* current = entry->parent_name;
    int depth = 0;
    while (current != NULL && depth < 64) {  // 防止循环
        if (strcmp(current, target_type) == 0) return true;

        ZhCTypeHierarchyEntry* parent_entry = zhc_typecheck_lookup(current);
        if (!parent_entry) break;
        current = parent_entry->parent_name;
        depth++;
    }

    // 检查接口
    if (zhc_implements_interface(obj_type, target_type)) return true;

    return false;
}

bool zhc_is_subtype(const char* subtype, const char* supertype) {
    return zhc_is_type(subtype, supertype);
}

bool zhc_implements_interface(const char* type_name, const char* interface_name) {
    if (!type_name || !interface_name) return false;

    ZhCTypeHierarchyEntry* entry = zhc_typecheck_lookup(type_name);
    if (!entry) return false;

    // 直接接口
    for (size_t i = 0; i < entry->interface_count; i++) {
        if (strcmp(entry->interfaces[i], interface_name) == 0) {
            return true;
        }
        // 递归检查接口继承
        if (zhc_implements_interface(entry->interfaces[i], interface_name)) {
            return true;
        }
    }

    // 通过继承获得接口
    if (entry->parent_name != NULL) {
        return zhc_implements_interface(entry->parent_name, interface_name);
    }

    return false;
}

bool zhc_type_equals(const char* type1, const char* type2) {
    if (!type1 || !type2) return false;
    return strcmp(type1, type2) == 0;
}

bool zhc_is_primitive_type(const char* type_name) {
    if (!type_name) return false;

    ZhCTypeHierarchyEntry* entry = zhc_typecheck_lookup(type_name);
    return entry != NULL && entry->is_primitive;
}

bool zhc_check_assignable(const char* target_type, const char* source_type) {
    return zhc_is_type(source_type, target_type);
}

// =============================================================================
// 类型转换
// =============================================================================

void* zhc_safe_cast(void* obj, const char* obj_type, const char* target_type) {
    if (!obj) return NULL;
    if (zhc_is_type(obj_type, target_type)) {
        return obj;
    }
    return NULL;
}

void* zhc_dynamic_cast(void* obj, const char* obj_type, const char* target_type) {
    if (!obj) return NULL;
    if (zhc_is_type(obj_type, target_type)) {
        return obj;
    }
    return NULL;
}

const char* zhc_get_type_name_str(const char* type_name) {
    ZhCTypeHierarchyEntry* entry = zhc_typecheck_lookup(type_name);
    return entry ? entry->type_name : type_name;
}

// =============================================================================
// 层次查询
// =============================================================================

size_t zhc_get_ancestors(const char* type_name, const char** ancestors, size_t max_count) {
    if (!type_name || !ancestors || max_count == 0) return 0;

    size_t count = 0;
    ZhCTypeHierarchyEntry* entry = zhc_typecheck_lookup(type_name);
    int depth = 0;

    while (entry != NULL && entry->parent_name != NULL && count < max_count && depth < 64) {
        ancestors[count++] = entry->parent_name;
        entry = zhc_typecheck_lookup(entry->parent_name);
        depth++;
    }

    return count;
}

const char* zhc_get_common_base(const char* type1, const char* type2) {
    if (!type1 || !type2) return NULL;

    // 收集 type1 的所有祖先
    const char* ancestors1[64];
    size_t count1 = zhc_get_ancestors(type1, ancestors1, 64);

    // 从 type2 向上查找
    ZhCTypeHierarchyEntry* entry = zhc_typecheck_lookup(type2);
    int depth = 0;
    while (entry != NULL && depth < 64) {
        // 检查自身
        if (strcmp(type2, type1) == 0) return type1;

        // 检查是否在 type1 的祖先中
        for (size_t i = 0; i < count1; i++) {
            if (strcmp(entry->type_name, ancestors1[i]) == 0) {
                return ancestors1[i];
            }
        }

        // 向上
        if (entry->parent_name) {
            entry = zhc_typecheck_lookup(entry->parent_name);
        } else {
            break;
        }
        depth++;
    }

    return NULL;
}
