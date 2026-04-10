/**
 * ZhC 智能指针运行时实现
 *
 * 提供智能指针的 C 运行时实现
 * 支持：独享指针、共享指针、弱指针
 *
 * 版本: 1.0.0
 * 作者: 阿福
 * 日期: 2026-04-10
 */

#include "zhc_smart_ptr.h"

// ============================================================================
// 内部辅助函数
// ============================================================================

/**
 * 创建控制块
 */
static ZhCControlBlock* _zhc_ctrl_block_create(void* object, const char* type_name,
                                                 void (*destructor)(void*)) {
    ZhCControlBlock* ctrl = (ZhCControlBlock*)malloc(sizeof(ZhCControlBlock));
    if (!ctrl) {
        fprintf(stderr, "[ZhC] 错误: 控制块分配失败\n");
        return NULL;
    }

    ctrl->ref_count = ZHC_SP_INIT_REFCOUNT;
    ctrl->weak_count = 0;
    ctrl->object = object;
    ctrl->destructor = destructor;

    if (type_name) {
        strncpy(ctrl->type_name, type_name, ZHC_SP_TYPE_NAME_MAX - 1);
        ctrl->type_name[ZHC_SP_TYPE_NAME_MAX - 1] = '\0';
    } else {
        ctrl->type_name[0] = '\0';
    }

#if ZHC_SP_DEBUG
    printf("[ZhC] 控制块创建: type=%s, ref=%d, weak=%d\n",
           ctrl->type_name, ctrl->ref_count, ctrl->weak_count);
#endif

    return ctrl;
}

/**
 * 销毁控制块
 */
static void _zhc_ctrl_block_destroy(ZhCControlBlock* ctrl) {
    if (!ctrl) return;

#if ZHC_SP_DEBUG
    printf("[ZhC] 控制块销毁: type=%s\n", ctrl->type_name);
#endif

    /* 销毁被管理对象 */
    if (ctrl->object) {
        if (ctrl->destructor) {
            ctrl->destructor(ctrl->object);
        } else {
            free(ctrl->object);
        }
        ctrl->object = NULL;
    }

    free(ctrl);
}

/**
 * 创建智能指针对象
 */
static ZhCSmartPtr* _zhc_smart_ptr_alloc(ZhCSmartPtrKind kind, const char* type_name,
                                           const char* var_name) {
    ZhCSmartPtr* ptr = (ZhCSmartPtr*)malloc(sizeof(ZhCSmartPtr));
    if (!ptr) {
        fprintf(stderr, "[ZhC] 错误: 智能指针分配失败\n");
        return NULL;
    }

    ptr->kind = kind;
    ptr->ptr = NULL;
    ptr->ctrl = NULL;
    ptr->is_valid = 1;

    if (type_name) {
        strncpy(ptr->type_name, type_name, ZHC_SP_TYPE_NAME_MAX - 1);
        ptr->type_name[ZHC_SP_TYPE_NAME_MAX - 1] = '\0';
    } else {
        ptr->type_name[0] = '\0';
    }

    if (var_name) {
        strncpy(ptr->var_name, var_name, ZHC_SP_VAR_NAME_MAX - 1);
        ptr->var_name[ZHC_SP_VAR_NAME_MAX - 1] = '\0';
    } else {
        ptr->var_name[0] = '\0';
    }

    return ptr;
}

// ============================================================================
// 独享指针 (unique_ptr) 实现
// ============================================================================

ZhCSmartPtr* zhc_unique_ptr_create(size_t size, const char* type_name,
                                    const char* var_name) {
    ZhCSmartPtr* ptr = _zhc_smart_ptr_alloc(ZHC_SP_UNIQUE, type_name, var_name);
    if (!ptr) return NULL;

    ptr->ptr = malloc(size);
    if (!ptr->ptr) {
        fprintf(stderr, "[ZhC] 错误: 独享指针对象分配失败 (size=%zu)\n", size);
        free(ptr);
        return NULL;
    }

#if ZHC_SP_DEBUG
    printf("[ZhC] 独享指针创建: %s %s, size=%zu\n",
           type_name ? type_name : "?", var_name ? var_name : "?", size);
#endif

    return ptr;
}

void* zhc_unique_ptr_get(ZhCSmartPtr* ptr) {
    if (!ptr || !ptr->is_valid) return NULL;
    return ptr->ptr;
}

