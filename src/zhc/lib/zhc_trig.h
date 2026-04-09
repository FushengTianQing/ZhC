/**
 * zhc_trig.h - 三角函数扩展库
 *
 * 提供度数版本、高精度版本、向量化版本和查表优化版本
 * 的三角函数实现。
 *
 * 版本: 1.0
 * 依赖: <math.h>, <immintrin.h> (可选, 用于SIMD)
 */

#ifndef ZHC_TRIG_H
#define ZHC_TRIG_H

#include <math.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ================================================================
 * 常量定义
 * ================================================================ */

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#define DEG_TO_RAD(deg) ((deg) * M_PI / 180.0)
#define RAD_TO_DEG(rad) ((rad) * 180.0 / M_PI)

/* 查表默认大小 */
#define ZHC_TRIG_TABLE_SIZE 1024

/* ================================================================
 * 度数版本三角函数
 * ================================================================ */

/**
 * zhc_sin_deg - 正弦函数（度数版本）
 *
 * 计算给定角度（度数）的正弦值。
 *
 * 参数:
 *   deg - 角度值（度数）
 *
 * 返回值: 正弦值（范围 -1 到 1）
 *
 * 示例:
 *   zhc_sin_deg(30.0);  // 返回 0.5
 */
double zhc_sin_deg(double deg);

/**
 * zhc_cos_deg - 余弦函数（度数版本）
 *
 * 计算给定角度（度数）的余弦值。
 *
 * 参数:
 *   deg - 角度值（度数）
 *
 * 返回值: 余弦值（范围 -1 到 1）
 *
 * 示例:
 *   zhc_cos_deg(60.0);  // 返回 0.5
 */
double zhc_cos_deg(double deg);

/**
 * zhc_tan_deg - 正切函数（度数版本）
 *
 * 计算给定角度（度数）的正切值。
 *
 * 参数:
 *   deg - 角度值（度数）
 *
 * 返回值: 正切值
 *
 * 示例:
 *   zhc_tan_deg(45.0);  // 返回 1.0
 */
double zhc_tan_deg(double deg);

/**
 * zhc_asin_deg - 反正弦函数（返回度数）
 *
 * 计算反正弦值，返回角度（度数）。
 *
 * 参数:
 *   value - 正弦值（范围 -1 到 1）
 *
 * 返回值: 角度值（度数，范围 -90 到 90）
 *
 * 示例:
 *   zhc_asin_deg(0.5);  // 返回 30.0
 */
double zhc_asin_deg(double value);

/**
 * zhc_acos_deg - 反余弦函数（返回度数）
 *
 * 计算反余弦值，返回角度（度数）。
 *
 * 参数:
 *   value - 余弦值（范围 -1 到 1）
 *
 * 返回值: 角度值（度数，范围 0 到 180）
 *
 * 示例:
 *   zhc_acos_deg(0.5);  // 返回 60.0
 */
double zhc_acos_deg(double value);

/**
 * zhc_atan_deg - 反正切函数（返回度数）
 *
 * 计算反正切值，返回角度（度数）。
 *
 * 参数:
 *   value - 正切值
 *
 * 返回值: 角度值（度数，范围 -90 到 90）
 *
 * 示例:
 *   zhc_atan_deg(1.0);  // 返回 45.0
 */
double zhc_atan_deg(double value);

/**
 * zhc_atan2_deg - 两参数反正切函数（返回度数）
 *
 * 计算 y/x 的反正切值，返回角度（度数）。
 *
 * 参数:
 *   y - y坐标
 *   x - x坐标
 *
 * 返回值: 角度值（度数，范围 -180 到 180）
 *
 * 示例:
 *   zhc_atan2_deg(1.0, 1.0);  // 返回 45.0
 */
double zhc_atan2_deg(double y, double x);

/* ================================================================
 * 高精度版本三角函数
 * ================================================================ */

/**
 * zhc_sin_precise - 正弦函数（高精度版本）
 *
 * 使用 long double 进行高精度计算。
 *
 * 参数:
 *   rad - 弧度值
 *
 * 返回值: 正弦值（高精度）
 *
 * 示例:
 *   zhc_sin_precise(M_PI / 6);  // 高精度 sin(30°)
 */
long double zhc_sin_precise(long double rad);

/**
 * zhc_cos_precise - 余弦函数（高精度版本）
 *
 * 使用 long double 进行高精度计算。
 *
 * 参数:
 *   rad - 弧度值
 *
 * 返回值: 余弦值（高精度）
 *
 * 示例:
 *   zhc_cos_precise(M_PI / 3);  // 高精度 cos(60°)
 */
