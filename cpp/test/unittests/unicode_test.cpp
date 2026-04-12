//===--- unicode_test.cpp - Unicode Unit Tests --------------------------===//
//
// Unit tests for Unicode utilities in the ZhC compiler.
//
//===----------------------------------------------------------------------===//

#include <gtest/gtest.h>

#include "zhc/Unicode.h"

using namespace zhc::unicode;

//===--- Code Point Classification Tests ---------------------------------===//

TEST(UnicodeTest, XIDStartASCII) {
  EXPECT_TRUE(isXIDStart('A'));
  EXPECT_TRUE(isXIDStart('Z'));
  EXPECT_TRUE(isXIDStart('a'));
  EXPECT_TRUE(isXIDStart('z'));
  EXPECT_TRUE(isXIDStart('_'));
  EXPECT_FALSE(isXIDStart('0'));
  EXPECT_FALSE(isXIDStart('9'));
  EXPECT_FALSE(isXIDStart('-'));
}

TEST(UnicodeTest, XIDStartCJK) {
  EXPECT_TRUE(isXIDStart(0x4E00));   // '一' (first CJK character)
  EXPECT_TRUE(isXIDStart(0x4E2D));   // '中'
  EXPECT_TRUE(isXIDStart(0x5F20));   // '张'
  EXPECT_TRUE(isXIDStart(0x9FFF));   // Last basic CJK
  EXPECT_TRUE(isXIDStart(0x3400));   // CJK Ext A start
  EXPECT_TRUE(isXIDStart(0x4DBF));   // CJK Ext A end
}

TEST(UnicodeTest, XIDStartLatinExtended) {
  EXPECT_TRUE(isXIDStart(0x00C0));   // 'À'
  EXPECT_TRUE(isXIDStart(0x00D6));   // 'Ö'
  EXPECT_TRUE(isXIDStart(0x00D8));   // 'Ø'
  EXPECT_TRUE(isXIDStart(0x00F6));   // 'ö'
  EXPECT_TRUE(isXIDStart(0x00F8));   // 'ø'
}

TEST(UnicodeTest, XIDContinue) {
  EXPECT_TRUE(isXIDContinue('0'));
  EXPECT_TRUE(isXIDContinue('9'));
  EXPECT_TRUE(isXIDContinue(0x4E2D));  // '中' (also XIDStart)
  EXPECT_TRUE(isXIDContinue(0x0300));  // Combining accent
  EXPECT_FALSE(isXIDContinue('-'));
  EXPECT_FALSE(isXIDContinue(' '));
}

TEST(UnicodeTest, CJKCharacter) {
  EXPECT_TRUE(isCJKCharacter(0x4E00));   // '一'
  EXPECT_TRUE(isCJKCharacter(0x4E2D));   // '中'
  EXPECT_TRUE(isCJKCharacter(0x9FFF));   // Last basic
  EXPECT_TRUE(isCJKCharacter(0x3400));   // Ext A
  EXPECT_TRUE(isCJKCharacter(0xF900));   // Compatibility
  EXPECT_FALSE(isCJKCharacter(0x0041));  // 'A'
  EXPECT_FALSE(isCJKCharacter(0x0030));  // '0'
}

TEST(UnicodeTest, ChinesePunctuation) {
  EXPECT_TRUE(isChinesePunctuation(0xFF08));   // '（' fullwidth left paren
  EXPECT_TRUE(isChinesePunctuation(0xFF09));   // '）' fullwidth right paren
  EXPECT_TRUE(isChinesePunctuation(0xFF1B));   // '；' fullwidth semicolon
  EXPECT_TRUE(isChinesePunctuation(0xFF01));   // '！' fullwidth exclamation
  EXPECT_TRUE(isChinesePunctuation(0x3000));   // Ideographic space
  EXPECT_FALSE(isChinesePunctuation('('));     // ASCII left paren
  EXPECT_FALSE(isChinesePunctuation(';'));     // ASCII semicolon
}

TEST(UnicodeTest, UnicodeWhitespace) {
  EXPECT_TRUE(isUnicodeWhitespace(' '));
  EXPECT_TRUE(isUnicodeWhitespace('\t'));
  EXPECT_TRUE(isUnicodeWhitespace('\n'));
  EXPECT_TRUE(isUnicodeWhitespace(0x00A0));   // NBSP
  EXPECT_TRUE(isUnicodeWhitespace(0x3000));   // Ideographic space
  EXPECT_FALSE(isUnicodeWhitespace('A'));
  EXPECT_FALSE(isUnicodeWhitespace(0x4E00));  // '一'
}

//===--- UTF-8 Encoding/Decoding Tests -----------------------------------===//

TEST(UnicodeTest, DecodeASCII) {
  uint32_t cp;
  EXPECT_EQ(decodeUTF8("A", cp), 1u);
  EXPECT_EQ(cp, 0x41u);
  
  EXPECT_EQ(decodeUTF8("z", cp), 1u);
  EXPECT_EQ(cp, 0x7Au);
}

