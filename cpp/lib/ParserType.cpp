//===--- ParserType.cpp - Type Parsing ---------------------------------------===//
//
// This file implements type parsing for the ZhC parser.
//
//===----------------------------------------------------------------------===//

#include "zhc/Parser.h"
#include "zhc/ASTContext.h"

#include "llvm/Support/raw_ostream.h"

namespace zhc {

//===----------------------------------------------------------------------===//
// Types
//===----------------------------------------------------------------------===//

std::unique_ptr<TypeNode> Parser::parseType() {
  // Parse base type first
  auto base = parseBaseType();

  // Pointer type suffix: type *
  while (consumeIf(TokenKind::star)) {
    base = std::make_unique<PointerTypeNode>(std::move(base));
  }

  // Array type suffix: type [size]
  while (consumeIf(TokenKind::lbracket)) {
    std::unique_ptr<ExprNode> size;
    if (CurrentToken.Kind != TokenKind::rbracket) {
      size = parseExpression();
    }
    expect(TokenKind::rbracket);
    base = std::make_unique<ArrayTypeNode>(std::move(base), std::move(size));
  }

  return base;
}

std::unique_ptr<TypeNode> Parser::parseBaseType() {
  if (isTypeKeyword(CurrentToken.Kind)) {
    TypeKind kind = keywordToTypeKind(CurrentToken.Kind);
    advance();
    return std::make_unique<PrimitiveTypeNode>(kind);
  }

  if (CurrentToken.Kind == TokenKind::IDENTIFIER) {
    llvm::StringRef name = CurrentToken.Spelling;
    advance();
    return std::make_unique<StructTypeNode>(name);
  }

  DiagEngine.report(getCurrentLocation(), DiagID::err_expected_type);
  return nullptr;
}

TypeKind Parser::keywordToTypeKind(TokenKind kind) {
  switch (kind) {
    case TokenKind::KW_int:    return TypeKind::Int32;
    case TokenKind::KW_float:  return TypeKind::Float64;
    case TokenKind::KW_char:   return TypeKind::Char;
    case TokenKind::KW_bool:   return TypeKind::Bool;
    case TokenKind::KW_void:   return TypeKind::Void;
    case TokenKind::KW_string: return TypeKind::String;
    default:                   return TypeKind::Void;
  }
}

bool Parser::isTypeKeyword(TokenKind kind) {
  switch (kind) {
    case TokenKind::KW_int:
    case TokenKind::KW_float:
    case TokenKind::KW_char:
    case TokenKind::KW_bool:
    case TokenKind::KW_void:
    case TokenKind::KW_string:
      return true;
    default:
      return false;
  }
}

} // namespace zhc
