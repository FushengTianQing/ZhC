/**
 * ZhC 异常处理头文件
 *
 * 提供异常处理运行时支持
 * 支持异常类型层次结构和 RTTI
 */

#ifndef ZHC_EXCEPTION_H
#define ZHC_EXCEPTION_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <setjmp.h>

// 编译器指令
#ifdef __cplusplus
extern "C" {
#endif

// 前向声明
struct ZhCExceptionType_;
struct ZhCException_;

// 最大异常类型名称长度
#define ZHC_EXCEPTION_TYPE_NAME_MAX 64

// 最大异常消息长度
#define ZHC_EXCEPTION_MESSAGE_MAX 256

// 最大堆栈跟踪深度
#define ZHC_EXCEPTION_STACK_DEPTH 32

// 最大异常字段数
#define ZHC_EXCEPTION_FIELDS_MAX 16

// 异常类型定义（使用字符串名称支持用户自定义类型）
typedef struct ZhCExceptionType_ {
    char name[ZHC_EXCEPTION_TYPE_NAME_MAX];           // 类型名称
    const char* base_type_name;                       // 父类名称（NULL 表示基类）
    int field_count;                                  // 字段数
    const char* field_names[ZHC_EXCEPTION_FIELDS_MAX]; // 字段名
    const char* field_types[ZHC_EXCEPTION_FIELDS_MAX];// 字段类型
    int is_builtin;                                   // 是否内置类型
} ZhCExceptionType;

// 异常对象结构
typedef struct ZhCException_ {
    ZhCExceptionType* type_info;                      // 类型信息
    int error_code;                                   // 错误代码
    char message[ZHC_EXCEPTION_MESSAGE_MAX];           // 错误消息
    void* context;                                    // 上下文数据
    struct ZhCException_* cause;                      // 原因异常
    const char* stack_trace[ZHC_EXCEPTION_STACK_DEPTH]; // 堆栈跟踪
    int stack_depth;                                  // 堆栈深度
    void* field_values[ZHC_EXCEPTION_FIELDS_MAX];      // 字段值
} ZhCException;

// 为了向后兼容，也支持旧的枚举类型
typedef enum {
    EXCEPTION_NONE = 0,
    EXCEPTION_RUNTIME,
    EXCEPTION_DIVISION_BY_ZERO,
    EXCEPTION_NULL_POINTER,
    EXCEPTION_OUT_OF_BOUNDS,
    EXCEPTION_TYPE_MISMATCH,
    EXCEPTION_STACK_OVERFLOW,
    EXCEPTION_IO,
    EXCEPTION_FILE_NOT_FOUND,
    EXCEPTION_FILE_PERMISSION,
    EXCEPTION_OVERFLOW,
    EXCEPTION_USER
} ExceptionType;

// 异常帧（用于栈展开）
typedef struct ExceptionFrame {
    jmp_buf jump_buffer;          // setjmp/longjmp 缓冲区
    struct ExceptionFrame* next;  // 下一个帧
    int is_try_block;             // 是否为 try 块
    const char* try_label;       // try 块标签
} ExceptionFrame;

// 异常处理状态
typedef struct ExceptionContext {
    ZhCException* current_exception;  // 当前异常
    ExceptionFrame* top_frame;       // 栈顶帧
    int in_cleanup;                   // 是否在清理中
} ExceptionContext;

// 全局异常上下文
extern ExceptionContext _zhc_exception_ctx;

// 初始化异常处理系统
void _zhc_exception_init(void);

// 清理异常处理系统
void _zhc_exception_cleanup(void);

// 创建异常对象（使用类型名称）
ZhCException* _zhc_exception_create(const char* type_name, int error_code, const char* message);

// 创建异常对象（使用 ZhCExceptionType）
ZhCException* _zhc_exception_create_with_type(ZhCExceptionType* type_info, int error_code, const char* message);

// 释放异常对象
void _zhc_exception_free(ZhCException* exc);

// 类型检查：是否是指定类型的实例或子类型
int _zhc_exception_is_a(ZhCException* exc, const char* type_name);
int _zhc_exception_is_a_type(ZhCException* exc, ZhCExceptionType* type_info);

// 获取异常类型名称
const char* _zhc_exception_get_type_name(ZhCException* exc);

// 设置异常字段
void _zhc_exception_set_field(ZhCException* exc, int field_index, void* value);

// 获取异常字段
void* _zhc_exception_get_field(ZhCException* exc, int field_index);

// 抛出异常（使用类型名称）
void _zhc_throw(const char* type_name, int error_code, const char* message);

// 抛出异常（兼容旧版）
void _zhc_throw_ex(ExceptionType type, int error_code, const char* message);

// 抛出异常（带上下文）
void _zhc_throw_with_context(const char* type_name, int error_code, const char* message, void* context);

// 重新抛出当前异常
void _zhc_rethrow(void);

// 获取当前异常
ZhCException* _zhc_get_current_exception(void);

// 清除当前异常
void _zhc_clear_exception(void);

// 进入 try 块
int _zhc_enter_try(const char* label);

// 退出 try 块
void _zhc_exit_try(void);

// 进入 catch 块
void _zhc_enter_catch(const char* label);

// 退出 catch 块
void _zhc_exit_catch(void);

// 进入 finally 块
void _zhc_enter_finally(void);

// 执行 finally 并跳转
void _zhc_finally_and_longjmp(void);

// 打印异常信息
void _zhc_print_exception(const ZhCException* e);

// 获取异常类型名称（兼容旧版）
const char* _zhc_exception_type_name(ExceptionType type);

// 获取异常类型名称（新版）
const char* _zhc_exception_get_typename(ZhCExceptionType* type_info);

// 类型注册表相关
void _zhc_register_exception_type(ZhCExceptionType* type_info);
ZhCExceptionType* _zhc_lookup_exception_type(const char* name);
int _zhc_is_subtype(const char* subtype, const char* supertype);

// 栈展开回调类型
typedef void (*destructor_fn)(void*);

// 注册析构函数
void _zhc_register_destructor(destructor_fn fn, void* obj);

// 执行栈展开
void _zhc_unwind_stack(void);

// 断言宏
#define ZHC_TRY(label) \
    if (_zhc_enter_try(label) == 0 && \
        (_zhc_setjmp(_zhc_exception_ctx.top_frame->jump_buffer) == 0))

#define ZHC_CATCH(label) \
    else if (_zhc_enter_catch(label) == 0)

#define ZHC_FINALLY \
    if (1) { \
        _zhc_enter_finally();

#define ZHC_END_TRY \
    }

// 抛出异常宏（兼容旧版）
#define ZHC_THROW(type, code, msg) \
    _zhc_throw_ex(type, code, msg)

#define ZHC_RETHROW() \
    _zhc_rethrow()

#ifdef __cplusplus
}
#endif

#endif // ZHC_EXCEPTION_H