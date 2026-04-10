/*
 * ZhC 定点数类型运行时实现
 *
 * 作者：远
 * 日期：2026-04-10
 */

#include "zhc_fixed.h"

/* 格式信息表 */
typedef struct {
    int int_bits;
    int frac_bits;
    int scale_factor;
    int is_signed;
} FixedPointInfo;

static const FixedPointInfo FORMAT_INFO[] = {
    /* ZHC_FP_FRACT_HALF */  {1, 7, 128, 1},
    /* ZHC_FP_FRACT */       {1, 15, 32768, 1},
    /* ZHC_FP_LONG_FRACT */  {1, 31, 2147483648LL, 1},
    /* ZHC_FP_ACCUM_SHORT */ {8, 8, 256, 1},
    /* ZHC_FP_ACCUM */       {16, 16, 65536, 1},
    /* ZHC_FP_LONG_ACCUM */  {32, 32, 4294967296LL, 1},
    /* ZHC_FP_FRACT_U */     {0, 8, 256, 0},
    /* ZHC_FP_ACCUM_U */     {8, 8, 256, 0},
};

int zhc_fixed_get_frac_bits(uint8_t format) {
    if (format >= sizeof(FORMAT_INFO) / sizeof(FORMAT_INFO[0])) {
        return 0;
    }
    return FORMAT_INFO[format].frac_bits;
}

int zhc_fixed_get_int_bits(uint8_t format) {
    if (format >= sizeof(FORMAT_INFO) / sizeof(FORMAT_INFO[0])) {
        return 0;
    }
    return FORMAT_INFO[format].int_bits;
}

int zhc_fixed_get_scale_factor(uint8_t format) {
    if (format >= sizeof(FORMAT_INFO) / sizeof(FORMAT_INFO[0])) {
        return 1;
    }
    return FORMAT_INFO[format].scale_factor;
}

int zhc_fixed_is_signed(uint8_t format) {
    if (format >= sizeof(FORMAT_INFO) / sizeof(FORMAT_INFO[0])) {
        return 1;
    }
    return FORMAT_INFO[format].is_signed;
}

/* ========== 定点数创建 ========== */

ZhcFixed32 zhc_fixed_create_i32(int32_t raw, uint8_t format) {
    ZhcFixed32 result;
    result.raw = raw;
    result.format = format;
    return result;
}

ZhcFixed64 zhc_fixed_create_i64(int64_t raw, uint8_t format) {
    ZhcFixed64 result;
    result.raw = raw;
    result.format = format;
    return result;
}

/* ========== 定点数与浮点数转换 ========== */

ZhcFixed32 zhc_fixed_from_float(float value, uint8_t format) {
    ZhcFixed32 result;
    int scale = zhc_fixed_get_scale_factor(format);

    /* 乘以缩放因子并四舍五入 */
    float scaled = value * (float)scale;
    int32_t rounded = (int32_t)(scaled >= 0 ? scaled + 0.5f : scaled - 0.5f);

    result.raw = rounded;
    result.format = format;
    return result;
}

float zhc_fixed_to_float(ZhcFixed32 fp) {
    int scale = zhc_fixed_get_scale_factor(fp.format);
    return (float)fp.raw / (float)scale;
}

ZhcFixed64 zhc_fixed_from_double(double value, uint8_t format) {
    ZhcFixed64 result;
    int scale = zhc_fixed_get_scale_factor(format);

    /* 乘以缩放因子并四舍五入 */
    double scaled = value * (double)scale;
    int64_t rounded = (int64_t)(scaled >= 0 ? scaled + 0.5 : scaled - 0.5);

    result.raw = rounded;
    result.format = format;
    return result;
}

double zhc_fixed_to_double(ZhcFixed64 fp) {
    int scale = zhc_fixed_get_scale_factor(fp.format);
    return (double)fp.raw / (double)scale;
}

/* ========== 定点数与整数转换 ========== */

int32_t zhc_fixed_to_i32(ZhcFixed32 fp) {
    int frac_bits = zhc_fixed_get_frac_bits(fp.format);
    /* 右移以截断小数部分 */
    return fp.raw >> frac_bits;
}

ZhcFixed32 zhc_fixed_from_i32(int32_t value, uint8_t format) {
    ZhcFixed32 result;
    int frac_bits = zhc_fixed_get_frac_bits(fp.format);

    /* 左移以创建定点数 */
    result.raw = value << frac_bits;
    result.format = format;
    return result;
}

/* ========== 定点数运算 ========== */

/* 检查两个定点数格式是否相同 */
static int check_same_format(ZhcFixed32 a, ZhcFixed32 b) {
    return a.format == b.format;
}

ZhcFixed32 zhc_fixed_add(ZhcFixed32 a, ZhcFixed32 b) {
    ZhcFixed32 result;
    if (!check_same_format(a, b)) {
        /* 格式不匹配，返回零 */
        result.raw = 0;
        result.format = a.format;
        return result;
    }
    result.raw = a.raw + b.raw;
    result.format = a.format;
    return result;
}

ZhcFixed32 zhc_fixed_sub(ZhcFixed32 a, ZhcFixed32 b) {
    ZhcFixed32 result;
    if (!check_same_format(a, b)) {
        result.raw = 0;
        result.format = a.format;
        return result;
    }
    result.raw = a.raw - b.raw;
    result.format = a.format;
    return result;
}

ZhcFixed32 zhc_fixed_mul(ZhcFixed32 a, ZhcFixed32 b) {
    ZhcFixed32 result;
    int32_t product;
    int frac_bits;

    if (!check_same_format(a, b)) {
        result.raw = 0;
        result.format = a.format;
        return result;
    }

    /* 乘法：结果右移以对齐小数位 */
    product = a.raw * b.raw;
    frac_bits = zhc_fixed_get_frac_bits(a.format);

    /* 乘积右移以保持小数精度 */
    result.raw = product >> frac_bits;
    result.format = a.format;
    return result;
}

ZhcFixed32 zhc_fixed_div(ZhcFixed32 a, ZhcFixed32 b) {
    ZhcFixed32 result;
    int64_t dividend;
    int frac_bits;

    if (!check_same_format(a, b) || b.raw == 0) {
        result.raw = 0;
        result.format = a.format;
        return result;
    }

    /* 被除数左移以对齐小数位 */
    frac_bits = zhc_fixed_get_frac_bits(a.format);
    dividend = ((int64_t)a.raw) << frac_bits;

    result.raw = (int32_t)(dividend / b.raw);
    result.format = a.format;
    return result;
}

/* ========== 定点数移位 ========== */

ZhcFixed32 zhc_fixed_shift_left(ZhcFixed32 fp, int bits) {
    ZhcFixed32 result;
    result.raw = fp.raw << bits;
    result.format = fp.format;
    return result;
}

ZhcFixed32 zhc_fixed_shift_right(ZhcFixed32 fp, int bits) {
    ZhcFixed32 result;
    if (zhc_fixed_is_signed(fp.format)) {
        /* 算术右移 */
        result.raw = fp.raw >> bits;
    } else {
        /* 逻辑右移 */
        result.raw = ((uint32_t)fp.raw) >> bits;
    }
    result.format = fp.format;
    return result;
}

/* ========== 定点数比较 ========== */

int zhc_fixed_compare(ZhcFixed32 a, ZhcFixed32 b) {
    if (!check_same_format(a, b)) {
        return 0;
    }
    if (a.raw > b.raw) return 1;
    if (a.raw < b.raw) return -1;
    return 0;
}
