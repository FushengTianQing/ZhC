/**
 * zhc_thread.h - 线程管理与同步原语库
 *
 * 提供：
 * - 线程创建与管理
 * - 互斥锁、读写锁
 * - 信号量、条件变量
 * - 原子操作
 * - 线程局部存储
 *
 * 版本: 1.0
 * 依赖: <pthread.h>, <semaphore.h>, <stdatomic.h>, <sched.h>, <unistd.h>
 */

#ifndef ZHC_THREAD_H
#define ZHC_THREAD_H

#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ================================================================
 * 类型定义
 * ================================================================ */

/** 线程句柄 */
typedef void* zhc_thread_t;

/** 线程属性 */
typedef struct {
    size_t stack_size;
    int priority;
    int detach_state;
    int sched_policy;
} zhc_thread_attr_t;

/** 互斥锁类型 */
typedef void* zhc_mutex_t;

/** 读写锁类型 */
typedef void* zhc_rwlock_t;

/** 信号量类型 */
typedef void* zhc_sem_t;

/** 条件变量类型 */
typedef void* zhc_cond_t;

/** 原子整数类型 */
typedef struct {
    volatile int value;
} zhc_atomic_int_t;

/** 线程本地存储键类型 */
typedef void* zhc_tls_key_t;

/* ================================================================
 * 常量定义
 * ================================================================ */

/** 互斥锁类型常量 */
#define ZHC_MUTEX_NORMAL     1  /** 普通互斥锁 */
#define ZHC_MUTEX_ERRORCHECK 2  /** 检错互斥锁 */
#define ZHC_MUTEX_RECURSIVE  3  /** 递归互斥锁 */

/** 线程调度策略 */
#define ZHC_SCHED_FIFO   1
#define ZHC_SCHED_RR     2
#define ZHC_SCHED_OTHER  3

/** 分离状态 */
#define ZHC_THREAD_JOINABLE  0
#define ZHC_THREAD_DETACHED   1

/** 线程本地存储 destructor 回调类型 */
typedef void (*zhc_tls_destructor_t)(void*);

/* ================================================================
 * 线程管理函数
 * ================================================================ */

/**
 * zhc_thread_create - 创建线程
 * @func: 线程入口函数
 * @arg: 传递给线程的参数
 * 返回: 线程句柄，NULL 表示失败
 */
zhc_thread_t zhc_thread_create(void* (*func)(void*), void* arg);

/**
 * zhc_thread_create_attr - 创建线程（带属性）
 * @attr: 线程属性
 * @func: 线程入口函数
 * @arg: 传递给线程的参数
 * 返回: 线程句柄，NULL 表示失败
 */
zhc_thread_t zhc_thread_create_attr(zhc_thread_attr_t* attr,
                                    void* (*func)(void*), void* arg);

/**
 * zhc_thread_join - 等待线程结束
 * @thread: 线程句柄
 * @retval: 线程返回值输出（可为 NULL）
 * 返回: 0 成功，-1 失败
 */
int zhc_thread_join(zhc_thread_t thread, void** retval);

/**
 * zhc_thread_detach - 分离线程
 * @thread: 线程句柄
 * 返回: 0 成功，-1 失败
 */
int zhc_thread_detach(zhc_thread_t thread);

/**
 * zhc_thread_self - 获取当前线程ID
 * 返回: 当前线程句柄
 */
zhc_thread_t zhc_thread_self(void);

/**
 * zhc_thread_equal - 比较两个线程ID是否相等
 * @t1: 线程1
 * @t2: 线程2
 * 返回: 1 相等，0 不等
 */
int zhc_thread_equal(zhc_thread_t t1, zhc_thread_t t2);

/**
 * zhc_thread_sleep - 线程休眠
 * @seconds: 休眠秒数（支持小数）
 */
void zhc_thread_sleep(double seconds);

/**
 * zhc_cpu_count - 获取CPU核心数
 * 返回: CPU核心数
 */
int zhc_cpu_count(void);

/**
 * zhc_thread_setaffinity - 设置线程亲和性
 * @thread: 线程句柄
 * @cpus: CPU核心数组
 * @size: 数组大小
 * 返回: 0 成功，-1 失败
 */
int zhc_thread_setaffinity(zhc_thread_t thread, int* cpus, size_t size);

