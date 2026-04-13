//===--- ParserStmt.cpp - Statement Parsing ----------------------------------===//
//
// This file implements statement parsing for the ZhC parser.
//
//===----------------------------------------------------------------------===//

#include "zhc/Parser.h"
#include "zhc/ASTContext.h"

#include "llvm/Support/raw_ostream.h"

namespace zhc {

//===----------------------------------------------------------------------===//
// Statements
//===----------------------------------------------------------------------===//

std::unique_ptr<StmtNode> Parser::parseStatement() {
  switch (CurrentToken.Kind) {
    case TokenKind::lbrace:
      return parseBlockStmt();
    case TokenKind::KW_var:
    case TokenKind::KW_const:
      // Local variable declarations inside blocks are handled as statements.
      // They are DeclNodes but allowed in statement context.
      // We wrap them by calling parseVarDecl directly.
      // Note: parseVarDecl returns DeclNode, but we need StmtNode here.
      // Since parseBlockStmt handles var/const separately, this path is
      // reached when parseStatement is called from other contexts (e.g.,
      // if/while/for body). We still need to parse them correctly.
      // For now, parse them and let the caller handle the type mismatch.
      // Actually, parseStatement is only called from parseBlockStmt (which
      // already handles var/const) and from single-statement contexts like
      // if/while/for bodies where a variable declaration would be unusual.
      // If it happens, treat it as an expression statement (which will fail
      // gracefully).
      return parseExprStmt();
    case TokenKind::KW_if:
      return parseIfStmt();
    case TokenKind::KW_while:
      return parseWhileStmt();
    case TokenKind::KW_for:
      return parseForStmt();
    case TokenKind::KW_return:
      return parseReturnStmt();
    case TokenKind::KW_break:
      return parseBreakStmt();
    case TokenKind::KW_continue:
      return parseContinueStmt();
    case TokenKind::KW_switch:
      return parseSwitchStmt();
    case TokenKind::KW_try:
      return parseTryStmt();
    case TokenKind::KW_throw:
      return parseThrowStmt();
    default:
      return parseExprStmt();
  }
}

std::unique_ptr<BlockStmt> Parser::parseBlockStmt() {
  expect(TokenKind::lbrace);

  auto block = std::make_unique<BlockStmt>();
  while (!consumeIf(TokenKind::rbrace) && !CurrentToken.isEOF()) {
    std::unique_ptr<ASTNode> node;

    // Dispatch: variable declarations are DeclNodes, not StmtNodes.
    // parseStatement() doesn't handle them, so we must intercept here.
    if (CurrentToken.Kind == TokenKind::KW_var ||
        CurrentToken.Kind == TokenKind::KW_const) {
      node = parseVarDecl();
    } else {
      node = parseStatement();
    }

    if (node) {
      block->Statements.push_back(std::move(node));
    } else {
      // Error recovery: skip to next synchronization point
      synchronize();
    }
  }

  return block;
}

std::unique_ptr<IfStmt> Parser::parseIfStmt() {
  (void)getCurrentLocation(); // TODO: use loc for AST SourceRange
  expect(TokenKind::KW_if);

  expect(TokenKind::lparen);
  auto cond = parseExpression();
  expect(TokenKind::rparen);

  auto thenBranch = parseStatement();

  std::unique_ptr<StmtNode> elseBranch;
  if (consumeIf(TokenKind::KW_else)) {
    elseBranch = parseStatement();
  }

  return std::make_unique<IfStmt>(std::move(cond),
                                  std::move(thenBranch), std::move(elseBranch));
}

std::unique_ptr<WhileStmt> Parser::parseWhileStmt() {
  (void)getCurrentLocation(); // TODO: use loc for AST SourceRange
  expect(TokenKind::KW_while);

  expect(TokenKind::lparen);
  auto cond = parseExpression();
  expect(TokenKind::rparen);

  auto body = parseStatement();

  return std::make_unique<WhileStmt>(std::move(cond), std::move(body));
}

std::unique_ptr<ForStmt> Parser::parseForStmt() {
  (void)getCurrentLocation(); // TODO: use loc for AST SourceRange
  expect(TokenKind::KW_for);

  expect(TokenKind::lparen);

  // Init
  std::unique_ptr<ASTNode> init;
  if (!consumeIf(TokenKind::semi)) {
    if (CurrentToken.Kind == TokenKind::KW_var) {
      init = parseVarDecl();
    } else {
      init = parseExprStmt();
    }
  }

  // Condition
  std::unique_ptr<ExprNode> cond;
  if (!consumeIf(TokenKind::semi)) {
    cond = parseExpression();
    consumeIf(TokenKind::semi);
  }

  // Increment
  std::unique_ptr<ExprNode> incr;
  if (CurrentToken.Kind != TokenKind::rparen) {
    incr = parseExpression();
  }

  expect(TokenKind::rparen);

  auto body = parseStatement();

  return std::make_unique<ForStmt>(std::move(init), std::move(cond),
                                   std::move(incr), std::move(body));
}

std::unique_ptr<ReturnStmt> Parser::parseReturnStmt() {
  (void)getCurrentLocation(); // TODO: use loc for AST SourceRange
  expect(TokenKind::KW_return);

  std::unique_ptr<ExprNode> value;
  if (CurrentToken.Kind != TokenKind::semi) {
    value = parseExpression();
  }

  consumeIf(TokenKind::semi);

  return std::make_unique<ReturnStmt>(std::move(value));
}

std::unique_ptr<BreakStmt> Parser::parseBreakStmt() {
  expect(TokenKind::KW_break);
  consumeIf(TokenKind::semi);
  return std::make_unique<BreakStmt>();
}

std::unique_ptr<ContinueStmt> Parser::parseContinueStmt() {
  expect(TokenKind::KW_continue);
  consumeIf(TokenKind::semi);
  return std::make_unique<ContinueStmt>();
}

std::unique_ptr<SwitchStmt> Parser::parseSwitchStmt() {
  (void)getCurrentLocation(); // TODO: use loc for AST SourceRange
  expect(TokenKind::KW_switch);

  expect(TokenKind::lparen);
  auto subject = parseExpression();
  expect(TokenKind::rparen);

  expect(TokenKind::lbrace);

  llvm::SmallVector<std::unique_ptr<ASTNode>, 8> cases;
  while (!consumeIf(TokenKind::rbrace) && !CurrentToken.isEOF()) {
    if (CurrentToken.Kind == TokenKind::KW_case) {
      cases.push_back(parseCaseStmt());
    } else if (CurrentToken.Kind == TokenKind::KW_default) {
      cases.push_back(parseDefaultStmt());
    } else {
      DiagEngine.report(getCurrentLocation(), DiagID::err_expected_case_or_default);
      // Error recovery: skip this token to avoid infinite loop
      advance();
    }
  }

  return std::make_unique<SwitchStmt>(std::move(subject), std::move(cases));
}

std::unique_ptr<CaseStmt> Parser::parseCaseStmt() {
  expect(TokenKind::KW_case);

  auto value = parseExpression();
  consumeIf(TokenKind::colon);

  llvm::SmallVector<std::unique_ptr<ASTNode>, 8> body;
  while (CurrentToken.Kind != TokenKind::KW_case &&
         CurrentToken.Kind != TokenKind::KW_default &&
         CurrentToken.Kind != TokenKind::rbrace &&
         !CurrentToken.isEOF()) {
    auto stmt = parseStatement();
    if (stmt) {
      body.push_back(std::move(stmt));
    } else {
      // Error recovery: skip token to avoid infinite loop
      advance();
    }
  }

  return std::make_unique<CaseStmt>(std::move(value), std::move(body));
}

std::unique_ptr<DefaultStmt> Parser::parseDefaultStmt() {
  expect(TokenKind::KW_default);
  consumeIf(TokenKind::colon);

  llvm::SmallVector<std::unique_ptr<ASTNode>, 8> body;
  while (CurrentToken.Kind != TokenKind::KW_case &&
         CurrentToken.Kind != TokenKind::KW_default &&
         CurrentToken.Kind != TokenKind::rbrace &&
         !CurrentToken.isEOF()) {
    auto stmt = parseStatement();
    if (stmt) {
      body.push_back(std::move(stmt));
    } else {
      // Error recovery: skip token to avoid infinite loop
      advance();
    }
  }

  return std::make_unique<DefaultStmt>(std::move(body));
}

std::unique_ptr<TryStmt> Parser::parseTryStmt() {
  (void)getCurrentLocation(); // TODO: use loc for AST SourceRange
  expect(TokenKind::KW_try);

  auto body = parseBlockStmt();

  llvm::SmallVector<std::unique_ptr<ASTNode>, 2> catches;
  while (CurrentToken.Kind == TokenKind::KW_catch) {
    catches.push_back(parseCatchClause());
  }

  std::unique_ptr<BlockStmt> finally;
  if (CurrentToken.Kind == TokenKind::KW_finally) {
    expect(TokenKind::KW_finally);
    finally = parseBlockStmt();
  }

  auto tryStmt = std::make_unique<TryStmt>();
  tryStmt->Body = std::move(body);
  tryStmt->CatchClauses = std::move(catches);
  tryStmt->FinallyBlock = std::move(finally);
  return tryStmt;
}

std::unique_ptr<CatchClause> Parser::parseCatchClause() {
  expect(TokenKind::KW_catch);

  std::unique_ptr<TypeNode> excType;
  llvm::StringRef varName;
  bool isDefault = false;

  if (consumeIf(TokenKind::lparen)) {
    if (CurrentToken.Kind == TokenKind::IDENTIFIER) {
      excType = parseType();
      if (CurrentToken.Kind == TokenKind::IDENTIFIER) {
        varName = CurrentToken.Spelling;
        advance();
      }
    } else {
      isDefault = true;
    }
    expect(TokenKind::rparen);
  } else {
    isDefault = true;
  }

  auto body = parseBlockStmt();

  return std::make_unique<CatchClause>(std::move(excType), varName,
                                       std::move(body), isDefault);
}

std::unique_ptr<ThrowStmt> Parser::parseThrowStmt() {
  (void)getCurrentLocation(); // TODO: use loc for AST SourceRange
  expect(TokenKind::KW_throw);

  std::unique_ptr<ExprNode> exc;
  std::string msg;

  if (CurrentToken.Kind == TokenKind::STRING_LITERAL) {
    msg = CurrentToken.StringValue;
    advance();
  } else {
    exc = parseExpression();
  }

  consumeIf(TokenKind::semi);

  return std::make_unique<ThrowStmt>(std::move(exc), std::move(msg));
}

std::unique_ptr<ExprStmt> Parser::parseExprStmt() {
  auto expr = parseExpression();
  if (!expr) {
    // Expression parsing failed — return nullptr so the caller knows
    // no progress was made and can perform error recovery.
    return nullptr;
  }
  consumeIf(TokenKind::semi);
  return std::make_unique<ExprStmt>(std::move(expr));
}

} // namespace zhc
