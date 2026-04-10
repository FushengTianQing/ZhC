#include "zhc_coroutine.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

// ========================================================================
// 全局变量
// ========================================================================

static int g_coroutine_id_counter = 0;
static int g_channel_id_counter = 0;

// ========================================================================
// 协程生命周期管理
// ========================================================================

ZhcCoroutine *zhc_coroutine_create(void (*func)(void *), void *arg, size_t stack_size) {
    if (!func) {
        return NULL;
    }

    ZhcCoroutine *coro = (ZhcCoroutine *)malloc(sizeof(ZhcCoroutine));
    if (!coro) {
        return NULL;
    }

    // 初始化协程结构体
    coro->id = ++g_coroutine_id_counter;
    coro->state = ZHC_CORO_CREATED;
    coro->func = func;
    coro->arg = arg;
    coro->result = NULL;
    coro->exception = NULL;
    coro->upvalue_count = 0;

    // 分配栈空间
    if (stack_size == 0) {
        stack_size = 64 * 1024;  // 默认 64KB 栈
    }

    coro->ctx.stack_size = stack_size;
    coro->ctx.stack_ptr = malloc(stack_size);
    coro->ctx.stack_base = coro->ctx.stack_ptr;

    if (!coro->ctx.stack_ptr) {
        free(coro);
        return NULL;
    }

    // 初始化栈内容为 0
    memset(coro->ctx.stack_ptr, 0, stack_size);

    return coro;
}

void zhc_coroutine_start(ZhcCoroutine *coro) {
    if (!coro || coro->state != ZHC_CORO_CREATED) {
        return;
    }

    coro->state = ZHC_CORO_RUNNING;

    // 调用协程函数
    if (coro->func) {
        coro->func(coro->arg);
    }

    // 函数返回表示协程完成
    coro->state = ZHC_CORO_COMPLETED;
}

void *zhc_coroutine_resume(ZhcCoroutine *coro) {
    if (!coro) {
        return NULL;
    }

    if (coro->state != ZHC_CORO_SUSPENDED && coro->state != ZHC_CORO_CREATED) {
        return coro->result;
    }

    coro->state = ZHC_CORO_RUNNING;

    // TODO: 使用 setjmp/longjmp 或 ucontext 恢复执行上下文
    // 目前实现仅为占位符

    if (coro->func && coro->state == ZHC_CORO_RUNNING) {
        coro->func(coro->arg);
        coro->state = ZHC_CORO_COMPLETED;
    }

    return coro->result;
}

void zhc_coroutine_yield(void *value) {
    // TODO: 实现上下文切换
    // 目前实现仅为占位符
    // 在实际实现中，这里会使用 setjmp 保存当前上下文，
    // 并切换到调度器的上下文
}

void zhc_coroutine_destroy(ZhcCoroutine *coro) {
    if (!coro) {
        return;
    }

    if (coro->ctx.stack_ptr) {
        free(coro->ctx.stack_ptr);
    }

    free(coro);
}

bool zhc_coroutine_is_done(const ZhcCoroutine *coro) {
    if (!coro) {
        return true;
    }

    return coro->state == ZHC_CORO_COMPLETED ||
           coro->state == ZHC_CORO_CANCELLED;
}

ZhcCoroutineState zhc_coroutine_get_state(const ZhcCoroutine *coro) {
    if (!coro) {
        return ZHC_CORO_CANCELLED;
    }

    return coro->state;
}

// ========================================================================
// 通道操作
// ========================================================================

ZhcChannel *zhc_channel_create(size_t element_size, size_t buffer_size) {
    if (element_size == 0) {
        return NULL;
    }

    ZhcChannel *ch = (ZhcChannel *)malloc(sizeof(ZhcChannel));
    if (!ch) {
        return NULL;
    }

    // 初始化通道结构体
    ch->id = ++g_channel_id_counter;
    ch->element_size = element_size;
    ch->buffer_size = buffer_size;
    ch->capacity = buffer_size;
    ch->count = 0;
    ch->closed = false;
    ch->sender_count = 0;
    ch->receiver_count = 0;

    // 分配缓冲区
    if (buffer_size > 0) {
        ch->buffer = malloc(element_size * buffer_size);
        if (!ch->buffer) {
            free(ch);
            return NULL;
        }
        memset(ch->buffer, 0, element_size * buffer_size);
    } else {
        ch->buffer = NULL;  // 无缓冲通道
    }

    // 分配等待队列
    ch->waiting_senders = (ZhcCoroutine **)malloc(sizeof(ZhcCoroutine *) * 100);
    ch->waiting_receivers = (ZhcCoroutine **)malloc(sizeof(ZhcCoroutine *) * 100);

    if (!ch->waiting_senders || !ch->waiting_receivers) {
        if (ch->buffer) free(ch->buffer);
        if (ch->waiting_senders) free(ch->waiting_senders);
        if (ch->waiting_receivers) free(ch->waiting_receivers);
        free(ch);
        return NULL;
    }

    return ch;
}

