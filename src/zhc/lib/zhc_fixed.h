#ifndef ZHC_FIXED_H
#define ZHC_FIXED_H

#include <stddef.h>
#include <stdint.h>

/*
 * ZhC 定点数类型运行时支持
 *
 * 定点数格式：
 * - Qm.n: m 位整数（含符号）+ n 位小数
 * - 总位宽 = m + n
 *
 * 支持的格式：
 * - Q0.7 (8bit): 短定点小数
 * - Q1.15 (16bit): 标准定点小数
 * - Q1.31 (32bit): 长定点小数
 * - Q8.8 (16bit): 短定点累加
 * - Q16.16 (32bit): 标准定点累加
 * - Q32.32 (64bit): 长定点累加
 */

/* 定点数格式定义 */
typedef enum {
    ZHC_FP_FRACT_HALF,   /* Q0.7, 8bit */
    ZHC_FP_FRACT,        /* Q1.15, 16bit */
    ZHC_FP_LONG_FRACT,   /* Q1.31, 32bit */
    ZHC_FP_ACCUM_SHORT,   /* Q8.8, 16bit */
    ZHC_FP_ACCUM,        /* Q16.16, 32bit */
    ZHC_FP_LONG_ACCUM,   /* Q32.32, 64bit */
    ZHC_FP_FRACT_U,      /* Q0.8 unsigned, 8bit */
    ZHC_FP_ACCUM_U,      /* Q8.8 unsigned, 16bit */
} ZhcFixedPointFormat;

/* 定点数结构体 */
typedef struct {
    int32_t raw;         /* 原始整数值 */
    uint8_t format;      /* 格式 */
    uint8_t reserved[3]; /* 对齐填充 */
} ZhcFixed32;

typedef struct {
    int64_t raw;          /* 原始整数值 */
    uint8_t format;       /* 格式 */
    uint8_t reserved[7];  /* 对齐填充 */
} ZhcFixed64;

/* 定点数创建 */
ZhcFixed32 zhc_fixed_create_i32(int32_t raw, uint8_t format);
ZhcFixed64 zhc_fixed_create_i64(int64_t raw, uint8_t format);

/* 定点数与浮点数转换 */
ZhcFixed32 zhc_fixed_from_float(float value, uint8_t format);
float zhc_fixed_to_float(ZhcFixed32 fp);
ZhcFixed64 zhc_fixed_from_double(double value, uint8_t format);
double zhc_fixed_to_double(ZhcFixed64 fp);

/* 定点数与整数转换 */
int32_t zhc_fixed_to_i32(ZhcFixed32 fp);
ZhcFixed32 zhc_fixed_from_i32(int32_t value, uint8_t format);

/* 定点数运算 */
ZhcFixed32 zhc_fixed_add(ZhcFixed32 a, ZhcFixed32 b);
ZhcFixed32 zhc_fixed_sub(ZhcFixed32 a, ZhcFixed32 b);
ZhcFixed32 zhc_fixed_mul(ZhcFixed32 a, ZhcFixed32 b);
ZhcFixed32 zhc_fixed_div(ZhcFixed32 a, ZhcFixed32 b);

/* 定点数移位 */
ZhcFixed32 zhc_fixed_shift_left(ZhcFixed32 fp, int bits);
ZhcFixed32 zhc_fixed_shift_right(ZhcFixed32 fp, int bits);

/* 定点数比较 */
int zhc_fixed_compare(ZhcFixed32 a, ZhcFixed32 b);

/* 格式信息 */
int zhc_fixed_get_frac_bits(uint8_t format);
int zhc_fixed_get_int_bits(uint8_t format);
int zhc_fixed_get_scale_factor(uint8_t format);
int zhc_fixed_is_signed(uint8_t format);

#endif /* ZHC_FIXED_H */
