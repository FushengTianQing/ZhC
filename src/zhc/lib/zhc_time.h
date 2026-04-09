/**
 * zhc_time.h - 时间获取与格式化库
 *
 * 提供完整的时间功能：
 * - 时间获取（Unix 时间戳、微秒精度）
 * - 时间结构化与格式化
 * - 时间计算与转换
 * - 高精度计时器
 * - 延时函数
 *
 * 版本: 1.0
 * 依赖: <time.h>, <sys/time.h>
 */

#ifndef ZHC_TIME_H
#define ZHC_TIME_H

#include <time.h>
#include <sys/time.h>
#include <stdbool.h>
#include <stddef.h>
#include <unistd.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ================================================================
 * 类型定义
 * ================================================================ */

/**
 * 时间戳类型（Unix 时间戳，秒）
 */
typedef long long zhc_timestamp_t;

/**
 * 时间结构体
 * 对应 C 标准库的 struct tm，但使用更直观的中文命名
 */
typedef struct {
    int sec;        /* 秒 (0-59) */
    int min;        /* 分 (0-59) */
    int hour;       /* 时 (0-23) */
    int day;        /* 日 (1-31) */
    int month;      /* 月 (1-12) */
    int year;       /* 年 (从 1900 开始计) */
    int wday;       /* 星期 (0-6, 周日=0) */
    int yday;       /* 年日 (0-365) */
    int isdst;      /* 夏令时标志 (>0=是, 0=否, <0=未知) */
} zhc_tm_t;

/**
 * 计时器类型
 * 使用微秒级精度
 */
typedef struct {
    long long start_us;  /* 开始时间（微秒） */
    long long end_us;    /* 结束时间（微秒，0 表示未停止） */
} zhc_timer_t;

/* ================================================================
 * 时间获取函数
 * ================================================================ */

/**
 * zhc_time_now - 获取当前时间戳
 *
 * 返回自 1970-01-01 00:00:00 UTC 以来的秒数
 *
 * 返回: 当前 Unix 时间戳
 */
zhc_timestamp_t zhc_time_now(void);

/**
 * zhc_time_now_us - 获取当前时间（微秒精度）
 *
 * 返回自 1970-01-01 00:00:00 UTC 以来的微秒数
 *
 * 返回: 当前时间戳（微秒）
 */
long long zhc_time_now_us(void);

/**
 * zhc_clock - 获取 CPU 时钟时间
 *
 * 返回程序启动以来的处理器时间（秒）
 *
 * 返回: CPU 时间（秒）
 */
double zhc_clock(void);

/**
 * zhc_time_to_struct - 时间戳转时间结构
 *
 * 将 Unix 时间戳转换为本地时区的时间结构
 *
 * 参数:
 *   timestamp - Unix 时间戳（秒）
 *   tm_out    - 输出的时间结构指针
 */
void zhc_time_to_struct(zhc_timestamp_t timestamp, zhc_tm_t* tm_out);

/**
 * zhc_struct_to_time - 时间结构转时间戳
 *
 * 将本地时区的时间结构转换为 Unix 时间戳
 *
 * 参数:
 *   tm - 输入的时间结构
 *
 * 返回: Unix 时间戳
 */
zhc_timestamp_t zhc_struct_to_time(zhc_tm_t* tm);

/* ================================================================
 * 时间格式化函数
 * ================================================================ */

/**
 * zhc_time_format - 格式化时间字符串
 *
 * 将时间结构格式化为字符串，支持以下格式说明符：
 *   %Y - 四位数年份 (如 2026)
 *   %y - 两位数年份 (如 26)
 *   %m - 月份 (01-12)
 *   %d - 日 (01-31)
 *   %H - 24小时制小时 (00-23)
 *   %I - 12小时制小时 (01-12)
 *   %M - 分钟 (00-59)
 *   %S - 秒 (00-59)
 *   %A - 完整星期名称 (如 Sunday)
 *   %a - 星期缩写 (如 Sun)
 *   %B - 完整月份名称 (如 April)
 *   %b - 月份缩写 (如 Apr)
 *   %% - 转义百分号
 *
 * 参数:
 *   buffer - 输出缓冲区
 *   size   - 缓冲区大小
 *   format - 格式字符串
 *   tm     - 时间结构
 *
 * 返回: 写入的字符数（不包括终止符），0 表示失败
 */
int zhc_time_format(char* buffer, size_t size, const char* format, zhc_tm_t* tm);