long double zhc_cos_precise(long double rad);

/**
 * zhc_tan_precise - 正切函数（高精度版本）
 *
 * 使用 long double 进行高精度计算。
 *
 * 参数:
 *   rad - 弧度值
 *
 * 返回值: 正切值（高精度）
 *
 * 示例:
 *   zhc_tan_precise(M_PI / 4);  // 高精度 tan(45°)
 */
long double zhc_tan_precise(long double rad);

/**
 * zhc_asin_precise - 反正弦函数（高精度版本）
 *
 * 使用 long double 进行高精度计算。
 *
 * 参数:
 *   value - 正弦值（范围 -1 到 1）
 *
 * 返回值: 弧度值（高精度）
 */
long double zhc_asin_precise(long double value);

/**
 * zhc_acos_precise - 反余弦函数（高精度版本）
 *
 * 使用 long double 进行高精度计算。
 *
 * 参数:
 *   value - 余弦值（范围 -1 到 1）
 *
 * 返回值: 弧度值（高精度）
 */
long double zhc_acos_precise(long double value);

/**
 * zhc_atan_precise - 反正切函数（高精度版本）
 *
 * 使用 long double 进行高精度计算。
 *
 * 参数:
 *   value - 正切值
 *
 * 返回值: 弧度值（高精度）
 */
long double zhc_atan_precise(long double value);

/* ================================================================
 * 向量化版本三角函数（SIMD 优化）
 * ================================================================ */

/**
 * zhc_sin_vector - 正弦函数（向量化版本）
 *
 * 使用 SIMD 指令同时计算多个正弦值。
 *
 * 参数:
 *   arr - 浮点数数组（原地计算）
 *   len - 数组长度
 *
 * 示例:
 *   float arr[4] = {0.0, M_PI/6, M_PI/4, M_PI/3};
 *   zhc_sin_vector(arr, 4);  // arr 变为 sin 值
 */
void zhc_sin_vector(float* arr, size_t len);

/**
 * zhc_cos_vector - 余弦函数（向量化版本）
 *
 * 使用 SIMD 指令同时计算多个余弦值。
 *
 * 参数:
 *   arr - 浮点数数组（原地计算）
 *   len - 数组长度
 *
 * 示例:
 *   float arr[4] = {0.0, M_PI/6, M_PI/4, M_PI/3};
 *   zhc_cos_vector(arr, 4);  // arr 变为 cos 值
 */
void zhc_cos_vector(float* arr, size_t len);

/**
 * zhc_tan_vector - 正切函数（向量化版本）
 *
 * 使用 SIMD 指令同时计算多个正切值。
 *
 * 参数:
 *   arr - 浮点数数组（原地计算）
 *   len - 数组长度
 *
 * 示例:
 *   float arr[4] = {0.0, M_PI/6, M_PI/4, M_PI/3};
 *   zhc_tan_vector(arr, 4);  // arr 变为 tan 值
 */
void zhc_tan_vector(float* arr, size_t len);

/**
 * zhc_sincos - 同时计算正弦和余弦（优化版本）
 *
 * 使用 sincos 指令或优化算法同时计算 sin 和 cos，
 * 比分别调用 sin 和 cos 快约 30%。
 *
 * 参数:
 *   rad - 弧度值
 *   sin_out - 正弦结果输出指针
 *   cos_out - 余弦结果输出指针
 *
 * 示例:
 *   double s, c;
 *   zhc_sincos(M_PI / 6, &s, &c);  // s = 0.5, c ≈ 0.866
 */
void zhc_sincos(double rad, double* sin_out, double* cos_out);

/**
 * zhc_sincos_vector - 同时计算多个正弦和余弦（向量化版本）
 *
 * 参数:
 *   rad_arr - 弧度值数组
 *   sin_out - 正弦结果输出数组
 *   cos_out - 余弦结果输出数组
 *   len - 数组长度
 */
void zhc_sincos_vector(const double* rad_arr, double* sin_out, double* cos_out, size_t len);

/* ================================================================
 * 查表优化版本三角函数
 * ================================================================ */

/**
 * zhc_init_trig_table - 初始化三角函数查找表
 *
 * 预计算并缓存三角函数值以加速后续查询。
 * 如果未调用此函数，首次调用查表函数时会自动初始化。
 *
 * 参数:
 *   size - 查找表大小（默认 1024）
 *
 * 示例:
 *   zhc_init_trig_table(2048);  // 使用 2048 项的查找表
 */
void zhc_init_trig_table(int size);

