/**
 * ZhC 智能指针运行时头文件
 *
 * 提供智能指针的 C 运行时支持
 * 支持：独享指针 (unique_ptr)、共享指针 (shared_ptr)、弱指针 (weak_ptr)
 *
 * 版本: 1.0.0
 * 作者: 阿福
 * 日期: 2026-04-10
 */

#ifndef ZHC_SMART_PTR_H
#define ZHC_SMART_PTR_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// 常量定义
// ============================================================================

/* 最大类型名长度 */
#define ZHC_SP_TYPE_NAME_MAX 64

/* 最大变量名长度 */
#define ZHC_SP_VAR_NAME_MAX 128

/* 默认初始引用计数 */
#define ZHC_SP_INIT_REFCOUNT 1

/* 调试标志 */
#ifndef ZHC_SP_DEBUG
#define ZHC_SP_DEBUG 0
#endif

// ============================================================================
// 类型定义
// ============================================================================

/**
 * 智能指针类型枚举
 */
typedef enum ZhCSmartPtrKind {
    ZHC_SP_UNIQUE = 0,   /* 独享指针 - 唯一所有权 */
    ZHC_SP_SHARED = 1,   /* 共享指针 - 引用计数所有权 */
    ZHC_SP_WEAK   = 2    /* 弱指针 - 不影响引用计数 */
} ZhCSmartPtrKind;

/**
 * 控制块 - 管理共享指针的引用计数
 *
 * 每个 shared_ptr 对象共享同一个 ControlBlock。
 * 当强引用计数降为 0 时销毁被管理对象，
 * 当弱引用计数也降为 0 时释放控制块本身。
 */
typedef struct ZhCControlBlock {
    int ref_count;       /* 强引用计数 */
    int weak_count;      /* 弱引用计数 */
    void* object;        /* 被管理的对象指针 */
    char type_name[ZHC_SP_TYPE_NAME_MAX]; /* 对象类型名 */
    void (*destructor)(void*);            /* 自定义析构函数 */
} ZhCControlBlock;

/**
 * 智能指针结构
 *
 * 统一表示独享指针、共享指针和弱指针。
 */
typedef struct ZhCSmartPtr {
    ZhCSmartPtrKind kind;        /* 指针类型 */
    void* ptr;                   /* 独享指针: 直接对象指针; 共享指针: ControlBlock* */
    ZhCControlBlock* ctrl;       /* 控制块引用（共享/弱指针使用） */
    char type_name[ZHC_SP_TYPE_NAME_MAX]; /* 被管理对象类型名 */
    char var_name[ZHC_SP_VAR_NAME_MAX];   /* 变量名（调试用） */
    int is_valid;                /* 指针是否有效（移动后变为无效） */
} ZhCSmartPtr;

// ============================================================================
// 独享指针 (unique_ptr) 操作
// ============================================================================

/**
 * 创建独享指针
 *
 * 分配对象内存并包装为独享指针。
 *
 * @param size 对象大小
 * @param type_name 类型名
 * @param var_name 变量名（调试用）
 * @return 新的独享指针
 */
ZhCSmartPtr* zhc_unique_ptr_create(size_t size, const char* type_name,
                                    const char* var_name);

/**
 * 获取独享指针的对象
 *
 * @param ptr 独享指针
 * @return 被管理对象的指针
 */
void* zhc_unique_ptr_get(ZhCSmartPtr* ptr);

/**
 * 释放独享指针
 *
 * @param ptr 独享指针
 */
void zhc_unique_ptr_release(ZhCSmartPtr* ptr);

/**
 * 移动独享指针
 *
 * 将所有权从 src 转移到 dst，src 变为无效。
 *
 * @param src 源指针
 * @return 被移动的指针（与 src 相同的底层对象）
 */
ZhCSmartPtr* zhc_unique_ptr_move(ZhCSmartPtr* src);

// ============================================================================
// 共享指针 (shared_ptr) 操作
// ============================================================================

/**
 * 创建共享指针
 *
 * 分配对象内存和控制块。
 *
 * @param size 对象大小
 * @param type_name 类型名
 * @param var_name 变量名
 * @return 新的共享指针
 */
ZhCSmartPtr* zhc_shared_ptr_create(size_t size, const char* type_name,
                                    const char* var_name);

/**
 * 从已有指针创建共享指针
 *
 * @param object 已有对象指针
 * @param type_name 类型名
 * @param destructor 析构函数（可为 NULL）
 * @return 新的共享指针
 */
ZhCSmartPtr* zhc_shared_ptr_from_raw(void* object, const char* type_name,
                                      void (*destructor)(void*));

/**
 * 获取共享指针的对象
 */
void* zhc_shared_ptr_get(ZhCSmartPtr* ptr);

/**
 * 增加引用计数（拷贝共享指针时调用）
 */
void zhc_shared_ptr_retain(ZhCSmartPtr* ptr);

/**
 * 减少引用计数（共享指针离开作用域时调用）
 * 引用计数为 0 时自动销毁对象。
 */
void zhc_shared_ptr_release(ZhCSmartPtr* ptr);

/**
 * 获取当前引用计数
 */
int zhc_shared_ptr_use_count(ZhCSmartPtr* ptr);

// ============================================================================
// 弱指针 (weak_ptr) 操作
// ============================================================================

/**
 * 从共享指针创建弱指针
 *
 * @param shared 共享指针
 * @return 新的弱指针
 */
ZhCSmartPtr* zhc_weak_ptr_from_shared(ZhCSmartPtr* shared);

/**
 * 尝试将弱指针提升为共享指针
 *
 * 如果被引用的对象仍然存活，返回一个新的共享指针；
 * 否则返回 NULL。
 *
 * @param weak 弱指针
 * @return 提升后的共享指针，或 NULL
 */
ZhCSmartPtr* zhc_weak_ptr_lock(ZhCSmartPtr* weak);

/**
 * 释放弱指针
 */
void zhc_weak_ptr_release(ZhCSmartPtr* ptr);

/**
 * 检查弱指针是否过期
 */
int zhc_weak_ptr_expired(ZhCSmartPtr* ptr);

// ============================================================================
// 通用操作
// ============================================================================

/**
 * 销毁智能指针（根据类型调用对应的释放函数）
 */
void zhc_smart_ptr_destroy(ZhCSmartPtr* ptr);

/**
 * 获取智能指针指向的对象
 */
void* zhc_smart_ptr_get_object(ZhCSmartPtr* ptr);

/**
 * 检查智能指针是否有效
 */
int zhc_smart_ptr_is_valid(ZhCSmartPtr* ptr);

/**
 * 打印智能指针调试信息
 */
void zhc_smart_ptr_debug_print(ZhCSmartPtr* ptr);

#ifdef __cplusplus
}
#endif

#endif /* ZHC_SMART_PTR_H */