/**
 * zhc_time_parse - 解析时间字符串
 *
 * 将字符串解析为时间结构
 *
 * 参数:
 *   str     - 输入字符串
 *   format  - 格式字符串（与 zhc_time_format 相同）
 *   tm_out  - 输出的时间结构（可为 NULL）
 *
 * 返回: 解析得到的时间戳，-1 表示解析失败
 */
zhc_timestamp_t zhc_time_parse(const char* str, const char* format, zhc_tm_t* tm_out);

/* ================================================================
 * 时间计算函数
 * ================================================================ */

/**
 * zhc_time_diff - 计算时间差
 *
 * 计算两个时间戳之间的差值
 *
 * 参数:
 *   end   - 结束时间戳
 *   start - 开始时间戳
 *
 * 返回: 时间差（秒），可为负数
 */
double zhc_time_diff(zhc_timestamp_t end, zhc_timestamp_t start);

/**
 * zhc_time_add_seconds - 时间加秒
 */
zhc_timestamp_t zhc_time_add_seconds(zhc_timestamp_t time, int seconds);

/**
 * zhc_time_add_minutes - 时间加分
 */
zhc_timestamp_t zhc_time_add_minutes(zhc_timestamp_t time, int minutes);

/**
 * zhc_time_add_hours - 时间加时
 */
zhc_timestamp_t zhc_time_add_hours(zhc_timestamp_t time, int hours);

/**
 * zhc_time_add_days - 时间加天
 */
zhc_timestamp_t zhc_time_add_days(zhc_timestamp_t time, int days);

/**
 * zhc_is_leap_year - 判断闰年
 *
 * 参数:
 *   year - 年份（公历年份）
 *
 * 返回: true 表示是闰年，false 表示平年
 */
bool zhc_is_leap_year(int year);

/**
 * zhc_days_in_month - 获取月份天数
 *
 * 参数:
 *   year  - 年份
 *   month - 月份 (1-12)
 *
 * 返回: 该月的天数，非法输入返回 0
 */
int zhc_days_in_month(int year, int month);

/* ================================================================
 * 计时器函数
 * ================================================================ */

/**
 * zhc_timer_start - 开始计时
 *
 * 返回: 初始化好的计时器
 */
zhc_timer_t zhc_timer_start(void);

/**
 * zhc_timer_end - 结束计时
 *
 * 停止计时器并返回经过的时间
 *
 * 参数:
 *   timer - 计时器指针
 *
 * 返回: 经过的时间（秒）
 */
double zhc_timer_end(zhc_timer_t* timer);

/**
 * zhc_timer_elapsed - 获取已用时间
 *
 * 获取计时器从开始到当前的时间，不停止计时器
 *
 * 参数:
 *   timer - 计时器指针
 *
 * 返回: 经过的时间（秒）
 */
double zhc_timer_elapsed(zhc_timer_t* timer);

/**
 * zhc_timer_reset - 重置计时器
 *
 * 将计时器重置为当前时间
 *
 * 参数:
 *   timer - 计时器指针
 */
void zhc_timer_reset(zhc_timer_t* timer);

/* ================================================================
 * 延时函数
 * ================================================================ */

/**
 * zhc_sleep - 秒级延时
 *
 * 参数:
 *   seconds - 延时秒数
 */
void zhc_sleep(int seconds);

/**
 * zhc_sleep_ms - 毫秒级延时
 *
 * 参数:
 *   milliseconds - 延时毫秒数
 */
void zhc_sleep_ms(int milliseconds);

/**
 * zhc_sleep_us - 微秒级延时
 *
 * 参数:
 *   microseconds - 延时微秒数
 */
void zhc_sleep_us(int microseconds);

/* ================================================================
 * 实现
 * ================================================================ */

#ifdef ZHC_TIME_IMPLEMENTATION

/* ---------- 时间获取 ---------- */

zhc_timestamp_t zhc_time_now(void) {
    return (zhc_timestamp_t)time(NULL);
}

long long zhc_time_now_us(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (long long)tv.tv_sec * 1000000LL + tv.tv_usec;
}

double zhc_clock(void) {
    return (double)clock() / CLOCKS_PER_SEC;
}

void zhc_time_to_struct(zhc_timestamp_t timestamp, zhc_tm_t* tm_out) {
    time_t t = (time_t)timestamp;
    struct tm* tm = localtime(&t);

    tm_out->sec = tm->tm_sec;
    tm_out->min = tm->tm_min;
    tm_out->hour = tm->tm_hour;
    tm_out->day = tm->tm_mday;
    tm_out->month = tm->tm_mon + 1;
    tm_out->year = tm->tm_year + 1900;
    tm_out->wday = tm->tm_wday;
    tm_out->yday = tm->tm_yday;
    tm_out->isdst = tm->tm_isdst;
}

