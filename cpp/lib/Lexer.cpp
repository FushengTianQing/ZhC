//===--- Lexer.cpp - ZhC Lexer Implementation ---------------------------===//
//
// This file implements the Lexer class for tokenizing ZhC source code.
//
//===----------------------------------------------------------------------===//

#include "zhc/Lexer.h"
#include "zhc/Keywords.h"

#include "llvm/ADT/StringRef.h"

namespace zhc {

//===--- TokenKind Utilities ---------------------------------------------===//

llvm::StringRef getPunctuatorSpelling(TokenKind K) {
  switch (K) {
#define PUNCTUATOR(X, Y) case TokenKind::X: return Y;
#include "TokenKinds.def"
  default:
    return "";
  }
}

llvm::StringRef getTokenKindName(TokenKind K) {
  switch (K) {
#define TOKEN(X) case TokenKind::X: return #X;
#define PUNCTUATOR(X, Y) case TokenKind::X: return #X;
#define KEYWORD(X) case TokenKind::KW_##X: return "KW_" #X;
#include "TokenKinds.def"
  default:
    return "UNKNOWN";
  }
}

bool isKeyword(TokenKind K) {
  switch (K) {
#define KEYWORD(X) case TokenKind::KW_##X: return true;
#include "TokenKinds.def"
  default:
    return false;
  }
}

bool isPunctuator(TokenKind K) {
  switch (K) {
#define PUNCTUATOR(X, Y) case TokenKind::X: return true;
#include "TokenKinds.def"
  default:
    return false;
  }
}

bool isLiteral(TokenKind K) {
  return K == TokenKind::INTEGER_LITERAL ||
         K == TokenKind::FLOAT_LITERAL ||
         K == TokenKind::STRING_LITERAL ||
         K == TokenKind::CHAR_LITERAL ||
         K == TokenKind::BOOL_LITERAL ||
         K == TokenKind::NONE_LITERAL;
}

//===--- Lexer Implementation --------------------------------------------===//

Lexer::Lexer(llvm::StringRef source, uint32_t fileID)
    : Source(source), Cursor(source.data()), FileID(fileID) {
  Line = 1;
  Column = 1;
}

Token Lexer::lexNext() {
  // Return cached peek token if available
  if (HasPeekToken) {
    HasPeekToken = false;
    return PeekToken;
  }
  
  skipWhitespace();
  
  if (isEOF()) {
    return makeToken(TokenKind::eof, "");
  }
  
  char c = *Cursor;
  
  // Number literal
  if (isdigit(c)) {
    return lexNumber();
  }
  
  // String literal
  if (c == '"') {
    return lexString();
  }
  
  // Character literal
  if (c == '\'') {
    return lexChar();
  }
  
  // Identifier or keyword
  if (isalpha(c) || c == '_' || (c & 0x80)) {  // UTF-8 lead byte
    return lexIdentifier();
  }
  
  // Punctuator
  return lexPunctuator();
}

Token Lexer::peekNext() {
  if (!HasPeekToken) {
    PeekToken = lexNext();
    HasPeekToken = true;
  }
  return PeekToken;
}

SourceLocation Lexer::getCurrentLocation() const {
  return SourceLocation(Line, Column, FileID);
}

bool Lexer::isEOF() const {
  return Cursor >= Source.end();
}

void Lexer::skipWhitespace() {
  while (!isEOF()) {
    char c = *Cursor;
    
    if (c == ' ' || c == '\t') {
      advance(1);
      continue;
    }
    
    if (c == '\n') {
      advance(1);
      continue;
    }
    
    // Comment: # to end of line
    if (c == '#') {
      while (!isEOF() && *Cursor != '\n') {
        advance(1);
      }
      continue;
    }
    
    break;
  }
}

Token Lexer::lexNumber() {
  const char* start = Cursor;
  
  // Hex: 0x...
  if (*Cursor == '0' && Cursor + 1 < Source.end() && 
      (Cursor[1] == 'x' || Cursor[1] == 'X')) {
    advance(2);
    while (!isEOF() && isxdigit(*Cursor)) {
      advance(1);
    }
    Token T = makeToken(TokenKind::INTEGER_LITERAL, 
                        llvm::StringRef(start, Cursor - start));
    // Parse hex value
    T.IntegerValue = std::stoull(T.Spelling.str(), nullptr, 16);
    return T;
  }
  
  // Binary: 0b...
  if (*Cursor == '0' && Cursor + 1 < Source.end() && 
      (Cursor[1] == 'b' || Cursor[1] == 'B')) {
    advance(2);
    while (!isEOF() && (*Cursor == '0' || *Cursor == '1')) {
      advance(1);
    }
    Token T = makeToken(TokenKind::INTEGER_LITERAL,
                        llvm::StringRef(start, Cursor - start));
    // Parse binary value
    T.IntegerValue = std::stoull(T.Spelling.str().substr(2), nullptr, 2);
    return T;
  }
  
  // Decimal integer or float
  bool isFloat = false;
  while (!isEOF() && isdigit(*Cursor)) {
    advance(1);
  }
  
  // Float: . or e/E
  if (!isEOF() && *Cursor == '.') {
    isFloat = true;
    advance(1);
    while (!isEOF() && isdigit(*Cursor)) {
      advance(1);
    }
  }
  
  if (!isEOF() && (*Cursor == 'e' || *Cursor == 'E')) {
    isFloat = true;
    advance(1);
    if (!isEOF() && (*Cursor == '+' || *Cursor == '-')) {
      advance(1);
    }
    while (!isEOF() && isdigit(*Cursor)) {
      advance(1);
    }
  }
  
  Token T = makeToken(isFloat ? TokenKind::FLOAT_LITERAL : TokenKind::INTEGER_LITERAL,
                      llvm::StringRef(start, Cursor - start));
  
  if (isFloat) {
    T.FloatValue = std::stod(T.Spelling.str());
  } else {
    T.IntegerValue = std::stoull(T.Spelling.str());
  }
  
  return T;
}

Token Lexer::lexString() {
  const char* start = Cursor;
  advance(1);  // Skip opening quote
  
  std::string value;
  while (!isEOF() && *Cursor != '"') {
    if (*Cursor == '\\') {
      advance(1);
      if (!isEOF()) {
        char esc = *Cursor;
        switch (esc) {
          case 'n': value += '\n'; break;
          case 't': value += '\t'; break;
          case 'r': value += '\r'; break;
          case '\\': value += '\\'; break;
          case '"': value += '"'; break;
          default: value += esc; break;
        }
        advance(1);
      }
    } else {
      // UTF-8 character
      uint8_t len = utf8::charLength(static_cast<uint8_t>(*Cursor));
      value.append(Cursor, len);
      advance(len);
    }
  }
  
  if (!isEOF() && *Cursor == '"') {
    advance(1);  // Skip closing quote
  }
  
  Token T = makeToken(TokenKind::STRING_LITERAL,
                      llvm::StringRef(start, Cursor - start));
  T.StringValue = value;
  return T;
}

Token Lexer::lexChar() {
  const char* start = Cursor;
  advance(1);  // Skip opening quote
  
  std::string value;
  if (!isEOF() && *Cursor != '\'') {
    if (*Cursor == '\\') {
      advance(1);
      if (!isEOF()) {
        char esc = *Cursor;
        switch (esc) {
          case 'n': value = '\n'; break;
          case 't': value = '\t'; break;
          case 'r': value = '\r'; break;
          case '\\': value = '\\'; break;
          case '\'': value = '\''; break;
          default: value = esc; break;
        }
        advance(1);
      }
    } else {
      // UTF-8 character
      uint8_t len = utf8::charLength(static_cast<uint8_t>(*Cursor));
      value.append(Cursor, len);
      advance(len);
    }
  }
  
  if (!isEOF() && *Cursor == '\'') {
    advance(1);  // Skip closing quote
  }
  
  Token T = makeToken(TokenKind::CHAR_LITERAL,
                      llvm::StringRef(start, Cursor - start));
  T.StringValue = value;
  return T;
}

Token Lexer::lexIdentifier() {
  const char* start = Cursor;
  
  // Handle UTF-8 identifiers (Chinese keywords)
  while (!isEOF()) {
    char c = *Cursor;
    if (isalnum(c) || c == '_') {
      advance(1);
    } else if (c & 0x80) {  // UTF-8 lead byte
      uint8_t len = utf8::charLength(static_cast<uint8_t>(c));
      advance(len);
    } else {
      break;
    }
  }
  
  llvm::StringRef spelling(start, Cursor - start);
  
  // Check if it's a keyword
  auto kw = getKeywordTable().lookup(spelling);
  if (kw) {
    return makeToken(*kw, spelling);
  }
  
  // Check for boolean literals
  if (spelling == "真" || spelling == "true") {
    Token T = makeToken(TokenKind::BOOL_LITERAL, spelling);
    T.IntegerValue = 1;
    return T;
  }
  if (spelling == "假" || spelling == "false") {
    Token T = makeToken(TokenKind::BOOL_LITERAL, spelling);
    T.IntegerValue = 0;
    return T;
  }
  
  // Check for none literal
  if (spelling == "空" || spelling == "none" || spelling == "null") {
    return makeToken(TokenKind::NONE_LITERAL, spelling);
  }
  
  return makeToken(TokenKind::IDENTIFIER, spelling);
}

Token Lexer::lexPunctuator() {
  const char* start = Cursor;
  
  // Try longest match first (3-char punctuators)
  if (Cursor + 2 < Source.end()) {
    llvm::StringRef three(start, 3);
    // Check 3-char punctuators (none currently, but future expansion)
  }
  
  // Try 2-char punctuators
  if (Cursor + 1 < Source.end()) {
    llvm::StringRef two(start, 2);
    
    // Map 2-char punctuators to TokenKind
    static const struct {
      const char* spelling;
      TokenKind kind;
    } twoCharPunctuators[] = {
      {"==", TokenKind::eq},
      {"!=", TokenKind::neq},
      {"<=", TokenKind::le},
      {">=", TokenKind::ge},
      {"&&", TokenKind::logical_and},
      {"||", TokenKind::logical_or},
      {"<<", TokenKind::shl},
      {">>", TokenKind::shr},
      {"+=", TokenKind::pluseq},
      {"-=", TokenKind::minuseq},
      {"*=", TokenKind::stareq},
      {"/=", TokenKind::slasheq},
      {"%=", TokenKind::percenteq},
      {"&=", TokenKind::ampeq},
      {"|=", TokenKind::pipeeq},
      {"^=", TokenKind::careteq},
      {"->", TokenKind::arrow},
      {"::", TokenKind::double_colon},
      {"..", TokenKind::dot_dot},
      {"..=", TokenKind::dot_dot_eq},  // Actually 3-char, handled separately
      {"<<=", TokenKind::shleq},       // Actually 3-char
      {">>=", TokenKind::shreq},       // Actually 3-char
    };
    
    for (const auto& p : twoCharPunctuators) {
      if (two == p.spelling) {
        advance(2);
        return makeToken(p.kind, two);
      }
    }
  }
  
  // Single-char punctuator
  char c = *Cursor;
  advance(1);
  
  static const struct {
    char spelling;
    TokenKind kind;
  } singleCharPunctuators[] = {
    {'+', TokenKind::plus},
    {'-', TokenKind::minus},
    {'*', TokenKind::star},
    {'/', TokenKind::slash},
    {'%', TokenKind::percent},
    {'&', TokenKind::amp},
    {'|', TokenKind::pipe},
    {'^', TokenKind::caret},
    {'~', TokenKind::tilde},
    {'!', TokenKind::logical_not},
    {'<', TokenKind::lt},
    {'>', TokenKind::gt},
    {'=', TokenKind::equal},
    {'?', TokenKind::question},
    {':', TokenKind::colon},
    {'.', TokenKind::dot},
    {'(', TokenKind::lparen},
    {')', TokenKind::rparen},
    {'{', TokenKind::lbrace},
    {'}', TokenKind::rbrace},
    {'[', TokenKind::lbracket},
    {']', TokenKind::rbracket},
    {',', TokenKind::comma},
    {';', TokenKind::semi},
    {'@', TokenKind::at},
    {'$', TokenKind::dollar},
    {'`', TokenKind::backquote},
  };
  
  for (const auto& p : singleCharPunctuators) {
    if (c == p.spelling) {
      return makeToken(p.kind, llvm::StringRef(start, 1));
    }
  }
  
  // Unknown character
  return makeToken(TokenKind::unknown, llvm::StringRef(start, 1));
}

Token Lexer::makeToken(TokenKind K, llvm::StringRef spelling) {
  Token T;
  T.Kind = K;
  T.Location = llvm::SMLoc::getFromPointer(spelling.data());
  T.Spelling = spelling;
  T.Range.Start = SourceLocation(Line, Column, FileID);
  T.Range.End = SourceLocation(Line, Column + static_cast<uint32_t>(spelling.size()), FileID);
  return T;
}

void Lexer::advance(size_t n) {
  for (size_t i = 0; i < n && !isEOF(); ++i) {
    if (*Cursor == '\n') {
      Line++;
      Column = 1;
    } else {
      Column++;
    }
    Cursor++;
  }
}

} // namespace zhc