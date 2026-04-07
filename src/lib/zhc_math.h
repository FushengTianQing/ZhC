/**
 * zhc_math.h - 中文C编译器数学库
 *
 * 提供 math 模块对应的所有函数实现。
 * 本头文件应在使用 math 模块时通过 #include "zhc_math.h" 引入。
 *
 * 版本: 1.0
 * 作者: ZHC编译器团队
 */

#ifndef ZHC_MATH_H
#define ZHC_MATH_H

#include <math.h>
#include <stdio.h>
#include <stdlib.h>

/* ============================================================
 * 常量定义
 * ============================================================ */

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#ifndef M_E
#define M_E 2.7182818284590452354
#endif

/* ============================================================
 * 三角函数
 * ============================================================ */

/**
 * zhc_sin - 正弦函数
 *
 * 封装 sin，计算角度的正弦值。
 *
 * 参数:
 *   x - 弧度值
 *
 * 返回值: 正弦值
 */
double zhc_sin(double x) {
    return sin(x);
}

/**
 * zhc_cos - 余弦函数
 *
 * 封装 cos，计算角度的余弦值。
 *
 * 参数:
 *   x - 弧度值
 *
 * 返回值: 余弦值
 */
double zhc_cos(double x) {
    return cos(x);
}

/**
 * zhc_tan - 正切函数
 *
 * 封装 tan，计算角度的正切值。
 *
 * 参数:
 *   x - 弧度值
 *
 * 返回值: 正切值
 */
double zhc_tan(double x) {
    return tan(x);
}

/**
 * zhc_asin - 反正弦函数
 *
 * 封装 asin，计算反正弦值。
 *
 * 参数:
 *   x - 正弦值（范围 -1 到 1）
 *
 * 返回值: 弧度值（范围 -π/2 到 π/2）
 */
double zhc_asin(double x) {
    return asin(x);
}

/**
 * zhc_acos - 反余弦函数
 *
 * 封装 acos，计算反余弦值。
 *
 * 参数:
 *   x - 余弦值（范围 -1 到 1）
 *
 * 返回值: 弧度值（范围 0 到 π）
 */
double zhc_acos(double x) {
    return acos(x);
}

/**
 * zhc_atan - 反正切函数
 *
 * 封装 atan，计算反正切值。
 *
 * 参数:
 *   x - 正切值
 *
 * 返回值: 弧度值（范围 -π/2 到 π/2）
 */
double zhc_atan(double x) {
    return atan(x);
}

/**
 * zhc_atan2 - 两参数反正切函数
 *
 * 封装 atan2，计算 y/x 的反正切值。
 *
 * 参数:
 *   y - y坐标
 *   x - x坐标
 *
 * 返回值: 弧度值（范围 -π 到 π）
 */
double zhc_atan2(double y, double x) {
    return atan2(y, x);
}

/* ============================================================
 * 双曲函数
 * ============================================================ */

/**
 * zhc_sinh - 双曲正弦函数
 *
 * 封装 sinh，计算双曲正弦值。
 *
 * 参数:
 *   x - 输入值
 *
 * 返回值: 双曲正弦值
 */
double zhc_sinh(double x) {
    return sinh(x);
}

/**
 * zhc_cosh - 双曲余弦函数
 *
 * 封装 cosh，计算双曲余弦值。
 *
 * 参数:
 *   x - 输入值
 *
 * 返回值: 双曲余弦值
 */
double zhc_cosh(double x) {
    return cosh(x);
}

/**
 * zhc_tanh - 双曲正切函数
 *
 * 封装 tanh，计算双曲正切值。
 *
 * 参数:
 *   x - 输入值
 *
 * 返回值: 双曲正切值
 */
double zhc_tanh(double x) {
    return tanh(x);
}

/* ============================================================
 * 指数与对数
 * ============================================================ */

/**
 * zhc_exp - 自然指数函数
 *
 * 封装 exp，计算 e 的 x 次方。
 *
 * 参数:
 *   x - 指数值
 *
 * 返回值: e^x
 */
double zhc_exp(double x) {
    return exp(x);
}

/**
 * zhc_log - 自然对数函数
 *
 * 封装 log，计算自然对数。
 *
 * 参数:
 *   x - 输入值（必须 > 0）
 *
 * 返回值: ln(x)
 */
double zhc_log(double x) {
    if (x <= 0.0) {
        return NAN;
    }
    return log(x);
}

/**
 * zhc_log10 - 常用对数函数
 *
 * 封装 log10，计算以10为底的对数。
 *
 * 参数:
 *   x - 输入值（必须 > 0）
 *
 * 返回值: log10(x)
 */
double zhc_log10(double x) {
    if (x <= 0.0) {
        return NAN;
    }
    return log10(x);
}

/**
 * zhc_log2 - 二进制对数函数
 *
 * 封装 log2，计算以2为底的对数。
 *
 * 参数:
 *   x - 输入值（必须 > 0）
 *
 * 返回值: log2(x)
 */
double zhc_log2(double x) {
    if (x <= 0.0) {
        return NAN;
    }
    return log2(x);
}

/* ============================================================
 * 幂运算
 * ============================================================ */

/**
 * zhc_pow - 幂函数
 *
 * 封装 pow，计算底数的指数次方。
 *
 * 参数:
 *   base     - 底数
 *   exponent - 指数
 *
 * 返回值: base^exponent
 */
double zhc_pow(double base, double exponent) {
    return pow(base, exponent);
}

/**
 * zhc_sqrt - 平方根函数
 *
 * 封装 sqrt，计算平方根。
 *
 * 参数:
 *   x - 输入值（必须 ≥ 0）
 *
 * 返回值: √x
 */
