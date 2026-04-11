#ifndef ZHC_DYNAMIC_CAST_H
#define ZHC_DYNAMIC_CAST_H

#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

// =============================================================================
// ZhC 动态类型转换运行时（独立模块）
//
// 遵循 LLVM/C++ ABI 风格，提供完整的类型转换运行时支持：
// - safe_cast: 失败返回 NULL
// - dynamic_cast: 失败返回 NULL（调用方检查）
// - 类型检查: 返回布尔值
// - 详细错误信息: 通过 __zhc_dynamic_cast_result_t 结构返回
//
// 设计原则：
// - 零开销抽象：内联简单情况，避免函数指针间接
// - 可调试：错误信息包含转换路径
// - 可扩展：支持接口转换、多继承
//
// 作者：远
// 日期：2026-04-11
// =============================================================================

// =============================================================================
// 类型定义
// =============================================================================

/**
 * 转换结果状态码
 */
typedef enum {
    ZHC_CAST_SUCCESS = 0,          // 转换成功
    ZHC_CAST_NULL_SOURCE = 1,      // 源对象为空
    ZHC_CAST_INVALID_CAST = 2,     // 无效转换（类型不兼容）
    ZHC_CAST_AMBIGUOUS = 3,        // 歧义转换（多继承场景）
    ZHC_CAST_INTERFACE_NOT_FOUND = 4, // 接口未找到
    ZHC_CAST_TYPE_MISMATCH = 5,    // 类型不匹配
    ZHC_CAST_NOT_SUBTYPE = 6,      // 不是子类型
} zhc_cast_status_t;

/**
 * 转换结果结构体（类似 C++23 std::expected）
 *
 * 提供详细的转换结果信息：
 * - status: 转换状态
 * - result: 转换后的指针（成功时）
 * - cast_path: 转换路径（用于调试）
 * - ancestor_count: 祖先类型数量
 * - ancestors: 祖先类型数组
 */
typedef struct __zhc_dynamic_cast_result {
    zhc_cast_status_t status;
    void* result;                  // 转换后的指针
    const char* error_message;      // 错误消息
    const char* source_type;        // 源类型
    const char* target_type;        // 目标类型
    const char* cast_path[16];     // 转换路径（最多16层）
    int cast_path_length;           // 实际路径长度
    const char* ancestors[16];      // 源类型的祖先链
    int ancestor_count;             // 祖先数量
} __zhc_dynamic_cast_result_t;

// =============================================================================
// 函数声明
// =============================================================================

/**
 * 安全类型转换（失败返回 NULL）
 *
 * @param obj 对象指针
 * @param obj_type 对象类型名
 * @param target_type 目标类型名
 * @return 转换后的指针，失败返回 NULL
 */
void* zhc_safe_cast(void* obj, const char* obj_type, const char* target_type);

/**
 * 动态类型转换（返回结果结构体）
 *
 * @param obj 对象指针
 * @param obj_type 对象类型名
 * @param target_type 目标类型名
 * @param result 输出参数，存储转换结果详情
 * @return 转换后的指针，失败返回 NULL
 */
void* zhc_dynamic_cast_ex(void* obj, const char* obj_type,
                          const char* target_type,
                          __zhc_dynamic_cast_result_t* result);

/**
 * 类型检查（is 表达式）
 *
 * @param obj 对象指针
 * @param obj_type 对象类型名
 * @param target_type 目标类型名
 * @return true 如果对象是目标类型或其子类型
 */
bool zhc_is_type(void* obj, const char* obj_type, const char* target_type);

/**
 * 类型检查（返回详细信息）
 *
 * @param obj 对象指针
 * @param obj_type 对象类型名
 * @param target_type 目标类型名
 * @param ancestors 输出参数，存储祖先类型数组
 * @param max_ancestors 祖先数组最大长度
 * @return true 如果类型兼容，同时填充 ancestors
 */
bool zhc_is_type_ex(void* obj, const char* obj_type, const char* target_type,
                    const char** ancestors, size_t max_ancestors);

/**
 * 获取转换路径
 *
 * 计算从源类型到目标类型的转换路径。
 *
 * @param source_type 源类型名
 * @param target_type 目标类型名
 * @param path 输出参数，存储转换路径数组
 * @param max_path 最大路径长度
 * @return 实际路径长度，0 表示无法转换
 */
int zhc_get_cast_path(const char* source_type, const char* target_type,
                      const char** path, size_t max_path);

/**
 * 尝试类型转换（返回结果结构体）
 *
 * 这是推荐使用的 API，失败时不抛异常。
 *
 * @param obj 对象指针
 * @param obj_type 对象类型名
 * @param target_type 目标类型名
 * @return 转换结果结构体
 */
__zhc_dynamic_cast_result_t zhc_try_cast(void* obj, const char* obj_type,
                                         const char* target_type);

/**
 * 初始化动态转换运行时
 *
 * 由编译器在程序入口自动调用。
 */
void zhc_dynamic_cast_init(void);

#ifdef __cplusplus
}
#endif

#endif  // ZHC_DYNAMIC_CAST_H
