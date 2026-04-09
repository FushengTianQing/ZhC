/**
 * zhc_container.h - 容器库
 *
 * 提供：
 * - 动态数组
 * - 链表（单向/双向）
 * - 哈希表
 * - 二叉搜索树
 * - 堆
 *
 * 版本: 1.0
 * 依赖: <stdlib.h>, <string.h>, <stdbool.h>
 */

#ifndef ZHC_CONTAINER_H
#define ZHC_CONTAINER_H

#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ================================================================
 * 常量定义
 * ================================================================ */

/** 默认容量 */
#define ZHC_ARRAY_DEFAULT_CAPACITY 16

/** 增长因子 */
#define ZHC_ARRAY_GROWTH_FACTOR 2

/** 默认负载因子 */
#define ZHC_HASH_DEFAULT_LOAD_FACTOR 0.75f

/** 默认哈希表容量 */
#define ZHC_HASH_DEFAULT_CAPACITY 16

/** 链表类型 */
#define ZHC_LIST_SINGLE  1  /** 单向链表 */
#define ZHC_LIST_DOUBLE  2  /** 双向链表 */

/** 遍历类型 */
#define ZHC_TRAVERSAL_PREORDER   1  /** 前序遍历 */
#define ZHC_TRAVERSAL_INORDER    2  /** 中序遍历 */
#define ZHC_TRAVERSAL_POSTORDER  3  /** 后序遍历 */
#define ZHC_TRAVERSAL_LEVELORDER 4  /** 层序遍历 */

/** 树类型 */
#define ZHC_TREE_BST   1  /** 二叉搜索树 */
#define ZHC_TREE_RBT   2  /** 红黑树 */
#define ZHC_TREE_AVL   3  /** AVL 树 */
#define ZHC_TREE_HEAP  4  /** 堆 */

/** 堆类型 */
#define ZHC_HEAP_MIN   1  /** 最小堆 */
#define ZHC_HEAP_MAX   2  /** 最大堆 */

/* ================================================================
 * 动态数组
 * ================================================================ */

/**
 * 动态数组类型
 */
typedef void* zhc_array_t;

/**
 * 动态数组迭代器类型
 */
typedef void* zhc_array_iter_t;

/**
 * zhc_array_create - 创建动态数组
 * @element_size: 元素大小（字节）
 * 返回: 数组句柄，NULL 表示失败
 */
zhc_array_t zhc_array_create(size_t element_size);

/**
 * zhc_array_create_capacity - 创建带初始容量的动态数组
 * @element_size: 元素大小（字节）
 * @capacity: 初始容量
 * 返回: 数组句柄，NULL 表示失败
 */
zhc_array_t zhc_array_create_capacity(size_t element_size, int capacity);

/**
 * zhc_array_destroy - 销毁动态数组
 * @arr: 数组句柄
 */
void zhc_array_destroy(zhc_array_t arr);

/**
 * zhc_array_add - 添加元素到末尾
 * @arr: 数组句柄
 * @element: 元素指针
 * 返回: 0 成功，-1 失败
 */
int zhc_array_add(zhc_array_t arr, const void* element);

/**
 * zhc_array_add_batch - 批量添加元素
 * @arr: 数组句柄
 * @elements: 元素数组指针
 * @count: 元素数量
 * 返回: 成功添加的数量
 */
int zhc_array_add_batch(zhc_array_t arr, const void* elements, int count);

/**
 * zhc_array_insert - 在指定位置插入元素
 * @arr: 数组句柄
 * @index: 插入位置（0 <= index <= size）
 * @element: 元素指针
 * 返回: 0 成功，-1 失败
 */
int zhc_array_insert(zhc_array_t arr, int index, const void* element);

/**
 * zhc_array_remove - 删除指定位置元素
 * @arr: 数组句柄
 * @index: 删除位置
 * 返回: 0 成功，-1 失败
 */
int zhc_array_remove(zhc_array_t arr, int index);

/**
 * zhc_array_get - 获取指定位置元素
 * @arr: 数组句柄
 * @index: 元素位置
 * 返回: 元素指针，NULL 表示无效索引
 */
void* zhc_array_get(zhc_array_t arr, int index);

/**
 * zhc_array_set - 设置指定位置元素
 * @arr: 数组句柄
 * @index: 元素位置
 * @element: 元素指针
 * 返回: 0 成功，-1 失败
 */
int zhc_array_set(zhc_array_t arr, int index, const void* element);

/**
 * zhc_array_size - 获取数组大小
 * @arr: 数组句柄
 * 返回: 元素数量
 */
int zhc_array_size(zhc_array_t arr);

/**
 * zhc_array_capacity - 获取数组容量
 * @arr: 数组句柄
 * 返回: 容量大小
 */
int zhc_array_capacity(zhc_array_t arr);

/**
 * zhc_array_empty - 判断数组是否为空
 * @arr: 数组句柄
 * 返回: true 为空，false 非空
 */
bool zhc_array_empty(zhc_array_t arr);

/**
 * zhc_array_clear - 清空数组
 * @arr: 数组句柄
 */
void zhc_array_clear(zhc_array_t arr);

/**
 * zhc_array_resize - 调整数组大小
 * @arr: 数组句柄
 * @new_size: 新大小
 * 返回: 0 成功，-1 失败
 */
int zhc_array_resize(zhc_array_t arr, int new_size);

/**
 * zhc_array_reserve - 预留容量
 * @arr: 数组句柄
 * @capacity: 预留容量
 * 返回: 0 成功，-1 失败
 */
int zhc_array_reserve(zhc_array_t arr, int capacity);

/**
 * zhc_array_sort - 排序数组
 * @arr: 数组句柄
 * @compare: 比较函数 (a, b) -> a-b
 */
void zhc_array_sort(zhc_array_t arr, int (*compare)(const void*, const void*));

/**
 * zhc_array_bsearch - 二分查找
 * @arr: 数组句柄（必须已排序）
 * @key: 查找键
 * @compare: 比较函数
 * 返回: 找到返回索引，否则返回 -1
 */
int zhc_array_bsearch(zhc_array_t arr, const void* key, int (*compare)(const void*, const void*));

/**
 * zhc_array_foreach - 遍历数组
 * @arr: 数组句柄
 * @callback: 回调函数
 */
void zhc_array_foreach(zhc_array_t arr, void (*callback)(void*));

/* ================================================================
 * 链表
 * ================================================================ */

/**
 * 链表类型
 */
typedef void* zhc_list_t;

/**
 * 链表节点类型
 */
typedef void* zhc_list_node_t;

/**
 * zhc_list_create - 创建链表
 * @element_size: 元素大小（字节）
 * 返回: 链表句柄，NULL 表示失败
 */
zhc_list_t zhc_list_create(size_t element_size);

/**
 * zhc_list_create_type - 创建指定类型链表
 * @element_size: 元素大小（字节）
 * @list_type: 链表类型（ZHC_LIST_SINGLE 或 ZHC_LIST_DOUBLE）
 * 返回: 链表句柄，NULL 表示失败
 */
zhc_list_t zhc_list_create_type(size_t element_size, int list_type);

/**
 * zhc_list_destroy - 销毁链表
 * @list: 链表句柄
 */
void zhc_list_destroy(zhc_list_t list);

/**
 * zhc_list_push_front - 在头部插入
 * @list: 链表句柄
 * @element: 元素指针
 * 返回: 0 成功，-1 失败
 */
