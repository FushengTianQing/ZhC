/**
 * ZhC 闭包运行时实现
 *
 * 提供闭包和 Lambda 表达式的运行时支持
 * 实现变量捕获模式和 upvalue 内存管理
 */

#include "zhc_closure.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// ============================================================================
// 闭包类型管理
// ============================================================================

void _zhc_closure_type_init(ZhCClosureType* ct, const char* name) {
    if (!ct || !name) return;

    memset(ct, 0, sizeof(ZhCClosureType));
    strncpy(ct->name, name, ZHC_CLOSURE_NAME_MAX - 1);
    ct->name[ZHC_CLOSURE_NAME_MAX - 1] = '\0';
    ct->param_count = 0;
    ct->upvalue_count = 0;
}

void _zhc_closure_type_add_param(ZhCClosureType* ct, const char* param_type) {
    if (!ct || !param_type) return;
    if (ct->param_count >= ZHC_CLOSURE_MAX_PARAMS) return;

    strncpy(
        ct->param_types[ct->param_count],
        param_type,
        ZHC_CLOSURE_NAME_MAX - 1
    );
    ct->param_types[ct->param_count][ZHC_CLOSURE_NAME_MAX - 1] = '\0';
    ct->param_count++;
}

void _zhc_closure_type_set_return(ZhCClosureType* ct, const char* return_type) {
    if (!ct || !return_type) return;

    strncpy(ct->return_type, return_type, ZHC_CLOSURE_NAME_MAX - 1);
    ct->return_type[ZHC_CLOSURE_NAME_MAX - 1] = '\0';
}

void _zhc_closure_type_add_upvalue(ZhCClosureType* ct, ZhCUpvalue* upvalue) {
    if (!ct || !upvalue) return;
    if (ct->upvalue_count >= ZHC_CLOSURE_MAX_UPVALUES) return;

    ct->upvalues[ct->upvalue_count] = upvalue;
    ct->upvalue_count++;
}

// ============================================================================
// upvalue 管理
// ============================================================================

ZhCUpvalue* _zhc_upvalue_create(const char* name, ZhCCaptureMode mode, int is_mutable) {
    if (!name) return NULL;

    ZhCUpvalue* upvalue = (ZhCUpvalue*)malloc(sizeof(ZhCUpvalue));
    if (!upvalue) return NULL;

    memset(upvalue, 0, sizeof(ZhCUpvalue));
    strncpy(upvalue->name, name, ZHC_UPVALUE_NAME_MAX - 1);
    upvalue->name[ZHC_UPVALUE_NAME_MAX - 1] = '\0';
    upvalue->mode = mode;
    upvalue->is_mutable = is_mutable;
    upvalue->index = -1;  // 索引后续由闭包分配
    upvalue->value = NULL;
    upvalue->next = NULL;

    return upvalue;
}

void _zhc_upvalue_free(ZhCUpvalue* upvalue) {
    if (!upvalue) return;
    free(upvalue);
}

void _zhc_upvalue_set(ZhCUpvalue* upvalue, void* value) {
    if (!upvalue) return;

    // 检查是否可修改
    if (!upvalue->is_mutable && upvalue->mode == ZHC_CAPTURE_VALUE) {
        // 值捕获模式下不允许修改
        return;
    }

    upvalue->value = value;
}

void* _zhc_upvalue_get(ZhCUpvalue* upvalue) {
    if (!upvalue) return NULL;
    return upvalue->value;
}

// ============================================================================
// 闭包创建和销毁
// ============================================================================

ZhCClosure* _zhc_closure_create(void* func_ptr, int upvalue_count) {
    if (!func_ptr) return NULL;
    if (upvalue_count < 0 || upvalue_count > ZHC_CLOSURE_MAX_UPVALUES) return NULL;

    ZhCClosure* closure = (ZhCClosure*)malloc(sizeof(ZhCClosure));
    if (!closure) return NULL;

    memset(closure, 0, sizeof(ZhCClosure));
    closure->func_ptr = func_ptr;
    closure->upvalue_count = upvalue_count;
    closure->closure_type = NULL;

    if (upvalue_count > 0) {
        closure->upvalues = (void**)malloc(sizeof(void*) * upvalue_count);
        if (!closure->upvalues) {
            free(closure);
            return NULL;
        }
        memset(closure->upvalues, 0, sizeof(void*) * upvalue_count);
    } else {
        closure->upvalues = NULL;
    }

    return closure;
}

void _zhc_closure_free(ZhCClosure* closure) {
    if (!closure) return;

    if (closure->upvalues) {
        free(closure->upvalues);
        closure->upvalues = NULL;
    }

    free(closure);
}