void zhc_unique_ptr_release(ZhCSmartPtr* ptr) {
    if (!ptr) return;

#if ZHC_SP_DEBUG
    printf("[ZhC] 独享指针释放: %s\n", ptr->var_name);
#endif

    if (ptr->ptr && ptr->is_valid) {
        free(ptr->ptr);
        ptr->ptr = NULL;
    }
    ptr->is_valid = 0;
    free(ptr);
}

ZhCSmartPtr* zhc_unique_ptr_move(ZhCSmartPtr* src) {
    if (!src || !src->is_valid) {
#if ZHC_SP_DEBUG
        printf("[ZhC] 独享指针移动失败: 源指针无效\n");
#endif
        return NULL;
    }

    /* 创建新的智能指针壳（共享底层对象） */
    ZhCSmartPtr* dst = _zhc_smart_ptr_alloc(ZHC_SP_UNIQUE, src->type_name, src->var_name);
    if (!dst) return NULL;

    dst->ptr = src->ptr;

    /* 源指针失效 */
    src->ptr = NULL;
    src->is_valid = 0;

#if ZHC_SP_DEBUG
    printf("[ZhC] 独享指针移动: %s -> 新指针\n", src->var_name);
#endif

    return dst;
}

// ============================================================================
// 共享指针 (shared_ptr) 实现
// ============================================================================

ZhCSmartPtr* zhc_shared_ptr_create(size_t size, const char* type_name,
                                    const char* var_name) {
    ZhCSmartPtr* ptr = _zhc_smart_ptr_alloc(ZHC_SP_SHARED, type_name, var_name);
    if (!ptr) return NULL;

    void* object = malloc(size);
    if (!object) {
        fprintf(stderr, "[ZhC] 错误: 共享指针对象分配失败 (size=%zu)\n", size);
        free(ptr);
        return NULL;
    }

    ptr->ctrl = _zhc_ctrl_block_create(object, type_name, NULL);
    if (!ptr->ctrl) {
        free(object);
        free(ptr);
        return NULL;
    }

    ptr->ptr = ptr->ctrl; /* ptr 指向控制块 */

#if ZHC_SP_DEBUG
    printf("[ZhC] 共享指针创建: %s %s, ref_count=%d\n",
           type_name ? type_name : "?", var_name ? var_name : "?",
           ptr->ctrl->ref_count);
#endif

    return ptr;
}

ZhCSmartPtr* zhc_shared_ptr_from_raw(void* object, const char* type_name,
                                      void (*destructor)(void*)) {
    if (!object) return NULL;

    ZhCSmartPtr* ptr = _zhc_smart_ptr_alloc(ZHC_SP_SHARED, type_name, NULL);
    if (!ptr) return NULL;

    ptr->ctrl = _zhc_ctrl_block_create(object, type_name, destructor);
    if (!ptr->ctrl) {
        free(ptr);
        return NULL;
    }

    ptr->ptr = ptr->ctrl;

    return ptr;
}

void* zhc_shared_ptr_get(ZhCSmartPtr* ptr) {
    if (!ptr || !ptr->is_valid || !ptr->ctrl) return NULL;
    return ptr->ctrl->object;
}

void zhc_shared_ptr_retain(ZhCSmartPtr* ptr) {
    if (!ptr || !ptr->ctrl) return;
    ptr->ctrl->ref_count++;

#if ZHC_SP_DEBUG
    printf("[ZhC] 共享指针 retain: %s, ref_count=%d\n",
           ptr->var_name, ptr->ctrl->ref_count);
#endif
}

void zhc_shared_ptr_release(ZhCSmartPtr* ptr) {
    if (!ptr || !ptr->ctrl) {
        if (ptr) free(ptr);
        return;
    }

    ptr->ctrl->ref_count--;

#if ZHC_SP_DEBUG
    printf("[ZhC] 共享指针 release: %s, ref_count=%d\n",
           ptr->var_name, ptr->ctrl->ref_count);
#endif

    if (ptr->ctrl->ref_count <= 0) {
        /* 强引用为 0，销毁对象 */
        _zhc_ctrl_block_destroy(ptr->ctrl);
        ptr->ctrl = NULL;
    }

    ptr->is_valid = 0;
    free(ptr);
}

int zhc_shared_ptr_use_count(ZhCSmartPtr* ptr) {
    if (!ptr || !ptr->ctrl) return 0;
    return ptr->ctrl->ref_count;
}

// ============================================================================
// 弱指针 (weak_ptr) 实现
// ============================================================================

