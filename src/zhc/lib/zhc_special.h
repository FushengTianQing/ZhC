/**
 * zhc_special.h - 特殊数学函数库
 *
 * 提供科学计算所需的特殊数学函数：
 * - Gamma 和 Beta 函数
 * - 误差函数
 * - 贝塞尔函数
 * - 椭圆积分
 * - 统计分布函数
 *
 * 版本: 1.0
 * 依赖: <math.h>
 */

#ifndef ZHC_SPECIAL_H
#define ZHC_SPECIAL_H

#include <math.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#define M_SQRT2PI 0.79788456080286535588  /* sqrt(2/pi) */
#define M_SQRT_PI 1.77245385090551602729  /* sqrt(pi) */

/* ================================================================
 * Gamma 和 Beta 函数
 * ================================================================ */

/**
 * zhc_gamma - Gamma 函数
 *
 * 使用 Lanczos 近似计算 Gamma 函数。
 * Gamma(n) = (n-1)! 对于正整数 n。
 *
 * 参数:
 *   x - 输入值（不能是负整数）
 *
 * 返回值: Gamma(x) 的值
 *
 * 示例:
 *   zhc_gamma(5.0);  // 返回 24.0 (4!)
 */
double zhc_gamma(double x);

/**
 * zhc_lgamma - 对数 Gamma 函数
 *
 * 计算 log(Gamma(x))，在 x 较大时比直接计算更稳定。
 *
 * 参数:
 *   x - 输入值（不能是负整数或零）
 *
 * 返回值: log(Gamma(x))
 */
double zhc_lgamma(double x);

/**
 * zhc_gamma_sign - Gamma 函数符号
 *
 * 返回 Gamma(x) 的符号。
 *
 * 参数:
 *   x - 输入值
 *
 * 返回值: Gamma(x) > 0 返回 1，Gamma(x) < 0 返回 -1，Gamma(x) = 0 返回 0
 */
int zhc_gamma_sign(double x);

/**
 * zhc_beta - Beta 函数
 *
 * B(a,b) = Gamma(a) * Gamma(b) / Gamma(a+b)
 *
 * 参数:
 *   a - 第一个参数（必须为正）
 *   b - 第二个参数（必须为正）
 *
 * 返回值: Beta(a,b) 的值
 *
 * 示例:
 *   zhc_beta(2.0, 3.0);  // 返回 0.08333...
 */
double zhc_beta(double a, double b);

/**
 * zhc_lbeta - 对数 Beta 函数
 *
 * 计算 log(Beta(a,b))，在 a,b 较大时更稳定。
 *
 * 参数:
 *   a - 第一个参数
 *   b - 第二个参数
 *
 * 返回值: log(Beta(a,b))
 */
double zhc_lbeta(double a, double b);

/* ================================================================
 * 误差函数
 * ================================================================ */

/**
 * zhc_erf - 误差函数
 *
 * erf(x) = 2/sqrt(pi) * integral from 0 to x of exp(-t^2) dt
 *
 * 参数:
 *   x - 输入值
 *
 * 返回值: 误差函数值（范围 -1 到 1）
 *
 * 示例:
 *   zhc_erf(1.0);  // 返回约 0.8427
 */
double zhc_erf(double x);

/**
 * zhc_erfc - 互补误差函数
 *
 * erfc(x) = 1 - erf(x)
 * 在 x 较大时比 1-erf(x) 更精确。
 *
 * 参数:
 *   x - 输入值
 *
 * 返回值: 互补误差函数值（范围 0 到 2）
 */
double zhc_erfc(double x);

/**
 * zhc_erf_inv - 误差函数的逆函数
 *
 * 返回满足 erf(y) = x 的 y 值。
 *
 * 参数:
 *   p - 概率值（范围 -1 到 1）
 *
 * 返回值: 满足 erf(y) = p 的 y 值
 */
double zhc_erf_inv(double p);

/**
 * zhc_erfc_inv - 互补误差函数的逆函数
 *
 * 返回满足 erfc(y) = x 的 y 值。
 *
 * 参数:
 *   p - 概率值（范围 0 到 2）
 *
 * 返回值: 满足 erfc(y) = p 的 y 值
 */
double zhc_erfc_inv(double p);

/* ================================================================
 * 贝塞尔函数
 * ================================================================ */

/**
 * zhc_bessel_j0 - 第一类贝塞尔函数 J_0(x)
 *
 * 参数:
 *   x - 输入值
 *
 * 返回值: J_0(x) 的值
 */
double zhc_bessel_j0(double x);

