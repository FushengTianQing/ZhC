#ifndef ZHC_COMPLEX_H
#define ZHC_COMPLEX_H

#include <stddef.h>
#include <math.h>

/*
 * ZhC 复数类型运行时支持
 *
 * 支持的类型：
 * - float _Complex (float_complex)
 * - double _Complex (double_complex)
 * - long double _Complex (long_double_complex)
 */

/* 复数类型定义 */
typedef struct {
    float real;
    float imag;
} ZhcFloatComplex;

typedef struct {
    double real;
    double imag;
} ZhcDoubleComplex;

typedef struct {
    long double real;
    long double imag;
} ZhcLongDoubleComplex;

/* 复数创建 */
ZhcDoubleComplex zhc_complex_create(double real, double imag);
ZhcFloatComplex zhc_complex_create_float(float real, float imag);
ZhcLongDoubleComplex zhc_complex_create_long_double(long double real, long double imag);

/* 复数运算 */
ZhcDoubleComplex zhc_complex_add(ZhcDoubleComplex a, ZhcDoubleComplex b);
ZhcDoubleComplex zhc_complex_sub(ZhcDoubleComplex a, ZhcDoubleComplex b);
ZhcDoubleComplex zhc_complex_mul(ZhcDoubleComplex a, ZhcDoubleComplex b);
ZhcDoubleComplex zhc_complex_div(ZhcDoubleComplex a, ZhcDoubleComplex b);
ZhcDoubleComplex zhc_complex_neg(ZhcDoubleComplex z);
ZhcDoubleComplex zhc_complex_conj(ZhcDoubleComplex z);

/* 复数属性 */
double zhc_complex_abs(ZhcDoubleComplex z);      /* |z| */
double zhc_complex_arg(ZhcDoubleComplex z);      /* arg(z) */
ZhcDoubleComplex zhc_complex_polar(double r, double theta);

/* 复数数学函数 */
ZhcDoubleComplex zhc_complex_sqrt(ZhcDoubleComplex z);
ZhcDoubleComplex zhc_complex_exp(ZhcDoubleComplex z);
ZhcDoubleComplex zhc_complex_log(ZhcDoubleComplex z);
ZhcDoubleComplex zhc_complex_pow(ZhcDoubleComplex z, ZhcDoubleComplex n);
ZhcDoubleComplex zhc_complex_sin(ZhcDoubleComplex z);
ZhcDoubleComplex zhc_complex_cos(ZhcDoubleComplex z);
ZhcDoubleComplex zhc_complex_tan(ZhcDoubleComplex z);
ZhcDoubleComplex zhc_complex_sinh(ZhcDoubleComplex z);
ZhcDoubleComplex zhc_complex_cosh(ZhcDoubleComplex z);
ZhcDoubleComplex zhc_complex_tanh(ZhcDoubleComplex z);

/* 实部/虚部访问 */
double zhc_complex_real(ZhcDoubleComplex z);
double zhc_complex_imag(ZhcDoubleComplex z);

/* 浮点复数版本 */
ZhcFloatComplex zhc_complex_sqrt_float(ZhcFloatComplex z);
ZhcFloatComplex zhc_complex_exp_float(ZhcFloatComplex z);
ZhcFloatComplex zhc_complex_log_float(ZhcFloatComplex z);
ZhcFloatComplex zhc_complex_sin_float(ZhcFloatComplex z);
ZhcFloatComplex zhc_complex_cos_float(ZhcFloatComplex z);
float zhc_complex_abs_float(ZhcFloatComplex z);

/* 长双精度复数版本 */
ZhcLongDoubleComplex zhc_complex_sqrt_long_double(ZhcLongDoubleComplex z);
ZhcLongDoubleComplex zhc_complex_exp_long_double(ZhcLongDoubleComplex z);
ZhcLongDoubleComplex zhc_complex_log_long_double(ZhcLongDoubleComplex z);
ZhcLongDoubleComplex zhc_complex_sin_long_double(ZhcLongDoubleComplex z);
ZhcLongDoubleComplex zhc_complex_cos_long_double(ZhcLongDoubleComplex z);
long double zhc_complex_abs_long_double(ZhcLongDoubleComplex z);

#endif /* ZHC_COMPLEX_H */