int zhc_list_push_front(zhc_list_t list, const void* element);

/**
 * zhc_list_push_back - 在尾部追加
 * @list: 链表句柄
 * @element: 元素指针
 * 返回: 0 成功，-1 失败
 */
int zhc_list_push_back(zhc_list_t list, const void* element);

/**
 * zhc_list_insert - 在指定位置插入
 * @list: 链表句柄
 * @index: 插入位置（0 <= index <= size）
 * @element: 元素指针
 * 返回: 0 成功，-1 失败
 */
int zhc_list_insert(zhc_list_t list, int index, const void* element);

/**
 * zhc_list_remove - 删除指定位置元素
 * @list: 链表句柄
 * @index: 删除位置
 * 返回: 0 成功，-1 失败
 */
int zhc_list_remove(zhc_list_t list, int index);

/**
 * zhc_list_remove_value - 删除第一个匹配的元素
 * @list: 链表句柄
 * @element: 元素指针
 * @compare: 比较函数（可为空）
 * 返回: 0 成功，-1 未找到
 */
int zhc_list_remove_value(zhc_list_t list, const void* element, int (*compare)(const void*, const void*));

/**
 * zhc_list_get - 获取指定位置元素
 * @list: 链表句柄
 * @index: 元素位置
 * 返回: 元素指针，NULL 表示无效索引
 */
void* zhc_list_get(zhc_list_t list, int index);

/**
 * zhc_list_set - 设置指定位置元素
 * @list: 链表句柄
 * @index: 元素位置
 * @element: 元素指针
 * 返回: 0 成功，-1 失败
 */
int zhc_list_set(zhc_list_t list, int index, const void* element);

/**
 * zhc_list_size - 获取链表大小
 * @list: 链表句柄
 * 返回: 元素数量
 */
int zhc_list_size(zhc_list_t list);

/**
 * zhc_list_empty - 判断链表是否为空
 * @list: 链表句柄
 * 返回: true 为空，false 非空
 */
bool zhc_list_empty(zhc_list_t list);

/**
 * zhc_list_clear - 清空链表
 * @list: 链表句柄
 */
void zhc_list_clear(zhc_list_t list);

/**
 * zhc_list_find - 查找元素
 * @list: 链表句柄
 * @element: 元素指针
 * @compare: 比较函数（可为空）
 * 返回: 元素索引，-1 未找到
 */
int zhc_list_find(zhc_list_t list, const void* element, int (*compare)(const void*, const void*));

/**
 * zhc_list_reverse - 反转链表
 * @list: 链表句柄
 * 返回: 0 成功
 */
int zhc_list_reverse(zhc_list_t list);

/**
 * zhc_list_sort - 排序链表
 * @list: 链表句柄
 * @compare: 比较函数
 * 返回: 0 成功
 */
int zhc_list_sort(zhc_list_t list, int (*compare)(const void*, const void*));

/**
 * zhc_list_foreach - 遍历链表
 * @list: 链表句柄
 * @callback: 回调函数
 */
void zhc_list_foreach(zhc_list_t list, void (*callback)(void*));

/**
 * zhc_list_front - 获取头节点
 * @list: 链表句柄
 * 返回: 头节点数据指针
 */
void* zhc_list_front(zhc_list_t list);

/**
 * zhc_list_back - 获取尾节点
 * @list: 链表句柄
 * 返回: 尾节点数据指针
 */
void* zhc_list_back(zhc_list_t list);

/**
 * zhc_list_node_next - 获取下一个节点
 * @node: 节点句柄
 * 返回: 下一个节点句柄
 */
void* zhc_list_node_next(void* node);

/**
 * zhc_list_node_prev - 获取上一个节点
 * @node: 节点句柄
 * 返回: 上一个节点句柄
 */
void* zhc_list_node_prev(void* node);

/**
 * zhc_list_node_data - 获取节点数据
 * @node: 节点句柄
 * 返回: 数据指针
 */
void* zhc_list_node_data(void* node);

/* ================================================================
 * 哈希表
 * ================================================================ */

/**
 * 哈希表类型
 */
typedef void* zhc_hash_t;

/**
 * 哈希表迭代器类型
 */
typedef void* zhc_hash_iter_t;

/**
 * zhc_hash_create - 创建哈希表
 * @initial_capacity: 初始容量（建议为素数）
 * @load_factor: 负载因子（超过此值触发扩容）
 * 返回: 哈希表句柄，NULL 表示失败
 */
zhc_hash_t zhc_hash_create(int initial_capacity, float load_factor);

/**
 * zhc_hash_create_full - 创建完整配置的哈希表
 * @initial_capacity: 初始容量
 * @load_factor: 负载因子
 * @hash_func: 哈希函数（可为空，使用默认）
 * @compare_func: 比较函数（可为空，使用默认）
 * @key_destructor: 键析构函数（可为空）
 * @value_destructor: 值析构函数（可为空）
 * 返回: 哈希表句柄
 */
zhc_hash_t zhc_hash_create_full(int initial_capacity, float load_factor,
                                 unsigned int (*hash_func)(const void*),
                                 int (*compare_func)(const void*, const void*),
                                 void (*key_destructor)(void*),
                                 void (*value_destructor)(void*));

/**
 * zhc_hash_destroy - 销毁哈希表
 * @map: 哈希表句柄
 */
void zhc_hash_destroy(zhc_hash_t map);

/**
 * zhc_hash_set - 设置键值对
 * @map: 哈希表句柄
 * @key: 键指针
 * @value: 值指针
 * 返回: 0 成功，-1 失败
 */
int zhc_hash_set(zhc_hash_t map, const void* key, const void* value);

/**
 * zhc_hash_get - 获取值
 * @map: 哈希表句柄
 * @key: 键指针
 * 返回: 值指针，NULL 表示未找到
 */
void* zhc_hash_get(zhc_hash_t map, const void* key);

/**
 * zhc_hash_remove - 删除键值对
 * @map: 哈希表句柄
 * @key: 键指针
 * 返回: 0 成功，-1 未找到
 */
int zhc_hash_remove(zhc_hash_t map, const void* key);

/**
 * zhc_hash_contains - 判断键是否存在
 * @map: 哈希表句柄
 * @key: 键指针
 * 返回: true 存在，false 不存在
 */
bool zhc_hash_contains(zhc_hash_t map, const void* key);

/**
 * zhc_hash_size - 获取哈希表大小
 * @map: 哈希表句柄
 * 返回: 键值对数量
 */
int zhc_hash_size(zhc_hash_t map);

/**
 * zhc_hash_empty - 判断哈希表是否为空
 * @map: 哈希表句柄
 * 返回: true 为空，false 非空
 */
bool zhc_hash_empty(zhc_hash_t map);

/**
 * zhc_hash_clear - 清空哈希表
 * @map: 哈希表句柄
 */
void zhc_hash_clear(zhc_hash_t map);

/**
 * zhc_hash_keys - 获取所有键
 * @map: 哈希表句柄
 * 返回: 动态数组，包含所有键
 */
zhc_array_t zhc_hash_keys(zhc_hash_t map);

/**
 * zhc_hash_values - 获取所有值
 * @map: 哈希表句柄
 * 返回: 动态数组，包含所有值
 */
zhc_array_t zhc_hash_values(zhc_hash_t map);

