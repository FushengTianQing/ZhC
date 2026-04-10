/*
 * ZhC 复数类型运行时实现
 *
 * 作者：远
 * 日期：2026-04-10
 */

#include "zhc_complex.h"

/* ========== 复数创建 ========== */

ZhcDoubleComplex zhc_complex_create(double real, double imag) {
    ZhcDoubleComplex z;
    z.real = real;
    z.imag = imag;
    return z;
}

ZhcFloatComplex zhc_complex_create_float(float real, float imag) {
    ZhcFloatComplex z;
    z.real = real;
    z.imag = imag;
    return z;
}

ZhcLongDoubleComplex zhc_complex_create_long_double(long double real, long double imag) {
    ZhcLongDoubleComplex z;
    z.real = real;
    z.imag = imag;
    return z;
}

/* ========== 复数运算 ========== */

ZhcDoubleComplex zhc_complex_add(ZhcDoubleComplex a, ZhcDoubleComplex b) {
    ZhcDoubleComplex result;
    result.real = a.real + b.real;
    result.imag = a.imag + b.imag;
    return result;
}

ZhcDoubleComplex zhc_complex_sub(ZhcDoubleComplex a, ZhcDoubleComplex b) {
    ZhcDoubleComplex result;
    result.real = a.real - b.real;
    result.imag = a.imag - b.imag;
    return result;
}

ZhcDoubleComplex zhc_complex_mul(ZhcDoubleComplex a, ZhcDoubleComplex b) {
    ZhcDoubleComplex result;
    /* (a+bi)(c+di) = (ac-bd) + (ad+bc)i */
    result.real = a.real * b.real - a.imag * b.imag;
    result.imag = a.real * b.imag + a.imag * b.real;
    return result;
}

ZhcDoubleComplex zhc_complex_div(ZhcDoubleComplex a, ZhcDoubleComplex b) {
    ZhcDoubleComplex result;
    /* (a+bi)/(c+di) = [(ac+bd) + (bc-ad)i] / (c²+d²) */
    double denom = b.real * b.real + b.imag * b.imag;
    if (denom == 0.0) {
        /* 除以零，返回 NaN */
        result.real = NAN;
        result.imag = NAN;
        return result;
    }
    result.real = (a.real * b.real + a.imag * b.imag) / denom;
    result.imag = (a.imag * b.real - a.real * b.imag) / denom;
    return result;
}

ZhcDoubleComplex zhc_complex_neg(ZhcDoubleComplex z) {
    ZhcDoubleComplex result;
    result.real = -z.real;
    result.imag = -z.imag;
    return result;
}

ZhcDoubleComplex zhc_complex_conj(ZhcDoubleComplex z) {
    ZhcDoubleComplex result;
    result.real = z.real;
    result.imag = -z.imag;
    return result;
}

/* ========== 复数属性 ========== */

double zhc_complex_abs(ZhcDoubleComplex z) {
    return sqrt(z.real * z.real + z.imag * z.imag);
}

double zhc_complex_arg(ZhcDoubleComplex z) {
    return atan2(z.imag, z.real);
}

ZhcDoubleComplex zhc_complex_polar(double r, double theta) {
    ZhcDoubleComplex z;
    z.real = r * cos(theta);
    z.imag = r * sin(theta);
    return z;
}

/* ========== 复数数学函数 ========== */

ZhcDoubleComplex zhc_complex_sqrt(ZhcDoubleComplex z) {
    ZhcDoubleComplex result;
    double r = zhc_complex_abs(z);
    double theta = zhc_complex_arg(z);
    double sqrt_r = sqrt(r);
    result.real = sqrt_r * cos(theta / 2.0);
    result.imag = sqrt_r * sin(theta / 2.0);
    return result;
}

ZhcDoubleComplex zhc_complex_exp(ZhcDoubleComplex z) {
    ZhcDoubleComplex result;
    double exp_real = exp(z.real);
    result.real = exp_real * cos(z.imag);
    result.imag = exp_real * sin(z.imag);
    return result;
}

ZhcDoubleComplex zhc_complex_log(ZhcDoubleComplex z) {
    ZhcDoubleComplex result;
    if (z.real == 0.0 && z.imag == 0.0) {
        result.real = -INFINITY;
        result.imag = 0.0;
        return result;
    }
    result.real = log(zhc_complex_abs(z));
    result.imag = zhc_complex_arg(z);
    return result;
}

ZhcDoubleComplex zhc_complex_pow(ZhcDoubleComplex z, ZhcDoubleComplex n) {
    if (z.real == 0.0 && z.imag == 0.0) {
        if (n.real > 0.0) {
            ZhcDoubleComplex zero = {0.0, 0.0};
            return zero;
        }
    }
    return zhc_complex_exp(zhc_complex_mul(n, zhc_complex_log(z)));
}

ZhcDoubleComplex zhc_complex_sin(ZhcDoubleComplex z) {
    ZhcDoubleComplex result;
    result.real = sin(z.real) * cosh(z.imag);
    result.imag = cos(z.real) * sinh(z.imag);
    return result;
}