/**
 * zhc_bessel_j1 - 第一类贝塞尔函数 J_1(x)
 *
 * 参数:
 *   x - 输入值
 *
 * 返回值: J_1(x) 的值
 */
double zhc_bessel_j1(double x);

/**
 * zhc_bessel_j - 第一类贝塞尔函数 J_n(x)
 *
 * 参数:
 *   n - 阶数（必须为非负整数）
 *   x - 输入值
 *
 * 返回值: J_n(x) 的值
 *
 * 示例:
 *   zhc_bessel_j(0, 1.0);  // J_0(1)
 *   zhc_bessel_j(1, 1.0);  // J_1(1)
 */
double zhc_bessel_j(int n, double x);

/**
 * zhc_bessel_y0 - 第二类贝塞尔函数 Y_0(x)
 *
 * 参数:
 *   x - 输入值（必须大于 0）
 *
 * 返回值: Y_0(x) 的值
 */
double zhc_bessel_y0(double x);

/**
 * zhc_bessel_y1 - 第二类贝塞尔函数 Y_1(x)
 *
 * 参数:
 *   x - 输入值（必须大于 0）
 *
 * 返回值: Y_1(x) 的值
 */
double zhc_bessel_y1(double x);

/**
 * zhc_bessel_y - 第二类贝塞尔函数 Y_n(x)
 *
 * 参数:
 *   n - 阶数（必须为非负整数）
 *   x - 输入值（必须大于 0）
 *
 * 返回值: Y_n(x) 的值
 */
double zhc_bessel_y(int n, double x);

/**
 * zhc_bessel_i0 - 第一类修正贝塞尔函数 I_0(x)
 *
 * 参数:
 *   x - 输入值
 *
 * 返回值: I_0(x) 的值
 */
double zhc_bessel_i0(double x);

/**
 * zhc_bessel_i1 - 第一类修正贝塞尔函数 I_1(x)
 *
 * 参数:
 *   x - 输入值
 *
 * 返回值: I_1(x) 的值
 */
double zhc_bessel_i1(double x);

/**
 * zhc_bessel_i - 第一类修正贝塞尔函数 I_n(x)
 *
 * 参数:
 *   n - 阶数（必须为非负整数）
 *   x - 输入值
 *
 * 返回值: I_n(x) 的值
 */
double zhc_bessel_i(int n, double x);

/**
 * zhc_bessel_k0 - 第二类修正贝塞尔函数 K_0(x)
 *
 * 参数:
 *   x - 输入值（必须大于 0）
 *
 * 返回值: K_0(x) 的值
 */
double zhc_bessel_k0(double x);

/**
 * zhc_bessel_k1 - 第二类修正贝塞尔函数 K_1(x)
 *
 * 参数:
 *   x - 输入值（必须大于 0）
 *
 * 返回值: K_1(x) 的值
 */
double zhc_bessel_k1(double x);

/**
 * zhc_bessel_k - 第二类修正贝塞尔函数 K_n(x)
 *
 * 参数:
 *   n - 阶数（必须为非负整数）
 *   x - 输入值（必须大于 0）
 *
 * 返回值: K_n(x) 的值
 */
double zhc_bessel_k(int n, double x);

/* ================================================================
 * 椭圆积分
 * ================================================================ */

/**
 * zhc_elliptic_k - 第一类完全椭圆积分 K(k)
 *
 * K(k) = integral from 0 to pi/2 of 1/sqrt(1-k^2*sin^2(theta)) dtheta
 *
 * 参数:
 *   k - 椭圆模（范围 -1 到 1，不包含奇点）
 *
 * 返回值: K(k) 的值
 *
 * 示例:
 *   zhc_elliptic_k(0.5);  // 第一类完全椭圆积分
 */
double zhc_elliptic_k(double k);

/**
 * zhc_elliptic_e - 第二类完全椭圆积分 E(k)
 *
 * E(k) = integral from 0 to pi/2 of sqrt(1-k^2*sin^2(theta)) dtheta
 *
 * 参数:
 *   k - 椭圆模（范围 -1 到 1）
 *
 * 返回值: E(k) 的值
 */
double zhc_elliptic_e(double k);

/**
 * zhc_elliptic_pi - 第三类完全椭圆积分 Pi(n,k)
 *
 * Pi(n,k) = integral from 0 to pi/2 of 1/(1-n*sin^2(theta)) dtheta
 *
 * 参数:
 *   n - 第三参数
 *   k - 椭圆模（范围 -1 到 1）
 *
 * 返回值: Pi(n,k) 的值
 */
double zhc_elliptic_pi(double n, double k);

/* ================================================================
 * 统计分布函数
 * ================================================================ */