/**
 * zhc_hash_foreach - 遍历哈希表
 * @map: 哈希表句柄
 * @callback: 回调函数 (key, value)
 */
void zhc_hash_foreach(zhc_hash_t map, void (*callback)(const void*, void*));

/* ================================================================
 * 二叉搜索树
 * ================================================================ */

/**
 * 二叉树类型
 */
typedef void* zhc_bst_t;

/**
 * 二叉树节点类型
 */
typedef void* zhc_bst_node_t;

/**
 * zhc_bst_create - 创建二叉搜索树
 * @compare: 比较函数（可为空，使用默认）
 * 返回: 树句柄，NULL 表示失败
 */
zhc_bst_t zhc_bst_create(int (*compare)(const void*, const void*));

/**
 * zhc_bst_destroy - 销毁二叉搜索树
 * @tree: 树句柄
 */
void zhc_bst_destroy(zhc_bst_t tree);

/**
 * zhc_bst_insert - 插入键
 * @tree: 树句柄
 * @key: 键指针
 * 返回: 0 成功，-1 失败
 */
int zhc_bst_insert(zhc_bst_t tree, const void* key);

/**
 * zhc_bst_delete - 删除键
 * @tree: 树句柄
 * @key: 键指针
 * 返回: 0 成功，-1 未找到
 */
int zhc_bst_delete(zhc_bst_t tree, const void* key);

/**
 * zhc_bst_search - 查找键
 * @tree: 树句柄
 * @key: 键指针
 * 返回: 键指针，NULL 未找到
 */
void* zhc_bst_search(zhc_bst_t tree, const void* key);

/**
 * zhc_bst_contains - 判断键是否存在
 * @tree: 树句柄
 * @key: 键指针
 * 返回: true 存在，false 不存在
 */
bool zhc_bst_contains(zhc_bst_t tree, const void* key);

/**
 * zhc_bst_min - 获取最小键
 * @tree: 树句柄
 * 返回: 最小键指针，NULL 空树
 */
void* zhc_bst_min(zhc_bst_t tree);

/**
 * zhc_bst_max - 获取最大键
 * @tree: 树句柄
 * 返回: 最大键指针，NULL 空树
 */
void* zhc_bst_max(zhc_bst_t tree);

/**
 * zhc_bst_size - 获取树大小
 * @tree: 树句柄
 * 返回: 节点数量
 */
int zhc_bst_size(zhc_bst_t tree);

/**
 * zhc_bst_empty - 判断树是否为空
 * @tree: 树句柄
 * 返回: true 为空，false 非空
 */
bool zhc_bst_empty(zhc_bst_t tree);

/**
 * zhc_bst_clear - 清空树
 * @tree: 树句柄
 */
void zhc_bst_clear(zhc_bst_t tree);

/**
 * zhc_bst_height - 获取树高度
 * @tree: 树句柄
 * 返回: 高度（空树为 0，单节点为 1）
 */
int zhc_bst_height(zhc_bst_t tree);

/**
 * zhc_bst_inorder - 中序遍历
 * @tree: 树句柄
 * @visit: 访问函数
 */
void zhc_bst_inorder(zhc_bst_t tree, void (*visit)(void*));

/**
 * zhc_bst_preorder - 前序遍历
 * @tree: 树句柄
 * @visit: 访问函数
 */
void zhc_bst_preorder(zhc_bst_t tree, void (*visit)(void*));

/**
 * zhc_bst_postorder - 后序遍历
 * @tree: 树句柄
 * @visit: 访问函数
 */
void zhc_bst_postorder(zhc_bst_t tree, void (*visit)(void*));

/**
 * zhc_bst_levelorder - 层序遍历
 * @tree: 树句柄
 * @visit: 访问函数
 */
void zhc_bst_levelorder(zhc_bst_t tree, void (*visit)(void*));

/**
 * zhc_bst_node_key - 获取节点键
 * @node: 节点句柄
 * 返回: 键指针
 */
void* zhc_bst_node_key(void* node);

/**
 * zhc_bst_node_left - 获取左子树
 * @node: 节点句柄
 * 返回: 左子节点句柄
 */
void* zhc_bst_node_left(void* node);

/**
 * zhc_bst_node_right - 获取右子树
 * @node: 节点句柄
 * 返回: 右子节点句柄
 */
void* zhc_bst_node_right(void* node);

/* ================================================================
 * 堆
 * ================================================================ */

/**
 * 堆类型
 */
typedef void* zhc_heap_t;

/**
 * zhc_heap_create - 创建堆
 * @heap_type: 堆类型（ZHC_HEAP_MIN 或 ZHC_HEAP_MAX）
 * @compare: 比较函数
 * 返回: 堆句柄，NULL 表示失败
 */
zhc_heap_t zhc_heap_create(int heap_type, int (*compare)(const void*, const void*));

/**
 * zhc_heap_destroy - 销毁堆
 * @heap: 堆句柄
 */
void zhc_heap_destroy(zhc_heap_t heap);

/**
 * zhc_heap_push - 推入元素
 * @heap: 堆句柄
 * @element: 元素指针
 * 返回: 0 成功，-1 失败
 */
int zhc_heap_push(zhc_heap_t heap, const void* element);

/**
 * zhc_heap_pop - 弹出堆顶元素
 * @heap: 堆句柄
 * @output: 输出缓冲区（可为 NULL）
 * 返回: 0 成功，-1 空堆
 */
int zhc_heap_pop(zhc_heap_t heap, void* output);

/**
 * zhc_heap_top - 查看堆顶元素
 * @heap: 堆句柄
 * 返回: 堆顶元素指针，NULL 空堆
 */
void* zhc_heap_top(zhc_heap_t heap);

/**
 * zhc_heap_size - 获取堆大小
 * @heap: 堆句柄
 * 返回: 元素数量
 */
int zhc_heap_size(zhc_heap_t heap);

/**
 * zhc_heap_empty - 判断堆是否为空
 * @heap: 堆句柄
 * 返回: true 为空，false 非空
 */
bool zhc_heap_empty(zhc_heap_t heap);

/* ================================================================
 * 实现
 * ================================================================ */

#ifdef ZHC_CONTAINER_IMPLEMENTATION

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ---------- 动态数组实现 ---------- */

typedef struct {
    void** data;
    int size;
    int capacity;
    size_t element_size;
} zhc_array_impl_t;

#define ZHC_ARRAY(arr) ((zhc_array_impl_t*)(arr))

zhc_array_t zhc_array_create(size_t element_size) {
    return zhc_array_create_capacity(element_size, ZHC_ARRAY_DEFAULT_CAPACITY);
}

zhc_array_t zhc_array_create_capacity(size_t element_size, int capacity) {
    zhc_array_impl_t* arr = (zhc_array_impl_t*)malloc(sizeof(zhc_array_impl_t));
    if (!arr) return NULL;

    arr->data = (void**)malloc(capacity * sizeof(void*));
    if (!arr->data) {
        free(arr);
        return NULL;
    }

    arr->size = 0;
    arr->capacity = capacity;
    arr->element_size = element_size;
    return arr;
}

void zhc_array_destroy(zhc_array_t arr) {
    if (!arr) return;
    zhc_array_impl_t* a = ZHC_ARRAY(arr);
    for (int i = 0; i < a->size; i++) {
        free(a->data[i]);
    }
    free(a->data);
    free(a);
}