/**
 * zhc_thread_getaffinity - 获取线程亲和性
 * @thread: 线程句柄
 * @cpus: CPU核心数组
 * @size: 数组大小
 * 返回: 实际设置的CPU数量，-1 失败
 */
int zhc_thread_getaffinity(zhc_thread_t thread, int* cpus, size_t size);

/**
 * zhc_thread_attr_init - 初始化线程属性
 * @attr: 属性结构指针
 * 返回: 0 成功，-1 失败
 */
int zhc_thread_attr_init(zhc_thread_attr_t* attr);

/**
 * zhc_thread_attr_destroy - 销毁线程属性
 * @attr: 属性结构指针
 * 返回: 0 成功，-1 失败
 */
int zhc_thread_attr_destroy(zhc_thread_attr_t* attr);

/**
 * zhc_thread_attr_setstacksize - 设置栈大小
 * @attr: 属性结构指针
 * @size: 栈大小（字节）
 * 返回: 0 成功，-1 失败
 */
int zhc_thread_attr_setstacksize(zhc_thread_attr_t* attr, size_t size);

/**
 * zhc_thread_attr_setdetachstate - 设置分离状态
 * @attr: 属性结构指针
 * @state: 分离状态（ZHC_THREAD_JOINABLE 或 ZHC_THREAD_DETACHED）
 * 返回: 0 成功，-1 失败
 */
int zhc_thread_attr_setdetachstate(zhc_thread_attr_t* attr, int state);

/* ================================================================
 * 互斥锁函数
 * ================================================================ */

/**
 * zhc_mutex_create - 创建互斥锁
 * 返回: 互斥锁句柄，NULL 表示失败
 */
zhc_mutex_t zhc_mutex_create(void);

/**
 * zhc_mutex_create_type - 创建指定类型的互斥锁
 * @type: 互斥锁类型（ZHC_MUTEX_NORMAL/ERRORCHECK/RECURSIVE）
 * 返回: 互斥锁句柄，NULL 表示失败
 */
zhc_mutex_t zhc_mutex_create_type(int type);

/**
 * zhc_mutex_destroy - 销毁互斥锁
 * @mutex: 互斥锁句柄
 * 返回: 0 成功，-1 失败
 */
int zhc_mutex_destroy(zhc_mutex_t mutex);

/**
 * zhc_mutex_lock - 加锁（阻塞）
 * @mutex: 互斥锁句柄
 * 返回: 0 成功，-1 失败
 */
int zhc_mutex_lock(zhc_mutex_t mutex);

/**
 * zhc_mutex_trylock - 尝试加锁（非阻塞）
 * @mutex: 互斥锁句柄
 * 返回: 0 成功，EBUSY 表示已被锁定
 */
int zhc_mutex_trylock(zhc_mutex_t mutex);

/**
 * zhc_mutex_unlock - 解锁
 * @mutex: 互斥锁句柄
 * 返回: 0 成功，-1 失败
 */
int zhc_mutex_unlock(zhc_mutex_t mutex);

/* ================================================================
 * 读写锁函数
 * ================================================================ */

/**
 * zhc_rwlock_create - 创建读写锁
 * 返回: 读写锁句柄，NULL 表示失败
 */
zhc_rwlock_t zhc_rwlock_create(void);

/**
 * zhc_rwlock_destroy - 销毁读写锁
 * @rwlock: 读写锁句柄
 * 返回: 0 成功，-1 失败
 */
int zhc_rwlock_destroy(zhc_rwlock_t rwlock);

/**
 * zhc_rwlock_read_lock - 读加锁（阻塞）
 * @rwlock: 读写锁句柄
 * 返回: 0 成功，-1 失败
 */
int zhc_rwlock_read_lock(zhc_rwlock_t rwlock);

/**
 * zhc_rwlock_read_trylock - 尝试读加锁（非阻塞）
 * @rwlock: 读写锁句柄
 * 返回: 0 成功，EBUSY 表示已被锁定
 */
int zhc_rwlock_read_trylock(zhc_rwlock_t rwlock);

/**
 * zhc_rwlock_write_lock - 写加锁（阻塞）
 * @rwlock: 读写锁句柄
 * 返回: 0 成功，-1 失败
 */
int zhc_rwlock_write_lock(zhc_rwlock_t rwlock);

/**
 * zhc_rwlock_write_trylock - 尝试写加锁（非阻塞）
 * @rwlock: 读写锁句柄
 * 返回: 0 成功，EBUSY 表示已被锁定
 */
