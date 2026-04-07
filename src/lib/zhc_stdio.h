/**
 * stdio.h - 中文C编译器标准输入输出库
 *
 * 提供 stdio 模块对应的所有函数实现。
 * 本头文件应在使用 stdio 模块时通过 #include "stdio.h" 引入。
 *
 * 版本: 1.0
 * 作者: ZHC编译器团队
 */

#ifndef ZHC_STDIO_H
#define ZHC_STDIO_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>

/* ============================================================
 * 格式化打印
 * ============================================================ */

/**
 * zhc_printf - 格式化打印到标准输出
 *
 * 封装 printf，语义完全等价。
 * 返回值: 成功打印的字符数，出错返回负数。
 */
int zhc_printf(const char *format, ...) {
    va_list args;
    va_start(args, format);
    int ret = vprintf(format, args);
    va_end(args);
    return ret;
}

/* ============================================================
 * 类型化读取函数
 * ============================================================ */

/**
 * zhc_read_int - 从标准输入读取整数
 *
 * 使用 scanf("%d") 实现。跳过前导空白字符。
 * 如果输入不是合法整数，不修改 *result，返回 0。
 *
 * 返回值: 1 表示成功读取，0 表示失败。
 */
int zhc_read_int(int *result) {
    if (result == NULL) return 0;
    return scanf("%d", result);
}

/**
 * zhc_read_float - 从标准输入读取浮点数
 *
 * 使用 scanf("%f") 实现。跳过前导空白字符。
 * 如果输入不是合法浮点数，不修改 *result，返回 0。
 *
 * 返回值: 1 表示成功读取，0 表示失败。
 */
int zhc_read_float(float *result) {
    if (result == NULL) return 0;
    return scanf("%f", result);
}

/**
 * zhc_read_char - 从标准输入读取单个字符
 *
 * 使用 getchar() 实现。
 * 不跳过空白字符——即会读取到空格、换行等。
 *
 * 返回值: 读取到的字符(0~255)，或 EOF(-1) 表示错误/结束。
 */
int zhc_read_char(void) {
    return getchar();
}

/**
 * zhc_read_string - 从标准输入读取一行字符串（安全版本）
 *
 * 使用 fgets() 实现安全读取，最多读取 size-1 个字符。
 * 读取到的字符串以 '\0' 结尾。
 * 如果行过长被截断，缓冲区中仍包含已读入的部分。
 *
 * 参数:
 *   buf  - 目标缓冲区（不能为 NULL）
 *   size - 缓冲区大小（必须 > 0）
 *
 * 返回值:
 *   > 0: 成功读取的字符数（不含 '\0'）
 *   0:   读到了空行（仅 '\n' 被读入并替换为 '\0'）
 *   -1:  失败或遇到 EOF 且缓冲区为空
 */
int zhc_read_string(char *buf, int size) {
    if (buf == NULL || size <= 0) return -1;

    char *ret = fgets(buf, size, stdin);

    if (ret == NULL) {
        buf[0] = '\0';
        return -1;
    }

    /* 去掉末尾的换行符（如果有） */
    int len = (int)strlen(buf);
    if (len > 0 && buf[len - 1] == '\n') {
        buf[len - 1] = '\0';
        len--;
    }

    return len;
}

/* ============================================================
 * 缓冲区刷新
 * ============================================================ */

/**
 * zhc_flush - 刷新标准输出缓冲区
 *
 * 封装 fflush(stdout)。
 *
 * 返回值: 0 表示成功，EOF 表示失败。
 */
int zhc_flush(void) {
    return fflush(stdout);
}

#endif /* ZHC_STDIO_H */