int zhc_array_add(zhc_array_t arr, const void* element) {
    if (!arr || !element) return -1;
    zhc_array_impl_t* a = ZHC_ARRAY(arr);

    if (a->size >= a->capacity) {
        int new_cap = a->capacity * ZHC_ARRAY_GROWTH_FACTOR;
        void** new_data = (void**)realloc(a->data, new_cap * sizeof(void*));
        if (!new_data) return -1;
        a->data = new_data;
        a->capacity = new_cap;
    }

    void* copy = malloc(a->element_size);
    if (!copy) return -1;
    memcpy(copy, element, a->element_size);
    a->data[a->size++] = copy;
    return 0;
}

int zhc_array_add_batch(zhc_array_t arr, const void* elements, int count) {
    if (!arr || !elements || count <= 0) return -1;
    int added = 0;
    const char* p = (const char*)elements;
    for (int i = 0; i < count; i++) {
        if (zhc_array_add(arr, p) == 0) {
            added++;
            p += ZHC_ARRAY(arr)->element_size;
        } else {
            break;
        }
    }
    return added;
}

int zhc_array_insert(zhc_array_t arr, int index, const void* element) {
    if (!arr || !element) return -1;
    zhc_array_impl_t* a = ZHC_ARRAY(arr);
    if (index < 0 || index > a->size) return -1;

    if (a->size >= a->capacity) {
        int new_cap = a->capacity * ZHC_ARRAY_GROWTH_FACTOR;
        void** new_data = (void**)realloc(a->data, new_cap * sizeof(void*));
        if (!new_data) return -1;
        a->data = new_data;
        a->capacity = new_cap;
    }

    memmove(a->data + index + 1, a->data + index, (a->size - index) * sizeof(void*));

    void* copy = malloc(a->element_size);
    if (!copy) return -1;
    memcpy(copy, element, a->element_size);
    a->data[index] = copy;
    a->size++;
    return 0;
}

int zhc_array_remove(zhc_array_t arr, int index) {
    if (!arr) return -1;
    zhc_array_impl_t* a = ZHC_ARRAY(arr);
    if (index < 0 || index >= a->size) return -1;

    free(a->data[index]);
    memmove(a->data + index, a->data + index + 1, (a->size - index - 1) * sizeof(void*));
    a->size--;
    return 0;
}

void* zhc_array_get(zhc_array_t arr, int index) {
    if (!arr) return NULL;
    zhc_array_impl_t* a = ZHC_ARRAY(arr);
    if (index < 0 || index >= a->size) return NULL;
    return a->data[index];
}

int zhc_array_set(zhc_array_t arr, int index, const void* element) {
    if (!arr || !element) return -1;
    zhc_array_impl_t* a = ZHC_ARRAY(arr);
    if (index < 0 || index >= a->size) return -1;
    memcpy(a->data[index], element, a->element_size);
    return 0;
}

int zhc_array_size(zhc_array_t arr) {
    if (!arr) return 0;
    return ZHC_ARRAY(arr)->size;
}

int zhc_array_capacity(zhc_array_t arr) {
    if (!arr) return 0;
    return ZHC_ARRAY(arr)->capacity;
}

bool zhc_array_empty(zhc_array_t arr) {
    return !arr || ZHC_ARRAY(arr)->size == 0;
}

void zhc_array_clear(zhc_array_t arr) {
    if (!arr) return;
    zhc_array_impl_t* a = ZHC_ARRAY(arr);
    for (int i = 0; i < a->size; i++) {
        free(a->data[i]);
        a->data[i] = NULL;
    }
    a->size = 0;
}

int zhc_array_resize(zhc_array_t arr, int new_size) {
    if (!arr || new_size < 0) return -1;
    zhc_array_impl_t* a = ZHC_ARRAY(arr);

    if (new_size > a->size) {
        for (int i = a->size; i < new_size; i++) {
            a->data[i] = malloc(a->element_size);
            if (!a->data[i]) return -1;
        }
    } else if (new_size < a->size) {
        for (int i = new_size; i < a->size; i++) {
            free(a->data[i]);
        }
    }

    a->size = new_size;
    return 0;
}

int zhc_array_reserve(zhc_array_t arr, int capacity) {
    if (!arr || capacity <= 0) return -1;
    zhc_array_impl_t* a = ZHC_ARRAY(arr);

    if (capacity > a->capacity) {
        void** new_data = (void**)realloc(a->data, capacity * sizeof(void*));
        if (!new_data) return -1;
        a->data = new_data;
        a->capacity = capacity;
    }
    return 0;
}

void zhc_array_sort(zhc_array_t arr, int (*compare)(const void*, const void*)) {
    if (!arr || !compare) return;
    qsort(ZHC_ARRAY(arr)->data, ZHC_ARRAY(arr)->size, sizeof(void*), compare);
}

int zhc_array_bsearch(zhc_array_t arr, const void* key, int (*compare)(const void*, const void*)) {
    if (!arr || !key || !compare) return -1;
    zhc_array_impl_t* a = ZHC_ARRAY(arr);
    void** result = (void**)bsearch(key, a->data, a->size, sizeof(void*), compare);
    if (!result) return -1;
    return (int)(result - a->data);
}

void zhc_array_foreach(zhc_array_t arr, void (*callback)(void*)) {
    if (!arr || !callback) return;
    zhc_array_impl_t* a = ZHC_ARRAY(arr);
    for (int i = 0; i < a->size; i++) {
        callback(a->data[i]);
    }
}

/* ---------- 链表实现 ---------- */

typedef struct zhc_list_node_impl {
    void* data;
    struct zhc_list_node_impl* next;
    struct zhc_list_node_impl* prev;
} zhc_list_node_impl_t;

typedef struct {
    zhc_list_node_impl_t* head;
    zhc_list_node_impl_t* tail;
    int size;
    int list_type;  /* ZHC_LIST_SINGLE or ZHC_LIST_DOUBLE */
    size_t element_size;
} zhc_list_impl_t;

#define ZHC_LIST(list) ((zhc_list_impl_t*)(list))
#define ZHC_LIST_NODE(node) ((zhc_list_node_impl_t*)(node))

zhc_list_t zhc_list_create(size_t element_size) {
    return zhc_list_create_type(element_size, ZHC_LIST_DOUBLE);
}

zhc_list_t zhc_list_create_type(size_t element_size, int list_type) {
    zhc_list_impl_t* list = (zhc_list_impl_t*)malloc(sizeof(zhc_list_impl_t));
    if (!list) return NULL;

    list->head = NULL;
    list->tail = NULL;
    list->size = 0;
    list->list_type = list_type;
    list->element_size = element_size;
    return list;
}

void zhc_list_destroy(zhc_list_t list) {
    if (!list) return;
    zhc_list_impl_t* l = ZHC_LIST(list);
    zhc_list_node_impl_t* current = l->head;
    while (current) {
        zhc_list_node_impl_t* next = current->next;
        free(current->data);
        free(current);
        current = next;
    }
    free(list);
}

