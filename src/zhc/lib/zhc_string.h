/**
 * zhc_string.h - 中文C编译器字符串处理库
 *
 * 提供 string 模块对应的所有函数实现。
 * 本头文件应在使用 string 模块时通过 #include "zhc_string.h" 引入。
 *
 * 版本: 1.0
 * 作者: ZHC编译器团队
 */

#ifndef ZHC_STRING_H
#define ZHC_STRING_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

/* ============================================================
 * 字符串基本操作
 * ============================================================ */

/**
 * zhc_strlen - 获取字符串长度
 *
 * 封装 strlen，返回字符串长度（不含'\0'）。
 * NULL 字符串返回 0。
 *
 * 参数:
 *   str - 目标字符串
 *
 * 返回值: 字符串长度
 */
int zhc_strlen(const char *str) {
    if (str == NULL) return 0;
    return (int)strlen(str);
}

/**
 * zhc_strcat - 连接两个字符串
 *
 * 封装 strcat，将 src 追加到 dest 末尾。
 * 调用者需保证 dest 缓冲区足够大。
 *
 * 参数:
 *   dest - 目标字符串缓冲区
 *   src  - 源字符串
 *
 * 返回值: 连接后的字符串指针（dest），失败返回 NULL
 */
char* zhc_strcat(char *dest, const char *src) {
    if (dest == NULL || src == NULL) return NULL;
    return strcat(dest, src);
}

/**
 * zhc_strcpy - 复制字符串
 *
 * 封装 strcpy，将 src 复制到 dest。
 * 调用者需保证 dest 缓冲区足够大。
 *
 * 参数:
 *   dest - 目标字符串缓冲区
 *   src  - 源字符串
 *
 * 返回值: 复制后的字符串指针（dest），失败返回 NULL
 */
char* zhc_strcpy(char *dest, const char *src) {
    if (dest == NULL || src == NULL) return NULL;
    return strcpy(dest, src);
}

/* ============================================================
 * 子串和查找
 * ============================================================ */

/**
 * zhc_substr - 提取子串
 *
 * 从字符串中提取指定范围的子串，返回新分配的字符串。
 * 调用者需要手动释放返回的字符串。
 *
 * 参数:
 *   str   - 源字符串
 *   start - 起始位置（从0开始）
 *   len   - 子串长度
 *
 * 返回值: 新分配的子串字符串，失败返回空字符串
 */
char* zhc_substr(const char *str, int start, int len) {
    /* 处理 NULL 输入 */
    if (str == NULL) {
        char *empty = (char*)malloc(1);
        if (empty) empty[0] = '\0';
        return empty;
    }

    int str_len = (int)strlen(str);

    /* 边界检查 */
    if (start < 0) start = 0;
    if (start >= str_len) {
        char *empty = (char*)malloc(1);
        if (empty) empty[0] = '\0';
        return empty;
    }
    if (len <= 0) {
        char *empty = (char*)malloc(1);
        if (empty) empty[0] = '\0';
        return empty;
    }

    /* 调整长度，避免越界 */
    if (start + len > str_len) {
        len = str_len - start;
    }

    /* 分配内存并复制子串 */
    char *result = (char*)malloc(len + 1);
    if (result == NULL) {
        char *empty = (char*)malloc(1);
        if (empty) empty[0] = '\0';
        return empty;
    }

    memcpy(result, str + start, len);
    result[len] = '\0';

    return result;
}

/**
 * zhc_find - 在字符串中查找子串
 *
 * 封装 strstr，返回子串首次出现的位置索引。
 *
 * 参数:
 *   str       - 源字符串
 *   substring - 要查找的子串
 *
 * 返回值: 子串首次出现的索引（从0开始），未找到返回 -1
 */
int zhc_find(const char *str, const char *substring) {
    if (str == NULL || substring == NULL) return -1;

    const char *found = strstr(str, substring);
    if (found == NULL) return -1;

    return (int)(found - str);
}

/**
 * zhc_replace - 替换字符串中的子串
 *
 * 将字符串中所有出现的 find 替换为 replace。
 * 返回新分配的字符串，调用者需要手动释放。
 *
 * 参数:
 *   str     - 源字符串
 *   find    - 要查找的子串
 *   replace - 用于替换的子串
 *
 * 返回值: 新分配的替换后的字符串
 */
