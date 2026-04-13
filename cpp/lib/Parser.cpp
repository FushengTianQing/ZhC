//===--- Parser.cpp - ZhC Parser Core ---------------------------------------===//
//
// This file implements the core parser infrastructure for the ZhC compiler.
// Declaration/Statement/Expression/Type parsing is split into separate files:
//   - ParserDecl.cpp: Declaration parsing
//   - ParserStmt.cpp: Statement parsing
//   - ParserExpr.cpp: Expression parsing (Pratt parser)
//   - ParserType.cpp: Type parsing
//
// Uses Pratt parsing (precedence climbing) for expressions.
//
//===----------------------------------------------------------------------===//

#include "zhc/Parser.h"
#include "zhc/ASTContext.h"

#include "llvm/Support/raw_ostream.h"

namespace zhc {

Parser::Parser(Lexer& lex, DiagnosticsEngine& diag, ASTContext& ctx)
    : Lex(lex), DiagEngine(diag), Context(ctx) {
  // Prime the lexer
  advance();
}

//===----------------------------------------------------------------------===//
// Token Management
//===----------------------------------------------------------------------===//

void Parser::advance() {
  CurrentToken = Lex.lexNext();
}

bool Parser::expect(TokenKind kind) {
  if (CurrentToken.Kind != kind) {
    DiagEngine.report(getCurrentLocation(), DiagID::err_expected,
                     {getTokenKindName(kind).str(),
                      getTokenKindName(CurrentToken.Kind).str()});
    return false;
  }
  advance();
  return true;
}

bool Parser::consumeIf(TokenKind kind) {
  if (CurrentToken.Kind == kind) {
    advance();
    return true;
  }
  return false;
}

SourceLocation Parser::getCurrentLocation() const {
  return Lex.getCurrentLocation();
}

//===----------------------------------------------------------------------===//
// Translation Unit
//===----------------------------------------------------------------------===//

std::unique_ptr<TranslationUnit> Parser::parseTranslationUnit() {
  auto unit = std::make_unique<TranslationUnit>();

  while (!CurrentToken.isEOF()) {
    auto decl = parseDeclaration();
    if (decl) {
      unit->Decls.push_back(std::move(decl));
    } else {
      // Error recovery: skip to next declaration
      synchronize();
    }
  }

  return unit;
}

//===----------------------------------------------------------------------===//
// Error Recovery
//===----------------------------------------------------------------------===//

void Parser::synchronize() {
  while (!CurrentToken.isEOF()) {
    switch (CurrentToken.Kind) {
      case TokenKind::semi:
        advance();
        return;
      case TokenKind::KW_func:
      case TokenKind::KW_var:
      case TokenKind::KW_const:
      case TokenKind::KW_struct:
      case TokenKind::KW_enum:
      case TokenKind::KW_typedef:
      case TokenKind::KW_if:
      case TokenKind::KW_while:
      case TokenKind::KW_for:
      case TokenKind::KW_return:
      case TokenKind::rbrace:
        return;
      default:
        advance();
    }
  }
}

} // namespace zhc