int zhc_list_push_front(zhc_list_t list, const void* element) {
    if (!list || !element) return -1;
    zhc_list_impl_t* l = ZHC_LIST(list);

    zhc_list_node_impl_t* node = (zhc_list_node_impl_t*)malloc(sizeof(zhc_list_node_impl_t));
    if (!node) return -1;

    node->data = malloc(l->element_size);
    if (!node->data) {
        free(node);
        return -1;
    }
    memcpy(node->data, element, l->element_size);
    node->prev = NULL;
    node->next = l->head;

    if (l->head) {
        l->head->prev = node;
    }
    l->head = node;

    if (!l->tail) {
        l->tail = node;
    }

    l->size++;
    return 0;
}

int zhc_list_push_back(zhc_list_t list, const void* element) {
    if (!list || !element) return -1;
    zhc_list_impl_t* l = ZHC_LIST(list);

    zhc_list_node_impl_t* node = (zhc_list_node_impl_t*)malloc(sizeof(zhc_list_node_impl_t));
    if (!node) return -1;

    node->data = malloc(l->element_size);
    if (!node->data) {
        free(node);
        return -1;
    }
    memcpy(node->data, element, l->element_size);
    node->next = NULL;
    node->prev = l->tail;

    if (l->tail) {
        l->tail->next = node;
    }
    l->tail = node;

    if (!l->head) {
        l->head = node;
    }

    l->size++;
    return 0;
}

int zhc_list_insert(zhc_list_t list, int index, const void* element) {
    if (!list || !element) return -1;
    zhc_list_impl_t* l = ZHC_LIST(list);
    if (index < 0 || index > l->size) return -1;

    if (index == 0) return zhc_list_push_front(list, element);
    if (index == l->size) return zhc_list_push_back(list, element);

    zhc_list_node_impl_t* current;
    if (index < l->size / 2) {
        current = l->head;
        for (int i = 0; i < index; i++) {
            current = current->next;
        }
    } else {
        current = l->tail;
        for (int i = l->size - 1; i > index; i--) {
            current = current->prev;
        }
    }

    zhc_list_node_impl_t* node = (zhc_list_node_impl_t*)malloc(sizeof(zhc_list_node_impl_t));
    if (!node) return -1;

    node->data = malloc(l->element_size);
    if (!node->data) {
        free(node);
        return -1;
    }
    memcpy(node->data, element, l->element_size);

    node->next = current;
    node->prev = current->prev;
    if (current->prev) {
        current->prev->next = node;
    }
    current->prev = node;

    l->size++;
    return 0;
}

int zhc_list_remove(zhc_list_t list, int index) {
    if (!list) return -1;
    zhc_list_impl_t* l = ZHC_LIST(list);
    if (index < 0 || index >= l->size) return -1;

    zhc_list_node_impl_t* current;
    if (index < l->size / 2) {
        current = l->head;
        for (int i = 0; i < index; i++) {
            current = current->next;
        }
    } else {
        current = l->tail;
        for (int i = l->size - 1; i > index; i--) {
            current = current->prev;
        }
    }

    if (current->prev) {
        current->prev->next = current->next;
    } else {
        l->head = current->next;
    }

    if (current->next) {
        current->next->prev = current->prev;
    } else {
        l->tail = current->prev;
    }

    free(current->data);
    free(current);
    l->size--;
    return 0;
}

int zhc_list_remove_value(zhc_list_t list, const void* element, int (*compare)(const void*, const void*)) {
    if (!list || !element) return -1;
    zhc_list_impl_t* l = ZHC_LIST(list);
    zhc_list_node_impl_t* current = l->head;
    int index = 0;

    while (current) {
        int cmp = compare ? compare(current->data, element) : memcmp(current->data, element, l->element_size);
        if (cmp == 0) {
            return zhc_list_remove(list, index);
        }
        current = current->next;
        index++;
    }
    return -1;
}

void* zhc_list_get(zhc_list_t list, int index) {
    if (!list) return NULL;
    zhc_list_impl_t* l = ZHC_LIST(list);
    if (index < 0 || index >= l->size) return NULL;

    zhc_list_node_impl_t* current;
    if (index < l->size / 2) {
        current = l->head;
        for (int i = 0; i < index; i++) {
            current = current->next;
        }
    } else {
        current = l->tail;
        for (int i = l->size - 1; i > index; i--) {
            current = current->prev;
        }
    }
    return current->data;
}

int zhc_list_set(zhc_list_t list, int index, const void* element) {
    if (!list || !element) return -1;
    void* data = zhc_list_get(list, index);
    if (!data) return -1;
    zhc_list_impl_t* l = ZHC_LIST(list);
    memcpy(data, element, l->element_size);
    return 0;
}

int zhc_list_size(zhc_list_t list) {
    if (!list) return 0;
    return ZHC_LIST(list)->size;
}

bool zhc_list_empty(zhc_list_t list) {
    return !list || ZHC_LIST(list)->size == 0;
}

void zhc_list_clear(zhc_list_t list) {
    if (!list) return;
    zhc_list_impl_t* l = ZHC_LIST(list);
    zhc_list_node_impl_t* current = l->head;
    while (current) {
        zhc_list_node_impl_t* next = current->next;
        free(current->data);
        free(current);
        current = next;
    }
    l->head = NULL;
    l->tail = NULL;
    l->size = 0;
}

int zhc_list_find(zhc_list_t list, const void* element, int (*compare)(const void*, const void*)) {
    if (!list || !element) return -1;
    zhc_list_impl_t* l = ZHC_LIST(list);
    zhc_list_node_impl_t* current = l->head;
    int index = 0;

    while (current) {
        int cmp = compare ? compare(current->data, element) : memcmp(current->data, element, l->element_size);
        if (cmp == 0) {
            return index;
        }
        current = current->next;
        index++;
    }
    return -1;
}

int zhc_list_reverse(zhc_list_t list) {
    if (!list) return -1;
    zhc_list_impl_t* l = ZHC_LIST(list);
    zhc_list_node_impl_t* current = l->head;
    zhc_list_node_impl_t* temp = NULL;

    l->tail = l->head;

    while (current) {
        temp = current->prev;
        current->prev = current->next;
        current->next = temp;
        current = current->prev;
    }

    if (temp) {
        l->head = temp->prev;
    }
    return 0;
}

int zhc_list_sort(zhc_list_t list, int (*compare)(const void*, const void*)) {
    if (!list || !compare) return -1;
    zhc_list_impl_t* l = ZHC_LIST(list);
    if (l->size <= 1) return 0;

    /* 收集到数组 */
    void** arr = (void**)malloc(l->size * sizeof(void*));
    if (!arr) return -1;

    zhc_list_node_impl_t* current = l->head;
    for (int i = 0; i < l->size; i++) {
        arr[i] = current->data;
        current = current->next;
    }

    qsort(arr, l->size, sizeof(void*), compare);

    /* 写回链表 */
    current = l->head;
    for (int i = 0; i < l->size; i++) {
        current->data = arr[i];
        current = current->next;
    }

    free(arr);
    return 0;
}

void zhc_list_foreach(zhc_list_t list, void (*callback)(void*)) {
    if (!list || !callback) return;
    zhc_list_impl_t* l = ZHC_LIST(list);
    zhc_list_node_impl_t* current = l->head;
    while (current) {
        callback(current->data);
        current = current->next;
    }
}

void* zhc_list_front(zhc_list_t list) {
    if (!list) return NULL;
    zhc_list_impl_t* l = ZHC_LIST(list);
    return l->head ? l->head->data : NULL;
}

void* zhc_list_back(zhc_list_t list) {
    if (!list) return NULL;
    zhc_list_impl_t* l = ZHC_LIST(list);
    return l->tail ? l->tail->data : NULL;
}