/**
 * zhc_normal_pdf - 正态分布概率密度函数
 *
 * f(x) = (1/(sigma*sqrt(2*pi))) * exp(-(x-mu)^2/(2*sigma^2))
 *
 * 参数:
 *   x - 随机变量值
 *   mean - 均值 (mu)
 *   stddev - 标准差 (sigma，必须大于 0)
 *
 * 返回值: 正态分布密度值
 *
 * 示例:
 *   zhc_normal_pdf(0.0, 0.0, 1.0);  // 标准正态分布密度，约 0.3989
 */
double zhc_normal_pdf(double x, double mean, double stddev);

/**
 * zhc_normal_cdf - 正态分布累积分布函数
 *
 * F(x) = (1/2) * [1 + erf((x-mu)/(sigma*sqrt(2)))]
 *
 * 参数:
 *   x - 随机变量值
 *   mean - 均值 (mu)
 *   stddev - 标准差 (sigma，必须大于 0)
 *
 * 返回值: 正态分布累积概率值（范围 0 到 1）
 *
 * 示例:
 *   zhc_normal_cdf(0.0, 0.0, 1.0);  // 0.5
 */
double zhc_normal_cdf(double x, double mean, double stddev);

/**
 * zhc_normal_inv - 正态分布逆累积分布函数
 *
 * 返回满足 NormalCDF(y) = p 的 y 值。
 *
 * 参数:
 *   p - 累积概率值（范围 0 到 1）
 *   mean - 均值 (mu)
 *   stddev - 标准差 (sigma，必须大于 0)
 *
 * 返回值: 满足条件的 x 值
 *
 * 示例:
 *   zhc_normal_inv(0.975, 0.0, 1.0);  // 约 1.96
 */
double zhc_normal_inv(double p, double mean, double stddev);

/**
 * zhc_chi2_pdf - 卡方分布概率密度函数
 *
 * 参数:
 *   x - 随机变量值（必须 >= 0）
 *   df - 自由度（必须为正整数）
 *
 * 返回值: 卡方分布密度值
 */
double zhc_chi2_pdf(double x, int df);

/**
 * zhc_chi2_cdf - 卡方分布累积分布函数
 *
 * 参数:
 *   x - 随机变量值（必须 >= 0）
 *   df - 自由度（必须为正整数）
 *
 * 返回值: 卡方分布累积概率值（范围 0 到 1）
 */
double zhc_chi2_cdf(double x, int df);

/**
 * zhc_t_pdf - t 分布概率密度函数
 *
 * 参数:
 *   x - 随机变量值
 *   df - 自由度（必须为正整数）
 *
 * 返回值: t 分布密度值
 */
double zhc_t_pdf(double x, int df);

/**
 * zhc_t_cdf - t 分布累积分布函数
 *
 * 参数:
 *   x - 随机变量值
 *   df - 自由度（必须为正整数）
 *
 * 返回值: t 分布累积概率值（范围 0 到 1）
 */
double zhc_t_cdf(double x, int df);

/**
 * zhc_f_pdf - F 分布概率密度函数
 *
 * 参数:
 *   x - 随机变量值（必须 >= 0）
 *   df1 - 第一自由度（必须为正整数）
 *   df2 - 第二自由度（必须为正整数）
 *
 * 返回值: F 分布密度值
 */
double zhc_f_pdf(double x, int df1, int df2);

/**
 * zhc_f_cdf - F 分布累积分布函数
 *
 * 参数:
 *   x - 随机变量值（必须 >= 0）
 *   df1 - 第一自由度（必须为正整数）
 *   df2 - 第二自由度（必须为正整数）
 *
 * 返回值: F 分布累积概率值（范围 0 到 1）
 */
double zhc_f_cdf(double x, int df1, int df2);

/* ================================================================
 * 实现部分
 * ================================================================ */

#ifdef ZHC_SPECIAL_IMPLEMENTATION

#include <stdlib.h>
#include <string.h>

/* 前向声明：辅助函数 */
static double zhc_gamma_inc(double a, double x);
static double zhc_incomplete_beta(double a, double b, double x);

/* ---------- Gamma 和 Beta 函数 ---------- */

/* Lanczos 近似系数 */
static const double gamma_lanczos_coef[] = {
    0.99999999999980993,
    676.5203681218851,
    -1259.1392167224028,
    771.32342877765313,
    -176.61502916214059,
    12.507343278686905,
    -0.13857109526572012,
    9.9843695780195716e-6,
    1.5056327351493116e-7
};