int zhc_rwlock_write_trylock(zhc_rwlock_t rwlock);

/**
 * zhc_rwlock_unlock - 解锁
 * @rwlock: 读写锁句柄
 * 返回: 0 成功，-1 失败
 */
int zhc_rwlock_unlock(zhc_rwlock_t rwlock);

/* ================================================================
 * 信号量函数
 * ================================================================ */

/**
 * zhc_sem_create - 创建信号量
 * @value: 初始值
 * 返回: 信号量句柄，NULL 表示失败
 */
zhc_sem_t zhc_sem_create(int value);

/**
 * zhc_sem_destroy - 销毁信号量
 * @sem: 信号量句柄
 * 返回: 0 成功，-1 失败
 */
int zhc_sem_destroy(zhc_sem_t sem);

/**
 * zhc_sem_wait - P 操作（等待，减1）
 * @sem: 信号量句柄
 * 返回: 0 成功，-1 失败
 */
int zhc_sem_wait(zhc_sem_t sem);

/**
 * zhc_sem_trywait - 尝试 P 操作（非阻塞）
 * @sem: 信号量句柄
 * 返回: 0 成功，-1 表示值为0
 */
int zhc_sem_trywait(zhc_sem_t sem);

/**
 * zhc_sem_post - V 操作（释放，加1）
 * @sem: 信号量句柄
 * 返回: 0 成功，-1 失败
 */
int zhc_sem_post(zhc_sem_t sem);

/**
 * zhc_sem_getvalue - 获取信号量值
 * @sem: 信号量句柄
 * @value: 值输出
 * 返回: 0 成功
 */
int zhc_sem_getvalue(zhc_sem_t sem, int* value);

/* ================================================================
 * 条件变量函数
 * ================================================================ */

/**
 * zhc_cond_create - 创建条件变量
 * 返回: 条件变量句柄，NULL 表示失败
 */
zhc_cond_t zhc_cond_create(void);

/**
 * zhc_cond_destroy - 销毁条件变量
 * @cond: 条件变量句柄
 * 返回: 0 成功，-1 失败
 */
int zhc_cond_destroy(zhc_cond_t cond);

/**
 * zhc_cond_wait - 等待条件变量
 * @cond: 条件变量句柄
 * @mutex: 互斥锁句柄
 * 返回: 0 成功，-1 失败
 */
int zhc_cond_wait(zhc_cond_t cond, zhc_mutex_t mutex);

/**
 * zhc_cond_timedwait - 超时等待条件变量
 * @cond: 条件变量句柄
 * @mutex: 互斥锁句柄
 * @timeout: 超时秒数
 * 返回: 0 超时，ETIMEDOUT 表示超时
 */
int zhc_cond_timedwait(zhc_cond_t cond, zhc_mutex_t mutex, double timeout);

/**
 * zhc_cond_signal - 通知单个等待线程
 * @cond: 条件变量句柄
 * 返回: 0 成功，-1 失败
 */
int zhc_cond_signal(zhc_cond_t cond);

/**
 * zhc_cond_broadcast - 通知所有等待线程
 * @cond: 条件变量句柄
 * 返回: 0 成功，-1 失败
 */
int zhc_cond_broadcast(zhc_cond_t cond);

/* ================================================================
 * 原子操作函数
 * ================================================================ */

/**
 * zhc_atomic_int_create - 创建原子整数
 * @value: 初始值
 * 返回: 原子整数指针
 */
zhc_atomic_int_t* zhc_atomic_int_create(int value);

/**
 * zhc_atomic_int_destroy - 销毁原子整数
 * @atom: 原子整数指针
 */
void zhc_atomic_int_destroy(zhc_atomic_int_t* atom);

/**
 * zhc_atomic_load - 原子加载
 * @atom: 原子整数指针
 * 返回: 当前值
 */
int zhc_atomic_load(zhc_atomic_int_t* atom);

/**
 * zhc_atomic_store - 原子存储
 * @atom: 原子整数指针
 * @value: 存储的值
 */
void zhc_atomic_store(zhc_atomic_int_t* atom, int value);

/**
 * zhc_atomic_fetch_add - 原子加法（返回旧值）
 * @atom: 原子整数指针
 * @delta: 增量
 * 返回: 操作前的值
 */
int zhc_atomic_fetch_add(zhc_atomic_int_t* atom, int delta);

