/**
 * ZhC 反射运行时头文件
 *
 * 提供运行时类型信息 (RTTI) 查询的 C 运行时支持
 * 支持：类型名称、大小、字段列表、方法列表、继承关系查询
 *
 * 版本: 1.0.0
 * 作者: 阿福
 * 日期: 2026-04-11
 */

#ifndef ZHC_REFLECTION_H
#define ZHC_REFLECTION_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// 常量定义
// ============================================================================

/* 最大类型名长度 */
#define ZHC_REF_TYPE_NAME_MAX 64

/* 最大字段名长度 */
#define ZHC_REF_FIELD_NAME_MAX 64

/* 最大方法名长度 */
#define ZHC_REF_METHOD_NAME_MAX 64

/* 最大字段数量 */
#define ZHC_REF_MAX_FIELDS 32

/* 最大方法数量 */
#define ZHC_REF_MAX_METHODS 32

/* 最大参数数量 */
#define ZHC_REF_MAX_PARAMS 16

/* 最大接口数量 */
#define ZHC_REF_MAX_INTERFACES 8

// ============================================================================
// 类型定义
// ============================================================================

/**
 * 类型分类枚举
 */
typedef enum ZhCTypeCategory {
    ZHC_TYPE_PRIMITIVE = 0,  /* 基本类型 */
    ZHC_TYPE_CLASS     = 1,  /* 类 */
    ZHC_TYPE_STRUCT    = 2,  /* 结构体 */
    ZHC_TYPE_UNION     = 3,  /* 共用体 */
    ZHC_TYPE_ENUM      = 4,  /* 枚举 */
    ZHC_TYPE_ARRAY     = 5,  /* 数组 */
    ZHC_TYPE_POINTER   = 6,  /* 指针 */
    ZHC_TYPE_FUNCTION  = 7,  /* 函数 */
} ZhCTypeCategory;

/**
 * 字段信息结构
 */
typedef struct ZhCFieldInfo {
    char name[ZHC_REF_FIELD_NAME_MAX];     /* 字段名 */
    char type_name[ZHC_REF_TYPE_NAME_MAX]; /* 类型名 */
    size_t offset;                          /* 内存偏移量 */
    size_t size;                            /* 字段大小 */
    int alignment;                          /* 对齐要求 */
    int is_public;                          /* 是否公开 */
    int is_static;                          /* 是否静态 */
    int is_const;                           /* 是否常量 */
} ZhCFieldInfo;

/**
 * 方法参数信息
 */
typedef struct ZhCParamInfo {
    char name[ZHC_REF_FIELD_NAME_MAX];     /* 参数名 */
    char type_name[ZHC_REF_TYPE_NAME_MAX]; /* 参数类型 */
} ZhCParamInfo;

/**
 * 方法信息结构
 */
typedef struct ZhCMethodInfo {
    char name[ZHC_REF_METHOD_NAME_MAX];        /* 方法名 */
    char return_type[ZHC_REF_TYPE_NAME_MAX];   /* 返回类型 */
    ZhCParamInfo params[ZHC_REF_MAX_PARAMS];   /* 参数列表 */
    int param_count;                            /* 参数数量 */
    int is_static;                              /* 是否静态 */
    int is_virtual;                             /* 是否虚函数 */
    int vtable_index;                           /* 虚表索引 */
} ZhCMethodInfo;

/**
 * 类型信息结构
 */
typedef struct ZhCTypeInfo {
    char name[ZHC_REF_TYPE_NAME_MAX];          /* 类型名 */
    size_t size;                                /* 类型大小 */
    int alignment;                              /* 对齐要求 */
    ZhCTypeCategory category;                   /* 类型分类 */
    
    /* 继承关系 */
    char base_class[ZHC_REF_TYPE_NAME_MAX];    /* 父类名 */
    char interfaces[ZHC_REF_MAX_INTERFACES][ZHC_REF_TYPE_NAME_MAX]; /* 接口列表 */
    int interface_count;                        /* 接口数量 */
    
    /* 字段信息 */
    ZhCFieldInfo fields[ZHC_REF_MAX_FIELDS];   /* 字段列表 */
    int field_count;                            /* 字段数量 */
    
    /* 方法信息 */
    ZhCMethodInfo methods[ZHC_REF_MAX_METHODS]; /* 方法列表 */
    int method_count;                            /* 方法数量 */
    
    /* 枚举常量（仅枚举类型使用） */
    char constant_names[ZHC_REF_MAX_FIELDS][ZHC_REF_FIELD_NAME_MAX];
    int constant_values[ZHC_REF_MAX_FIELDS];
    int constant_count;
} ZhCTypeInfo;

/**
 * 类型注册表项
 */
typedef struct ZhCTypeRegistryEntry {
    char name[ZHC_REF_TYPE_NAME_MAX];
    ZhCTypeInfo* info;
    struct ZhCTypeRegistryEntry* next;
} ZhCTypeRegistryEntry;

// ============================================================================
// 全局类型注册表 API
// ============================================================================

/**
 * 初始化类型注册表
 */
void zhc_reflection_init(void);

/**
 * 清理类型注册表
 */
void zhc_reflection_cleanup(void);

/**
 * 注册类型信息
 *
 * @param info 类型信息指针
 * @return 成功返回 0，失败返回 -1
 */