double zhc_gamma(double x) {
    /* 反射公式处理负数 */
    if (x < 0.5) {
        return M_PI / (sin(M_PI * x) * zhc_gamma(1.0 - x));
    }

    x -= 1.0;
    double y = gamma_lanczos_coef[0];

    for (int i = 1; i < 9; i++) {
        y += gamma_lanczos_coef[i] / (x + i);
    }

    double t = x + 7.5;
    return sqrt(2.0 * M_PI) * pow(t, x + 0.5) * exp(-t) * y;
}

double zhc_lgamma(double x) {
    if (x < 0.5) {
        return log(fabs(M_PI / sin(M_PI * x))) - zhc_lgamma(1.0 - x);
    }

    x -= 1.0;
    double y = gamma_lanczos_coef[0];

    for (int i = 1; i < 9; i++) {
        y += gamma_lanczos_coef[i] / (x + i);
    }

    double t = x + 7.5;
    return 0.5 * log(2.0 * M_PI) + (x + 0.5) * log(t) - t + log(y);
}

int zhc_gamma_sign(double x) {
    if (x < 0.5) {
        double g = zhc_gamma(1.0 - x);
        return (g > 0) ? -1 : 1;
    }
    double g = zhc_gamma(x);
    return (g >= 0) ? 1 : -1;
}

double zhc_beta(double a, double b) {
    return exp(zhc_lgamma(a) + zhc_lgamma(b) - zhc_lgamma(a + b));
}

double zhc_lbeta(double a, double b) {
    return zhc_lgamma(a) + zhc_lgamma(b) - zhc_lgamma(a + b);
}

/* ---------- 误差函数 ---------- */

/* Abramowitz and Stegun 近似系数 */
static const double erf_coef_a1 =  0.254829592;
static const double erf_coef_a2 = -0.284496736;
static const double erf_coef_a3 =  1.421413741;
static const double erf_coef_a4 = -1.453152027;
static const double erf_coef_a5 =  1.061405429;
static const double erf_p = 0.3275911;

double zhc_erf(double x) {
    /* 特殊值 */
    if (x == 0.0) return 0.0;
    if (x < 0.0) return -zhc_erf(-x);
    if (x >= 6.0) return 1.0;

    double t = 1.0 / (1.0 + erf_p * x);
    double y = 1.0 - (((((erf_coef_a5 * t + erf_coef_a4) * t)
        + erf_coef_a3) * t + erf_coef_a2) * t + erf_coef_a1) * t * exp(-x * x);

    return y;
}

double zhc_erfc(double x) {
    if (x < 0.0) {
        return 1.0 + zhc_erf(x);
    }
    if (x >= 6.0) return 0.0;
    return 1.0 - zhc_erf(x);
}

/* 逆误差函数 Newton-Raphson 迭代 */
double zhc_erf_inv(double p) {
    if (p <= -1.0 || p >= 1.0) return NAN;
    if (p == 0.0) return 0.0;

    /* 初始猜测 */
    double x;
    if (fabs(p) < 0.7) {
        x = p * sqrt(-2.0 * log(1.0 - p * p));
    } else {
        x = sqrt(-2.0 * log(0.5 - fabs(p) * 0.5));
        if (p < 0) x = -x;
    }

    /* Newton-Raphson 迭代 */
    for (int i = 0; i < 5; i++) {
        double err = zhc_erf(x) - p;
        if (fabs(err) < 1e-15) break;
        double deriv = 2.0 / sqrt(M_PI) * exp(-x * x);
        x -= err / deriv;
    }

    return x;
}

double zhc_erfc_inv(double p) {
    if (p <= 0.0 || p >= 2.0) return NAN;
    if (p == 1.0) return 0.0;
    if (p > 1.0) return -zhc_erf_inv(2.0 - p);
    return zhc_erf_inv(1.0 - p);
}

/* ---------- 贝塞尔函数 ---------- */

/* J_0(x) - 使用幂级数/渐近展开 */
double zhc_bessel_j0(double x) {
    if (fabs(x) < 1e-15) return 1.0;
    if (fabs(x) < 8.0) {
        double y = x * x;
        double ans1 = 57568490574.0 + y * (-13362590354.0 + y * (651619640.7
            + y * (-11214424.18 + y * (77392.33017 + y * (-184.9052456)))));
        double ans2 = 57568490411.0 + y * (1029532985.0 + y * (9494680.718
            + y * (59272.64853 + y * (267.8532712 + y * 1.0))));
        return ans1 / ans2;
    } else {
        double z = 8.0 / fabs(x);
        double y = z * z;
        double xx = x - M_PI / 4.0;
        double ans1 = 1.0 + y * (-0.1098628627e-2 + y * (0.2734510407e-4
            + y * (-0.2073370639e-5 + y * 0.2093887211e-6)));
        double ans2 = -0.1562499995e-1 + y * (0.1430488765e-3
            + y * (-0.6911147651e-5 + y * (0.7621095161e-6
            - y * 0.934935152e-7)));
        return sqrt(0.636619772 / fabs(x)) * (cos(xx) * ans1 - z * sin(xx) * ans2);
    }
}