void* zhc_list_node_next(void* node) {
    if (!node) return NULL;
    return ZHC_LIST_NODE(node)->next;
}

void* zhc_list_node_prev(void* node) {
    if (!node) return NULL;
    return ZHC_LIST_NODE(node)->prev;
}

void* zhc_list_node_data(void* node) {
    if (!node) return NULL;
    return ZHC_LIST_NODE(node)->data;
}

/* ---------- 哈希表实现 ---------- */

typedef struct zhc_hash_entry_impl {
    void* key;
    void* value;
    struct zhc_hash_entry_impl* next;
} zhc_hash_entry_impl_t;

typedef struct {
    zhc_hash_entry_impl_t** buckets;
    int capacity;
    int size;
    float load_factor;
    unsigned int (*hash_func)(const void*);
    int (*compare_func)(const void*, const void*);
    void (*key_destructor)(void*);
    void (*value_destructor)(void*);
} zhc_hash_impl_t;

#define ZHC_HASH(map) ((zhc_hash_impl_t*)(map))

static unsigned int default_hash(const void* key) {
    const char* str = (const char*)key;
    unsigned int hash = 5381;
    int c;
    while ((c = *str++)) {
        hash = ((hash << 5) + hash) + c;
    }
    return hash;
}

static int default_compare(const void* a, const void* b) {
    return strcmp((const char*)a, (const char*)b);
}

static void zhc_hash_rehash(zhc_hash_impl_t* h) {
    int old_capacity = h->capacity;
    zhc_hash_entry_impl_t** old_buckets = h->buckets;

    h->capacity *= 2;
    h->buckets = (zhc_hash_entry_impl_t**)calloc(h->capacity, sizeof(zhc_hash_entry_impl_t*));

    for (int i = 0; i < old_capacity; i++) {
        zhc_hash_entry_impl_t* entry = old_buckets[i];
        while (entry) {
            zhc_hash_entry_impl_t* next = entry->next;
            unsigned int hash = h->hash_func(entry->key) % h->capacity;
            entry->next = h->buckets[hash];
            h->buckets[hash] = entry;
            entry = next;
        }
    }
    free(old_buckets);
}

zhc_hash_t zhc_hash_create(int initial_capacity, float load_factor) {
    return zhc_hash_create_full(initial_capacity, load_factor, NULL, NULL, NULL, NULL);
}

zhc_hash_t zhc_hash_create_full(int initial_capacity, float load_factor,
                                 unsigned int (*hash_func)(const void*),
                                 int (*compare_func)(const void*, const void*),
                                 void (*key_destructor)(void*),
                                 void (*value_destructor)(void*)) {
    if (initial_capacity <= 0) initial_capacity = ZHC_HASH_DEFAULT_CAPACITY;
    if (load_factor <= 0) load_factor = ZHC_HASH_DEFAULT_LOAD_FACTOR;

    zhc_hash_impl_t* map = (zhc_hash_impl_t*)malloc(sizeof(zhc_hash_impl_t));
    if (!map) return NULL;

    map->buckets = (zhc_hash_entry_impl_t**)calloc(initial_capacity, sizeof(zhc_hash_entry_impl_t*));
    if (!map->buckets) {
        free(map);
        return NULL;
    }

    map->capacity = initial_capacity;
    map->size = 0;
    map->load_factor = load_factor;
    map->hash_func = hash_func ? hash_func : default_hash;
    map->compare_func = compare_func ? compare_func : default_compare;
    map->key_destructor = key_destructor;
    map->value_destructor = value_destructor;

    return map;
}

void zhc_hash_destroy(zhc_hash_t map) {
    if (!map) return;
    zhc_hash_impl_t* m = ZHC_HASH(map);

    for (int i = 0; i < m->capacity; i++) {
        zhc_hash_entry_impl_t* entry = m->buckets[i];
        while (entry) {
            zhc_hash_entry_impl_t* next = entry->next;
            if (m->key_destructor) m->key_destructor(entry->key);
            if (m->value_destructor) m->value_destructor(entry->value);
            free(entry);
            entry = next;
        }
    }
    free(m->buckets);
    free(m);
}

int zhc_hash_set(zhc_hash_t map, const void* key, const void* value) {
    if (!map || !key) return -1;
    zhc_hash_impl_t* m = ZHC_HASH(map);

    if ((float)m->size / m->capacity > m->load_factor) {
        zhc_hash_rehash(m);
    }

    unsigned int hash = m->hash_func(key) % m->capacity;
    zhc_hash_entry_impl_t* entry = m->buckets[hash];

    /* 查找是否已存在 */
    while (entry) {
        if (m->compare_func(entry->key, key) == 0) {
            if (m->value_destructor) m->value_destructor(entry->value);
            entry->value = (void*)value;
            return 0;
        }
        entry = entry->next;
    }

    /* 插入新条目 */
    entry = (zhc_hash_entry_impl_t*)malloc(sizeof(zhc_hash_entry_impl_t));
    if (!entry) return -1;

    entry->key = (void*)key;
    entry->value = (void*)value;
    entry->next = m->buckets[hash];
    m->buckets[hash] = entry;
    m->size++;

    return 0;
}

void* zhc_hash_get(zhc_hash_t map, const void* key) {
    if (!map || !key) return NULL;
    zhc_hash_impl_t* m = ZHC_HASH(map);

    unsigned int hash = m->hash_func(key) % m->capacity;
    zhc_hash_entry_impl_t* entry = m->buckets[hash];

    while (entry) {
        if (m->compare_func(entry->key, key) == 0) {
            return entry->value;
        }
        entry = entry->next;
    }
    return NULL;
}

int zhc_hash_remove(zhc_hash_t map, const void* key) {
    if (!map || !key) return -1;
    zhc_hash_impl_t* m = ZHC_HASH(map);

    unsigned int hash = m->hash_func(key) % m->capacity;
    zhc_hash_entry_impl_t* entry = m->buckets[hash];
    zhc_hash_entry_impl_t* prev = NULL;

    while (entry) {
        if (m->compare_func(entry->key, key) == 0) {
            if (prev) {
                prev->next = entry->next;
            } else {
                m->buckets[hash] = entry->next;
            }
            if (m->key_destructor) m->key_destructor(entry->key);
            if (m->value_destructor) m->value_destructor(entry->value);
            free(entry);
            m->size--;
            return 0;
        }
        prev = entry;
        entry = entry->next;
    }
    return -1;
}

bool zhc_hash_contains(zhc_hash_t map, const void* key) {
    return zhc_hash_get(map, key) != NULL;
}

int zhc_hash_size(zhc_hash_t map) {
    if (!map) return 0;
    return ZHC_HASH(map)->size;
}

bool zhc_hash_empty(zhc_hash_t map) {
    return !map || ZHC_HASH(map)->size == 0;
}

void zhc_hash_clear(zhc_hash_t map) {
    if (!map) return;
    zhc_hash_impl_t* m = ZHC_HASH(map);

    for (int i = 0; i < m->capacity; i++) {
        zhc_hash_entry_impl_t* entry = m->buckets[i];
        while (entry) {
            zhc_hash_entry_impl_t* next = entry->next;
            if (m->key_destructor) m->key_destructor(entry->key);
            if (m->value_destructor) m->value_destructor(entry->value);
            free(entry);
            entry = next;
        }
        m->buckets[i] = NULL;
    }
    m->size = 0;
}

