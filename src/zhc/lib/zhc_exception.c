/**
 * ZhC 异常处理实现
 *
 * 使用 setjmp/longjmp 实现异常传播
 * 支持异常类型层次结构和 RTTI
 */

#include "zhc_exception.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

// ============================================================================
// 内置异常类型定义
// ============================================================================

// 基类：异常
static ZhCExceptionType _exc_exception = {
    .name = "异常",
    .base_type_name = NULL,
    .field_count = 2,
    .field_names = {"消息", "错误码"},
    .field_types = {"字符串", "整数型"},
    .is_builtin = 1,
};

// Error 分支（不可恢复）
static ZhCExceptionType _exc_error = {
    .name = "错误",
    .base_type_name = "异常",
    .field_count = 0,
    .field_names = {NULL},
    .field_types = {NULL},
    .is_builtin = 1,
};

static ZhCExceptionType _exc_memory_error = {
    .name = "内存错误",
    .base_type_name = "错误",
    .field_count = 0,
    .field_names = {NULL},
    .field_types = {NULL},
    .is_builtin = 1,
};

static ZhCExceptionType _exc_stack_overflow = {
    .name = "栈溢出错误",
    .base_type_name = "错误",
    .field_count = 1,
    .field_names = {"栈大小"},
    .field_types = {"整数型"},
    .is_builtin = 1,
};

static ZhCExceptionType _exc_system_error = {
    .name = "系统错误",
    .base_type_name = "错误",
    .field_count = 1,
    .field_names = {"系统错误码"},
    .field_types = {"整数型"},
    .is_builtin = 1,
};

// Exception 分支（可恢复）
static ZhCExceptionType _exc_runtime = {
    .name = "运行时异常",
    .base_type_name = "异常",
    .field_count = 0,
    .field_names = {NULL},
    .field_types = {NULL},
    .is_builtin = 1,
};

static ZhCExceptionType _exc_null_pointer = {
    .name = "空指针异常",
    .base_type_name = "运行时异常",
    .field_count = 1,
    .field_names = {"变量名"},
    .field_types = {"字符串"},
    .is_builtin = 1,
};

static ZhCExceptionType _exc_out_of_bounds = {
    .name = "数组越界异常",
    .base_type_name = "运行时异常",
    .field_count = 2,
    .field_names = {"数组长度", "访问索引"},
    .field_types = {"整数型", "整数型"},
    .is_builtin = 1,
};

static ZhCExceptionType _exc_type_mismatch = {
    .name = "类型转换异常",
    .base_type_name = "运行时异常",
    .field_count = 2,
    .field_names = {"源类型", "目标类型"},
    .field_types = {"字符串", "字符串"},
    .is_builtin = 1,
};

// IO 异常
static ZhCExceptionType _exc_io = {
    .name = "输入输出异常",
    .base_type_name = "异常",
    .field_count = 1,
    .field_names = {"文件路径"},
    .field_types = {"字符串"},
    .is_builtin = 1,
};

static ZhCExceptionType _exc_file_not_found = {
    .name = "文件未找到异常",
    .base_type_name = "输入输出异常",
    .field_count = 1,
    .field_names = {"文件路径"},
    .field_types = {"字符串"},
    .is_builtin = 1,
};

static ZhCExceptionType _exc_file_permission = {
    .name = "文件权限异常",
    .base_type_name = "输入输出异常",
    .field_count = 2,
    .field_names = {"文件路径", "所需权限"},
    .field_types = {"字符串", "字符串"},
    .is_builtin = 1,
};

// 算术异常
static ZhCExceptionType _exc_arithmetic = {
    .name = "算术异常",
    .base_type_name = "异常",
    .field_count = 0,
    .field_names = {NULL},
    .field_types = {NULL},
    .is_builtin = 1,
};

static ZhCExceptionType _exc_division_by_zero = {
    .name = "除零异常",
    .base_type_name = "算术异常",
    .field_count = 2,
    .field_names = {"分子", "分母"},
    .field_types = {"浮点型", "浮点型"},
    .is_builtin = 1,
};

static ZhCExceptionType _exc_overflow = {
    .name = "溢出异常",
    .base_type_name = "算术异常",
    .field_count = 2,
    .field_names = {"操作", "值"},
    .field_types = {"字符串", "整数型"},
    .is_builtin = 1,
};