/**
 * zhc_atomic_fetch_sub - 原子减法（返回旧值）
 * @atom: 原子整数指针
 * @delta: 减量
 * 返回: 操作前的值
 */
int zhc_atomic_fetch_sub(zhc_atomic_int_t* atom, int delta);

/**
 * zhc_atomic_inc - 原子递增
 * @atom: 原子整数指针
 * 返回: 操作后的值
 */
int zhc_atomic_inc(zhc_atomic_int_t* atom);

/**
 * zhc_atomic_dec - 原子递减
 * @atom: 原子整数指针
 * 返回: 操作后的值
 */
int zhc_atomic_dec(zhc_atomic_int_t* atom);

/**
 * zhc_atomic_add - 原子加法（返回新值）
 * @atom: 原子整数指针
 * @delta: 增量
 * 返回: 操作后的值
 */
int zhc_atomic_add(zhc_atomic_int_t* atom, int delta);

/**
 * zhc_atomic_sub - 原子减法（返回新值）
 * @atom: 原子整数指针
 * @delta: 减量
 * 返回: 操作后的值
 */
int zhc_atomic_sub(zhc_atomic_int_t* atom, int delta);

/**
 * zhc_atomic_cas - 比较并交换
 * @atom: 原子整数指针
 * @old_val: 期望的旧值
 * @new_val: 新值
 * 返回: 1 成功（交换发生），0 失败（值不匹配）
 */
int zhc_atomic_cas(zhc_atomic_int_t* atom, int old_val, int new_val);

/**
 * zhc_atomic_exchange - 原子交换
 * @atom: 原子整数指针
 * @new_val: 新值
 * 返回: 原来的值
 */
int zhc_atomic_exchange(zhc_atomic_int_t* atom, int new_val);

/* ================================================================
 * 线程局部存储函数
 * ================================================================ */

/**
 * zhc_tls_create - 创建线程局部存储键
 * @destructor: 析构函数（可为 NULL）
 * 返回: 存储键，NULL 表示失败
 */
zhc_tls_key_t zhc_tls_create(zhc_tls_destructor_t destructor);

/**
 * zhc_tls_get - 获取线程局部存储值
 * @key: 存储键
 * 返回: 存储的值（每个线程不同）
 */
void* zhc_tls_get(zhc_tls_key_t key);

/**
 * zhc_tls_set - 设置线程局部存储值
 * @key: 存储键
 * @value: 要存储的值
 * 返回: 0 成功，-1 失败
 */
int zhc_tls_set(zhc_tls_key_t key, void* value);

/**
 * zhc_tls_destroy - 销毁线程局部存储键
 * @key: 存储键
 * 返回: 0 成功，-1 失败
 */
int zhc_tls_destroy(zhc_tls_key_t key);

/* ================================================================
 * 实现
 * ================================================================ */

#ifdef ZHC_THREAD_IMPLEMENTATION

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <pthread.h>
#include <semaphore.h>
#include <sched.h>
#include <unistd.h>
#include <sys/sysinfo.h>

/* ---------- 线程管理实现 ---------- */

zhc_thread_t zhc_thread_create(void* (*func)(void*), void* arg) {
    pthread_t thread;
    if (pthread_create(&thread, NULL, func, arg) != 0) {
        return NULL;
    }
    return (zhc_thread_t)thread;
}

zhc_thread_t zhc_thread_create_attr(zhc_thread_attr_t* attr,
                                    void* (*func)(void*), void* arg) {
    pthread_attr_t pattr;
    pthread_t thread;

    if (attr) {
        pthread_attr_init(&pattr);
        if (attr->stack_size > 0) {
            pthread_attr_setstacksize(&pattr, attr->stack_size);
        }
        if (attr->detach_state == ZHC_THREAD_DETACHED) {
            pthread_attr_setdetachstate(&pattr, PTHREAD_CREATE_DETACHED);
        }
    }

    if (pthread_create(&thread, attr ? &pattr : NULL, func, arg) != 0) {
        if (attr) pthread_attr_destroy(&pattr);
        return NULL;
    }

    if (attr) pthread_attr_destroy(&pattr);
    return (zhc_thread_t)thread;
}

int zhc_thread_join(zhc_thread_t thread, void** retval) {
    return pthread_join((pthread_t)thread, retval);
}

int zhc_thread_detach(zhc_thread_t thread) {
    return pthread_detach((pthread_t)thread);
}

