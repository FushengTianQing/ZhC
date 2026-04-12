//===--- Unicode.h - Unicode Support Utilities ---------------------------===//
//
// Unicode utilities for the ZhC compiler (中文编程语言).
// Follows Unicode UAX #31 (Identifier and Pattern Syntax).
//
//===----------------------------------------------------------------------===//

#ifndef ZHC_UNICODE_H
#define ZHC_UNICODE_H

#include "llvm/ADT/StringRef.h"
#include <cstdint>

namespace zhc {
namespace unicode {

/// Check if a code point is a Unicode identifier start character (XID_Start)
/// Includes: CJK Unified Ideographs, Latin letters, underscore, etc.
bool isXIDStart(uint32_t codePoint);

/// Check if a code point is a Unicode identifier continuation character (XID_Continue)
/// Includes: XID_Start + digits + connecting marks, etc.
bool isXIDContinue(uint32_t codePoint);

/// Check if a code point is a CJK Unified Ideograph
/// Range: U+4E00~U+9FFF (Basic), U+3400~U+4DBF (Ext A), U+20000~U+2A6DF (Ext B)
bool isCJKCharacter(uint32_t codePoint);

/// Check if a code point is Chinese/fullwidth punctuation that needs special handling
bool isChinesePunctuation(uint32_t codePoint);

/// Check if a code point is Unicode whitespace (not just ASCII space)
bool isUnicodeWhitespace(uint32_t codePoint);

/// Decode a UTF-8 sequence from buffer, returning the code point
/// @param ptr Pointer to start of UTF-8 sequence
/// @param codePoint Output code point
/// @returns Number of bytes consumed, 0 if invalid UTF-8
unsigned decodeUTF8(const char* ptr, uint32_t& codePoint);

/// Encode a Unicode code point to UTF-8
/// @param codePoint Unicode code point
/// @param out Output buffer (must be at least 4 bytes)
/// @returns Number of bytes written
unsigned encodeUTF8(uint32_t codePoint, char* out);

/// Get the byte length of a UTF-8 sequence from its lead byte
unsigned getUTF8SequenceLength(unsigned char firstByte);

/// Count the number of Unicode code points in a string (not bytes)
size_t countCodePoints(llvm::StringRef str);

/// Check if a byte sequence is valid UTF-8
bool isValidUTF8(llvm::StringRef str);

/// Convert a Unicode escape sequence (\uXXXX or \UXXXXXXXX) to code point
/// @param ptr Pointer past the 'u' or 'U' character
/// @param codePoint Output code point
/// @returns Number of hex digits consumed, 0 if invalid
unsigned parseUnicodeEscape(const char* ptr, uint32_t& codePoint);

} // namespace unicode
} // namespace zhc

#endif // ZHC_UNICODE_H