//===--- lexer_test.cpp - ZhC Lexer Unit Tests --------------------------===//
//
// Unit tests for the ZhC lexer.
//
//===----------------------------------------------------------------------===//

#include <gtest/gtest.h>

#include "zhc/Lexer.h"
#include "zhc/Keywords.h"

using namespace zhc;

//===--- TokenKind Tests ------------------------------------------------===//

TEST(TokenKindTest, PunctuatorSpelling) {
  EXPECT_EQ(getPunctuatorSpelling(TokenKind::plus), "+");
  EXPECT_EQ(getPunctuatorSpelling(TokenKind::minus), "-");
  EXPECT_EQ(getPunctuatorSpelling(TokenKind::star), "*");
  EXPECT_EQ(getPunctuatorSpelling(TokenKind::eq), "==");
  EXPECT_EQ(getPunctuatorSpelling(TokenKind::arrow), "->");
  EXPECT_EQ(getPunctuatorSpelling(TokenKind::dot_dot), "..");
}

TEST(TokenKindTest, IsKeyword) {
  EXPECT_TRUE(isKeyword(TokenKind::KW_if));
  EXPECT_TRUE(isKeyword(TokenKind::KW_func));
  EXPECT_TRUE(isKeyword(TokenKind::KW_return));
  EXPECT_FALSE(isKeyword(TokenKind::IDENTIFIER));
  EXPECT_FALSE(isKeyword(TokenKind::plus));
}

TEST(TokenKindTest, IsPunctuator) {
  EXPECT_TRUE(isPunctuator(TokenKind::plus));
  EXPECT_TRUE(isPunctuator(TokenKind::lparen));
  EXPECT_TRUE(isPunctuator(TokenKind::eq));
  EXPECT_FALSE(isPunctuator(TokenKind::IDENTIFIER));
  EXPECT_FALSE(isPunctuator(TokenKind::KW_if));
}

TEST(TokenKindTest, IsLiteral) {
  EXPECT_TRUE(isLiteral(TokenKind::INTEGER_LITERAL));
  EXPECT_TRUE(isLiteral(TokenKind::FLOAT_LITERAL));
  EXPECT_TRUE(isLiteral(TokenKind::STRING_LITERAL));
  EXPECT_FALSE(isLiteral(TokenKind::IDENTIFIER));
  EXPECT_FALSE(isLiteral(TokenKind::KW_if));
}

//===--- Lexer Tests ----------------------------------------------------===//

class LexerTest : public ::testing::Test {
protected:
  // Hold source string ownership so Token::Spelling (StringRef) remains valid
  std::string HeldSource;
  
  Token lexSingle(const std::string& source) {
    HeldSource = source;
    Lexer lexer(HeldSource);
    return lexer.lexNext();
  }
  
  std::vector<Token> lexAll(const std::string& source) {
    HeldSource = source;
    Lexer lexer(HeldSource);
    std::vector<Token> tokens;
    while (true) {
      Token tok = lexer.lexNext();
      tokens.push_back(tok);
      if (tok.isEOF()) break;
    }
    return tokens;
  }
};

// Basic token types
TEST_F(LexerTest, IntegerLiteral) {
  Token tok = lexSingle("42");
  EXPECT_EQ(tok.Kind, TokenKind::INTEGER_LITERAL);
  EXPECT_EQ(tok.Spelling, "42");
  EXPECT_EQ(tok.IntegerValue, 42);
}

TEST_F(LexerTest, IntegerLiteralZero) {
  Token tok = lexSingle("0");
  EXPECT_EQ(tok.Kind, TokenKind::INTEGER_LITERAL);
  EXPECT_EQ(tok.IntegerValue, 0);
}

TEST_F(LexerTest, HexLiteral) {
  Token tok = lexSingle("0xFF");
  EXPECT_EQ(tok.Kind, TokenKind::INTEGER_LITERAL);
  EXPECT_EQ(tok.IntegerValue, 255);
}

TEST_F(LexerTest, BinaryLiteral) {
  Token tok = lexSingle("0b1010");
  EXPECT_EQ(tok.Kind, TokenKind::INTEGER_LITERAL);
  EXPECT_EQ(tok.IntegerValue, 10);
}

TEST_F(LexerTest, FloatLiteral) {
  Token tok = lexSingle("3.14");
  EXPECT_EQ(tok.Kind, TokenKind::FLOAT_LITERAL);
  EXPECT_EQ(tok.Spelling, "3.14");
  EXPECT_DOUBLE_EQ(tok.FloatValue, 3.14);
}

TEST_F(LexerTest, FloatScientific) {
  Token tok = lexSingle("1.0e-10");
  EXPECT_EQ(tok.Kind, TokenKind::FLOAT_LITERAL);
  EXPECT_DOUBLE_EQ(tok.FloatValue, 1.0e-10);
}

TEST_F(LexerTest, StringLiteral) {
  Token tok = lexSingle("\"hello\"");
  EXPECT_EQ(tok.Kind, TokenKind::STRING_LITERAL);
  EXPECT_EQ(tok.StringValue, "hello");
}

