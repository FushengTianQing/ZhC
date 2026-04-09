// -*- coding: utf-8 -*-
/*
 * zhc_encoding.c - 字符编码转换实现
 *
 * 提供字符编码转换的 C 实现
 *
 * 注意：此实现提供基础框架，实际转换由 Python codecs 模块处理。
 * 在生产环境中，可以使用 iconv 库替代。
 *
 * 作者：阿福
 * 日期：2026-04-10
 */

#include "zhc_encoding.h"
#include <stdlib.h>
#include <string.h>

// ============================================================================
// 编码名称映射
// ============================================================================

static const char* encoding_names[] = {
    "auto",         // ZHC_ENCODING_AUTO
    "utf-8",        // ZHC_ENCODING_UTF8
    "gbk",          // ZHC_ENCODING_GBK
    "gb2312",       // ZHC_ENCODING_GB2312
    "gb18030",      // ZHC_ENCODING_GB18030
    "big5",         // ZHC_ENCODING_BIG5
    "shift-jis",    // ZHC_ENCODING_SHIFT_JIS
    "euc-kr",       // ZHC_ENCODING_EUC_KR
    "iso-8859-1",   // ZHC_ENCODING_ISO_8859_1
    "windows-1252", // ZHC_ENCODING_WINDOWS_1252
    "ascii",        // ZHC_ENCODING_ASCII
    "utf-16",       // ZHC_ENCODING_UTF16
    "utf-16le",     // ZHC_ENCODING_UTF16LE
    "utf-16be",     // ZHC_ENCODING_UTF16BE
    "utf-32",       // ZHC_ENCODING_UTF32
};

// ============================================================================
// 辅助函数
// ============================================================================

const char* zhc_encoding_name(ZHCEncoding encoding) {
    if (encoding < 0 || encoding > ZHC_ENCODING_UTF32) {
        return "unknown";
    }
    return encoding_names[encoding];
}

int zhc_is_valid_encoding(ZHCEncoding encoding) {
    return encoding >= 0 && encoding <= ZHC_ENCODING_UTF32;
}

int zhc_is_valid_utf8(const uint8_t* data, size_t data_len) {
    if (data == NULL || data_len == 0) {
        return 1;
    }

    size_t i = 0;
    while (i < data_len) {
        uint8_t c = data[i];

        if (c <= 0x7F) {
            i++;
            continue;
        }

        int seq_len = 0;
        if ((c & 0xE0) == 0xC0) {
            seq_len = 2;
        } else if ((c & 0xF0) == 0xE0) {
            seq_len = 3;
        } else if ((c & 0xF8) == 0xF0) {
            seq_len = 4;
        } else {
            return 0;
        }

        if (i + seq_len > data_len) {
            return 0;
        }

        for (int j = 1; j < seq_len; j++) {
            if ((data[i + j] & 0xC0) != 0x80) {
                return 0;
            }
        }

        i += seq_len;
    }

    return 1;
}

// ============================================================================
// 编码检测
// ============================================================================

ZHCEncodingDetectionResult zhc_detect_encoding(
    const uint8_t* data,
    size_t data_len
) {
    ZHCEncodingDetectionResult result = {ZHC_ENCODING_UTF8, 0.0f};

    if (data == NULL || data_len == 0) {
        result.encoding = ZHC_ENCODING_UTF8;
        result.confidence = 1.0f;
        return result;
    }

    // 检查 BOM
    if (data_len >= 3 && data[0] == 0xEF && data[1] == 0xBB && data[2] == 0xBF) {
        result.encoding = ZHC_ENCODING_UTF8;
        result.confidence = 1.0f;
        return result;
    }

    if (data_len >= 2) {
        if (data[0] == 0xFF && data[1] == 0xFE) {
            result.encoding = ZHC_ENCODING_UTF16LE;
            result.confidence = 1.0f;
            return result;
        }
        if (data[0] == 0xFE && data[1] == 0xFF) {
            result.encoding = ZHC_ENCODING_UTF16BE;
            result.confidence = 1.0f;
            return result;
        }
    }

    // 检查是否为有效的 UTF-8
    if (zhc_is_valid_utf8(data, data_len)) {
        int has_multibyte = 0;
        for (size_t i = 0; i < data_len; i++) {
            if (data[i] > 0x7F) {
                has_multibyte = 1;
                break;
            }
        }

        if (has_multibyte) {
            result.encoding = ZHC_ENCODING_UTF8;
            result.confidence = 0.8f;
        } else {
            result.encoding = ZHC_ENCODING_ASCII;
            result.confidence = 1.0f;
        }
    } else {
        result.encoding = ZHC_ENCODING_GBK;
        result.confidence = 0.5f;
    }

    return result;
}

// ============================================================================
// 编码转换
// ============================================================================

size_t zhc_convert_encoding_size(
    const uint8_t* input,
    size_t input_len,
    ZHCEncoding from_encoding,
    ZHCEncoding to_encoding
) {
    if (input == NULL || input_len == 0) {
        return 0;
    }

    // 估算：UTF-8 最大扩展 4 倍
    // 其他编码通常使用 1-2 字节
    (void)from_encoding;
    (void)to_encoding;

    return input_len * 4 + 1;
}

int zhc_convert_encoding(
    const uint8_t* input,
    size_t input_len,
    ZHCEncoding from_encoding,
    ZHCEncoding to_encoding,
    uint8_t* output,
    size_t output_size
) {
    // 此函数需要实际的编码转换实现
    // 在生产环境中，应使用 iconv 或 Python codecs
    // 这里只是一个框架实现

    if (input == NULL || input_len == 0) {
        return -1;
    }

    size_t required_size = zhc_convert_encoding_size(
        input, input_len, from_encoding, to_encoding
    );

    if (output == NULL) {
        return (int)required_size;
    }

    if (output_size < required_size) {
        return -1;
    }

    // 如果源和目标编码相同，直接复制
    if (from_encoding == to_encoding) {
        memcpy(output, input, input_len);
        return (int)input_len;
    }

    // 实际的编码转换需要外部库支持
    // 这里返回错误，表示需要 Python 回调
    return -1;
}

int zhc_to_utf8(
    const uint8_t* input,
    size_t input_len,
    ZHCEncoding from_encoding,
    char* output,
    size_t output_size
) {
    return zhc_convert_encoding(
        input, input_len,
        from_encoding, ZHC_ENCODING_UTF8,
        (uint8_t*)output, output_size
    );
}

int zhc_from_utf8(
    const char* input,
    size_t input_len,
    ZHCEncoding to_encoding,
    uint8_t* output,
    size_t output_size
) {
    return zhc_convert_encoding(
        (const uint8_t*)input, input_len,
        ZHC_ENCODING_UTF8, to_encoding,
        output, output_size
    );
}

// ============================================================================
// Unicode 规范化
// ============================================================================

size_t zhc_normalize_unicode_size(
    const char* input,
    size_t input_len,
    ZHCNormalizationForm form
) {
    if (input == NULL || input_len == 0) {
        return 0;
    }

    // 规范化通常不会显著改变长度
    (void)form;
    return input_len + 1;
}

int zhc_normalize_unicode(
    const char* input,
    size_t input_len,
    ZHCNormalizationForm form,
    char* output,
    size_t output_size
) {
    if (input == NULL || input_len == 0) {
        return -1;
    }

    size_t required_size = zhc_normalize_unicode_size(input, input_len, form);

    if (output == NULL) {
        return (int)required_size;
    }

    if (output_size < required_size) {
        return -1;
    }

    // 实际的规范化需要外部库支持
    // 这里返回错误，表示需要 Python 回调
    (void)form;
    return -1;
}