// 用户自定义异常（默认基类）
static ZhCExceptionType _exc_user = {
    .name = "用户异常",
    .base_type_name = "异常",
    .field_count = 0,
    .field_names = {NULL},
    .field_types = {NULL},
    .is_builtin = 0,
};

// 内置类型数组
static ZhCExceptionType* _builtin_types[] = {
    &_exc_exception,
    &_exc_error,
    &_exc_memory_error,
    &_exc_stack_overflow,
    &_exc_system_error,
    &_exc_runtime,
    &_exc_null_pointer,
    &_exc_out_of_bounds,
    &_exc_type_mismatch,
    &_exc_io,
    &_exc_file_not_found,
    &_exc_file_permission,
    &_exc_arithmetic,
    &_exc_division_by_zero,
    &_exc_overflow,
    &_exc_user,
    NULL,
};

// 类型注册表
#define MAX_REGISTERED_TYPES 128
static ZhCExceptionType* _registered_types[MAX_REGISTERED_TYPES];
static int _registered_type_count = 0;

// 类型名称到类型的映射
static ZhCExceptionType* _type_map[128] = {NULL};  // 简单的哈希表

// ============================================================================
// 辅助函数
// ============================================================================

// 简单的字符串哈希
static int _hash_string(const char* str) {
    int hash = 0;
    while (*str) {
        hash = hash * 31 + *str;
        str++;
    }
    return hash & 127;
}

// 获取类型（通过名称查找）
static ZhCExceptionType* _get_type_by_name(const char* name) {
    // 先检查内置类型
    for (int i = 0; _builtin_types[i] != NULL; i++) {
        if (strcmp(_builtin_types[i]->name, name) == 0) {
            return _builtin_types[i];
        }
    }
    // 检查注册类型
    ZhCExceptionType* type = _type_map[_hash_string(name)];
    if (type && strcmp(type->name, name) == 0) {
        return type;
    }
    return NULL;
}

// ============================================================================
// 全局异常上下文
// ============================================================================

ExceptionContext _zhc_exception_ctx = {
    .current_exception = NULL,
    .top_frame = NULL,
    .in_cleanup = 0
};

// ============================================================================
// 初始化和清理
// ============================================================================

// 初始化异常处理系统
void _zhc_exception_init(void) {
    _zhc_exception_ctx.current_exception = NULL;
    _zhc_exception_ctx.top_frame = NULL;
    _zhc_exception_ctx.in_cleanup = 0;
    _registered_type_count = 0;
    memset(_type_map, 0, sizeof(_type_map));
}

// 清理异常处理系统
void _zhc_exception_cleanup(void) {
    if (_zhc_exception_ctx.current_exception) {
        _zhc_exception_free(_zhc_exception_ctx.current_exception);
        _zhc_exception_ctx.current_exception = NULL;
    }
}

// ============================================================================
// 类型注册
// ============================================================================

void _zhc_register_exception_type(ZhCExceptionType* type_info) {
    if (_registered_type_count >= MAX_REGISTERED_TYPES) {
        return;  // 表已满
    }
    _registered_types[_registered_type_count++] = type_info;
    _type_map[_hash_string(type_info->name)] = type_info;
}

ZhCExceptionType* _zhc_lookup_exception_type(const char* name) {
    return _get_type_by_name(name);
}

int _zhc_is_subtype(const char* subtype_name, const char* supertype_name) {
    if (strcmp(subtype_name, supertype_name) == 0) {
        return 1;
    }

    ZhCExceptionType* type = _get_type_by_name(subtype_name);
    if (!type || !type->base_type_name) {
        return 0;
    }

    return _zhc_is_subtype(type->base_type_name, supertype_name);
}

// ============================================================================
// 异常对象管理
// ============================================================================

// 创建异常对象
ZhCException* _zhc_exception_create(const char* type_name, int error_code, const char* message) {
    ZhCExceptionType* type_info = _get_type_by_name(type_name);
    if (!type_info) {
        type_info = &_exc_user;  // 默认使用用户异常
    }
    return _zhc_exception_create_with_type(type_info, error_code, message);
}

// 创建异常对象（使用 ZhCExceptionType）
ZhCException* _zhc_exception_create_with_type(ZhCExceptionType* type_info, int error_code, const char* message) {
    ZhCException* e = (ZhCException*)malloc(sizeof(ZhCException));
    if (!e) {
        return NULL;
    }

    e->type_info = type_info;
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
    memset(e->field_values, 0, sizeof(e->field_values));

    return e;
}