int zhc_channel_send(ZhcChannel *ch, const void *data) {
    if (!ch || !data) {
        return -1;
    }

    if (ch->closed) {
        return -1;
    }

    // 有缓冲通道
    if (ch->buffer_size > 0) {
        if (ch->count >= ch->capacity) {
            // 缓冲区满，暂停发送者
            // TODO: 实现协程暂停
            return -1;
        }

        // 将数据复制到缓冲区
        char *buf = (char *)ch->buffer;
        memcpy(buf + ch->count * ch->element_size, data, ch->element_size);
        ch->count++;

        // 唤醒等待的接收者
        if (ch->receiver_count > 0) {
            // TODO: 唤醒接收者协程
            ch->receiver_count--;
        }
    } else {
        // 无缓冲通道 - 同步发送
        // TODO: 实现同步等待
    }

    return 0;
}

ssize_t zhc_channel_recv(ZhcChannel *ch, void *out_data) {
    if (!ch || !out_data) {
        return -1;
    }

    if (ch->closed && ch->count == 0) {
        return 0;  // 通道关闭且为空
    }

    // 有缓冲通道
    if (ch->buffer_size > 0) {
        if (ch->count == 0) {
            // 缓冲区空，暂停接收者
            // TODO: 实现协程暂停
            return -1;
        }

        // 从缓冲区取出数据
        char *buf = (char *)ch->buffer;
        memcpy(out_data, buf, ch->element_size);

        // 移动缓冲区数据（简单实现，实际应该用环形队列）
        memmove(buf, buf + ch->element_size, (ch->count - 1) * ch->element_size);
        ch->count--;

        // 唤醒等待的发送者
        if (ch->sender_count > 0) {
            // TODO: 唤醒发送者协程
            ch->sender_count--;
        }

        return ch->element_size;
    } else {
        // 无缓冲通道 - 同步接收
        // TODO: 实现同步等待
    }

    return -1;
}

void zhc_channel_close(ZhcChannel *ch) {
    if (!ch) {
        return;
    }

    ch->closed = true;

    // 唤醒所有等待的协程
    // TODO: 实现
}

void zhc_channel_destroy(ZhcChannel *ch) {
    if (!ch) {
        return;
    }

    if (ch->buffer) {
        free(ch->buffer);
    }

    if (ch->waiting_senders) {
        free(ch->waiting_senders);
    }

    if (ch->waiting_receivers) {
        free(ch->waiting_receivers);
    }

    free(ch);
}

bool zhc_channel_is_empty(const ZhcChannel *ch) {
    if (!ch) {
        return true;
    }

    return ch->count == 0;
}

bool zhc_channel_is_full(const ZhcChannel *ch) {
    if (!ch) {
        return true;
    }

    if (ch->buffer_size == 0) {
        return false;  // 无缓冲通道永远不会满
    }

    return ch->count >= ch->capacity;
}

// ========================================================================
// 调度器接口
// ========================================================================

void *zhc_scheduler_instance(void) {
    // TODO: 实现单例调度器
    return NULL;
}

void zhc_scheduler_add_coroutine(ZhcCoroutine *coro) {
    if (!coro) {
        return;
    }
    // TODO: 添加到调度器
}

void zhc_scheduler_remove_coroutine(ZhcCoroutine *coro) {
    if (!coro) {
        return;
    }
    // TODO: 从调度器移除
}

ZhcCoroutine *zhc_scheduler_schedule(void) {
    // TODO: 实现调度算法
    return NULL;
}

// ========================================================================
// 调试接口
// ========================================================================

const char *zhc_coroutine_state_to_string(ZhcCoroutineState state) {
    switch (state) {
        case ZHC_CORO_CREATED: return "CREATED";
        case ZHC_CORO_RUNNING: return "RUNNING";
        case ZHC_CORO_SUSPENDED: return "SUSPENDED";
        case ZHC_CORO_WAITING: return "WAITING";
        case ZHC_CORO_COMPLETED: return "COMPLETED";
        case ZHC_CORO_CANCELLED: return "CANCELLED";
        default: return "UNKNOWN";
    }
}

void zhc_coroutine_print_info(const ZhcCoroutine *coro) {
    if (!coro) {
        printf("Coroutine: NULL\n");
        return;
    }

    printf("Coroutine %d: state=%s, func=%p, stack_size=%zu\n",
           coro->id,
           zhc_coroutine_state_to_string(coro->state),
           (void *)coro->func,
           coro->ctx.stack_size);
}

void zhc_channel_print_info(const ZhcChannel *ch) {
    if (!ch) {
        printf("Channel: NULL\n");
        return;
    }

    printf("Channel %d: element_size=%zu, buffer=%zu/%zu, closed=%s, senders=%d, receivers=%d\n",
           ch->id,
           ch->element_size,
           ch->count,
           ch->capacity,
           ch->closed ? "true" : "false",
           ch->sender_count,
           ch->receiver_count);
}