char* zhc_replace(const char *str, const char *find, const char *replace) {
    /* 处理 NULL 输入 */
    if (str == NULL) {
        char *empty = (char*)malloc(1);
        if (empty) empty[0] = '\0';
        return empty;
    }

    /* 如果 find 为空或未找到，返回 str 的副本 */
    if (find == NULL || strlen(find) == 0) {
        char *result = (char*)malloc(strlen(str) + 1);
        if (result) strcpy(result, str);
        return result;
    }

    int find_len = (int)strlen(find);
    int replace_len = (replace == NULL) ? 0 : (int)strlen(replace);
    int count = 0;

    /* 统计 find 出现的次数 */
    const char *pos = str;
    while ((pos = strstr(pos, find)) != NULL) {
        count++;
        pos += find_len;
    }

    /* 如果未找到，返回 str 的副本 */
    if (count == 0) {
        char *result = (char*)malloc(strlen(str) + 1);
        if (result) strcpy(result, str);
        return result;
    }

    /* 计算结果字符串长度 */
    int new_len = (int)strlen(str) + count * (replace_len - find_len);
    char *result = (char*)malloc(new_len + 1);
    if (result == NULL) {
        char *empty = (char*)malloc(1);
        if (empty) empty[0] = '\0';
        return empty;
    }

    /* 执行替换 */
    char *dest = result;
    const char *src = str;
    while ((pos = strstr(src, find)) != NULL) {
        /* 复制 find 之前的部分 */
        int len = (int)(pos - src);
        memcpy(dest, src, len);
        dest += len;

        /* 复制替换字符串 */
        if (replace != NULL && replace_len > 0) {
            memcpy(dest, replace, replace_len);
            dest += replace_len;
        }

        /* 跳过 find */
        src = pos + find_len;
    }

    /* 复制剩余部分 */
    strcpy(dest, src);

    return result;
}

/* ============================================================
 * 字符串比较
 * ============================================================ */

/**
 * zhc_strcmp - 比较两个字符串
 *
 * 封装 strcmp，按字典序比较两个字符串。
 *
 * 参数:
 *   str1 - 第一个字符串
 *   str2 - 第二个字符串
 *
 * 返回值:
 *   < 0: str1 < str2
 *   = 0: str1 == str2
 *   > 0: str1 > str2
 *   -2:  错误（NULL指针）
 */
int zhc_strcmp(const char *str1, const char *str2) {
    if (str1 == NULL || str2 == NULL) return -2;
    return strcmp(str1, str2);
}

/* ============================================================
 * 大小写转换
 * ============================================================ */

/**
 * zhc_tolower - 将字符串转换为小写
 *
 * 直接修改原字符串，将所有大写字母转换为小写。
 *
 * 参数:
 *   str - 要转换的字符串
 *
 * 返回值: 转换后的字符串指针（str），失败返回 NULL
 */
char* zhc_tolower(char *str) {
    if (str == NULL) return NULL;

    for (int i = 0; str[i] != '\0'; i++) {
        str[i] = tolower((unsigned char)str[i]);
    }

    return str;
}

/**
 * zhc_toupper - 将字符串转换为大写
 *
 * 直接修改原字符串，将所有小写字母转换为大写。
 *
 * 参数:
 *   str - 要转换的字符串
 *
 * 返回值: 转换后的字符串指针（str），失败返回 NULL
 */
char* zhc_toupper(char *str) {
    if (str == NULL) return NULL;

    for (int i = 0; str[i] != '\0'; i++) {
        str[i] = toupper((unsigned char)str[i]);
    }

    return str;
}

/* ============================================================
 * 空白字符处理
 * ============================================================ */

/**
 * zhc_trim - 去除首尾空白字符
 *
 * 直接修改原字符串，去除开头和结尾的空白字符。
 *
 * 参数:
 *   str - 要处理的字符串
 *
 * 返回值: 处理后的字符串指针（str），失败返回 NULL
 */
char* zhc_trim(char *str) {
    if (str == NULL) return NULL;

    int len = (int)strlen(str);
    if (len == 0) return str;

    /* 去除前导空白 */
    int start = 0;
    while (start < len && isspace((unsigned char)str[start])) {
        start++;
    }

    /* 去除尾部空白 */
    int end = len - 1;
    while (end >= start && isspace((unsigned char)str[end])) {
        end--;
    }

    /* 移动字符串 */
    if (start > 0) {
        memmove(str, str + start, end - start + 1);
    }

    str[end - start + 1] = '\0';

    return str;
}

#endif /* ZHC_STRING_H */