zhc_timestamp_t zhc_struct_to_time(zhc_tm_t* tm) {
    struct tm t = {
        .tm_sec = tm->sec,
        .tm_min = tm->min,
        .tm_hour = tm->hour,
        .tm_mday = tm->day,
        .tm_mon = tm->month - 1,
        .tm_year = tm->year - 1900,
        .tm_isdst = -1
    };
    return (zhc_timestamp_t)mktime(&t);
}

/* ---------- 时间格式化 ---------- */

int zhc_time_format(char* buffer, size_t size, const char* format, zhc_tm_t* tm) {
    struct tm t = {
        .tm_sec = tm->sec,
        .tm_min = tm->min,
        .tm_hour = tm->hour,
        .tm_mday = tm->day,
        .tm_mon = tm->month - 1,
        .tm_year = tm->year - 1900,
        .tm_wday = tm->wday,
        .tm_yday = tm->yday,
        .tm_isdst = tm->isdst
    };
    return (int)strftime(buffer, size, format, &t);
}

zhc_timestamp_t zhc_time_parse(const char* str, const char* format, zhc_tm_t* tm_out) {
    struct tm t = {0};
    char* result = strptime(str, format, &t);

    if (result == NULL || *result != '\0') {
        return -1;
    }

    if (tm_out != NULL) {
        tm_out->sec = t.tm_sec;
        tm_out->min = t.tm_min;
        tm_out->hour = t.tm_hour;
        tm_out->day = t.tm_mday;
        tm_out->month = t.tm_mon + 1;
        tm_out->year = t.tm_year + 1900;
        tm_out->wday = t.tm_wday;
        tm_out->yday = t.tm_yday;
        tm_out->isdst = t.tm_isdst;
    }

    return (zhc_timestamp_t)mktime(&t);
}

/* ---------- 时间计算 ---------- */

double zhc_time_diff(zhc_timestamp_t end, zhc_timestamp_t start) {
    return (double)(end - start);
}

zhc_timestamp_t zhc_time_add_seconds(zhc_timestamp_t time, int seconds) {
    return time + seconds;
}

zhc_timestamp_t zhc_time_add_minutes(zhc_timestamp_t time, int minutes) {
    return time + (zhc_timestamp_t)minutes * 60;
}

zhc_timestamp_t zhc_time_add_hours(zhc_timestamp_t time, int hours) {
    return time + (zhc_timestamp_t)hours * 3600;
}

zhc_timestamp_t zhc_time_add_days(zhc_timestamp_t time, int days) {
    return time + (zhc_timestamp_t)days * 86400;
}

bool zhc_is_leap_year(int year) {
    return (year % 4 == 0 && year % 100 != 0) || (year % 400 == 0);
}

int zhc_days_in_month(int year, int month) {
    if (month < 1 || month > 12) return 0;

    static const int days[] = {0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};

    if (month == 2 && zhc_is_leap_year(year)) {
        return 29;
    }
    return days[month];
}

/* ---------- 计时器 ---------- */

zhc_timer_t zhc_timer_start(void) {
    zhc_timer_t timer;
    struct timeval tv;
    gettimeofday(&tv, NULL);
    timer.start_us = (long long)tv.tv_sec * 1000000LL + tv.tv_usec;
    timer.end_us = 0;
    return timer;
}

double zhc_timer_end(zhc_timer_t* timer) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    timer->end_us = (long long)tv.tv_sec * 1000000LL + tv.tv_usec;
    return (timer->end_us - timer->start_us) / 1000000.0;
}

double zhc_timer_elapsed(zhc_timer_t* timer) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    long long now = (long long)tv.tv_sec * 1000000LL + tv.tv_usec;
    return (now - timer->start_us) / 1000000.0;
}

void zhc_timer_reset(zhc_timer_t* timer) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    timer->start_us = (long long)tv.tv_sec * 1000000LL + tv.tv_usec;
    timer->end_us = 0;
}

/* ---------- 延时 ---------- */

void zhc_sleep(int seconds) {
    sleep((unsigned int)seconds);
}

void zhc_sleep_ms(int milliseconds) {
    usleep((unsigned int)(milliseconds * 1000));
}

void zhc_sleep_us(int microseconds) {
    usleep((unsigned int)microseconds);
}

#endif /* ZHC_TIME_IMPLEMENTATION */

#ifdef __cplusplus
}
#endif

#endif /* ZHC_TIME_H */