/* J_1(x) */
double zhc_bessel_j1(double x) {
    if (fabs(x) < 8.0) {
        double y = x * x;
        double ans1 = x * (72362614232.0 + y * (-7895059235.0 + y * (242396853.1
            + y * (-2972611.439 + y * (15704.4820 + y * (-30.16036606))))));
        double ans2 = 144725228442.0 + y * (2300535178.0 + y * (18583304.74
            + y * (99447.43394 + y * (376.9991397 + y * 1.0))));
        return ans1 / ans2;
    } else {
        double z = 8.0 / fabs(x);
        double y = z * z;
        double xx = x - 3.0 * M_PI / 4.0;
        double ans1 = 1.0 + y * (-0.1098628627e-2 + y * (0.2734510407e-4
            + y * (-0.2073370639e-5 + y * 0.2093887211e-6)));
        double ans2 = -0.1562499995e-1 + y * (0.1430488765e-3
            + y * (-0.6911147651e-5 + y * (0.7621095161e-6
            - y * 0.934935152e-7)));
        return sqrt(0.636619772 / fabs(x)) * (cos(xx) * ans1 - z * sin(xx) * ans2);
    }
}

double zhc_bessel_j(int n, double x) {
    if (n == 0) return zhc_bessel_j0(x);
    if (n == 1) return zhc_bessel_j1(x);
    if (n < 0) return 0;

    /* 递推关系: J_n = (2*(n-1)/x)*J_(n-1) - J_(n-2) */
    double j0 = zhc_bessel_j0(x);
    double j1 = zhc_bessel_j1(x);
    double jn = 0;

    for (int i = 2; i <= n; i++) {
        jn = 2.0 * (i - 1) / x * j1 - j0;
        j0 = j1;
        j1 = jn;
    }

    return jn;
}

/* Y_0(x) */
double zhc_bessel_y0(double x) {
    if (x <= 0.0) return NAN;

    if (x < 8.0) {
        double y = x * x;
        double ans1 = -2957821389.0 + y * (7062834065.0 + y * (-512359803.6
            + y * (10879881.29 + y * (-86327.92757 + y * 228.4622733))));
        double ans2 = 40076544269.0 + y * (745249964.8 + y * (7189466.438
            + y * (47447.26470 + y * (226.1030244 + y * 1.0))));
        return (ans1 / ans2) + 0.636619772 * zhc_bessel_j0(x) * log(x);
    } else {
        double z = 8.0 / x;
        double y = z * z;
        double xx = x - M_PI / 4.0;
        double ans1 = 1.0 + y * (-0.1098628627e-2 + y * (0.2734510407e-4
            + y * (-0.2073370639e-5 + y * 0.2093887211e-6)));
        double ans2 = -0.1562499995e-1 + y * (0.1430488765e-3
            + y * (-0.6911147651e-5 + y * (0.7621095161e-6
            - y * 0.934935152e-7)));
        return sqrt(0.636619772 / x) * (sin(xx) * ans1 + z * cos(xx) * ans2);
    }
}

/* Y_1(x) */
double zhc_bessel_y1(double x) {
    if (x <= 0.0) return NAN;

    if (x < 8.0) {
        double y = x * x;
        double ans1 = x * (-0.4900604943e13 + y * (0.1275274390e13 + y * (-0.5153438139e11
            + y * (0.7349261951e9 + y * (-0.4721589760e7 + y * (0.1143372188e5 + y))))));
        double ans2 = 0.2499580570e14 + y * (0.4243969669e12 + y * (0.3739239037e10
            + y * (0.2245904090e8 + y * (0.8510421510e5 + y * 228.4622733 + y))));
        return (ans1 / ans2) + 0.636619772 * (zhc_bessel_j1(x) * log(x) - 1.0 / x);
    } else {
        double z = 8.0 / x;
        double y = z * z;
        double xx = x - 3.0 * M_PI / 4.0;
        double ans1 = 1.0 + y * (-0.1098628627e-2 + y * (0.2734510407e-4
            + y * (-0.2073370639e-5 + y * 0.2093887211e-6)));
        double ans2 = -0.1562499995e-1 + y * (0.1430488765e-3
            + y * (-0.6911147651e-5 + y * (0.7621095161e-6
            - y * 0.934935152e-7)));
        return sqrt(0.636619772 / x) * (sin(xx) * ans1 + z * cos(xx) * ans2);
    }
}