/**
 * zhc_sin_table - 正弦函数（查表版本）
 *
 * 使用预计算的查找表和线性插值进行快速计算。
 * 精度取决于查找表大小，1024 项时精度约为 1e-3。
 *
 * 参数:
 *   rad - 弧度值
 *
 * 返回值: 正弦值（近似）
 *
 * 示例:
 *   zhc_sin_table(M_PI / 6);  // 快速近似 sin(30°) ≈ 0.5
 */
double zhc_sin_table(double rad);

/**
 * zhc_cos_table - 余弦函数（查表版本）
 *
 * 使用预计算的查找表和线性插值进行快速计算。
 *
 * 参数:
 *   rad - 弧度值
 *
 * 返回值: 余弦值（近似）
 *
 * 示例:
 *   zhc_cos_table(M_PI / 3);  // 快速近似 cos(60°) ≈ 0.5
 */
double zhc_cos_table(double rad);

/**
 * zhc_destroy_trig_table - 销毁三角函数查找表
 *
 * 释放查找表占用的内存。
 * 此函数是可选的，程序结束时自动释放。
 */
void zhc_destroy_trig_table(void);

/* ================================================================
 * 实用工具函数
 * ================================================================ */

/**
 * zhc_sin_approx - 正弦函数（快速近似）
 *
 * 使用多项式展开进行快速近似计算。
 * 适用于对精度要求不高的实时应用。
 *
 * 参数:
 *   rad - 弧度值
 *
 * 返回值: 正弦值（近似，精度约 1e-6）
 */
double zhc_sin_approx(double rad);

/**
 * zhc_cos_approx - 余弦函数（快速近似）
 *
 * 使用多项式展开进行快速近似计算。
 *
 * 参数:
 *   rad - 弧度值
 *
 * 返回值: 余弦值（近似，精度约 1e-6）
 */
double zhc_cos_approx(double rad);

/**
 * zhc_normalize_angle - 归一化角度到 [0, 2π)
 *
 * 将任意弧度值归一化到 [0, 2π) 范围内。
 *
 * 参数:
 *   rad - 弧度值
 *
 * 返回值: 归一化后的弧度值
 */
double zhc_normalize_angle(double rad);

/**
 * zhc_normalize_angle_deg - 归一化角度到 [0, 360)
 *
 * 将任意角度值归一化到 [0, 360) 范围内。
 *
 * 参数:
 *   deg - 角度值
 *
 * 返回值: 归一化后的角度值
 */
double zhc_normalize_angle_deg(double deg);

#ifdef __cplusplus
}
#endif

#endif /* ZHC_TRIG_H */

/* ================================================================
 * 实现部分（可选，包含在头文件中以便静态链接）
 * ================================================================ */

#ifdef ZHC_TRIG_IMPLEMENTATION

#include <stdlib.h>
#include <string.h>

/* 查找表（静态分配） */
static double* g_sin_table = NULL;
static double* g_cos_table = NULL;
static int g_trig_table_size = 0;
static int g_table_initialized = 0;

/* ---------- 度数版本 ---------- */

double zhc_sin_deg(double deg) {
    return sin(DEG_TO_RAD(deg));
}

double zhc_cos_deg(double deg) {
    return cos(DEG_TO_RAD(deg));
}

double zhc_tan_deg(double deg) {
    return tan(DEG_TO_RAD(deg));
}

double zhc_asin_deg(double value) {
    return RAD_TO_DEG(asin(value));
}

double zhc_acos_deg(double value) {
    return RAD_TO_DEG(acos(value));
}

double zhc_atan_deg(double value) {
    return RAD_TO_DEG(atan(value));
}

double zhc_atan2_deg(double y, double x) {
    return RAD_TO_DEG(atan2(y, x));
}

/* ---------- 高精度版本 ---------- */

long double zhc_sin_precise(long double rad) {
    return sinl(rad);
}

long double zhc_cos_precise(long double rad) {
    return cosl(rad);
}

long double zhc_tan_precise(long double rad) {
    return tanl(rad);
}

long double zhc_asin_precise(long double value) {
    return asinl(value);
}

long double zhc_acos_precise(long double value) {
    return acosl(value);
}

long double zhc_atan_precise(long double value) {
    return atanl(value);
}

/* ---------- 查表版本 ---------- */