TEST_F(LexerTest, StringLiteralEscape) {
  Token tok = lexSingle("\"hello\\nworld\"");
  EXPECT_EQ(tok.Kind, TokenKind::STRING_LITERAL);
  EXPECT_EQ(tok.StringValue, "hello\nworld");
}

TEST_F(LexerTest, StringLiteralChinese) {
  Token tok = lexSingle("\"你好世界\"");
  EXPECT_EQ(tok.Kind, TokenKind::STRING_LITERAL);
  EXPECT_EQ(tok.StringValue, "你好世界");
}

TEST_F(LexerTest, BoolLiteralTrue) {
  Token tok = lexSingle("true");
  EXPECT_EQ(tok.Kind, TokenKind::BOOL_LITERAL);
  EXPECT_EQ(tok.IntegerValue, 1);
}

TEST_F(LexerTest, BoolLiteralFalse) {
  Token tok = lexSingle("false");
  EXPECT_EQ(tok.Kind, TokenKind::BOOL_LITERAL);
  EXPECT_EQ(tok.IntegerValue, 0);
}

TEST_F(LexerTest, BoolLiteralChineseTrue) {
  Token tok = lexSingle("真");
  EXPECT_EQ(tok.Kind, TokenKind::BOOL_LITERAL);
  EXPECT_EQ(tok.IntegerValue, 1);
}

TEST_F(LexerTest, BoolLiteralChineseFalse) {
  Token tok = lexSingle("假");
  EXPECT_EQ(tok.Kind, TokenKind::BOOL_LITERAL);
  EXPECT_EQ(tok.IntegerValue, 0);
}

TEST_F(LexerTest, NoneLiteral) {
  Token tok = lexSingle("none");
  EXPECT_EQ(tok.Kind, TokenKind::NONE_LITERAL);
}

TEST_F(LexerTest, NoneLiteralChinese) {
  Token tok = lexSingle("空");
  EXPECT_EQ(tok.Kind, TokenKind::NONE_LITERAL);
}

// Identifiers
TEST_F(LexerTest, Identifier) {
  Token tok = lexSingle("myVar");
  EXPECT_EQ(tok.Kind, TokenKind::IDENTIFIER);
  EXPECT_EQ(tok.Spelling, "myVar");
}

TEST_F(LexerTest, IdentifierUnderscore) {
  Token tok = lexSingle("_private");
  EXPECT_EQ(tok.Kind, TokenKind::IDENTIFIER);
  EXPECT_EQ(tok.Spelling, "_private");
}

TEST_F(LexerTest, IdentifierChinese) {
  Token tok = lexSingle("变量名");
  EXPECT_EQ(tok.Kind, TokenKind::IDENTIFIER);
  EXPECT_EQ(tok.Spelling, "变量名");
}

// Keywords
TEST_F(LexerTest, KeywordIf) {
  Token tok = lexSingle("if");
  EXPECT_EQ(tok.Kind, TokenKind::KW_if);
}

TEST_F(LexerTest, KeywordIfChinese) {
  Token tok = lexSingle("如果");
  EXPECT_EQ(tok.Kind, TokenKind::KW_if);
}

TEST_F(LexerTest, KeywordFunc) {
  Token tok = lexSingle("func");
  EXPECT_EQ(tok.Kind, TokenKind::KW_func);
}

TEST_F(LexerTest, KeywordFuncChinese) {
  Token tok = lexSingle("函数");
  EXPECT_EQ(tok.Kind, TokenKind::KW_func);
}

TEST_F(LexerTest, KeywordReturn) {
  Token tok = lexSingle("return");
  EXPECT_EQ(tok.Kind, TokenKind::KW_return);
}

TEST_F(LexerTest, KeywordReturnChinese) {
  Token tok = lexSingle("返回");
  EXPECT_EQ(tok.Kind, TokenKind::KW_return);
}

// Punctuators
TEST_F(LexerTest, PunctuatorPlus) {
  Token tok = lexSingle("+");
  EXPECT_EQ(tok.Kind, TokenKind::plus);
}

TEST_F(LexerTest, PunctuatorEq) {
  Token tok = lexSingle("==");
  EXPECT_EQ(tok.Kind, TokenKind::eq);
}

TEST_F(LexerTest, PunctuatorArrow) {
  Token tok = lexSingle("->");
  EXPECT_EQ(tok.Kind, TokenKind::arrow);
}

TEST_F(LexerTest, PunctuatorDotDot) {
  Token tok = lexSingle("..");
  EXPECT_EQ(tok.Kind, TokenKind::dot_dot);
}

TEST_F(LexerTest, PunctuatorAssign) {
  Token tok = lexSingle("=");
  EXPECT_EQ(tok.Kind, TokenKind::equal);
}