double zhc_bessel_y(int n, double x) {
    if (n == 0) return zhc_bessel_y0(x);
    if (n == 1) return zhc_bessel_y1(x);
    if (n < 0 || x <= 0.0) return NAN;

    /* 递推关系: Y_n = (2*(n-1)/x)*Y_(n-1) - Y_(n-2) */
    double y0 = zhc_bessel_y0(x);
    double y1 = zhc_bessel_y1(x);
    double yn = 0;

    for (int i = 2; i <= n; i++) {
        yn = 2.0 * (i - 1) / x * y1 - y0;
        y0 = y1;
        y1 = yn;
    }

    return yn;
}

/* 修正贝塞尔函数 I_0(x) */
double zhc_bessel_i0(double x) {
    double ax = fabs(x);
    if (ax < 3.75) {
        double y = x / 3.75;
        y = y * y;
        return 1.0 + y * (3.5156229 + y * (3.0899424 + y * (1.2067492
            + y * (0.2659732 + y * (0.0360768 + y * 0.0045813)))));
    } else {
        double y = 3.75 / ax;
        return (exp(ax) / sqrt(ax)) * (0.39894228 + y * (0.01328592
            + y * (0.00225319 + y * (-0.00157565 + y * (0.00916281
            + y * (-0.02057706 + y * (0.02635537 + y * (-0.01647633
            + y * 0.00392377))))))));
    }
}

/* I_1(x) */
double zhc_bessel_i1(double x) {
    double ax = fabs(x);
    if (ax < 3.75) {
        double y = x / 3.75;
        y = y * y;
        return ax * (0.5 + y * (0.87890594 + y * (0.51498869 + y * (0.15084934
            + y * (0.02658733 + y * (0.00301532 + y * 0.00032411))))));
    } else {
        double y = 3.75 / ax;
        return (exp(ax) / sqrt(ax)) * (0.39894228 + y * (-0.03988024
            + y * (-0.00362018 + y * (0.00163801 + y * (-0.01031555
            + y * (0.02282967 + y * (-0.02895312 + y * (0.01787654
            + y * -0.00420059))))))));
    }
}

double zhc_bessel_i(int n, double x) {
    if (n == 0) return zhc_bessel_i0(x);
    if (n == 1) return zhc_bessel_i1(x);
    if (n < 0) return 0;

    /* 递推关系: I_n = (2*(n-1)/x)*I_(n-1) + I_(n-2) */
    double i0 = zhc_bessel_i0(x);
    double i1 = zhc_bessel_i1(x);
    double in_val = 0;

    for (int i = 2; i <= n; i++) {
        in_val = 2.0 * (i - 1) / x * i1 + i0;
        i0 = i1;
        i1 = in_val;
    }

    return in_val;
}

/* K_0(x) */
double zhc_bessel_k0(double x) {
    if (x <= 0.0) return NAN;

    if (x < 2.0) {
        double y = x * x / 4.0;
        return -log(x / 2.0) * zhc_bessel_i0(x) + (-0.57721566 + y * (0.42278420
            + y * (0.23069756 + y * (0.03488590 + y * (0.00262698
            + y * (0.00010750 + y * 0.00000740))))));
    } else {
        double y = 2.0 / x;
        return (exp(-x) / sqrt(x)) * (1.25331414 + y * (-0.0783238
            + y * (0.02189568 + y * (-0.01062446 + y * (0.00587872
            + y * (-0.00059929 + y * 0.00014566))))));
    }
}

/* K_1(x) */
double zhc_bessel_k1(double x) {
    if (x <= 0.0) return NAN;

    if (x < 2.0) {
        double y = x * x / 4.0;
        return log(x / 2.0) * zhc_bessel_i1(x) + (1.0 / x) * (1.0 + y * (0.15443144
            + y * (-0.67278579 + y * (-0.18156897 + y * (-0.01919402
            + y * (-0.00110404 + y * -0.00004686))))));
    } else {
        double y = 2.0 / x;
        return (exp(-x) / sqrt(x)) * (1.25331414 + y * (0.23498619
            + y * (-0.03656202 + y * (0.01504268 + y * (-0.00780353
            + y * (0.00325614 + y * -0.00068245))))));
    }
}

