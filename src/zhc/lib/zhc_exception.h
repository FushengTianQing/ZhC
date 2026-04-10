/**
 * ZhC 异常处理头文件
 *
 * 提供异常处理运行时支持
 */

#ifndef ZHC_EXCEPTION_H
#define ZHC_EXCEPTION_H

#include <stdio.h>
#include <stdlib.h>
#include <setjmp.h>

// 编译器指令
#ifdef __cplusplus
extern "C" {
#endif

// 异常处理类型
typedef enum {
    EXCEPTION_NONE = 0,
    EXCEPTION_RUNTIME,
    EXCEPTION_DIVISION_BY_ZERO,
    EXCEPTION_NULL_POINTER,
    EXCEPTION_OUT_OF_BOUNDS,
    EXCEPTION_TYPE_MISMATCH,
    EXCEPTION_STACK_OVERFLOW,
    EXCEPTION_USER
} ExceptionType;

// 异常对象结构
typedef struct ZhCException {
    ExceptionType type;          // 异常类型
    int error_code;               // 错误代码
    char message[256];            // 错误消息
    void* context;                // 上下文数据
    struct ZhCException* cause;   // 原因异常
    const char* stack_trace[32];  // 堆栈跟踪
    int stack_depth;              // 堆栈深度
} ZhCException;

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

// 创建异常对象
ZhCException* _zhc_exception_create(ExceptionType type, int error_code, const char* message);

// 抛出异常
void _zhc_throw(ExceptionType type, int error_code, const char* message);

// 抛出异常（带上下文）
void _zhc_throw_with_context(ExceptionType type, int error_code, const char* message, void* context);

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

// 获取异常类型名称
const char* _zhc_exception_type_name(ExceptionType type);

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

// 抛出异常宏
#define ZHC_THROW(type, code, msg) \
    _zhc_throw(type, code, msg)

#define ZHC_RETHROW() \
    _zhc_rethrow()

#ifdef __cplusplus
}
#endif

#endif // ZHC_EXCEPTION_H