zhc_thread_t zhc_thread_self(void) {
    return (zhc_thread_t)pthread_self();
}

int zhc_thread_equal(zhc_thread_t t1, zhc_thread_t t2) {
    return pthread_equal((pthread_t)t1, (pthread_t)t2);
}

void zhc_thread_sleep(double seconds) {
    usleep((useconds_t)(seconds * 1000000));
}

int zhc_cpu_count(void) {
    return get_nprocs();
}

int zhc_thread_setaffinity(zhc_thread_t thread, int* cpus, size_t size) {
#ifdef __linux__
    cpu_set_t cset;
    CPU_ZERO(&cset);
    for (size_t i = 0; i < size; i++) {
        CPU_SET(cpus[i], &cset);
    }
    return sched_setaffinity((pid_t)(uintptr_t)thread, sizeof(cpu_set_t), &cset);
#else
    (void)thread; (void)cpus; (void)size;
    return -1;
#endif
}

int zhc_thread_getaffinity(zhc_thread_t thread, int* cpus, size_t size) {
#ifdef __linux__
    cpu_set_t cset;
    CPU_ZERO(&cset);
    if (sched_getaffinity((pid_t)(uintptr_t)thread, sizeof(cpu_set_t), &cset) != 0) {
        return -1;
    }
    size_t count = 0;
    for (int i = 0; i < CPU_SETSIZE && count < size; i++) {
        if (CPU_ISSET(i, &cset)) {
            cpus[count++] = i;
        }
    }
    return (int)count;
#else
    (void)thread; (void)cpus; (void)size;
    return -1;
#endif
}

int zhc_thread_attr_init(zhc_thread_attr_t* attr) {
    if (!attr) return -1;
    memset(attr, 0, sizeof(zhc_thread_attr_t));
    attr->stack_size = 0;
    attr->priority = 0;
    attr->detach_state = ZHC_THREAD_JOINABLE;
    attr->sched_policy = ZHC_SCHED_OTHER;
    return 0;
}

int zhc_thread_attr_destroy(zhc_thread_attr_t* attr) {
    (void)attr;
    return 0;
}

int zhc_thread_attr_setstacksize(zhc_thread_attr_t* attr, size_t size) {
    if (!attr) return -1;
    attr->stack_size = size;
    return 0;
}

int zhc_thread_attr_setdetachstate(zhc_thread_attr_t* attr, int state) {
    if (!attr) return -1;
    attr->detach_state = state;
    return 0;
}

/* ---------- 互斥锁实现 ---------- */

zhc_mutex_t zhc_mutex_create(void) {
    pthread_mutex_t* mutex = (pthread_mutex_t*)malloc(sizeof(pthread_mutex_t));
    if (!mutex) return NULL;
    if (pthread_mutex_init(mutex, NULL) != 0) {
        free(mutex);
        return NULL;
    }
    return (zhc_mutex_t)mutex;
}

zhc_mutex_t zhc_mutex_create_type(int type) {
    pthread_mutex_t* mutex = (pthread_mutex_t*)malloc(sizeof(pthread_mutex_t));
    if (!mutex) return NULL;

    pthread_mutexattr_t attr;
    pthread_mutexattr_init(&attr);

    switch (type) {
        case ZHC_MUTEX_ERRORCHECK:
            pthread_mutexattr_settype(&attr, PTHREAD_MUTEX_ERRORCHECK);
            break;
        case ZHC_MUTEX_RECURSIVE:
            pthread_mutexattr_settype(&attr, PTHREAD_MUTEX_RECURSIVE);
            break;
        case ZHC_MUTEX_NORMAL:
        default:
            pthread_mutexattr_settype(&attr, PTHREAD_MUTEX_NORMAL);
            break;
    }

    if (pthread_mutex_init(mutex, &attr) != 0) {
        pthread_mutexattr_destroy(&attr);
        free(mutex);
        return NULL;
    }
    pthread_mutexattr_destroy(&attr);
    return (zhc_mutex_t)mutex;
}

int zhc_mutex_destroy(zhc_mutex_t mutex) {
    if (!mutex) return -1;
    int ret = pthread_mutex_destroy((pthread_mutex_t*)mutex);
    free((pthread_mutex_t*)mutex);
    return ret;
}

int zhc_mutex_lock(zhc_mutex_t mutex) {
    if (!mutex) return -1;
    return pthread_mutex_lock((pthread_mutex_t*)mutex);
}

