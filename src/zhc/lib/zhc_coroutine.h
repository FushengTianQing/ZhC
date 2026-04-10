#ifndef ZHC_COROUTINE_H
#define ZHC_COROUTINE_H

#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// ========================================================================
// 协程状态
// ========================================================================

typedef enum ZhcCoroutineState {
    ZHC_CORO_CREATED = 0,
    ZHC_CORO_RUNNING = 1,
    ZHC_CORO_SUSPENDED = 2,
    ZHC_CORO_WAITING = 3,
    ZHC_CORO_COMPLETED = 4,
    ZHC_CORO_CANCELLED = 5,
} ZhcCoroutineState;

// ========================================================================
// 协程上下文
// ========================================================================

// 前向声明
struct ZhcCoroutine;
struct ZhcChannel;

// 协程上下文结构体（保存协程执行状态）
typedef struct ZhcCoroutineContext {
    void *stack_ptr;           // 栈指针
    void *stack_base;          // 栈基址
    size_t stack_size;         // 栈大小
    void *regs[8];            // 保存的寄存器（用于上下文切换）
} ZhcCoroutineContext;

// ========================================================================
// 协程结构体
// ========================================================================

typedef struct ZhcCoroutine {
    int id;                    // 协程 ID
    ZhcCoroutineState state;    // 协程状态
    void (*func)(void *);      // 协程函数指针
    void *arg;                 // 协程参数
    void *result;              // 协程结果
    void *exception;           // 协程异常
    ZhcCoroutineContext ctx;   // 协程上下文
    void *upvalues;           // upvalue 数组
    int upvalue_count;         // upvalue 数量
} ZhcCoroutine;

// ========================================================================
// 通道结构体
// ========================================================================

typedef struct ZhcChannel {
    int id;                    // 通道 ID
    void *buffer;              // 缓冲区指针
    size_t buffer_size;        // 缓冲区大小
    size_t capacity;           // 缓冲区容量
    size_t count;              // 当前元素数量
    size_t element_size;       // 元素大小
    bool closed;               // 是否已关闭
    struct ZhcCoroutine **waiting_senders;   // 等待的发送者
    struct ZhcCoroutine **waiting_receivers;  // 等待的接收者
    int sender_count;          // 等待发送者数量
    int receiver_count;        // 等待接收者数量
} ZhcChannel;

// ========================================================================
// 协程生命周期管理
// ========================================================================

/**
 * 创建协程
 * @param func 协程函数
 * @param arg 协程参数
 * @param stack_size 栈大小
 * @return 协程指针，失败返回 NULL
 */
ZhcCoroutine *zhc_coroutine_create(void (*func)(void *), void *arg, size_t stack_size);

/**
 * 启动协程
 * @param coro 协程指针
 */
void zhc_coroutine_start(ZhcCoroutine *coro);

/**
 * 恢复协程
 * @param coro 协程指针
 * @return 协程结果
 */
void *zhc_coroutine_resume(ZhcCoroutine *coro);

/**
 * 协程让出控制权
 * @param value 让出的值
 */
void zhc_coroutine_yield(void *value);

/**
 * 销毁协程
 * @param coro 协程指针
 */
void zhc_coroutine_destroy(ZhcCoroutine *coro);

/**
 * 检查协程是否完成
 * @param coro 协程指针
 * @return 是否完成
 */
bool zhc_coroutine_is_done(const ZhcCoroutine *coro);

/**
 * 获取协程状态
 * @param coro 协程指针
 * @return 协程状态
 */
ZhcCoroutineState zhc_coroutine_get_state(const ZhcCoroutine *coro);

// ========================================================================
// 通道操作
// ========================================================================

/**
 * 创建通道
 * @param element_size 元素大小
 * @param buffer_size 缓冲区大小（0 表示无缓冲）
 * @return 通道指针，失败返回 NULL
 */
ZhcChannel *zhc_channel_create(size_t element_size, size_t buffer_size);

/**
 * 发送数据到通道
 * @param ch 通道指针
 * @param data 数据指针
 * @return 成功返回 0，失败返回 -1
 */
int zhc_channel_send(ZhcChannel *ch, const void *data);

/**
 * 从通道接收数据
 * @param ch 通道指针
 * @param out_data 输出数据缓冲区
 * @return 成功返回接收的字节数，失败返回 -1，通道关闭返回 0
 */
ssize_t zhc_channel_recv(ZhcChannel *ch, void *out_data);

/**
 * 关闭通道
 * @param ch 通道指针
 */
void zhc_channel_close(ZhcChannel *ch);

/**
 * 销毁通道
 * @param ch 通道指针
 */
void zhc_channel_destroy(ZhcChannel *ch);

/**
 * 检查通道是否为空
 * @param ch 通道指针
 * @return 是否为空
 */
bool zhc_channel_is_empty(const ZhcChannel *ch);

/**
 * 检查通道是否已满
 * @param ch 通道指针
 * @return 是否已满
 */
bool zhc_channel_is_full(const ZhcChannel *ch);

// ========================================================================
// 调度器接口
// ========================================================================

/**
 * 获取调度器实例
 * @return 调度器指针
 */
void *zhc_scheduler_instance(void);

/**
 * 将协程添加到调度器
 * @param coro 协程指针
 */
void zhc_scheduler_add_coroutine(ZhcCoroutine *coro);

/**
 * 从调度器移除协程
 * @param coro 协程指针
 */
void zhc_scheduler_remove_coroutine(ZhcCoroutine *coro);

/**
 * 调度下一个协程
 * @return 下一个要执行的协程，没有返回 NULL
 */
ZhcCoroutine *zhc_scheduler_schedule(void);

// ========================================================================
// 调试接口
// ========================================================================

/**
 * 获取协程状态字符串
 * @param state 协程状态
 * @return 状态字符串
 */
const char *zhc_coroutine_state_to_string(ZhcCoroutineState state);

/**
 * 打印协程信息
 * @param coro 协程指针
 */
void zhc_coroutine_print_info(const ZhcCoroutine *coro);

/**
 * 打印通道信息
 * @param ch 通道指针
 */
void zhc_channel_print_info(const ZhcChannel *ch);

#ifdef __cplusplus
}
#endif

#endif /* ZHC_COROUTINE_H */
