// -*- coding: utf-8 -*-
/*
 * zhc_encoding.h - 字符编码转换头文件
 *
 * 提供字符编码转换的 C 接口定义
 *
 * 作者：阿福
 * 日期：2026-04-10
 */

#ifndef ZHC_ENCODING_H
#define ZHC_ENCODING_H

#include <stddef.h>
#include <stdint.h>

// ============================================================================
// 编码类型定义
// ============================================================================

// 编码类型枚举
typedef enum {
    ZHC_ENCODING_AUTO = 0,      // 自动检测
    ZHC_ENCODING_UTF8 = 1,      // UTF-8
    ZHC_ENCODING_GBK = 2,        // GBK
    ZHC_ENCODING_GB2312 = 3,    // GB2312
    ZHC_ENCODING_GB18030 = 4,   // GB18030
    ZHC_ENCODING_BIG5 = 5,      // Big5
    ZHC_ENCODING_SHIFT_JIS = 6, // Shift-JIS
    ZHC_ENCODING_EUC_KR = 7,    // EUC-KR
    ZHC_ENCODING_ISO_8859_1 = 8, // ISO-8859-1
    ZHC_ENCODING_WINDOWS_1252 = 9, // Windows-1252
    ZHC_ENCODING_ASCII = 10,    // ASCII
    ZHC_ENCODING_UTF16 = 11,    // UTF-16
    ZHC_ENCODING_UTF16LE = 12,  // UTF-16 LE
    ZHC_ENCODING_UTF16BE = 13,  // UTF-16 BE
    ZHC_ENCODING_UTF32 = 14,    // UTF-32
} ZHCEncoding;

// Unicode 规范化形式
typedef enum {
    ZHC_NFC = 0, // 标准组合
    ZHC_NFD = 1, // 标准分解
    ZHC_NFKC = 2, // 兼容组合
    ZHC_NFKD = 3  // 兼容分解
} ZHCNormalizationForm;

// 编码检测结果
typedef struct {
    ZHCEncoding encoding;
    float confidence;  // 置信度 0.0-1.0
} ZHCEncodingDetectionResult;

// ============================================================================
// 编码转换函数
// ============================================================================

/**
 * 转换编码
 *
 * @param input 输入数据
 * @param input_len 输入长度
 * @param from_encoding 源编码
 * @param to_encoding 目标编码
 * @param output 输出缓冲区（可以为 NULL 用于查询长度）
 * @param output_size 输出缓冲区大小
 * @return 转换后的字节数，-1 表示错误
 */
int zhc_convert_encoding(
    const uint8_t* input,
    size_t input_len,
    ZHCEncoding from_encoding,
    ZHCEncoding to_encoding,
    uint8_t* output,
    size_t output_size
);

/**
 * 获取转换所需的目标缓冲区大小
 *
 * @param input 输入数据
 * @param input_len 输入长度
 * @param from_encoding 源编码
 * @param to_encoding 目标编码
 * @return 所需的缓冲区大小，0 表示错误
 */
size_t zhc_convert_encoding_size(
    const uint8_t* input,
    size_t input_len,
    ZHCEncoding from_encoding,
    ZHCEncoding to_encoding
);

/**
 * 检测字节序列的编码
 *
 * @param data 输入数据
 * @param data_len 输入长度
 * @return 检测结果
 */
ZHCEncodingDetectionResult zhc_detect_encoding(
    const uint8_t* data,
    size_t data_len
);

/**
 * 将数据转换为 UTF-8
 *
 * @param input 输入数据
 * @param input_len 输入长度
 * @param from_encoding 源编码
 * @param output 输出缓冲区（可以为 NULL）
 * @param output_size 输出缓冲区大小
 * @return 转换后的字节数，-1 表示错误
 */
int zhc_to_utf8(
    const uint8_t* input,
    size_t input_len,
    ZHCEncoding from_encoding,
    char* output,
    size_t output_size
);

/**
 * 从 UTF-8 转换
 *
 * @param input UTF-8 输入
 * @param input_len 输入长度
 * @param to_encoding 目标编码
 * @param output 输出缓冲区（可以为 NULL）
 * @param output_size 输出缓冲区大小
 * @return 转换后的字节数，-1 表示错误
 */
int zhc_from_utf8(
    const char* input,
    size_t input_len,
    ZHCEncoding to_encoding,
    uint8_t* output,
    size_t output_size
);

// ============================================================================
// Unicode 规范化函数
// ============================================================================

/**
 * Unicode 规范化
 *
 * @param input 输入字符串（UTF-8）
 * @param input_len 输入长度
 * @param form 规范化形式
 * @param output 输出缓冲区（可以为 NULL）
 * @param output_size 输出缓冲区大小
 * @return 规范化后的长度，-1 表示错误
 */
int zhc_normalize_unicode(
    const char* input,
    size_t input_len,
    ZHCNormalizationForm form,
    char* output,
    size_t output_size
);

/**
 * 获取规范化后的字符串长度
 *
 * @param input 输入字符串（UTF-8）
 * @param input_len 输入长度
 * @param form 规范化形式
 * @return 规范化后的长度，0 表示错误
 */
size_t zhc_normalize_unicode_size(
    const char* input,
    size_t input_len,
    ZHCNormalizationForm form
);

// ============================================================================
// 辅助函数
// ============================================================================

/**
 * 获取编码名称
 *
 * @param encoding 编码类型
 * @return 编码名称字符串
 */
const char* zhc_encoding_name(ZHCEncoding encoding);

/**
 * 检查编码是否有效
 *
 * @param encoding 编码类型
 * @return 是否有效
 */
int zhc_is_valid_encoding(ZHCEncoding encoding);

/**
 * 检查数据是否为有效的 UTF-8
 *
 * @param data 数据
 * @param data_len 数据长度
 * @return 是否为有效的 UTF-8
 */
int zhc_is_valid_utf8(const uint8_t* data, size_t data_len);

#endif // ZHC_ENCODING_H
