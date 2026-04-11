/**
 * ZhC 反射运行时实现
 *
 * 提供运行时类型信息 (RTTI) 查询的 C 运行时实现
 *
 * 版本: 1.0.0
 * 作者: 阿福
 * 日期: 2026-04-11
 */

#include "zhc_reflection.h"

// ============================================================================
// 内部数据结构
// ============================================================================

/* 类型注册表（链表实现） */
static ZhCTypeRegistryEntry* g_type_registry = NULL;
static int g_type_count = 0;
static int g_initialized = 0;

/* 基本类型信息（静态分配） */
static ZhCTypeInfo g_primitive_types[] = {
    {"整数型", 4, 4, ZHC_TYPE_PRIMITIVE, "", {}, 0, {}, 0, {}, 0, {}, {}, 0},
    {"字符型", 1, 1, ZHC_TYPE_PRIMITIVE, "", {}, 0, {}, 0, {}, 0, {}, {}, 0},
    {"浮点型", 4, 4, ZHC_TYPE_PRIMITIVE, "", {}, 0, {}, 0, {}, 0, {}, {}, 0},
    {"双精度浮点型", 8, 8, ZHC_TYPE_PRIMITIVE, "", {}, 0, {}, 0, {}, 0, {}, {}, 0},
    {"逻辑型", 1, 1, ZHC_TYPE_PRIMITIVE, "", {}, 0, {}, 0, {}, 0, {}, {}, 0},
    {"长整数型", 8, 8, ZHC_TYPE_PRIMITIVE, "", {}, 0, {}, 0, {}, 0, {}, {}, 0},
    {"短整数型", 2, 2, ZHC_TYPE_PRIMITIVE, "", {}, 0, {}, 0, {}, 0, {}, {}, 0},
    {"空型", 0, 1, ZHC_TYPE_PRIMITIVE, "", {}, 0, {}, 0, {}, 0, {}, {}, 0},
    {"字符串型", 8, 8, ZHC_TYPE_POINTER, "", {}, 0, {}, 0, {}, 0, {}, {}, 0},
};
#define PRIMITIVE_TYPE_COUNT (sizeof(g_primitive_types) / sizeof(g_primitive_types[0]))

// ============================================================================
// 内部辅助函数
// ============================================================================

/**
 * 安全字符串复制
 */
static void safe_strcpy(char* dest, const char* src, size_t max_len) {
    if (!dest || !src) {
        if (dest) dest[0] = '\0';
        return;
    }
    strncpy(dest, src, max_len - 1);
    dest[max_len - 1] = '\0';
}

/**
 * 在注册表中查找条目
 */
static ZhCTypeRegistryEntry* find_entry(const char* name) {
    ZhCTypeRegistryEntry* entry = g_type_registry;
    while (entry) {
        if (strcmp(entry->name, name) == 0) {
            return entry;
        }
        entry = entry->next;
    }
    return NULL;
}

/**
 * 在基本类型中查找
 */
static const ZhCTypeInfo* find_primitive(const char* name) {
    for (size_t i = 0; i < PRIMITIVE_TYPE_COUNT; i++) {
        if (strcmp(g_primitive_types[i].name, name) == 0) {
            return &g_primitive_types[i];
        }
    }
    return NULL;
}

// ============================================================================
// 全局类型注册表 API
// ============================================================================

void zhc_reflection_init(void) {
    if (g_initialized) return;
    g_type_registry = NULL;
    g_type_count = 0;
    g_initialized = 1;
}

void zhc_reflection_cleanup(void) {
    ZhCTypeRegistryEntry* entry = g_type_registry;
    while (entry) {
        ZhCTypeRegistryEntry* next = entry->next;
        if (entry->info) {
            free(entry->info);
        }
        free(entry);
        entry = next;
    }
    g_type_registry = NULL;
    g_type_count = 0;
    g_initialized = 0;
}

int zhc_reflection_register_type(const ZhCTypeInfo* info) {
    if (!info) return -1;
    
    /* 检查是否已注册 */
    if (find_entry(info->name)) {
        return -1;  /* 已存在 */
    }
    
    /* 分配新条目 */
    ZhCTypeRegistryEntry* entry = (ZhCTypeRegistryEntry*)malloc(sizeof(ZhCTypeRegistryEntry));
    if (!entry) return -1;
    
    /* 分配并复制类型信息 */
    ZhCTypeInfo* new_info = (ZhCTypeInfo*)malloc(sizeof(ZhCTypeInfo));
    if (!new_info) {
        free(entry);
        return -1;
    }
    memcpy(new_info, info, sizeof(ZhCTypeInfo));
    
    safe_strcpy(entry->name, info->name, ZHC_REF_TYPE_NAME_MAX);
    entry->info = new_info;
    entry->next = g_type_registry;
    g_type_registry = entry;
    g_type_count++;
    
    return 0;
}

const ZhCTypeInfo* zhc_reflection_lookup_type(const char* name) {
    if (!name) return NULL;
    
    /* 先查注册表 */
    ZhCTypeRegistryEntry* entry = find_entry(name);
    if (entry) return entry->info;
    
    /* 再查基本类型 */
    return find_primitive(name);
}

int zhc_reflection_is_type_registered(const char* name) {
    return zhc_reflection_lookup_type(name) != NULL ? 1 : 0;
}

int zhc_reflection_get_type_count(void) {
    return g_type_count + (int)PRIMITIVE_TYPE_COUNT;
}