int zhc_reflection_register_type(const ZhCTypeInfo* info);

/**
 * 按名称查找类型信息
 *
 * @param name 类型名
 * @return 类型信息指针，未找到返回 NULL
 */
const ZhCTypeInfo* zhc_reflection_lookup_type(const char* name);

/**
 * 检查类型是否已注册
 *
 * @param name 类型名
 * @return 已注册返回 1，否则返回 0
 */
int zhc_reflection_is_type_registered(const char* name);

/**
 * 获取所有已注册类型数量
 *
 * @return 类型数量
 */
int zhc_reflection_get_type_count(void);

/**
 * 获取所有已注册类型名称
 *
 * @param names 输出数组
 * @param max_count 最大数量
 * @return 实际类型数量
 */
int zhc_reflection_get_all_type_names(char names[][ZHC_REF_TYPE_NAME_MAX], int max_count);

// ============================================================================
// 类型查询 API
// ============================================================================

/**
 * 获取对象的类型信息
 *
 * @param obj 对象指针
 * @param type_name 对象类型名（如果已知）
 * @return 类型信息指针，失败返回 NULL
 */
const ZhCTypeInfo* zhc_reflection_get_type_info(const void* obj, const char* type_name);

/**
 * 获取类型名称
 *
 * @param type_name 类型名
 * @return 类型名称字符串，失败返回 NULL
 */
const char* zhc_reflection_get_type_name(const char* type_name);

/**
 * 获取类型大小
 *
 * @param type_name 类型名
 * @return 类型大小（字节），失败返回 0
 */
size_t zhc_reflection_get_type_size(const char* type_name);

/**
 * 检查是否是基本类型
 *
 * @param type_name 类型名
 * @return 是基本类型返回 1，否则返回 0
 */
int zhc_reflection_is_primitive(const char* type_name);

/**
 * 获取类型的字段数量
 *
 * @param type_name 类型名
 * @return 字段数量，失败返回 -1
 */
int zhc_reflection_get_field_count(const char* type_name);

/**
 * 获取字段信息
 *
 * @param type_name 类型名
 * @param field_name 字段名
 * @param out_field 输出字段信息
 * @return 成功返回 0，失败返回 -1
 */
int zhc_reflection_get_field(const char* type_name, const char* field_name, ZhCFieldInfo* out_field);

/**
 * 获取字段偏移量
 *
 * @param type_name 类型名
 * @param field_name 字段名
 * @return 字段偏移量，失败返回 -1
 */
size_t zhc_reflection_get_field_offset(const char* type_name, const char* field_name);

/**
 * 动态获取字段值
 *
 * @param obj 对象指针
 * @param type_name 对象类型名
 * @param field_name 字段名
 * @param out_value 输出值缓冲区
 * @param value_size 值缓冲区大小
 * @return 成功返回 0，失败返回 -1
 */
int zhc_reflection_get_field_value(const void* obj, const char* type_name, 
                                    const char* field_name, void* out_value, size_t value_size);

/**
 * 动态设置字段值
 *
 * @param obj 对象指针
 * @param type_name 对象类型名
 * @param field_name 字段名
 * @param value 值指针
 * @param value_size 值大小
 * @return 成功返回 0，失败返回 -1
 */
int zhc_reflection_set_field_value(void* obj, const char* type_name,
                                    const char* field_name, const void* value, size_t value_size);

// ============================================================================
// 继承关系查询 API
// ============================================================================

/**
 * 获取父类名称
 *
 * @param type_name 类型名
 * @return 父类名称，无父类或失败返回 NULL
 */
const char* zhc_reflection_get_base_class(const char* type_name);

/**
 * 检查是否是子类
 *
 * @param derived_type 子类名
 * @param base_type 基类名
 * @return 是子类返回 1，否则返回 0
 */
int zhc_reflection_is_subclass_of(const char* derived_type, const char* base_type);

/**
 * 检查是否可以赋值
 *
 * @param target_type 目标类型名
 * @param source_type 源类型名
 * @return 可赋值返回 1，否则返回 0
 */
int zhc_reflection_is_assignable_from(const char* target_type, const char* source_type);

// ============================================================================
// 方法查询 API
// ============================================================================

/**
 * 获取类型的方法数量
 *
 * @param type_name 类型名
 * @return 方法数量，失败返回 -1
 */
int zhc_reflection_get_method_count(const char* type_name);

/**
 * 获取方法信息
 *
 * @param type_name 类型名
 * @param method_name 方法名
 * @param out_method 输出方法信息
 * @return 成功返回 0，失败返回 -1
 */
int zhc_reflection_get_method(const char* type_name, const char* method_name, ZhCMethodInfo* out_method);

// ============================================================================
// 辅助宏
// ============================================================================

/**
 * 快速获取字段指针
 */
#define ZHC_GET_FIELD_PTR(obj_ptr, type_name, field_name) \
    ((void*)((char*)(obj_ptr) + zhc_reflection_get_field_offset(type_name, field_name)))

/**
 * 快速获取字段值（基本类型）
 */
#define ZHC_GET_FIELD(obj_ptr, type_name, field_name, value_type) \
    (*(value_type*)ZHC_GET_FIELD_PTR(obj_ptr, type_name, field_name))

#ifdef __cplusplus
}
#endif

#endif /* ZHC_REFLECTION_H */