double zhc_sqrt(double x) {
    if (x < 0.0) {
        return NAN;
    }
    return sqrt(x);
}

/**
 * zhc_cbrt - 立方根函数
 *
 * 封装 cbrt，计算立方根。
 *
 * 参数:
 *   x - 输入值
 *
 * 返回值: ³√x
 */
double zhc_cbrt(double x) {
    return cbrt(x);
}

/**
 * zhc_nroot - n次方根函数
 *
 * 计算 x 的 n 次方根。
 *
 * 参数:
 *   x - 输入值
 *   n - 根指数
 *
 * 返回值: ⁿ√x
 */
double zhc_nroot(double x, double n) {
    if (n == 0.0) return NAN;
    if (x < 0.0 && ((int)n) % 2 == 0) return NAN;
    return pow(x, 1.0 / n);
}

/* ============================================================
 * 取整与取余
 * ============================================================ */

/**
 * zhc_ceil - 向上取整
 *
 * 封装 ceil，返回不小于数值的最小整数。
 *
 * 参数:
 *   x - 输入值
 *
 * 返回值: 向上取整结果
 */
double zhc_ceil(double x) {
    return ceil(x);
}

/**
 * zhc_floor - 向下取整
 *
 * 封装 floor，返回不大于数值的最大整数。
 *
 * 参数:
 *   x - 输入值
 *
 * 返回值: 向下取整结果
 */
double zhc_floor(double x) {
    return floor(x);
}

/**
 * zhc_round - 四舍五入取整
 *
 * 封装 round，返回最接近数值的整数。
 *
 * 参数:
 *   x - 输入值
 *
 * 返回值: 四舍五入结果
 */
double zhc_round(double x) {
    return round(x);
}

/**
 * zhc_trunc - 截断取整
 *
 * 封装 trunc，返回数值的整数部分。
 *
 * 参数:
 *   x - 输入值
 *
 * 返回值: 截断结果
 */
double zhc_trunc(double x) {
    return trunc(x);
}

/**
 * zhc_fmod - 浮点取余
 *
 * 封装 fmod，计算浮点数除法的余数。
 *
 * 参数:
 *   x - 被除数
 *   y - 除数
 *
 * 返回值: 余数
 */
double zhc_fmod(double x, double y) {
    if (y == 0.0) return NAN;
    return fmod(x, y);
}

/* ============================================================
 * 其他数学函数
 * ============================================================ */

/**
 * zhc_fabs - 浮点绝对值
 *
 * 封装 fabs，计算浮点数的绝对值。
 *
 * 参数:
 *   x - 输入值
 *
 * 返回值: 绝对值
 */
double zhc_fabs(double x) {
    return fabs(x);
}

/**
 * zhc_fmax - 求最大值
 *
 * 封装 fmax，返回两个数中的较大值。
 *
 * 参数:
 *   x - 第一个数
 *   y - 第二个数
 *
 * 返回值: 较大值
 */
double zhc_fmax(double x, double y) {
    return fmax(x, y);
}

/**
 * zhc_fmin - 求最小值
 *
 * 封装 fmin，返回两个数中的较小值。
 *
 * 参数:
 *   x - 第一个数
 *   y - 第二个数
 *
 * 返回值: 较小值
 */
double zhc_fmin(double x, double y) {
    return fmin(x, y);
}

/**
 * zhc_isnan - 判断是否为NaN
 *
 * 封装 isnan，判断是否为非数字。
 *
 * 参数:
 *   x - 输入值
 *
 * 返回值: 1表示是NaN，0表示不是
 */
int zhc_isnan(double x) {
    return isnan(x);
}

/**
 * zhc_isinf - 判断是否为无穷大
 *
 * 封装 isinf，判断是否为无穷大。
 *
 * 参数:
 *   x - 输入值
 *
 * 返回值: 1表示正无穷，-1表示负无穷，0表示不是无穷大
 */
int zhc_isinf(double x) {
    return isinf(x);
}

/**
 * zhc_deg2rad - 角度转弧度
 *
 * 将角度转换为弧度。
 *
 * 参数:
 *   deg - 角度值
 *
 * 返回值: 弧度值
 */
double zhc_deg2rad(double deg) {
    return deg * M_PI / 180.0;
}

/**
 * zhc_rad2deg - 弧度转角度
 *
 * 将弧度转换为角度。
 *
 * 参数:
 *   rad - 弧度值
 *
 * 返回值: 角度值
 */
double zhc_rad2deg(double rad) {
    return rad * 180.0 / M_PI;
}

/* ============================================================
 * 高级数学函数
 * ============================================================ */

/**
 * zhc_remainder - 取余函数
 *
 * 封装 remainder，计算 IEEE 754 风格的余数。
 *
 * 参数:
 *   x - 被除数
 *   y - 除数
 *
 * 返回值: 余数
 */
double zhc_remainder(double x, double y) {
    if (y == 0.0) return NAN;
    return remainder(x, y);
}

/**
 * zhc_copysign - 复制符号
 *
 * 封装 copysign，复制符号。
 *
 * 参数:
 *   x - 数值的大小
 *   y - 符号的来源
 *
 * 返回值: 带有y符号的x
 */
double zhc_copysign(double x, double y) {
    return copysign(x, y);
}

/**
 * zhc_nextafter - 下一个浮点数
 *
 * 封装 nextafter，返回从 x 向 y 方向的下一个浮点数。
 *
 * 参数:
 *   x - 起始值
 *   y - 方向值
 *
 * 返回值: 下一个浮点数
 */
double zhc_nextafter(double x, double y) {
    return nextafter(x, y);
}

#endif /* ZHC_MATH_H */