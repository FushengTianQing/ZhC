//===--- Unicode.cpp - Unicode Support Implementation --------------------===//
//
// Implementation of Unicode utilities for the ZhC compiler.
//
//===----------------------------------------------------------------------===//

#include "zhc/Unicode.h"

#include <cstring>

namespace zhc {
namespace unicode {

//===--- Code Point Classification ----------------------------------------===//

bool isXIDStart(uint32_t cp) {
  // ASCII letters and underscore
  if ((cp >= 'A' && cp <= 'Z') || (cp >= 'a' && cp <= 'z') || cp == '_') {
    return true;
  }
  
  // CJK Unified Ideographs (U+4E00 ~ U+9FFF) - most common Chinese characters
  if (cp >= 0x4E00 && cp <= 0x9FFF) return true;
  
  // CJK Extension A (U+3400 ~ U+4DBF)
  if (cp >= 0x3400 && cp <= 0x4DBF) return true;
  
  // CJK Extension B (U+20000 ~ U+2A6DF)
  if (cp >= 0x20000 && cp <= 0x2A6DF) return true;
  
  // CJK Extension C-G (U+2A700 ~ U+2EBEF)
  if (cp >= 0x2A700 && cp <= 0x2EBEF) return true;
  
  // CJK Compatibility Ideographs (U+F900 ~ U+FAFF)
  if (cp >= 0xF900 && cp <= 0xFAFF) return true;
  
  // Latin Extended (À-Ö, Ø-ö, ø-ÿ, and more)
  if (cp >= 0x00C0 && cp <= 0x00D6) return true;
  if (cp >= 0x00D8 && cp <= 0x00F6) return true;
  if (cp >= 0x00F8 && cp <= 0x02FF) return true;
  
  // Greek (U+0370 ~ U+03FF)
  if (cp >= 0x0370 && cp <= 0x03FF) return true;
  
  // Cyrillic (U+0400 ~ U+04FF)
  if (cp >= 0x0400 && cp <= 0x04FF) return true;
  
  // Hiragana (U+3040 ~ U+309F)
  if (cp >= 0x3040 && cp <= 0x309F) return true;
  
  // Katakana (U+30A0 ~ U+30FF)
  if (cp >= 0x30A0 && cp <= 0x30FF) return true;
  
  // Hangul Syllables (U+AC00 ~ U+D7AF)
  if (cp >= 0xAC00 && cp <= 0xD7AF) return true;
  
  // General punctuation that's considered identifier start (Letterlike symbols)
  // This is a simplified version - a full implementation would use Unicode data tables
  
  return false;
}

bool isXIDContinue(uint32_t cp) {
  // XID_Start is a subset of XID_Continue
  if (isXIDStart(cp)) return true;
  
  // ASCII digits
  if (cp >= '0' && cp <= '9') return true;
  
  // Combining Diacritical Marks (U+0300 ~ U+036F)
  if (cp >= 0x0300 && cp <= 0x036F) return true;
  
  // Middle dot (·)
  if (cp == 0x00B7) return true;
  
  // Connector punctuation (low line already covered by '_')
  // Underscore variants
  if (cp == 0x203F || cp == 0x2040) return true;  // ‿ ⁀
  
  return false;
}

bool isCJKCharacter(uint32_t cp) {
  // CJK Unified Ideographs (U+4E00 ~ U+9FFF)
  if (cp >= 0x4E00 && cp <= 0x9FFF) return true;
  
  // CJK Extension A (U+3400 ~ U+4DBF)
  if (cp >= 0x3400 && cp <= 0x4DBF) return true;
  
  // CJK Extension B (U+20000 ~ U+2A6DF)
  if (cp >= 0x20000 && cp <= 0x2A6DF) return true;
  
  // CJK Compatibility Ideographs (U+F900 ~ U+FAFF)
  if (cp >= 0xF900 && cp <= 0xFAFF) return true;
  
  // CJK Radicals Supplement (U+2E80 ~ U+2EFF)
  if (cp >= 0x2E80 && cp <= 0x2EFF) return true;
  
  // Kangxi Radicals (U+2F00 ~ U+2FDF)
  if (cp >= 0x2F00 && cp <= 0x2FDF) return true;
  
  // CJK Strokes (U+31C0 ~ U+31EF)
  if (cp >= 0x31C0 && cp <= 0x31EF) return true;
  
  return false;
}

bool isChinesePunctuation(uint32_t cp) {
  // Fullwidth ASCII variants
  if (cp >= 0xFF01 && cp <= 0xFF5E) return true;   // ！～
  if (cp >= 0xFF5F && cp <= 0xFF60) return true;   // ｟｠
  if (cp >= 0xFF61 && cp <= 0xFF9F) return true;   // ｡～ﾟ (halfwidth katakana punct)
  
  // CJK Symbol and Punctuation (U+3000 ~ U+303F)
  if (cp >= 0x3000 && cp <= 0x303F) return true;
  
  // CJK Compatibility Forms (U+FE30 ~ U+FE4F)
  if (cp >= 0xFE30 && cp <= 0xFE4F) return true;
  
  return false;
}

bool isUnicodeWhitespace(uint32_t cp) {
  // ASCII whitespace
  if (cp == ' ' || cp == '\t' || cp == '\n' || cp == '\r' ||
      cp == '\f' || cp == '\v') {
    return true;
  }
  
  // Unicode whitespace characters
  switch (cp) {
    case 0x00A0:   // No-Break Space (NBSP)
    case 0x1680:   // Ogham Space Mark
    case 0x2000:   // En Quad
    case 0x2001:   // Em Quad
    case 0x2002:   // En Space
    case 0x2003:   // Em Space
    case 0x2004:   // Three-Per-Em Space
    case 0x2005:   // Four-Per-Em Space
    case 0x2006:   // Six-Per-Em Space
    case 0x2007:   // Figure Space
    case 0x2008:   // Punctuation Space
    case 0x2009:   // Thin Space
    case 0x200A:   // Hair Space
    case 0x2028:   // Line Separator
    case 0x2029:   // Paragraph Separator
    case 0x202F:   // Narrow No-Break Space
    case 0x205F:   // Medium Mathematical Space
    case 0x3000:   // Ideographic Space (全角空格)
      return true;
    default:
      return false;
  }
}

//===--- UTF-8 Encoding/Decoding -----------------------------------------===//

unsigned decodeUTF8(const char* ptr, uint32_t& codePoint) {
  const unsigned char* p = reinterpret_cast<const unsigned char*>(ptr);
  
  codePoint = 0;
  
  unsigned char b0 = p[0];
  
  if (b0 < 0x80) {
    // 1-byte: 0xxxxxxx
    codePoint = b0;
    return 1;
  } else if ((b0 & 0xE0) == 0xC0) {
    // 2-byte: 110xxxxx 10xxxxxx
    if ((p[1] & 0xC0) != 0x80) return 0;
    codePoint = ((uint32_t)(b0 & 0x1F) << 6) | (p[1] & 0x3F);
    if (codePoint < 0x80) return 0;  // Overlong encoding
    return 2;
  } else if ((b0 & 0xF0) == 0xE0) {
    // 3-byte: 1110xxxx 10xxxxxx 10xxxxxx
    if ((p[1] & 0xC0) != 0x80 || (p[2] & 0xC0) != 0x80) return 0;
    codePoint = ((uint32_t)(b0 & 0x0F) << 12) |
                ((uint32_t)(p[1] & 0x3F) << 6) |
                (p[2] & 0x3F);
    if (codePoint < 0x800) return 0;  // Overlong encoding
    // Surrogate pairs are invalid in UTF-8
    if (codePoint >= 0xD800 && codePoint <= 0xDFFF) return 0;
    return 3;
  } else if ((b0 & 0xF8) == 0xF0) {
    // 4-byte: 11110xxx 10xxxxxx 10xxxxxx 10xxxxxx
    if ((p[1] & 0xC0) != 0x80 || (p[2] & 0xC0) != 0x80 ||
        (p[3] & 0xC0) != 0x80) return 0;
    codePoint = ((uint32_t)(b0 & 0x07) << 18) |
                ((uint32_t)(p[1] & 0x3F) << 12) |
                ((uint32_t)(p[2] & 0x3F) << 6) |
                (p[3] & 0x3F);
    if (codePoint < 0x10000 || codePoint > 0x10FFFF) return 0;  // Overlong/overflow
    return 4;
  }
  
  return 0;  // Invalid lead byte
}

unsigned encodeUTF8(uint32_t codePoint, char* out) {
  if (codePoint < 0x80) {
    out[0] = static_cast<char>(codePoint);
    return 1;
  } else if (codePoint < 0x800) {
    out[0] = static_cast<char>(0xC0 | (codePoint >> 6));
    out[1] = static_cast<char>(0x80 | (codePoint & 0x3F));
    return 2;
  } else if (codePoint < 0x10000) {
    out[0] = static_cast<char>(0xE0 | (codePoint >> 12));
    out[1] = static_cast<char>(0x80 | ((codePoint >> 6) & 0x3F));
    out[2] = static_cast<char>(0x80 | (codePoint & 0x3F));
    return 3;
  } else if (codePoint <= 0x10FFFF) {
    out[0] = static_cast<char>(0xF0 | (codePoint >> 18));
    out[1] = static_cast<char>(0x80 | ((codePoint >> 12) & 0x3F));
    out[2] = static_cast<char>(0x80 | ((codePoint >> 6) & 0x3F));
    out[3] = static_cast<char>(0x80 | (codePoint & 0x3F));
    return 4;
  }
  return 0;  // Invalid code point
}

unsigned getUTF8SequenceLength(unsigned char firstByte) {
  if (firstByte < 0x80) return 1;
  if ((firstByte & 0xE0) == 0xC0) return 2;
  if ((firstByte & 0xF0) == 0xE0) return 3;
  if ((firstByte & 0xF8) == 0xF0) return 4;
  return 0;  // Invalid
}

size_t countCodePoints(llvm::StringRef str) {
  size_t count = 0;
  size_t i = 0;
  
  while (i < str.size()) {
    unsigned char b = static_cast<unsigned char>(str[i]);
    unsigned len = getUTF8SequenceLength(b);
    if (len == 0) {
      // Invalid byte, skip
      i++;
      continue;
    }
    if (i + len > str.size()) break;
    
    // Validate the sequence
    uint32_t cp;
    if (decodeUTF8(str.data() + i, cp) > 0) {
      count++;
    }
    i += len;
  }
  
  return count;
}

bool isValidUTF8(llvm::StringRef str) {
  size_t i = 0;
  
  while (i < str.size()) {
    unsigned char b = static_cast<unsigned char>(str[i]);
    unsigned len = getUTF8SequenceLength(b);
    
    if (len == 0) return false;
    if (i + len > str.size()) return false;
    
    uint32_t cp;
    if (decodeUTF8(str.data() + i, cp) == 0) return false;
    
    i += len;
  }
  
  return true;
}

unsigned parseUnicodeEscape(const char* ptr, uint32_t& codePoint) {
  codePoint = 0;
  
  // Check for 4-digit \uXXXX or 8-digit \UXXXXXXXX
  // ptr should point past the 'u' or 'U'
  unsigned numDigits = 4;  // Default \uXXXX
  
  unsigned i = 0;
  while (i < numDigits) {
    char c = ptr[i];
    if (c == 0) return 0;
    
    codePoint <<= 4;
    if (c >= '0' && c <= '9') {
      codePoint |= (c - '0');
    } else if (c >= 'a' && c <= 'f') {
      codePoint |= (c - 'a' + 10);
    } else if (c >= 'A' && c <= 'F') {
      codePoint |= (c - 'A' + 10);
    } else {
      return 0;  // Invalid hex digit
    }
    i++;
  }
  
  // Validate code point range
  if (codePoint > 0x10FFFF) return 0;
  if (codePoint >= 0xD800 && codePoint <= 0xDFFF) return 0;  // Surrogate
  
  return numDigits;
}

} // namespace unicode
} // namespace zhc