int zhc_mutex_trylock(zhc_mutex_t mutex) {
    if (!mutex) return -1;
    return pthread_mutex_trylock((pthread_mutex_t*)mutex);
}

int zhc_mutex_unlock(zhc_mutex_t mutex) {
    if (!mutex) return -1;
    return pthread_mutex_unlock((pthread_mutex_t*)mutex);
}

/* ---------- 读写锁实现 ---------- */

zhc_rwlock_t zhc_rwlock_create(void) {
    pthread_rwlock_t* rwlock = (pthread_rwlock_t*)malloc(sizeof(pthread_rwlock_t));
    if (!rwlock) return NULL;
    if (pthread_rwlock_init(rwlock, NULL) != 0) {
        free(rwlock);
        return NULL;
    }
    return (zhc_rwlock_t)rwlock;
}

int zhc_rwlock_destroy(zhc_rwlock_t rwlock) {
    if (!rwlock) return -1;
    int ret = pthread_rwlock_destroy((pthread_rwlock_t*)rwlock);
    free((pthread_rwlock_t*)rwlock);
    return ret;
}

int zhc_rwlock_read_lock(zhc_rwlock_t rwlock) {
    if (!rwlock) return -1;
    return pthread_rwlock_rdlock((pthread_rwlock_t*)rwlock);
}

int zhc_rwlock_read_trylock(zhc_rwlock_t rwlock) {
    if (!rwlock) return -1;
    return pthread_rwlock_tryrdlock((pthread_rwlock_t*)rwlock);
}

int zhc_rwlock_write_lock(zhc_rwlock_t rwlock) {
    if (!rwlock) return -1;
    return pthread_rwlock_wrlock((pthread_rwlock_t*)rwlock);
}

int zhc_rwlock_write_trylock(zhc_rwlock_t rwlock) {
    if (!rwlock) return -1;
    return pthread_rwlock_trywrlock((pthread_rwlock_t*)rwlock);
}

int zhc_rwlock_unlock(zhc_rwlock_t rwlock) {
    if (!rwlock) return -1;
    return pthread_rwlock_unlock((pthread_rwlock_t*)rwlock);
}

/* ---------- 信号量实现 ---------- */

zhc_sem_t zhc_sem_create(int value) {
    sem_t* sem = (sem_t*)malloc(sizeof(sem_t));
    if (!sem) return NULL;
    if (sem_init(sem, 0, (unsigned int)value) != 0) {
        free(sem);
        return NULL;
    }
    return (zhc_sem_t)sem;
}

int zhc_sem_destroy(zhc_sem_t sem) {
    if (!sem) return -1;
    int ret = sem_destroy((sem_t*)sem);
    free((sem_t*)sem);
    return ret;
}

int zhc_sem_wait(zhc_sem_t sem) {
    if (!sem) return -1;
    return sem_wait((sem_t*)sem);
}

int zhc_sem_trywait(zhc_sem_t sem) {
    if (!sem) return -1;
    return sem_trywait((sem_t*)sem);
}

int zhc_sem_post(zhc_sem_t sem) {
    if (!sem) return -1;
    return sem_post((sem_t*)sem);
}

int zhc_sem_getvalue(zhc_sem_t sem, int* value) {
    if (!sem || !value) return -1;
    return sem_getvalue((sem_t*)sem, value);
}

/* ---------- 条件变量实现 ---------- */

zhc_cond_t zhc_cond_create(void) {
    pthread_cond_t* cond = (pthread_cond_t*)malloc(sizeof(pthread_cond_t));
    if (!cond) return NULL;
    if (pthread_cond_init(cond, NULL) != 0) {
        free(cond);
        return NULL;
    }
    return (zhc_cond_t)cond;
}

int zhc_cond_destroy(zhc_cond_t cond) {
    if (!cond) return -1;
    int ret = pthread_cond_destroy((pthread_cond_t*)cond);
    free((pthread_cond_t*)cond);
    return ret;
}

int zhc_cond_wait(zhc_cond_t cond, zhc_mutex_t mutex) {
    if (!cond || !mutex) return -1;
    return pthread_cond_wait((pthread_cond_t*)cond, (pthread_mutex_t*)mutex);
}

