/**
 * ZhC 异常处理实现
 *
 * 使用 setjmp/longjmp 实现异常传播
 */

#include "zhc_exception.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

// 全局异常上下文
ExceptionContext _zhc_exception_ctx = {
    .current_exception = NULL,
    .top_frame = NULL,
    .in_cleanup = 0
};

// 初始化异常处理系统
void _zhc_exception_init(void) {
    _zhc_exception_ctx.current_exception = NULL;
    _zhc_exception_ctx.top_frame = NULL;
    _zhc_exception_ctx.in_cleanup = 0;
}

// 清理异常处理系统
void _zhc_exception_cleanup(void) {
    if (_zhc_exception_ctx.current_exception) {
        free(_zhc_exception_ctx.current_exception);
        _zhc_exception_ctx.current_exception = NULL;
    }
}

// 创建异常对象
ZhCException* _zhc_exception_create(ExceptionType type, int error_code, const char* message) {
    ZhCException* e = (ZhCException*)malloc(sizeof(ZhCException));
    if (!e) {
        return NULL;
    }

    e->type = type;
    e->error_code = error_code;
    if (message) {
        strncpy(e->message, message, sizeof(e->message) - 1);
        e->message[sizeof(e->message) - 1] = '\0';
    } else {
        e->message[0] = '\0';
    }
    e->context = NULL;
    e->cause = NULL;
    e->stack_depth = 0;

    return e;
}

// 抛出异常
void _zhc_throw(ExceptionType type, int error_code, const char* message) {
    // 如果已经有异常，设置为原因
    ZhCException* current = _zhc_exception_ctx.current_exception;

    // 创建新异常
    ZhCException* e = _zhc_exception_create(type, error_code, message);
    if (!e) {
        // 如果无法创建异常，输出错误并终止
        fprintf(stderr, "Fatal error: cannot create exception\n");
        abort();
    }

    // 保留之前的异常作为原因
    if (current) {
        e->cause = current;
    }

    // 设置当前异常
    _zhc_exception_ctx.current_exception = e;

    // 如果有活动的 try 帧，执行 longjmp
    if (_zhc_exception_ctx.top_frame) {
        _zhc_exception_ctx.in_cleanup = 1;
        longjmp(_zhc_exception_ctx.top_frame->jump_buffer, 1);
    }

    // 没有活动的 try 帧，打印异常并终止
    _zhc_print_exception(e);
    abort();
}

// 抛出异常（带上下文）
void _zhc_throw_with_context(ExceptionType type, int error_code, const char* message, void* context) {
    ZhCException* e = _zhc_exception_create(type, error_code, message);
    if (e) {
        e->context = context;
    }
    _zhc_throw(type, error_code, message);
}

// 重新抛出当前异常
void _zhc_rethrow(void) {
    if (!_zhc_exception_ctx.current_exception) {
        _zhc_throw(EXCEPTION_NONE, -1, "No current exception to rethrow");
        return;
    }

    // 如果有活动的 try 帧，执行 longjmp
    if (_zhc_exception_ctx.top_frame) {
        _zhc_exception_ctx.in_cleanup = 1;
        longjmp(_zhc_exception_ctx.top_frame->jump_buffer, 1);
    }
}

// 获取当前异常
ZhCException* _zhc_get_current_exception(void) {
    return _zhc_exception_ctx.current_exception;
}

// 清除当前异常
void _zhc_clear_exception(void) {
    if (_zhc_exception_ctx.current_exception) {
        free(_zhc_exception_ctx.current_exception);
        _zhc_exception_ctx.current_exception = NULL;
    }
}

// 进入 try 块
int _zhc_enter_try(const char* label) {
    ExceptionFrame* frame = (ExceptionFrame*)malloc(sizeof(ExceptionFrame));
    if (!frame) {
        return -1;
    }

    frame->is_try_block = 1;
    frame->try_label = label;
    frame->next = _zhc_exception_ctx.top_frame;
    _zhc_exception_ctx.top_frame = frame;

    // setjmp 返回 0 表示首次调用（正常执行路径）
    // setjmp 返回非 0 表示从 longjmp 返回（异常路径）
    return setjmp(frame->jump_buffer) == 0 ? 0 : 1;
}

// 退出 try 块
void _zhc_exit_try(void) {
    if (_zhc_exception_ctx.top_frame && _zhc_exception_ctx.top_frame->is_try_block) {
        ExceptionFrame* frame = _zhc_exception_ctx.top_frame;
        _zhc_exception_ctx.top_frame = frame->next;
        free(frame);
    }
}

// 进入 catch 块
void _zhc_enter_catch(const char* label) {
    _zhc_exception_ctx.in_cleanup = 0;
}

// 退出 catch 块
void _zhc_exit_catch(void) {
    // 清除已处理的异常
    _zhc_clear_exception();
}

// 进入 finally 块
void _zhc_enter_finally(void) {
    // nothing special needed
}

// 执行 finally 并跳转（用于 finally 中的 return）
void _zhc_finally_and_longjmp(void) {
    if (_zhc_exception_ctx.current_exception && _zhc_exception_ctx.top_frame) {
        longjmp(_zhc_exception_ctx.top_frame->jump_buffer, 1);
    }
}

// 打印异常信息
void _zhc_print_exception(const ZhCException* e) {
    if (!e) {
        fprintf(stderr, "Exception: (null)\n");
        return;
    }

    fprintf(stderr, "Exception: %s\n", _zhc_exception_type_name(e->type));
    fprintf(stderr, "  Error code: %d\n", e->error_code);
    if (e->message[0]) {
        fprintf(stderr, "  Message: %s\n", e->message);
    }
    if (e->cause) {
        fprintf(stderr, "  Caused by: %s\n", _zhc_exception_type_name(e->cause->type));
    }
}

// 获取异常类型名称
const char* _zhc_exception_type_name(ExceptionType type) {
    switch (type) {
        case EXCEPTION_NONE:           return "No exception";
        case EXCEPTION_RUNTIME:        return "Runtime error";
        case EXCEPTION_DIVISION_BY_ZERO: return "Division by zero";
        case EXCEPTION_NULL_POINTER:    return "Null pointer";
        case EXCEPTION_OUT_OF_BOUNDS:   return "Out of bounds";
        case EXCEPTION_TYPE_MISMATCH:  return "Type mismatch";
        case EXCEPTION_STACK_OVERFLOW:  return "Stack overflow";
        case EXCEPTION_USER:            return "User exception";
        default:                        return "Unknown exception";
    }
}

// 析构函数链表
typedef struct DestructorNode {
    destructor_fn fn;
    void* obj;
    struct DestructorNode* next;
} DestructorNode;

static DestructorNode* _destructor_list = NULL;

// 注册析构函数
void _zhc_register_destructor(destructor_fn fn, void* obj) {
    DestructorNode* node = (DestructorNode*)malloc(sizeof(DestructorNode));
    if (!node) return;

    node->fn = fn;
    node->obj = obj;
    node->next = _destructor_list;
    _destructor_list = node;
}

// 执行栈展开
void _zhc_unwind_stack(void) {
    DestructorNode* current = _destructor_list;
    while (current) {
        if (current->fn && current->obj) {
            current->fn(current->obj);
        }
        DestructorNode* next = current->next;
        free(current);
        current = next;
    }
    _destructor_list = NULL;
}