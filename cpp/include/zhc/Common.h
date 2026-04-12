//===--- Common.h - ZhC Common Definitions ------------------------------===//
//
// This file defines common types and utilities used throughout the ZhC compiler.
//
//===----------------------------------------------------------------------===//

#ifndef ZHC_COMMON_H
#define ZHC_COMMON_H

#include <cstdint>
#include <string>
#include <string_view>
#include <vector>
#include <memory>
#include <unordered_map>

namespace zhc {

/// Source location in a file (line, column)
struct SourceLocation {
  uint32_t Line = 0;
  uint32_t Column = 0;
  uint32_t FileID = 0;  // Index into SourceManager's file table
  
  SourceLocation() = default;
  SourceLocation(uint32_t line, uint32_t col, uint32_t fileID = 0)
      : Line(line), Column(col), FileID(fileID) {}
  
  bool isValid() const { return Line > 0 && Column > 0; }
};

/// Source range spanning from Start to End
struct SourceRange {
  SourceLocation Start;
  SourceLocation End;
  
  SourceRange() = default;
  SourceRange(SourceLocation start, SourceLocation end)
      : Start(start), End(end) {}
  
  bool isValid() const { return Start.isValid() && End.isValid(); }
};

/// UTF-8 aware string utilities
namespace utf8 {

/// Check if a byte is the start of a UTF-8 character
inline bool isLeadByte(uint8_t b) {
  return (b & 0xC0) != 0x80;  // Not a continuation byte
}

/// Get the byte length of a UTF-8 character from its lead byte
inline uint8_t charLength(uint8_t leadByte) {
  if ((leadByte & 0x80) == 0) return 1;       // ASCII
  if ((leadByte & 0xE0) == 0xC0) return 2;    // 2-byte
  if ((leadByte & 0xF0) == 0xE0) return 3;    // 3-byte
  if ((leadByte & 0xF8) == 0xF0) return 4;    // 4-byte
  return 1;  // Invalid, treat as single byte
}

/// Count UTF-8 characters in a string
size_t countChars(std::string_view str);

/// Get the nth UTF-8 character position (byte offset)
size_t charPosition(std::string_view str, size_t charIndex);

} // namespace utf8

} // namespace zhc

#endif // ZHC_COMMON_H