ZhCSmartPtr* zhc_weak_ptr_from_shared(ZhCSmartPtr* shared) {
    if (!shared || !shared->ctrl) return NULL;

    ZhCSmartPtr* weak = _zhc_smart_ptr_alloc(ZHC_SP_WEAK, shared->type_name, NULL);
    if (!weak) return NULL;

    weak->ctrl = shared->ctrl;
    weak->ctrl->weak_count++;

#if ZHC_SP_DEBUG
    printf("[ZhC] 弱指针创建: %s, weak_count=%d\n",
           shared->type_name, weak->ctrl->weak_count);
#endif

    return weak;
}

ZhCSmartPtr* zhc_weak_ptr_lock(ZhCSmartPtr* weak) {
    if (!weak || !weak->ctrl) return NULL;

    /* 如果对象已被销毁 */
    if (weak->ctrl->ref_count <= 0 || !weak->ctrl->object) {
#if ZHC_SP_DEBUG
        printf("[ZhC] 弱指针 lock 失败: 对象已销毁\n");
#endif
        return NULL;
    }

    /* 创建新的共享指针 */
    ZhCSmartPtr* shared = _zhc_smart_ptr_alloc(ZHC_SP_SHARED, weak->type_name, NULL);
    if (!shared) return NULL;

    shared->ctrl = weak->ctrl;
    shared->ctrl->ref_count++;
    shared->ptr = shared->ctrl;

#if ZHC_SP_DEBUG
    printf("[ZhC] 弱指针 lock 成功: ref_count=%d\n", shared->ctrl->ref_count);
#endif

    return shared;
}

void zhc_weak_ptr_release(ZhCSmartPtr* ptr) {
    if (!ptr) return;

    if (ptr->ctrl) {
        ptr->ctrl->weak_count--;

#if ZHC_SP_DEBUG
        printf("[ZhC] 弱指针 release: weak_count=%d\n", ptr->ctrl->weak_count);
#endif

        /* 如果强引用和弱引用都为 0，释放控制块 */
        if (ptr->ctrl->ref_count <= 0 && ptr->ctrl->weak_count <= 0) {
            free(ptr->ctrl);
        }
    }

    free(ptr);
}

int zhc_weak_ptr_expired(ZhCSmartPtr* ptr) {
    if (!ptr || !ptr->ctrl) return 1;
    return ptr->ctrl->ref_count <= 0;
}

// ============================================================================
// 通用操作
// ============================================================================

void zhc_smart_ptr_destroy(ZhCSmartPtr* ptr) {
    if (!ptr) return;

    switch (ptr->kind) {
        case ZHC_SP_UNIQUE:
            zhc_unique_ptr_release(ptr);
            break;
        case ZHC_SP_SHARED:
            zhc_shared_ptr_release(ptr);
            break;
        case ZHC_SP_WEAK:
            zhc_weak_ptr_release(ptr);
            break;
    }
}

void* zhc_smart_ptr_get_object(ZhCSmartPtr* ptr) {
    if (!ptr || !ptr->is_valid) return NULL;

    switch (ptr->kind) {
        case ZHC_SP_UNIQUE:
            return ptr->ptr;
        case ZHC_SP_SHARED:
            return ptr->ctrl ? ptr->ctrl->object : NULL;
        case ZHC_SP_WEAK:
            return NULL; /* 弱指针不能直接访问对象 */
    }
    return NULL;
}

int zhc_smart_ptr_is_valid(ZhCSmartPtr* ptr) {
    return ptr && ptr->is_valid;
}

void zhc_smart_ptr_debug_print(ZhCSmartPtr* ptr) {
    if (!ptr) {
        printf("[ZhC] 智能指针: NULL\n");
        return;
    }

    const char* kind_str;
    switch (ptr->kind) {
        case ZHC_SP_UNIQUE: kind_str = "unique"; break;
        case ZHC_SP_SHARED: kind_str = "shared"; break;
        case ZHC_SP_WEAK:   kind_str = "weak"; break;
        default:            kind_str = "unknown"; break;
    }

    printf("[ZhC] 智能指针: kind=%s, type=%s, var=%s, valid=%d",
           kind_str, ptr->type_name, ptr->var_name, ptr->is_valid);

    if (ptr->ctrl) {
        printf(", ref_count=%d, weak_count=%d",
               ptr->ctrl->ref_count, ptr->ctrl->weak_count);
    }

    printf("\n");
}
