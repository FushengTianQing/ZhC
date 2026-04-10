/**
 * ZhC 闭包运行时头文件
 *
 * 提供闭包和 Lambda 表达式的运行时支持
 * 支持变量捕获模式和 upvalue 内存管理
 */

/**
 * ZhC 编译器运行时库
 * 版本: 1.0.0
 */

#ifndef ZHC_CLOSURE_H
#define ZHC_CLOSURE_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// 编译器指令
#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// 常量定义
// ============================================================================

// 最大闭包参数数量
#define ZHC_CLOSURE_MAX_PARAMS 16

// 最大 upvalue 数量
#define ZHC_CLOSURE_MAX_UPVALUES 32

// 最大闭包名称长度
#define ZHC_CLOSURE_NAME_MAX 64

// 最大捕获变量名称长度
#define ZHC_UPVALUE_NAME_MAX 32

// ============================================================================
// 类型定义
// ============================================================================

/**
 * 捕获模式 - 描述变量如何被闭包捕获
 */
typedef enum ZhCCaptureMode {
    ZHC_CAPTURE_REFERENCE = 0,  // 引用捕获 - 闭包可以直接修改原变量
    ZHC_CAPTURE_VALUE = 1,       // 值捕获 - 闭包获得变量的拷贝
    ZHC_CAPTURE_CONST_REF = 2   // 常量引用 - 闭包获得只读引用
} ZhCCaptureMode;

/**
 * upvalue 结构 - 表示被捕获的变量
 */
typedef struct ZhCUpvalue {
    char name[ZHC_UPVALUE_NAME_MAX];     // 变量名
    ZhCCaptureMode mode;                  // 捕获模式
    int index;                            // 在闭包环境中的索引
    int is_mutable;                      // 是否可变
    void* value;                         // 指向实际值的指针
    struct ZhCUpvalue* next;             // 下一个 upvalue（用于链表）
} ZhCUpvalue;

/**
 * 闭包类型信息
 */
typedef struct ZhCClosureType {
    char name[ZHC_CLOSURE_NAME_MAX];           // 类型名称
    int param_count;                            // 参数数量
    char param_types[ZHC_CLOSURE_MAX_PARAMS][ZHC_CLOSURE_NAME_MAX];  // 参数类型
    char return_type[ZHC_CLOSURE_NAME_MAX];    // 返回类型
    int upvalue_count;                         // upvalue 数量
    ZhCUpvalue* upvalues[ZHC_CLOSURE_MAX_UPVALUES];  // upvalue 数组
} ZhCClosureType;

/**
 * ZhCClosure 闭包结构体
 *
 * 闭包包含：
 * 1. func_ptr - 指向闭包所包装的函数的指针
 * 2. upvalues - 指向 upvalue 指针数组的指针
 * 3. upvalue_count - upvalue 数量
 */
typedef struct ZhCClosure {
    void* func_ptr;                 // 函数指针
    void** upvalues;                // upvalue 指针数组
    int upvalue_count;              // upvalue 数量
    ZhCClosureType* closure_type;   // 闭包类型信息（可选）
} ZhCClosure;

/**
 * 闭包调用上下文
 */
typedef struct ZhCClosureCallContext {
    ZhCClosure* closure;            // 要调用的闭包
    void** args;                    // 参数数组
    int arg_count;                  // 参数数量
    void* result;                   // 返回值
} ZhCClosureCallContext;

// ============================================================================
// 函数声明
// ============================================================================

// 闭包类型管理
void _zhc_closure_type_init(ZhCClosureType* ct, const char* name);
void _zhc_closure_type_add_param(ZhCClosureType* ct, const char* param_type);
void _zhc_closure_type_set_return(ZhCClosureType* ct, const char* return_type);
void _zhc_closure_type_add_upvalue(ZhCClosureType* ct, ZhCUpvalue* upvalue);

// upvalue 管理
ZhCUpvalue* _zhc_upvalue_create(const char* name, ZhCCaptureMode mode, int is_mutable);
void _zhc_upvalue_free(ZhCUpvalue* upvalue);
void _zhc_upvalue_set(ZhCUpvalue* upvalue, void* value);
void* _zhc_upvalue_get(ZhCUpvalue* upvalue);

// 闭包创建和销毁
ZhCClosure* _zhc_closure_create(void* func_ptr, int upvalue_count);
void _zhc_closure_free(ZhCClosure* closure);
ZhCClosure* _zhc_closure_create_with_type(ZhCClosureType* closure_type, void* func_ptr);

// 闭包调用
void* _zhc_closure_call(ZhCClosure* closure, void** args, int arg_count);

// upvalue 数组操作
void _zhc_closure_set_upvalue(ZhCClosure* closure, int index, void* value);
void* _zhc_closure_get_upvalue(ZhCClosure* closure, int index);

// 闭包环境管理（用于嵌套闭包）
ZhCClosure** _zhc_closure_create_env(int size);
void _zhc_closure_free_env(ZhCClosure** env, int size);
void _zhc_closure_env_set(ZhCClosure** env, int index, ZhCClosure* closure);
ZhCClosure* _zhc_closure_env_get(ZhCClosure** env, int index);

// 闭包信息打印（调试用）
void _zhc_closure_print(const ZhCClosure* closure);
void _zhc_closure_type_print(const ZhCClosureType* ct);
void _zhc_upvalue_print(const ZhCUpvalue* upvalue);

// ============================================================================
// 宏定义
// ============================================================================

// 创建值捕获的 upvalue
#define ZHC_MAKE_UPVALUE_VALUE(name) \
    _zhc_upvalue_create(name, ZHC_CAPTURE_VALUE, 0)

// 创建可变引用的 upvalue
#define ZHC_MAKE_UPVALUE_REF(name) \
    _zhc_upvalue_create(name, ZHC_CAPTURE_REFERENCE, 1)

// 创建常量引用的 upvalue
#define ZHC_MAKE_UPVALUE_CONST_REF(name) \
    _zhc_upvalue_create(name, ZHC_CAPTURE_CONST_REF, 0)

// 获取闭包的函数指针并调用
#define ZHC_CLOSURE_CALL(closure, ...) \
    _zhc_closure_call(closure, (void*[]){__VA_ARGS__}, (sizeof((void*[]){__VA_ARGS__}) / sizeof(void*)))

#ifdef __cplusplus
}
#endif

#endif // ZHC_CLOSURE_H