zhc_array_t zhc_hash_keys(zhc_hash_t map) {
    if (!map) return NULL;
    zhc_hash_impl_t* m = ZHC_HASH(map);
    zhc_array_t arr = zhc_array_create(sizeof(void*));

    for (int i = 0; i < m->capacity; i++) {
        zhc_hash_entry_impl_t* entry = m->buckets[i];
        while (entry) {
            zhc_array_add(arr, &entry->key);
            entry = entry->next;
        }
    }
    return arr;
}

zhc_array_t zhc_hash_values(zhc_hash_t map) {
    if (!map) return NULL;
    zhc_hash_impl_t* m = ZHC_HASH(map);
    zhc_array_t arr = zhc_array_create(sizeof(void*));

    for (int i = 0; i < m->capacity; i++) {
        zhc_hash_entry_impl_t* entry = m->buckets[i];
        while (entry) {
            zhc_array_add(arr, &entry->value);
            entry = entry->next;
        }
    }
    return arr;
}

void zhc_hash_foreach(zhc_hash_t map, void (*callback)(const void*, void*)) {
    if (!map || !callback) return;
    zhc_hash_impl_t* m = ZHC_HASH(map);

    for (int i = 0; i < m->capacity; i++) {
        zhc_hash_entry_impl_t* entry = m->buckets[i];
        while (entry) {
            callback(entry->key, entry->value);
            entry = entry->next;
        }
    }
}

/* ---------- 二叉搜索树实现 ---------- */

typedef struct zhc_bst_node_impl {
    void* key;
    struct zhc_bst_node_impl* left;
    struct zhc_bst_node_impl* right;
} zhc_bst_node_impl_t;

typedef struct {
    zhc_bst_node_impl_t* root;
    int size;
    int (*compare)(const void*, const void*);
} zhc_bst_impl_t;

#define ZHC_BST(tree) ((zhc_bst_impl_t*)(tree))
#define ZHC_BST_NODE(node) ((zhc_bst_node_impl_t*)(node))

static int default_bst_compare(const void* a, const void* b) {
    if (*(int*)a < *(int*)b) return -1;
    if (*(int*)a > *(int*)b) return 1;
    return 0;
}

static zhc_bst_node_impl_t* bst_min_node(zhc_bst_node_impl_t* node) {
    while (node && node->left) {
        node = node->left;
    }
    return node;
}

static zhc_bst_node_impl_t* bst_max_node(zhc_bst_node_impl_t* node) {
    while (node && node->right) {
        node = node->right;
    }
    return node;
}

static void bst_destroy_rec(zhc_bst_node_impl_t* node) {
    if (!node) return;
    bst_destroy_rec(node->left);
    bst_destroy_rec(node->right);
    free(node);
}

static void bst_inorder_rec(zhc_bst_node_impl_t* node, void (*visit)(void*)) {
    if (!node) return;
    bst_inorder_rec(node->left, visit);
    visit(node->key);
    bst_inorder_rec(node->right, visit);
}

static void bst_preorder_rec(zhc_bst_node_impl_t* node, void (*visit)(void*)) {
    if (!node) return;
    visit(node->key);
    bst_preorder_rec(node->left, visit);
    bst_preorder_rec(node->right, visit);
}

static void bst_postorder_rec(zhc_bst_node_impl_t* node, void (*visit)(void*)) {
    if (!node) return;
    bst_postorder_rec(node->left, visit);
    bst_postorder_rec(node->right, visit);
    visit(node->key);
}

static int bst_height_rec(zhc_bst_node_impl_t* node) {
    if (!node) return 0;
    int left_h = bst_height_rec(node->left);
    int right_h = bst_height_rec(node->right);
    return 1 + (left_h > right_h ? left_h : right_h);
}

zhc_bst_t zhc_bst_create(int (*compare)(const void*, const void*)) {
    zhc_bst_impl_t* tree = (zhc_bst_impl_t*)malloc(sizeof(zhc_bst_impl_t));
    if (!tree) return NULL;

    tree->root = NULL;
    tree->size = 0;
    tree->compare = compare ? compare : default_bst_compare;
    return tree;
}

void zhc_bst_destroy(zhc_bst_t tree) {
    if (!tree) return;
    bst_destroy_rec(ZHC_BST(tree)->root);
    free(tree);
}

int zhc_bst_insert(zhc_bst_t tree, const void* key) {
    if (!tree || !key) return -1;
    zhc_bst_impl_t* t = ZHC_BST(tree);

    zhc_bst_node_impl_t* new_node = (zhc_bst_node_impl_t*)malloc(sizeof(zhc_bst_node_impl_t));
    if (!new_node) return -1;

    new_node->key = (void*)key;
    new_node->left = NULL;
    new_node->right = NULL;

    if (!t->root) {
        t->root = new_node;
        t->size++;
        return 0;
    }

    zhc_bst_node_impl_t* current = t->root;
    while (1) {
        int cmp = t->compare(key, current->key);
        if (cmp < 0) {
            if (!current->left) {
                current->left = new_node;
                break;
            }
            current = current->left;
        } else if (cmp > 0) {
            if (!current->right) {
                current->right = new_node;
                break;
            }
            current = current->right;
        } else {
            /* 键已存在，替换 */
            free(new_node);
            return 0;
        }
    }
    t->size++;
    return 0;
}

int zhc_bst_delete(zhc_bst_t tree, const void* key) {
    if (!tree || !key) return -1;
    zhc_bst_impl_t* t = ZHC_BST(tree);

    zhc_bst_node_impl_t* current = t->root;
    zhc_bst_node_impl_t* parent = NULL;

    while (current) {
        int cmp = t->compare(key, current->key);
        if (cmp == 0) break;
        parent = current;
        current = cmp < 0 ? current->left : current->right;
    }

    if (!current) return -1;  /* 未找到 */

    /* 处理三种情况 */
    if (!current->left && !current->right) {
        /* 叶子节点 */
        if (!parent) {
            t->root = NULL;
        } else if (parent->left == current) {
            parent->left = NULL;
        } else {
            parent->right = NULL;
        }
    } else if (!current->left || !current->right) {
        /* 只有一个子节点 */
        zhc_bst_node_impl_t* child = current->left ? current->left : current->right;
        if (!parent) {
            t->root = child;
        } else if (parent->left == current) {
            parent->left = child;
        } else {
            parent->right = child;
        }
    } else {
        /* 两个子节点：找后继 */
        zhc_bst_node_impl_t* successor = bst_min_node(current->right);
        void* succ_key = successor->key;

        zhc_bst_delete(tree, succ_key);
        current->key = succ_key;
        return 0;
    }

    free(current);
    t->size--;
    return 0;
}

void* zhc_bst_search(zhc_bst_t tree, const void* key) {
    if (!tree || !key) return NULL;
    zhc_bst_impl_t* t = ZHC_BST(tree);

    zhc_bst_node_impl_t* current = t->root;
    while (current) {
        int cmp = t->compare(key, current->key);
        if (cmp == 0) return current->key;
        current = cmp < 0 ? current->left : current->right;
    }
    return NULL;
}

bool zhc_bst_contains(zhc_bst_t tree, const void* key) {
    return zhc_bst_search(tree, key) != NULL;
}

