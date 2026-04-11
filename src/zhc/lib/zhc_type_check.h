#ifndef ZHC_TYPE_CHECK_H
#define ZHC_TYPE_CHECK_H

#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

// =============================================================================
// ZhC 运行时类型检查器
// =============================================================================

// 类型层次关系表（由编译器生成）
typedef struct ZhCTypeHierarchyEntry {
    const char* type_name;
    const char* parent_name;
    const char** interfaces;
    size_t interface_count;
    bool is_class;
    bool is_struct;
    bool is_interface;
    bool is_primitive;
    struct ZhCTypeHierarchyEntry* next;
} ZhCTypeHierarchyEntry;

// 类型层次表管理器
typedef struct {
    ZhCTypeHierarchyEntry* entries;
    size_t count;
    ZhCTypeHierarchyEntry* primitives[16];  // 基本类型表
    size_t primitive_count;
} ZhCTypeHierarchyTable;

// 全局类型层次表
extern ZhCTypeHierarchyTable g_zhc_type_hierarchy;

// =============================================================================
// 初始化
// =============================================================================

/**
 * 初始化类型层次表
 */
void zhc_typecheck_init(void);

/**
 * 注册类型层次关系
 */
void zhc_typecheck_register(const char* type_name,
                           const char* parent_name,
                           const char** interfaces,
                           size_t interface_count,
                           bool is_class,
                           bool is_struct,
                           bool is_interface,
                           bool is_primitive);

// =============================================================================
// 类型查询
// =============================================================================

/**
 * 检查类型是否匹配
 * @param obj_type 对象类型名
 * @param target_type 目标类型名
 * @return true 如果 obj_type 是 target_type 或其子类型
 */
bool zhc_is_type(const char* obj_type, const char* target_type);

/**
 * 检查子类型关系
 * @param subtype 子类型名
 * @param supertype 父类型名
 * @return true 如果 subtype 是 supertype 的子类型
 */
bool zhc_is_subtype(const char* subtype, const char* supertype);

/**
 * 检查是否实现接口
 * @param type_name 类型名
 * @param interface_name 接口名
 * @return true 如果 type_name 实现了 interface_name
 */
bool zhc_implements_interface(const char* type_name, const char* interface_name);

/**
 * 检查类型是否相同
 * @param type1 类型名1
 * @param type2 类型名2
 * @return true 如果两个类型相同
 */
bool zhc_type_equals(const char* type1, const char* type2);

/**
 * 检查是否为基本类型
 * @param type_name 类型名
 * @return true 如果是基本类型
 */
bool zhc_is_primitive_type(const char* type_name);

/**
 * 检查赋值兼容性
 * @param target_type 目标类型
 * @param source_type 源类型
 * @return true 如果 source_type 可以赋值给 target_type
 */
bool zhc_check_assignable(const char* target_type, const char* source_type);

// =============================================================================
// 类型转换
// =============================================================================

/**
 * 安全类型转换
 * @param obj 对象指针
 * @param obj_type 对象类型名
 * @param target_type 目标类型名
 * @return 转换后的指针，失败返回 NULL
 */
void* zhc_safe_cast(void* obj, const char* obj_type, const char* target_type);

/**
 * 动态类型转换
 * @param obj 对象指针
 * @param obj_type 对象类型名
 * @param target_type 目标类型名
 * @return 转换后的指针，失败返回 NULL（调用方应检查返回值）
 */
void* zhc_dynamic_cast(void* obj, const char* obj_type, const char* target_type);

/**
 * 获取类型名称
 * @param type_name 类型名
 * @return 类型名字符串
 */
const char* zhc_get_type_name_str(const char* type_name);

// =============================================================================
// 内部函数
// =============================================================================

/**
 * 获取类型的祖先类型链
 * @param type_name 类型名
 * @param ancestors 输出数组
 * @param max_count 最大数量
 * @return 实际数量
 */
size_t zhc_get_ancestors(const char* type_name, const char** ancestors, size_t max_count);

/**
 * 获取两个类型的最近公共基类
 * @param type1 类型1
 * @param type2 类型2
 * @return 公共基类名，未找到返回 NULL
 */
const char* zhc_get_common_base(const char* type1, const char* type2);

/**
 * 查找类型条目
 */
ZhCTypeHierarchyEntry* zhc_typecheck_lookup(const char* type_name);

#ifdef __cplusplus
}
#endif

#endif  // ZHC_TYPE_CHECK_H