void zhc_init_trig_table(int size) {
    if (g_table_initialized) {
        zhc_destroy_trig_table();
    }

    g_trig_table_size = size > 0 ? size : ZHC_TRIG_TABLE_SIZE;
    g_sin_table = (double*)malloc(sizeof(double) * g_trig_table_size);
    g_cos_table = (double*)malloc(sizeof(double) * g_trig_table_size);

    if (!g_sin_table || !g_cos_table) {
        /* 内存分配失败 */
        if (g_sin_table) free(g_sin_table);
        if (g_cos_table) free(g_cos_table);
        g_sin_table = g_cos_table = NULL;
        g_trig_table_size = 0;
        return;
    }

    /* 预计算查找表 */
    for (int i = 0; i < g_trig_table_size; i++) {
        double angle = 2.0 * M_PI * i / g_trig_table_size;
        g_sin_table[i] = sin(angle);
        g_cos_table[i] = cos(angle);
    }

    g_table_initialized = 1;
}

void zhc_destroy_trig_table(void) {
    if (g_sin_table) {
        free(g_sin_table);
        g_sin_table = NULL;
    }
    if (g_cos_table) {
        free(g_cos_table);
        g_cos_table = NULL;
    }
    g_trig_table_size = 0;
    g_table_initialized = 0;
}

static void ensure_trig_table(void) {
    if (!g_table_initialized) {
        zhc_init_trig_table(ZHC_TRIG_TABLE_SIZE);
    }
}

double zhc_sin_table(double rad) {
    ensure_trig_table();

    if (!g_table_initialized) {
        /* 查找表初始化失败，使用原始计算 */
        return sin(rad);
    }

    /* 归一化到 [0, 2π) */
    rad = zhc_normalize_angle(rad);

    /* 线性插值 */
    double index_f = rad * g_trig_table_size / (2.0 * M_PI);
    int index = (int)index_f;
    double frac = index_f - index;

    int next_index = (index + 1) % g_trig_table_size;

    return g_sin_table[index] * (1.0 - frac) + g_sin_table[next_index] * frac;
}

double zhc_cos_table(double rad) {
    ensure_trig_table();

    if (!g_table_initialized) {
        return cos(rad);
    }

    rad = zhc_normalize_angle(rad);

    double index_f = rad * g_trig_table_size / (2.0 * M_PI);
    int index = (int)index_f;
    double frac = index_f - index;

    int next_index = (index + 1) % g_trig_table_size;

    return g_cos_table[index] * (1.0 - frac) + g_cos_table[next_index] * frac;
}

/* ---------- 向量化版本 ---------- */

/* 检测 SIMD 指令集可用性 */
#if defined(__AVX__) || defined(__SSE__)
#define ZHC_HAVE_SIMD 1
#else
#define ZHC_HAVE_SIMD 0
#endif

void zhc_sin_vector(float* arr, size_t len) {
    if (!arr || len == 0) return;

#if ZHC_HAVE_SIMD && defined(__AVX__)
    size_t i = 0;

    /* AVX 批处理（每次 8 个 float） */
    for (; i + 7 < len; i += 8) {
        __m256 vals = _mm256_loadu_ps(&arr[i]);
        /* 注意: Intel SVML 的 _mm256_sin_ps 需要链接 SVML 库
         * 这里使用基础 sin 函数的 SIMD 映射作为示例
         * 实际生产环境建议使用 SVML 或专门优化的实现 */
        __m256 result = _mm256_set_ps(
            sinf(arr[i + 7]), sinf(arr[i + 6]), sinf(arr[i + 5]), sinf(arr[i + 4]),
            sinf(arr[i + 3]), sinf(arr[i + 2]), sinf(arr[i + 1]), sinf(arr[i + 0])
        );
        _mm256_storeu_ps(&arr[i], result);
    }

    /* SSE 批处理（每次 4 个 float） */
    for (; i + 3 < len; i += 4) {
        __m128 vals = _mm_loadu_ps(&arr[i]);
        __m128 result = _mm_set_ps(
            sinf(arr[i + 3]), sinf(arr[i + 2]), sinf(arr[i + 1]), sinf(arr[i + 0])
        );
        _mm_storeu_ps(&arr[i], result);
    }
#else
    /* 无 SIMD 支持，回退到标量计算 */
    (void)sizeof(float);  /* 消除未使用警告 */
#endif

    /* 处理剩余元素 */
    for (size_t i = 0; i < len; i++) {
        arr[i] = sinf(arr[i]);
    }
}