double zhc_bessel_k(int n, double x) {
    if (n == 0) return zhc_bessel_k0(x);
    if (n == 1) return zhc_bessel_k1(x);
    if (n < 0 || x <= 0.0) return NAN;

    /* 递推关系: K_n = (2*(n-1)/x)*K_(n-1) + K_(n-2) */
    double k0 = zhc_bessel_k0(x);
    double k1 = zhc_bessel_k1(x);
    double kn = 0;

    for (int i = 2; i <= n; i++) {
        kn = 2.0 * (i - 1) / x * k1 + k0;
        k0 = k1;
        k1 = kn;
    }

    return kn;
}

/* ---------- 椭圆积分 ---------- */

/* 第一类完全椭圆积分 K(k) */
double zhc_elliptic_k(double k) {
    if (k < 0.0 || k >= 1.0) return NAN;
    if (k == 0.0) return M_PI / 2.0;
    if (k < 0.9) {
        double y = 1.0 - k * k;
        double a1 = 0.44325141463;
        double a2 = 0.06260601220;
        double a3 = 0.04757383546;
        double a4 = 0.01736506451;
        return (a1 + y * (a2 + y * (a3 + y * a4))) * (-log(y) / 2.0);
    } else {
        double y = 1.0 - k;
        double b0 = 1.38629436112;
        double b1 = 0.09666344259;
        double b2 = 0.03590092383;
        double b3 = 0.03742563713;
        double b4 = 0.01451196212;
        return b0 + y * (b1 + y * (b2 + y * (b3 + y * b4)));
    }
}

/* 第二类完全椭圆积分 E(k) */
double zhc_elliptic_e(double k) {
    if (k < 0.0 || k > 1.0) return NAN;
    if (k == 0.0) return M_PI / 2.0;
    if (k < 0.9) {
        double y = 1.0 - k * k;
        double a1 = 0.44325141463;
        double a2 = 0.06260601220;
        double a3 = 0.04757383546;
        double a4 = 0.01736506451;
        return (1.0 + y * (a1 + y * (a2 + y * (a3 + y * a4)))) * M_PI / 2.0;
    } else {
        double y = 1.0 - k;
        double c0 = 1.0;
        double c1 = 0.46301517478;
        double c2 = 0.10778154055;
        double c3 = 0.24585053740;
        double c4 = 0.04124954144;
        return c0 + y * (c1 + y * (c2 + y * (c3 + y * c4)));
    }
}

/* 第三类完全椭圆积分 Pi(n,k) */
double zhc_elliptic_pi(double n, double k) {
    if (k < 0.0 || k >= 1.0) return NAN;

    double y = 1.0 - k * k;
    double a1 = 0.44325141463;
    double a2 = 0.06260601220;
    double a3 = 0.04757383546;
    double a4 = 0.01736506451;

    /* 简化近似 */
    double en = 1.0 + n;
    if (fabs(n) < 1e-10) {
        return zhc_elliptic_k(k);
    }
    return zhc_elliptic_k(k) * (1.0 + n * 0.25 * (y + 1.0) / en);
}

/* ---------- 统计分布函数 ---------- */

/* 正态分布概率密度函数 */
double zhc_normal_pdf(double x, double mean, double stddev) {
    if (stddev <= 0.0) return NAN;
    double z = (x - mean) / stddev;
    return exp(-0.5 * z * z) / (stddev * sqrt(2.0 * M_PI));
}

/* 正态分布累积分布函数 */
double zhc_normal_cdf(double x, double mean, double stddev) {
    if (stddev <= 0.0) return NAN;
    double z = (x - mean) / stddev;
    return 0.5 * (1.0 + zhc_erf(z / sqrt(2.0)));
}

/* 正态分布逆累积分布函数 */
double zhc_normal_inv(double p, double mean, double stddev) {
    if (p <= 0.0 || p >= 1.0 || stddev <= 0.0) return NAN;
    double z = sqrt(2.0) * zhc_erf_inv(2.0 * p - 1.0);
    return mean + stddev * z;
}

/* 卡方分布概率密度函数 */
double zhc_chi2_pdf(double x, int df) {
    if (x <= 0.0 || df <= 0) return NAN;
    if (df % 2 == 0) {
        /* 偶数自由度 */
        double k = df / 2.0;
        return pow(x, k - 1.0) * exp(-x / 2.0) / (pow(2.0, k) * zhc_gamma(k));
    } else {
        /* 奇数自由度 */
        double k = df / 2.0;
        return pow(x, k - 1.0) * exp(-x / 2.0) / (pow(2.0, k) * zhc_gamma(k));
    }
}

/* 卡方分布累积分布函数 */
double zhc_chi2_cdf(double x, int df) {
    if (x <= 0.0 || df <= 0) return 0.0;
    return zhc_gamma_inc(df / 2.0, x / 2.0) / zhc_gamma(df / 2.0);
}

