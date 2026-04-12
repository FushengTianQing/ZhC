//===--- Lexer.h - ZhC Lexer Interface ----------------------------------===//
//
// This file defines the Lexer interface and Token structure for the ZhC compiler.
//
//===----------------------------------------------------------------------===//

#ifndef ZHC_LEXER_H
#define ZHC_LEXER_H

#include "zhc/Common.h"
#include "llvm/ADT/StringRef.h"
#include "llvm/Support/SMLoc.h"

namespace zhc {

/// Token kind enumeration (generated from TokenKinds.def)
enum class TokenKind {
#define TOKEN(X) X,
#define PUNCTUATOR(X, Y) X,
#define KEYWORD(X) KW_##X,
#include "TokenKinds.def"
  NUM_TOKENS  // Total number of token kinds
};

/// Get the spelling for a punctuator token
llvm::StringRef getPunctuatorSpelling(TokenKind K);

/// Get the name of a token kind (for debugging)
llvm::StringRef getTokenKindName(TokenKind K);

/// Check if a token is a keyword
bool isKeyword(TokenKind K);

/// Check if a token is a punctuator
bool isPunctuator(TokenKind K);

/// Check if a token is a literal
bool isLiteral(TokenKind K);

/// Token structure representing a lexical unit
struct Token {
  TokenKind Kind = TokenKind::unknown;
  llvm::SMLoc Location;           // Source location (for LLVM diagnostics)
  llvm::StringRef Spelling;       // Original text in source
  SourceRange Range;              // Full source range
  
  // Literal values (parsed from spelling)
  uint64_t IntegerValue = 0;
  double FloatValue = 0.0;
  std::string StringValue;
  
  Token() = default;
  
  bool is(TokenKind K) const { return Kind == K; }
  bool isNot(TokenKind K) const { return Kind != K; }
  bool isOneOf(TokenKind K1, TokenKind K2) const {
    return is(K1) || is(K2);
  }
  template<typename... Ts>
  bool isOneOf(TokenKind K1, TokenKind K2, Ts... Ks) const {
    return is(K1) || isOneOf(K2, Ks...);
  }
  
  bool isValid() const { return Kind != TokenKind::unknown; }
  bool isEOF() const { return Kind == TokenKind::eof; }
};

/// Lexer class - tokenizes ZhC source code
class Lexer {
public:
  /// Construct a lexer for the given source buffer
  Lexer(llvm::StringRef source, uint32_t fileID = 0);
  
  /// Lex the next token from the source
  Token lexNext();
  
  /// Peek at the next token without consuming it
  Token peekNext();
  
  /// Get the current source location
  SourceLocation getCurrentLocation() const;
  
  /// Check if we've reached the end of source
  bool isEOF() const;
  
private:
  llvm::StringRef Source;
  const char* Cursor = nullptr;
  uint32_t FileID = 0;
  uint32_t Line = 1;
  uint32_t Column = 1;
  
  // Cached peek token
  bool HasPeekToken = false;
  Token PeekToken;
  
  /// Skip whitespace and comments
  void skipWhitespace();
  
  /// Lex a number literal (integer or float)
  Token lexNumber();
  
  /// Lex a string literal
  Token lexString();
  
  /// Lex a character literal
  Token lexChar();
  
  /// Lex an identifier or keyword
  Token lexIdentifier();
  
  /// Lex a punctuator
  Token lexPunctuator();
  
  /// Create a token at the current location
  Token makeToken(TokenKind K, llvm::StringRef spelling);
  
  /// Advance the cursor by n bytes, updating line/column
  void advance(size_t n);
};

} // namespace zhc

#endif // ZHC_LEXER_H