//===--- Common.cpp - ZhC Common Utilities Implementation -----------------===//
//
// This file implements common utilities for the ZhC compiler.
//
//===----------------------------------------------------------------------===//

#include "zhc/Common.h"

namespace zhc {

namespace utf8 {

size_t countChars(std::string_view str) {
  size_t count = 0;
  for (size_t i = 0; i < str.size(); ) {
    uint8_t b = static_cast<uint8_t>(str[i]);
    if (isLeadByte(b)) {
      count++;
    }
    i += charLength(b);
  }
  return count;
}

size_t charPosition(std::string_view str, size_t charIndex) {
  size_t count = 0;
  size_t bytePos = 0;
  
  while (bytePos < str.size() && count < charIndex) {
    uint8_t b = static_cast<uint8_t>(str[bytePos]);
    bytePos += charLength(b);
    if (isLeadByte(b)) {
      count++;
    }
  }
  
  return bytePos;
}

} // namespace utf8

} // namespace zhc