// 释放异常对象
void _zhc_exception_free(ZhCException* exc) {
    if (!exc) return;

    // 递归释放 cause
    if (exc->cause) {
        _zhc_exception_free(exc->cause);
        exc->cause = NULL;
    }

    // 释放字段值（用户负责分配和释放）
    // 这里只是清零指针

    free(exc);
}

// ============================================================================
// 类型检查
// ============================================================================

// 类型检查：是否是指定类型的实例或子类型
int _zhc_exception_is_a(ZhCException* exc, const char* type_name) {
    if (!exc || !exc->type_info) return 0;
    return _zhc_is_subtype(exc->type_info->name, type_name);
}

int _zhc_exception_is_a_type(ZhCException* exc, ZhCExceptionType* type_info) {
    if (!exc || !exc->type_info || !type_info) return 0;
    return _zhc_is_subtype(exc->type_info->name, type_info->name);
}

// 获取异常类型名称
const char* _zhc_exception_get_type_name(ZhCException* exc) {
    if (!exc || !exc->type_info) return "Unknown";
    return exc->type_info->name;
}

// ============================================================================
// 字段管理
// ============================================================================

void _zhc_exception_set_field(ZhCException* exc, int field_index, void* value) {
    if (!exc || field_index < 0 || field_index >= ZHC_EXCEPTION_FIELDS_MAX) return;
    exc->field_values[field_index] = value;
}

void* _zhc_exception_get_field(ZhCException* exc, int field_index) {
    if (!exc || field_index < 0 || field_index >= ZHC_EXCEPTION_FIELDS_MAX) return NULL;
    return exc->field_values[field_index];
}

// ============================================================================
// 异常抛出
// ============================================================================