ZhcDoubleComplex zhc_complex_cos(ZhcDoubleComplex z) {
    ZhcDoubleComplex result;
    result.real = cos(z.real) * cosh(z.imag);
    result.imag = -sin(z.real) * sinh(z.imag);
    return result;
}

ZhcDoubleComplex zhc_complex_tan(ZhcDoubleComplex z) {
    ZhcDoubleComplex sin_z = zhc_complex_sin(z);
    ZhcDoubleComplex cos_z = zhc_complex_cos(z);
    return zhc_complex_div(sin_z, cos_z);
}

ZhcDoubleComplex zhc_complex_sinh(ZhcDoubleComplex z) {
    ZhcDoubleComplex result;
    result.real = sinh(z.real) * cos(z.imag);
    result.imag = cosh(z.real) * sin(z.imag);
    return result;
}

ZhcDoubleComplex zhc_complex_cosh(ZhcDoubleComplex z) {
    ZhcDoubleComplex result;
    result.real = cosh(z.real) * cos(z.imag);
    result.imag = sinh(z.real) * sin(z.imag);
    return result;
}

ZhcDoubleComplex zhc_complex_tanh(ZhcDoubleComplex z) {
    ZhcDoubleComplex sinh_z = zhc_complex_sinh(z);
    ZhcDoubleComplex cosh_z = zhc_complex_cosh(z);
    return zhc_complex_div(sinh_z, cosh_z);
}

/* ========== 实部/虚部访问 ========== */

double zhc_complex_real(ZhcDoubleComplex z) {
    return z.real;
}

double zhc_complex_imag(ZhcDoubleComplex z) {
    return z.imag;
}

/* ========== 浮点复数版本 ========== */

ZhcFloatComplex zhc_complex_sqrt_float(ZhcFloatComplex z) {
    ZhcFloatComplex result;
    float r = sqrtf(z.real * z.real + z.imag * z.imag);
    float theta = atan2f(z.imag, z.real);
    float sqrt_r = sqrtf(r);
    result.real = sqrt_r * cosf(theta / 2.0f);
    result.imag = sqrt_r * sinf(theta / 2.0f);
    return result;
}

ZhcFloatComplex zhc_complex_exp_float(ZhcFloatComplex z) {
    ZhcFloatComplex result;
    float exp_real = expf(z.real);
    result.real = exp_real * cosf(z.imag);
    result.imag = exp_real * sinf(z.imag);
    return result;
}

ZhcFloatComplex zhc_complex_log_float(ZhcFloatComplex z) {
    ZhcFloatComplex result;
    float r = sqrtf(z.real * z.real + z.imag * z.imag);
    result.real = logf(r);
    result.imag = atan2f(z.imag, z.real);
    return result;
}

ZhcFloatComplex zhc_complex_sin_float(ZhcFloatComplex z) {
    ZhcFloatComplex result;
    result.real = sinf(z.real) * coshf(z.imag);
    result.imag = cosf(z.real) * sinhf(z.imag);
    return result;
}

ZhcFloatComplex zhc_complex_cos_float(ZhcFloatComplex z) {
    ZhcFloatComplex result;
    result.real = cosf(z.real) * coshf(z.imag);
    result.imag = -sinf(z.real) * sinhf(z.imag);
    return result;
}

float zhc_complex_abs_float(ZhcFloatComplex z) {
    return sqrtf(z.real * z.real + z.imag * z.imag);
}

/* ========== 长双精度复数版本 ========== */

ZhcLongDoubleComplex zhc_complex_sqrt_long_double(ZhcLongDoubleComplex z) {
    ZhcLongDoubleComplex result;
    long double r = sqrtl(z.real * z.real + z.imag * z.imag);
    long double theta = atan2l(z.imag, z.real);
    long double sqrt_r = sqrtl(r);
    result.real = sqrt_r * cosl(theta / 2.0L);
    result.imag = sqrt_r * sinl(theta / 2.0L);
    return result;
}

ZhcLongDoubleComplex zhc_complex_exp_long_double(ZhcLongDoubleComplex z) {
    ZhcLongDoubleComplex result;
    long double exp_real = expl(z.real);
    result.real = exp_real * cosl(z.imag);
    result.imag = exp_real * sinl(z.imag);
    return result;
}

ZhcLongDoubleComplex zhc_complex_log_long_double(ZhcLongDoubleComplex z) {
    ZhcLongDoubleComplex result;
    long double r = sqrtl(z.real * z.real + z.imag * z.imag);
    result.real = logl(r);
    result.imag = atan2l(z.imag, z.real);
    return result;
}

ZhcLongDoubleComplex zhc_complex_sin_long_double(ZhcLongDoubleComplex z) {
    ZhcLongDoubleComplex result;
    result.real = sinl(z.real) * coshl(z.imag);
    result.imag = cosl(z.real) * sinhl(z.imag);
    return result;
}

ZhcLongDoubleComplex zhc_complex_cos_long_double(ZhcLongDoubleComplex z) {
    ZhcLongDoubleComplex result;
    result.real = cosl(z.real) * coshl(z.imag);
    result.imag = -sinl(z.real) * sinhl(z.imag);
    return result;
}

long double zhc_complex_abs_long_double(ZhcLongDoubleComplex z) {
    return sqrtl(z.real * z.real + z.imag * z.imag);
}