/* t 分布概率密度函数 */
double zhc_t_pdf(double x, int df) {
    if (df <= 0) return NAN;
    double k = (df + 1.0) / 2.0;
    return zhc_gamma(k) / (sqrt(df * M_PI) * zhc_gamma(k - 0.5))
        * pow(1.0 + x * x / df, -k);
}

/* t 分布累积分布函数 */
double zhc_t_cdf(double x, int df) {
    if (df <= 0) return NAN;
    double w = df / (df + x * x);
    double y = 0.5 * zhc_incomplete_beta(df / 2.0, 0.5, w);
    if (x >= 0.0) return 1.0 - y;
    return y;
}

/* F 分布概率密度函数 */
double zhc_f_pdf(double x, int df1, int df2) {
    if (x <= 0.0 || df1 <= 0 || df2 <= 0) return NAN;
    double k1 = df1 / 2.0;
    double k2 = df2 / 2.0;
    double z = pow(df1 * x, k1) * pow(df2, k2) / pow(df1 * x + df2, k1 + k2);
    return z / (x * zhc_beta(k1, k2));
}

/* F 分布累积分布函数 */
double zhc_f_cdf(double x, int df1, int df2) {
    if (x <= 0.0 || df1 <= 0 || df2 <= 0) return 0.0;
    double w = df1 * x / (df1 * x + df2);
    return zhc_incomplete_beta(df1 / 2.0, df2 / 2.0, w);
}

/* 辅助函数: 不完全 Gamma 函数 (使用级数展开) */
static double zhc_gamma_inc(double a, double x) {
    if (x < 0.0 || a <= 0.0) return NAN;
    if (x == 0.0) return 0.0;

    /* 对于小的 x，使用级数展开 */
    if (x < 1.0) {
        double sum = 1.0 / a;
        double term = sum;
        for (int n = 1; n < 100; n++) {
            term *= x / (a + n);
            sum += term;
            if (fabs(term) < 1e-15) break;
        }
        return sum * exp(-x + a * log(x) - zhc_lgamma(a));
    } else {
        /* 对于大的 x，使用连分数展开 */
        double b = x + 1.0 - a;
        double c = 1.0 / 1e-30;
        double d = 1.0 / b;
        double h = d;
        for (int i = 1; i < 100; i++) {
            double an = -i * (i - a);
            b += 2.0;
            d = an * d + b;
            if (fabs(d) < 1e-30) d = 1e-30;
            c = b + an / c;
            if (fabs(c) < 1e-30) c = 1e-30;
            d = 1.0 / d;
            double delta = d * c;
            h *= delta;
            if (fabs(delta - 1.0) < 1e-15) break;
        }
        return exp(-x + a * log(x) - zhc_lgamma(a)) * h;
    }
}

/* 辅助函数: 不完全 Beta 函数 (使用连分数) */
static double zhc_incomplete_beta(double a, double b, double x) {
    if (x < 0.0 || x > 1.0 || a <= 0.0 || b <= 0.0) return NAN;
    if (x == 0.0) return 0.0;
    if (x == 1.0) return 1.0;

    /* 使用不完整 Beta 函数的对称性 */
    if (x > (a + 1.0) / (a + b + 2.0)) {
        return 1.0 - zhc_incomplete_beta(b, a, 1.0 - x);
    }

    /* 使用连分数展开 */
    double lbeta = zhc_lbeta(a, b);
    double front = exp(log(x) * a + log(1.0 - x) * b - lbeta) / a;

    /* 简化的连分数计算 */
    double am = 1.0, bm = 1.0;
    double az = 1.0;
    double qab = a + b;
    double qap = a + 1.0;
    double qam = a - 1.0;
    double bz = 1.0 - qab * x / qap;

    for (int m = 1; m <= 100; m++) {
        double em = m;
        double tem = em + em;
        double d = em * (b - m) * x / ((qam - tem) * (a + tem));
        double ap = az + d * am;
        double bp = bz + d * bm;
        d = -(a + em) * (qab + em) * x / ((qap + tem) * (a + tem));
        double app = ap + d * az;
        double bpp = bp + d * bz;
        double aold = az;
        am = ap / bpp;
        bm = bp / bpp;
        az = app / bpp;
        bz = 1.0;
        if (fabs(az - aold) < 1e-15 * fabs(az)) {
            return front * az;
        }
    }
    return front * az;
}

#endif /* ZHC_SPECIAL_IMPLEMENTATION */

#ifdef __cplusplus
}
#endif

#endif /* ZHC_SPECIAL_H */