// 抛出异常
void _zhc_throw(const char* type_name, int error_code, const char* message) {
    ZhCException* current = _zhc_exception_ctx.current_exception;

    ZhCException* e = _zhc_exception_create(type_name, error_code, message);
    if (!e) {
        fprintf(stderr, "Fatal error: cannot create exception\n");
        abort();
    }

    // 保留之前的异常作为原因
    if (current) {
        e->cause = current;
    }

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

// 抛出异常（兼容旧版枚举类型）
void _zhc_throw_ex(ExceptionType type, int error_code, const char* message) {
    const char* type_name = NULL;
    switch (type) {
        case EXCEPTION_NONE:           type_name = "异常"; break;
        case EXCEPTION_RUNTIME:        type_name = "运行时异常"; break;
        case EXCEPTION_DIVISION_BY_ZERO: type_name = "除零异常"; break;
        case EXCEPTION_NULL_POINTER:    type_name = "空指针异常"; break;
        case EXCEPTION_OUT_OF_BOUNDS:   type_name = "数组越界异常"; break;
        case EXCEPTION_TYPE_MISMATCH:  type_name = "类型转换异常"; break;
        case EXCEPTION_STACK_OVERFLOW:  type_name = "栈溢出错误"; break;
        case EXCEPTION_IO:              type_name = "输入输出异常"; break;
        case EXCEPTION_FILE_NOT_FOUND: type_name = "文件未找到异常"; break;
        case EXCEPTION_FILE_PERMISSION: type_name = "文件权限异常"; break;
        case EXCEPTION_OVERFLOW:        type_name = "溢出异常"; break;
        case EXCEPTION_USER:            type_name = "用户异常"; break;
        default:                        type_name = "异常"; break;
    }
    _zhc_throw(type_name, error_code, message);
}

// 抛出异常（带上下文）
void _zhc_throw_with_context(const char* type_name, int error_code, const char* message, void* context) {
    ZhCException* e = _zhc_exception_create(type_name, error_code, message);
    if (e) {
        e->context = context;
    }
    _zhc_throw(type_name, error_code, message);
}

// ============================================================================
// 异常重新抛出
// ============================================================================

void _zhc_rethrow(void) {
    if (!_zhc_exception_ctx.current_exception) {
        _zhc_throw("异常", -1, "No current exception to rethrow");
        return;
    }

    if (_zhc_exception_ctx.top_frame) {
        _zhc_exception_ctx.in_cleanup = 1;
        longjmp(_zhc_exception_ctx.top_frame->jump_buffer, 1);
    }
}

// ============================================================================
// 异常上下文管理
// ============================================================================

ZhCException* _zhc_get_current_exception(void) {
    return _zhc_exception_ctx.current_exception;
}

void _zhc_clear_exception(void) {
    if (_zhc_exception_ctx.current_exception) {
        _zhc_exception_free(_zhc_exception_ctx.current_exception);
        _zhc_exception_ctx.current_exception = NULL;
    }
}

// ============================================================================
// Try-Catch-Finally 支持
// ============================================================================

int _zhc_enter_try(const char* label) {
    ExceptionFrame* frame = (ExceptionFrame*)malloc(sizeof(ExceptionFrame));
    if (!frame) {
        return -1;
    }

    frame->is_try_block = 1;
    frame->try_label = label;
    frame->next = _zhc_exception_ctx.top_frame;
    _zhc_exception_ctx.top_frame = frame;

    return setjmp(frame->jump_buffer) == 0 ? 0 : 1;
}

void _zhc_exit_try(void) {
    if (_zhc_exception_ctx.top_frame && _zhc_exception_ctx.top_frame->is_try_block) {
        ExceptionFrame* frame = _zhc_exception_ctx.top_frame;
        _zhc_exception_ctx.top_frame = frame->next;
        free(frame);
    }
}

void _zhc_enter_catch(const char* label) {
    (void)label;  // 未使用
    _zhc_exception_ctx.in_cleanup = 0;
}

void _zhc_exit_catch(void) {
    _zhc_clear_exception();
}

void _zhc_enter_finally(void) {
    // nothing special needed
}

void _zhc_finally_and_longjmp(void) {
    if (_zhc_exception_ctx.current_exception && _zhc_exception_ctx.top_frame) {
        longjmp(_zhc_exception_ctx.top_frame->jump_buffer, 1);
    }
}

// ============================================================================
// 异常信息输出
// ============================================================================

void _zhc_print_exception(const ZhCException* e) {
    if (!e) {
        fprintf(stderr, "Exception: (null)\n");
        return;
    }

    fprintf(stderr, "Exception: %s\n", _zhc_exception_get_type_name((ZhCException*)e));
    fprintf(stderr, "  Error code: %d\n", e->error_code);
    if (e->message[0]) {
        fprintf(stderr, "  Message: %s\n", e->message);
    }
    if (e->cause) {
        fprintf(stderr, "  Caused by: %s\n", _zhc_exception_get_type_name(e->cause));
    }
}

// 获取异常类型名称（兼容旧版）
const char* _zhc_exception_type_name(ExceptionType type) {
    switch (type) {
        case EXCEPTION_NONE:           return "No exception";
        case EXCEPTION_RUNTIME:        return "Runtime error";
        case EXCEPTION_DIVISION_BY_ZERO: return "Division by zero";
        case EXCEPTION_NULL_POINTER:    return "Null pointer";
        case EXCEPTION_OUT_OF_BOUNDS:   return "Out of bounds";
        case EXCEPTION_TYPE_MISMATCH:  return "Type mismatch";
        case EXCEPTION_STACK_OVERFLOW:  return "Stack overflow";
        case EXCEPTION_IO:              return "IO error";
        case EXCEPTION_FILE_NOT_FOUND:  return "File not found";
        case EXCEPTION_FILE_PERMISSION: return "File permission";
        case EXCEPTION_OVERFLOW:        return "Overflow";
        case EXCEPTION_USER:            return "User exception";
        default:                        return "Unknown exception";
    }
}

// 获取异常类型名称（新版）
const char* _zhc_exception_get_typename(ZhCExceptionType* type_info) {
    if (!type_info) return "Unknown";
    return type_info->name;
}

// ============================================================================
// 栈展开和析构函数
// ============================================================================

typedef struct DestructorNode {
    destructor_fn fn;
    void* obj;
    struct DestructorNode* next;
} DestructorNode;

static DestructorNode* _destructor_list = NULL;

void _zhc_register_destructor(destructor_fn fn, void* obj) {
    DestructorNode* node = (DestructorNode*)malloc(sizeof(DestructorNode));
    if (!node) return;

    node->fn = fn;
    node->obj = obj;
    node->next = _destructor_list;
    _destructor_list = node;
}

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