ZhCClosure* _zhc_closure_create_with_type(ZhCClosureType* closure_type, void* func_ptr) {
    if (!func_ptr) return NULL;

    ZhCClosure* closure = _zhc_closure_create(func_ptr, closure_type ? closure_type->upvalue_count : 0);
    if (closure) {
        closure->closure_type = closure_type;
    }

    return closure;
}

// ============================================================================
// 闭包调用
// ============================================================================

void* _zhc_closure_call(ZhCClosure* closure, void** args, int arg_count) {
    if (!closure || !closure->func_ptr) return NULL;

    // 简单的函数指针调用
    // 注意：实际项目中这里应该使用正确的函数签名
    // 这里使用通用的函数指针类型调用

    typedef void* (*generic_func_t)(void**, int);
    generic_func_t func = (generic_func_t)closure->func_ptr;

    return func(args, arg_count);
}

// ============================================================================
// upvalue 数组操作
// ============================================================================

void _zhc_closure_set_upvalue(ZhCClosure* closure, int index, void* value) {
    if (!closure) return;
    if (index < 0 || index >= closure->upvalue_count) return;
    if (!closure->upvalues) return;

    closure->upvalues[index] = value;
}

void* _zhc_closure_get_upvalue(ZhCClosure* closure, int index) {
    if (!closure) return NULL;
    if (index < 0 || index >= closure->upvalue_count) return NULL;
    if (!closure->upvalues) return NULL;

    return closure->upvalues[index];
}

// ============================================================================
// 闭包环境管理（用于嵌套闭包）
// ============================================================================

ZhCClosure** _zhc_closure_create_env(int size) {
    if (size <= 0 || size > ZHC_CLOSURE_MAX_UPVALUES) return NULL;

    ZhCClosure** env = (ZhCClosure**)malloc(sizeof(ZhCClosure*) * size);
    if (!env) return NULL;

    memset(env, 0, sizeof(ZhCClosure*) * size);
    return env;
}

void _zhc_closure_free_env(ZhCClosure** env, int size) {
    if (!env) return;

    for (int i = 0; i < size; i++) {
        if (env[i]) {
            _zhc_closure_free(env[i]);
            env[i] = NULL;
        }
    }

    free(env);
}

void _zhc_closure_env_set(ZhCClosure** env, int index, ZhCClosure* closure) {
    if (!env) return;
    if (index < 0 || index >= ZHC_CLOSURE_MAX_UPVALUES) return;

    env[index] = closure;
}

ZhCClosure* _zhc_closure_env_get(ZhCClosure** env, int index) {
    if (!env) return NULL;
    if (index < 0 || index >= ZHC_CLOSURE_MAX_UPVALUES) return NULL;

    return env[index];
}

// ============================================================================
// 调试信息打印
// ============================================================================

void _zhc_closure_print(const ZhCClosure* closure) {
    if (!closure) {
        printf("Closure: (null)\n");
        return;
    }

    printf("Closure {\n");
    printf("  func_ptr: %p\n", closure->func_ptr);
    printf("  upvalue_count: %d\n", closure->upvalue_count);
    printf("  upvalues: %p\n", (void*)closure->upvalues);

    if (closure->closure_type) {
        printf("  type: %s\n", closure->closure_type->name);
    }

    printf("}\n");
}

void _zhc_closure_type_print(const ZhCClosureType* ct) {
    if (!ct) {
        printf("ClosureType: (null)\n");
        return;
    }

    printf("ClosureType {\n");
    printf("  name: %s\n", ct->name);
    printf("  params: %d\n", ct->param_count);
    for (int i = 0; i < ct->param_count; i++) {
        printf("    param[%d]: %s\n", i, ct->param_types[i]);
    }
    printf("  return: %s\n", ct->return_type);
    printf("  upvalues: %d\n", ct->upvalue_count);
    printf("}\n");
}

void _zhc_upvalue_print(const ZhCUpvalue* upvalue) {
    if (!upvalue) {
        printf("Upvalue: (null)\n");
        return;
    }

    const char* mode_str = "UNKNOWN";
    switch (upvalue->mode) {
        case ZHC_CAPTURE_REFERENCE: mode_str = "REFERENCE"; break;
        case ZHC_CAPTURE_VALUE: mode_str = "VALUE"; break;
        case ZHC_CAPTURE_CONST_REF: mode_str = "CONST_REF"; break;
    }

    printf("Upvalue {\n");
    printf("  name: %s\n", upvalue->name);
    printf("  mode: %s\n", mode_str);
    printf("  index: %d\n", upvalue->index);
    printf("  mutable: %s\n", upvalue->is_mutable ? "yes" : "no");
    printf("  value: %p\n", upvalue->value);
    printf("}\n");
}