void* zhc_bst_min(zhc_bst_t tree) {
    if (!tree) return NULL;
    zhc_bst_node_impl_t* node = ZHC_BST(tree)->root;
    if (!node) return NULL;
    return bst_min_node(node)->key;
}

void* zhc_bst_max(zhc_bst_t tree) {
    if (!tree) return NULL;
    zhc_bst_node_impl_t* node = ZHC_BST(tree)->root;
    if (!node) return NULL;
    return bst_max_node(node)->key;
}

int zhc_bst_size(zhc_bst_t tree) {
    if (!tree) return 0;
    return ZHC_BST(tree)->size;
}

bool zhc_bst_empty(zhc_bst_t tree) {
    return !tree || ZHC_BST(tree)->size == 0;
}

void zhc_bst_clear(zhc_bst_t tree) {
    if (!tree) return;
    bst_destroy_rec(ZHC_BST(tree)->root);
    ZHC_BST(tree)->root = NULL;
    ZHC_BST(tree)->size = 0;
}

int zhc_bst_height(zhc_bst_t tree) {
    if (!tree) return 0;
    return bst_height_rec(ZHC_BST(tree)->root);
}

void zhc_bst_inorder(zhc_bst_t tree, void (*visit)(void*)) {
    if (!tree || !visit) return;
    bst_inorder_rec(ZHC_BST(tree)->root, visit);
}

void zhc_bst_preorder(zhc_bst_t tree, void (*visit)(void*)) {
    if (!tree || !visit) return;
    bst_preorder_rec(ZHC_BST(tree)->root, visit);
}

void zhc_bst_postorder(zhc_bst_t tree, void (*visit)(void*)) {
    if (!tree || !visit) return;
    bst_postorder_rec(ZHC_BST(tree)->root, visit);
}

void zhc_bst_levelorder(zhc_bst_t tree, void (*visit)(void*)) {
    if (!tree || !visit) return;
    zhc_bst_impl_t* t = ZHC_BST(tree);
    if (!t->root) return;

    zhc_array_t queue = zhc_array_create(sizeof(void*));
    zhc_array_add(queue, &t->root);

    while (!zhc_array_empty(queue)) {
        zhc_bst_node_impl_t** p = (zhc_bst_node_impl_t**)zhc_array_get(queue, 0);
        zhc_bst_node_impl_t* node = *p;
        zhc_array_remove(queue, 0);

        visit(node->key);
        if (node->left) zhc_array_add(queue, &node->left);
        if (node->right) zhc_array_add(queue, &node->right);
    }

    zhc_array_destroy(queue);
}

void* zhc_bst_node_key(void* node) {
    if (!node) return NULL;
    return ZHC_BST_NODE(node)->key;
}

void* zhc_bst_node_left(void* node) {
    if (!node) return NULL;
    return ZHC_BST_NODE(node)->left;
}

void* zhc_bst_node_right(void* node) {
    if (!node) return NULL;
    return ZHC_BST_NODE(node)->right;
}

/* ---------- 堆实现 ---------- */

typedef struct {
    void** data;
    int size;
    int capacity;
    int heap_type;  /* ZHC_HEAP_MIN or ZHC_HEAP_MAX */
    int (*compare)(const void*, const void*);
} zhc_heap_impl_t;

#define ZHC_HEAP(heap) ((zhc_heap_impl_t*)(heap))

static void heap_sift_up(zhc_heap_impl_t* h, int index) {
    while (index > 0) {
        int parent = (index - 1) / 2;
        int cmp = h->compare(h->data[index], h->data[parent]);
        if ((h->heap_type == ZHC_HEAP_MIN && cmp < 0) ||
            (h->heap_type == ZHC_HEAP_MAX && cmp > 0)) {
            void* temp = h->data[index];
            h->data[index] = h->data[parent];
            h->data[parent] = temp;
            index = parent;
        } else {
            break;
        }
    }
}

static void heap_sift_down(zhc_heap_impl_t* h, int index) {
    while (1) {
        int left = 2 * index + 1;
        int right = 2 * index + 2;
        int smallest = index;

        if (left < h->size) {
            int cmp = h->compare(h->data[left], h->data[smallest]);
            if ((h->heap_type == ZHC_HEAP_MIN && cmp < 0) ||
                (h->heap_type == ZHC_HEAP_MAX && cmp > 0)) {
                smallest = left;
            }
        }

        if (right < h->size) {
            int cmp = h->compare(h->data[right], h->data[smallest]);
            if ((h->heap_type == ZHC_HEAP_MIN && cmp < 0) ||
                (h->heap_type == ZHC_HEAP_MAX && cmp > 0)) {
                smallest = right;
            }
        }

        if (smallest != index) {
            void* temp = h->data[index];
            h->data[index] = h->data[smallest];
            h->data[smallest] = temp;
            index = smallest;
        } else {
            break;
        }
    }
}

zhc_heap_t zhc_heap_create(int heap_type, int (*compare)(const void*, const void*)) {
    if (!compare) return NULL;

    zhc_heap_impl_t* heap = (zhc_heap_impl_t*)malloc(sizeof(zhc_heap_impl_t));
    if (!heap) return NULL;

    heap->data = (void**)malloc(ZHC_ARRAY_DEFAULT_CAPACITY * sizeof(void*));
    if (!heap->data) {
        free(heap);
        return NULL;
    }

    heap->size = 0;
    heap->capacity = ZHC_ARRAY_DEFAULT_CAPACITY;
    heap->heap_type = heap_type;
    heap->compare = compare;

    return heap;
}

void zhc_heap_destroy(zhc_heap_t heap) {
    if (!heap) return;
    free(ZHC_HEAP(heap)->data);
    free(heap);
}

int zhc_heap_push(zhc_heap_t heap, const void* element) {
    if (!heap || !element) return -1;
    zhc_heap_impl_t* h = ZHC_HEAP(heap);

    if (h->size >= h->capacity) {
        int new_cap = h->capacity * ZHC_ARRAY_GROWTH_FACTOR;
        void** new_data = (void**)realloc(h->data, new_cap * sizeof(void*));
        if (!new_data) return -1;
        h->data = new_data;
        h->capacity = new_cap;
    }

    h->data[h->size] = (void*)element;
    heap_sift_up(h, h->size);
    h->size++;
    return 0;
}

int zhc_heap_pop(zhc_heap_t heap, void* output) {
    if (!heap) return -1;
    zhc_heap_impl_t* h = ZHC_HEAP(heap);
    if (h->size == 0) return -1;

    if (output) {
        memcpy(output, h->data[0], sizeof(void*));
    }

    h->data[0] = h->data[h->size - 1];
    h->size--;
    heap_sift_down(h, 0);
    return 0;
}

void* zhc_heap_top(zhc_heap_t heap) {
    if (!heap || ZHC_HEAP(heap)->size == 0) return NULL;
    return ZHC_HEAP(heap)->data[0];
}

int zhc_heap_size(zhc_heap_t heap) {
    if (!heap) return 0;
    return ZHC_HEAP(heap)->size;
}

bool zhc_heap_empty(zhc_heap_t heap) {
    return !heap || ZHC_HEAP(heap)->size == 0;
}

#endif /* ZHC_CONTAINER_IMPLEMENTATION */

#ifdef __cplusplus
}
#endif

#endif /* ZHC_CONTAINER_H */