int zhc_cond_timedwait(zhc_cond_t cond, zhc_mutex_t mutex, double timeout) {
    if (!cond || !mutex) return -1;

    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    ts.tv_sec += (time_t)timeout;
    ts.tv_nsec += (long)((timeout - (double)(time_t)timeout) * 1000000000);
    if (ts.tv_nsec >= 1000000000) {
        ts.tv_sec += 1;
        ts.tv_nsec -= 1000000000;
    }

    return pthread_cond_timedwait((pthread_cond_t*)cond,
                                  (pthread_mutex_t*)mutex, &ts);
}

int zhc_cond_signal(zhc_cond_t cond) {
    if (!cond) return -1;
    return pthread_cond_signal((pthread_cond_t*)cond);
}

int zhc_cond_broadcast(zhc_cond_t cond) {
    if (!cond) return -1;
    return pthread_cond_broadcast((pthread_cond_t*)cond);
}

/* ---------- 原子操作实现 ---------- */

zhc_atomic_int_t* zhc_atomic_int_create(int value) {
    zhc_atomic_int_t* atom = (zhc_atomic_int_t*)malloc(sizeof(zhc_atomic_int_t));
    if (atom) {
        atom->value = value;
    }
    return atom;
}

void zhc_atomic_int_destroy(zhc_atomic_int_t* atom) {
    free(atom);
}

int zhc_atomic_load(zhc_atomic_int_t* atom) {
    if (!atom) return 0;
    return __sync_fetch_and_add(&atom->value, 0);
}

void zhc_atomic_store(zhc_atomic_int_t* atom, int value) {
    if (!atom) return;
    __sync_synchronize();
    atom->value = value;
    __sync_synchronize();
}

int zhc_atomic_fetch_add(zhc_atomic_int_t* atom, int delta) {
    if (!atom) return 0;
    return __sync_fetch_and_add(&atom->value, delta);
}

int zhc_atomic_fetch_sub(zhc_atomic_int_t* atom, int delta) {
    if (!atom) return 0;
    return __sync_fetch_and_sub(&atom->value, delta);
}

int zhc_atomic_inc(zhc_atomic_int_t* atom) {
    if (!atom) return 0;
    return __sync_add_and_fetch(&atom->value, 1);
}

int zhc_atomic_dec(zhc_atomic_int_t* atom) {
    if (!atom) return 0;
    return __sync_sub_and_fetch(&atom->value, 1);
}

int zhc_atomic_add(zhc_atomic_int_t* atom, int delta) {
    if (!atom) return 0;
    return __sync_add_and_fetch(&atom->value, delta);
}

int zhc_atomic_sub(zhc_atomic_int_t* atom, int delta) {
    if (!atom) return 0;
    return __sync_sub_and_fetch(&atom->value, delta);
}

int zhc_atomic_cas(zhc_atomic_int_t* atom, int old_val, int new_val) {
    if (!atom) return 0;
    return __sync_bool_compare_and_swap(&atom->value, old_val, new_val);
}

int zhc_atomic_exchange(zhc_atomic_int_t* atom, int new_val) {
    if (!atom) return 0;
    int old_val;
    do {
        old_val = atom->value;
    } while (!__sync_bool_compare_and_swap(&atom->value, old_val, new_val));
    return old_val;
}

/* ---------- 线程局部存储实现 ---------- */

static pthread_key_t s_tls_key;
static int s_tls_key_inited = 0;
static zhc_tls_destructor_t s_tls_destructor = NULL;

zhc_tls_key_t zhc_tls_create(zhc_tls_destructor_t destructor) {
    pthread_key_t* key = (pthread_key_t*)malloc(sizeof(pthread_key_t));
    if (!key) return NULL;

    if (pthread_key_create(key, destructor) != 0) {
        free(key);
        return NULL;
    }
    return (zhc_tls_key_t)key;
}

void* zhc_tls_get(zhc_tls_key_t key) {
    if (!key) return NULL;
    return pthread_getspecific(*(pthread_key_t*)key);
}

int zhc_tls_set(zhc_tls_key_t key, void* value) {
    if (!key) return -1;
    return pthread_setspecific(*(pthread_key_t*)key, value);
}

int zhc_tls_destroy(zhc_tls_key_t key) {
    if (!key) return -1;
    int ret = pthread_key_delete(*(pthread_key_t*)key);
    free((pthread_key_t*)key);
    return ret;
}

#endif /* ZHC_THREAD_IMPLEMENTATION */

#ifdef __cplusplus
}
#endif

#endif /* ZHC_THREAD_H */