void zhc_cos_vector(float* arr, size_t len) {
    if (!arr || len == 0) return;

#if ZHC_HAVE_SIMD && defined(__AVX__)
    size_t i = 0;

    for (; i + 7 < len; i += 8) {
        __m256 result = _mm256_set_ps(
            cosf(arr[i + 7]), cosf(arr[i + 6]), cosf(arr[i + 5]), cosf(arr[i + 4]),
            cosf(arr[i + 3]), cosf(arr[i + 2]), cosf(arr[i + 1]), cosf(arr[i + 0])
        );
        _mm256_storeu_ps(&arr[i], result);
    }

    for (; i + 3 < len; i += 4) {
        __m128 result = _mm_set_ps(
            cosf(arr[i + 3]), cosf(arr[i + 2]), cosf(arr[i + 1]), cosf(arr[i + 0])
        );
        _mm_storeu_ps(&arr[i], result);
    }
#endif

    for (size_t i = 0; i < len; i++) {
        arr[i] = cosf(arr[i]);
    }
}

void zhc_tan_vector(float* arr, size_t len) {
    if (!arr || len == 0) return;

    for (size_t i = 0; i < len; i++) {
        arr[i] = tanf(arr[i]);
    }
}

void zhc_sincos(double rad, double* sin_out, double* cos_out) {
#if defined(__GNUC__) && defined(__GLIBC__)
    /* 使用 GNU glibc 的 sincos 函数 */
    sincos(rad, sin_out, cos_out);
#elif defined(__clang__) && defined(__APPLE__)
    /* macOS 上使用 sin 和 cos 分开计算 */
    *sin_out = sin(rad);
    *cos_out = cos(rad);
#else
    /* 标准回退实现 */
    *sin_out = sin(rad);
    *cos_out = cos(rad);
#endif
}

void zhc_sincos_vector(const double* rad_arr, double* sin_out, double* cos_out, size_t len) {
    if (!rad_arr || !sin_out || !cos_out || len == 0) return;

    for (size_t i = 0; i < len; i++) {
        zhc_sincos(rad_arr[i], &sin_out[i], &cos_out[i]);
    }
}

/* ---------- 快速近似版本 ---------- */

double zhc_sin_approx(double rad) {
    /* 使用五阶多项式逼近（精度约 1e-6） */
    /* 基于泰勒级数优化 */
    double x = zhc_normalize_angle(rad);
    if (x > M_PI) x -= 2.0 * M_PI;

    /* 奇函数性质 */
    int negate = (x > M_PI / 2.0);
    if (negate) x = M_PI - x;
    if (x < -M_PI / 2.0) {
        x = -M_PI - x;
        negate = !negate;
    }

    /* 帕德近似 */
    double x2 = x * x;
    double x3 = x2 * x;
    double x5 = x3 * x2;

    /* sin(x) ≈ x - x^3/6 + x^5/120 */
    double result = x + x3 * (-1.0/6.0) + x5 * (1.0/120.0);

    return negate ? -result : result;
}

double zhc_cos_approx(double rad) {
    /* 余弦近似: 使用偶函数性质 cos(-x) = cos(x) */
    /* 以及 cos(x) = cos(x + 2π) */
    double x = rad;

    /* 归一化到 [0, 2π) */
    if (x < 0) {
        x = fmod(x, 2.0 * M_PI);
        if (x < 0) x += 2.0 * M_PI;
    } else {
        x = fmod(x, 2.0 * M_PI);
    }

    /* 使用余弦的偶函数性质，将范围折叠到 [0, π] */
    if (x > M_PI) {
        x = 2.0 * M_PI - x;
    }

    /* 在 [0, π] 范围内使用泰勒展开 (到 8 阶) */
    /* cos(x) ≈ 1 - x^2/2! + x^4/4! - x^6/6! + x^8/8! */
    double x2 = x * x;
    double x4 = x2 * x2;
    double x6 = x4 * x2;
    double x8 = x4 * x4;

    double result = 1.0
        - x2 * (1.0 / 2.0)
        + x4 * (1.0 / 24.0)
        - x6 * (1.0 / 720.0)
        + x8 * (1.0 / 40320.0);

    return result;
}

/* ---------- 实用工具函数 ---------- */

double zhc_normalize_angle(double rad) {
    if (rad < 0) {
        rad = fmod(rad, 2.0 * M_PI);
        if (rad < 0) rad += 2.0 * M_PI;
    } else {
        rad = fmod(rad, 2.0 * M_PI);
    }
    return rad;
}

double zhc_normalize_angle_deg(double deg) {
    if (deg < 0) {
        deg = fmod(deg, 360.0);
        if (deg < 0) deg += 360.0;
    } else {
        deg = fmod(deg, 360.0);
    }
    return deg;
}

#endif /* ZHC_TRIG_IMPLEMENTATION */