TEST(UnicodeTest, Decode2Byte) {
  uint32_t cp;
  // 'À' U+00C0 = C3 80
  const char* a = "\xC3\x80";
  EXPECT_EQ(decodeUTF8(a, cp), 2u);
  EXPECT_EQ(cp, 0x00C0u);
}

TEST(UnicodeTest, Decode3Byte) {
  uint32_t cp;
  // '中' U+4E2D = E4 B8 AD
  const char* zhong = "\xE4\xB8\xAD";
  EXPECT_EQ(decodeUTF8(zhong, cp), 3u);
  EXPECT_EQ(cp, 0x4E2Du);
  
  // '一' U+4E00 = E4 B8 80
  const char* yi = "\xE4\xB8\x80";
  EXPECT_EQ(decodeUTF8(yi, cp), 3u);
  EXPECT_EQ(cp, 0x4E00u);
}

TEST(UnicodeTest, Decode4Byte) {
  uint32_t cp;
  // '😀' U+1F600 = F0 9F 98 80
  const char* emoji = "\xF0\x9F\x98\x80";
  EXPECT_EQ(decodeUTF8(emoji, cp), 4u);
  EXPECT_EQ(cp, 0x1F600u);
}

TEST(UnicodeTest, DecodeInvalid) {
  uint32_t cp;
  // Invalid lead byte
  EXPECT_EQ(decodeUTF8("\xFF", cp), 0u);
  
  // Incomplete sequence
  EXPECT_EQ(decodeUTF8("\xE4", cp), 0u);  // Missing continuation bytes
  
  // Invalid continuation byte
  EXPECT_EQ(decodeUTF8("\xE4\xB8\x41", cp), 0u);  // 'A' instead of continuation
}

TEST(UnicodeTest, EncodeASCII) {
  char out[4];
  EXPECT_EQ(encodeUTF8(0x41, out), 1u);  // 'A'
  EXPECT_EQ(out[0], 'A');
}

TEST(UnicodeTest, Encode3Byte) {
  char out[4];
  EXPECT_EQ(encodeUTF8(0x4E2D, out), 3u);  // '中'
  EXPECT_EQ(out[0], '\xE4');
  EXPECT_EQ(out[1], '\xB8');
  EXPECT_EQ(out[2], '\xAD');
}

TEST(UnicodeTest, Encode4Byte) {
  char out[4];
  EXPECT_EQ(encodeUTF8(0x1F600, out), 4u);  // '😀'
  EXPECT_EQ(out[0], '\xF0');
  EXPECT_EQ(out[1], '\x9F');
  EXPECT_EQ(out[2], '\x98');
  EXPECT_EQ(out[3], '\x80');
}

TEST(UnicodeTest, SequenceLength) {
  EXPECT_EQ(getUTF8SequenceLength('A'), 1u);
  EXPECT_EQ(getUTF8SequenceLength('\xC3'), 2u);
  EXPECT_EQ(getUTF8SequenceLength('\xE4'), 3u);
  EXPECT_EQ(getUTF8SequenceLength('\xF0'), 4u);
  EXPECT_EQ(getUTF8SequenceLength('\xFF'), 0u);  // Invalid
}

//===--- String Operations Tests -----------------------------------------===//

TEST(UnicodeTest, CountCodePointsASCII) {
  EXPECT_EQ(countCodePoints("hello"), 5u);
  EXPECT_EQ(countCodePoints(""), 0u);
  EXPECT_EQ(countCodePoints("A"), 1u);
}

TEST(UnicodeTest, CountCodePointsCJK) {
  EXPECT_EQ(countCodePoints("你好世界"), 4u);
  EXPECT_EQ(countCodePoints("中"), 1u);
  EXPECT_EQ(countCodePoints("中文编程"), 4u);
}

TEST(UnicodeTest, CountCodePointsMixed) {
  EXPECT_EQ(countCodePoints("hello你好"), 7u);
  EXPECT_EQ(countCodePoints("A中B"), 3u);
  // "变量x = 5" = 变(1) + 量(1) + x(1) + space(1) + =(1) + space(1) + 5(1) = 7
  EXPECT_EQ(countCodePoints("变量x = 5"), 7u);
}

TEST(UnicodeTest, IsValidUTF8) {
  EXPECT_TRUE(isValidUTF8("hello"));
  EXPECT_TRUE(isValidUTF8("你好世界"));
  EXPECT_TRUE(isValidUTF8("hello你好"));
  EXPECT_FALSE(isValidUTF8("\xFF"));  // Invalid byte
  EXPECT_FALSE(isValidUTF8("\xE4\xB8"));  // Incomplete sequence
}

//===--- Unicode Escape Tests --------------------------------------------===//

TEST(UnicodeTest, ParseUnicodeEscape) {
  uint32_t cp;
  
  // \u4E2D = '中'
  EXPECT_EQ(parseUnicodeEscape("4E2D", cp), 4u);
  EXPECT_EQ(cp, 0x4E2Du);
  
  // \u0041 = 'A'
  EXPECT_EQ(parseUnicodeEscape("0041", cp), 4u);
  EXPECT_EQ(cp, 0x41u);
  
  // Invalid hex
  EXPECT_EQ(parseUnicodeEscape("4E2G", cp), 0u);  // 'G' is not hex
}