int zhc_reflection_get_all_type_names(char names[][ZHC_REF_TYPE_NAME_MAX], int max_count) {
    int count = 0;
    
    /* 基本类型 */
    for (size_t i = 0; i < PRIMITIVE_TYPE_COUNT && count < max_count; i++) {
        safe_strcpy(names[count], g_primitive_types[i].name, ZHC_REF_TYPE_NAME_MAX);
        count++;
    }
    
    /* 注册表中的类型 */
    ZhCTypeRegistryEntry* entry = g_type_registry;
    while (entry && count < max_count) {
        safe_strcpy(names[count], entry->name, ZHC_REF_TYPE_NAME_MAX);
        count++;
        entry = entry->next;
    }
    
    return count;
}

// ============================================================================
// 类型查询 API
// ============================================================================

const ZhCTypeInfo* zhc_reflection_get_type_info(const void* obj, const char* type_name) {
    (void)obj;  /* 对象指针暂不使用 */
    return zhc_reflection_lookup_type(type_name);
}

const char* zhc_reflection_get_type_name(const char* type_name) {
    const ZhCTypeInfo* info = zhc_reflection_lookup_type(type_name);
    return info ? info->name : NULL;
}

size_t zhc_reflection_get_type_size(const char* type_name) {
    const ZhCTypeInfo* info = zhc_reflection_lookup_type(type_name);
    return info ? info->size : 0;
}

int zhc_reflection_is_primitive(const char* type_name) {
    const ZhCTypeInfo* info = zhc_reflection_lookup_type(type_name);
    return (info && info->category == ZHC_TYPE_PRIMITIVE) ? 1 : 0;
}

int zhc_reflection_get_field_count(const char* type_name) {
    const ZhCTypeInfo* info = zhc_reflection_lookup_type(type_name);
    return info ? info->field_count : -1;
}

int zhc_reflection_get_field(const char* type_name, const char* field_name, ZhCFieldInfo* out_field) {
    const ZhCTypeInfo* info = zhc_reflection_lookup_type(type_name);
    if (!info || !out_field) return -1;
    
    for (int i = 0; i < info->field_count; i++) {
        if (strcmp(info->fields[i].name, field_name) == 0) {
            memcpy(out_field, &info->fields[i], sizeof(ZhCFieldInfo));
            return 0;
        }
    }
    return -1;  /* 字段未找到 */
}

size_t zhc_reflection_get_field_offset(const char* type_name, const char* field_name) {
    ZhCFieldInfo field;
    if (zhc_reflection_get_field(type_name, field_name, &field) == 0) {
        return field.offset;
    }
    return (size_t)-1;  /* (size_t)-1 表示失败 */
}

int zhc_reflection_get_field_value(const void* obj, const char* type_name,
                                    const char* field_name, void* out_value, size_t value_size) {
    const ZhCTypeInfo* info = zhc_reflection_lookup_type(type_name);
    if (!info || !obj || !out_value) return -1;
    
    for (int i = 0; i < info->field_count; i++) {
        if (strcmp(info->fields[i].name, field_name) == 0) {
            /* 检查大小 */
            if (value_size < info->fields[i].size) return -1;
            
            /* 复制字段值 */
            memcpy(out_value, (const char*)obj + info->fields[i].offset, info->fields[i].size);
            return 0;
        }
    }
    return -1;  /* 字段未找到 */
}

int zhc_reflection_set_field_value(void* obj, const char* type_name,
                                    const char* field_name, const void* value, size_t value_size) {
    const ZhCTypeInfo* info = zhc_reflection_lookup_type(type_name);
    if (!info || !obj || !value) return -1;
    
    for (int i = 0; i < info->field_count; i++) {
        if (strcmp(info->fields[i].name, field_name) == 0) {
            /* 检查大小 */
            size_t copy_size = value_size < info->fields[i].size ? value_size : info->fields[i].size;
            
            /* 检查是否常量字段 */
            if (info->fields[i].is_const) return -1;
            
            /* 复制值到字段 */
            memcpy((char*)obj + info->fields[i].offset, value, copy_size);
            return 0;
        }
    }
    return -1;  /* 字段未找到 */
}

// ============================================================================
// 继承关系查询 API
// ============================================================================

const char* zhc_reflection_get_base_class(const char* type_name) {
    const ZhCTypeInfo* info = zhc_reflection_lookup_type(type_name);
    if (!info) return NULL;
    
    /* 空字符串表示无父类 */
    return info->base_class[0] != '\0' ? info->base_class : NULL;
}

int zhc_reflection_is_subclass_of(const char* derived_type, const char* base_type) {
    if (!derived_type || !base_type) return 0;
    
    /* 相同类型 */
    if (strcmp(derived_type, base_type) == 0) return 1;
    
    /* 沿继承链向上查找 */
    const char* current = derived_type;
    int max_depth = 32;  /* 防止循环继承 */
    
    while (current && max_depth-- > 0) {
        const ZhCTypeInfo* info = zhc_reflection_lookup_type(current);
        if (!info || info->base_class[0] == '\0') break;
        
        if (strcmp(info->base_class, base_type) == 0) return 1;
        current = info->base_class;
    }
    
    return 0;
}

int zhc_reflection_is_assignable_from(const char* target_type, const char* source_type) {
    return zhc_reflection_is_subclass_of(source_type, target_type);
}

// ============================================================================
// 方法查询 API
// ============================================================================

int zhc_reflection_get_method_count(const char* type_name) {
    const ZhCTypeInfo* info = zhc_reflection_lookup_type(type_name);
    return info ? info->method_count : -1;
}

int zhc_reflection_get_method(const char* type_name, const char* method_name, ZhCMethodInfo* out_method) {
    const ZhCTypeInfo* info = zhc_reflection_lookup_type(type_name);
    if (!info || !out_method) return -1;
    
    for (int i = 0; i < info->method_count; i++) {
        if (strcmp(info->methods[i].name, method_name) == 0) {
            memcpy(out_method, &info->methods[i], sizeof(ZhCMethodInfo));
            return 0;
        }
    }
    return -1;  /* 方法未找到 */
}