// Multiple tokens
TEST_F(LexerTest, MultipleTokens) {
  auto tokens = lexAll("func main() { return 42; }");
  
  ASSERT_GE(tokens.size(), 8u);
  EXPECT_EQ(tokens[0].Kind, TokenKind::KW_func);
  EXPECT_EQ(tokens[1].Kind, TokenKind::IDENTIFIER);
  EXPECT_EQ(tokens[2].Kind, TokenKind::lparen);
  EXPECT_EQ(tokens[3].Kind, TokenKind::rparen);
  EXPECT_EQ(tokens[4].Kind, TokenKind::lbrace);
  EXPECT_EQ(tokens[5].Kind, TokenKind::KW_return);
  EXPECT_EQ(tokens[6].Kind, TokenKind::INTEGER_LITERAL);
  EXPECT_EQ(tokens[7].Kind, TokenKind::semi);
}

TEST_F(LexerTest, MultipleTokensChinese) {
  auto tokens = lexAll("函数 主() { 返回 42; }");
  
  ASSERT_GE(tokens.size(), 8u);
  EXPECT_EQ(tokens[0].Kind, TokenKind::KW_func);
  EXPECT_EQ(tokens[1].Kind, TokenKind::IDENTIFIER);  // "主" is not a keyword
  EXPECT_EQ(tokens[2].Kind, TokenKind::lparen);
  EXPECT_EQ(tokens[3].Kind, TokenKind::rparen);
  EXPECT_EQ(tokens[4].Kind, TokenKind::lbrace);
  EXPECT_EQ(tokens[5].Kind, TokenKind::KW_return);
  EXPECT_EQ(tokens[6].Kind, TokenKind::INTEGER_LITERAL);
  EXPECT_EQ(tokens[7].Kind, TokenKind::semi);
}

// Whitespace and comments
TEST_F(LexerTest, SkipWhitespace) {
  Token tok = lexSingle("   42");
  EXPECT_EQ(tok.Kind, TokenKind::INTEGER_LITERAL);
  EXPECT_EQ(tok.IntegerValue, 42);
}

TEST_F(LexerTest, CommentLine) {
  auto tokens = lexAll("42 # this is a comment\n43");
  ASSERT_GE(tokens.size(), 3u);
  EXPECT_EQ(tokens[0].IntegerValue, 42);
  EXPECT_EQ(tokens[1].IntegerValue, 43);
}

// EOF
TEST_F(LexerTest, EmptyInput) {
  auto tokens = lexAll("");
  ASSERT_EQ(tokens.size(), 1u);
  EXPECT_EQ(tokens[0].Kind, TokenKind::eof);
}

// Peek
TEST_F(LexerTest, PeekToken) {
  Lexer lexer("func main");
  
  Token peeked = lexer.peekNext();
  EXPECT_EQ(peeked.Kind, TokenKind::KW_func);
  
  Token actual = lexer.lexNext();
  EXPECT_EQ(actual.Kind, TokenKind::KW_func);
  
  Token next = lexer.lexNext();
  EXPECT_EQ(next.Kind, TokenKind::IDENTIFIER);
}

//===--- Keyword Table Tests ---------------------------------------------===//

TEST(KeywordTableTest, LookupEnglishKeyword) {
  const auto& table = getKeywordTable();
  
  auto kind = table.lookup("if");
  ASSERT_TRUE(kind.has_value());
  EXPECT_EQ(*kind, TokenKind::KW_if);
}

TEST(KeywordTableTest, LookupChineseKeyword) {
  const auto& table = getKeywordTable();
  
  auto kind = table.lookup("如果");
  ASSERT_TRUE(kind.has_value());
  EXPECT_EQ(*kind, TokenKind::KW_if);
}

TEST(KeywordTableTest, LookupNonKeyword) {
  const auto& table = getKeywordTable();
  
  auto kind = table.lookup("notakeyword");
  EXPECT_FALSE(kind.has_value());
}

TEST(KeywordTableTest, IsKeyword) {
  const auto& table = getKeywordTable();
  
  EXPECT_TRUE(table.isKeyword("if"));
  EXPECT_TRUE(table.isKeyword("如果"));
  EXPECT_TRUE(table.isKeyword("函数"));
  EXPECT_FALSE(table.isKeyword("myvar"));
}

//===--- UTF-8 Tests ----------------------------------------------------===//

TEST(UTF8Test, CountASCII) {
  EXPECT_EQ(zhc::utf8::countChars("hello"), 5u);
}

TEST(UTF8Test, CountChinese) {
  EXPECT_EQ(zhc::utf8::countChars("你好世界"), 4u);
}

TEST(UTF8Test, CountMixed) {
  EXPECT_EQ(zhc::utf8::countChars("hello你好"), 7u);
}

TEST(UTF8Test, CharPosition) {
  std::string_view str = "你好世界";
  EXPECT_EQ(zhc::utf8::charPosition(str, 0), 0u);
  EXPECT_EQ(zhc::utf8::charPosition(str, 1), 3u);
  EXPECT_EQ(zhc::utf8::charPosition(str, 2), 6u);
}