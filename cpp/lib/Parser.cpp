//===--- Parser.cpp - ZhC Parser Implementation --------------------------===//
//
// This file implements the recursive descent parser for the ZhC compiler.
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
    DiagEngine.error(getCurrentLocation(),
                     "期望 '" + getTokenKindName(kind).str() + "'，但得到 '" +
                     getTokenKindName(CurrentToken.Kind).str() + "'");
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
// Declarations
//===----------------------------------------------------------------------===//

std::unique_ptr<DeclNode> Parser::parseDeclaration() {
  // Check for keywords
  if (isKeyword(CurrentToken.Kind)) {
    switch (CurrentToken.Kind) {
      case TokenKind::KW_func:
        return parseFunctionDecl();
      case TokenKind::KW_var:
        return parseVarDecl();
      case TokenKind::KW_const:
        return parseVarDecl();
      case TokenKind::KW_struct:
        return parseStructDecl();
      case TokenKind::KW_enum:
        return parseEnumDecl();
      // union not a keyword in current token set; handled as identifier-based decl
      case TokenKind::KW_typedef:
        return parseTypedefDecl();
      case TokenKind::KW_module:
        return parseModuleDecl();
      case TokenKind::KW_import:
        return parseImportDecl();
      default:
        break;
    }
  }

  // Type-prefixed declaration (e.g., "整数型 变量名")
  if (isTypeKeyword(CurrentToken.Kind)) {
    return parseTypePrefixedDecl();
  }

  DiagEngine.error(getCurrentLocation(), "期望声明");
  return nullptr;
}

std::unique_ptr<FuncDecl> Parser::parseFunctionDecl() {
  (void)getCurrentLocation(); // TODO: use loc for AST SourceRange
  expect(TokenKind::KW_func);

  // Function name - save before consuming
  if (CurrentToken.Kind != TokenKind::IDENTIFIER) {
    DiagEngine.error(getCurrentLocation(), "期望标识符");
    return nullptr;
  }
  llvm::StringRef name = CurrentToken.Spelling;
  advance();

  // Parameters
  expect(TokenKind::lparen);
  llvm::SmallVector<std::unique_ptr<ParamDecl>, 8> params;
  if (!consumeIf(TokenKind::rparen)) {
    do {
      auto param = parseParamDecl();
      if (param) params.push_back(std::move(param));
    } while (consumeIf(TokenKind::comma));
    expect(TokenKind::rparen);
  }

  // Return type (optional)
  std::unique_ptr<TypeNode> retType;
  if (consumeIf(TokenKind::colon)) {
    retType = parseType();
  } else {
    retType = std::make_unique<PrimitiveTypeNode>(TypeKind::Void);
  }

  // Body
  std::unique_ptr<BlockStmt> body;
  if (CurrentToken.Kind == TokenKind::lbrace) {
    body = parseBlockStmt();
  }

  return std::make_unique<FuncDecl>(name, std::move(retType),
                                     std::move(params), std::move(body));
}

std::unique_ptr<VarDecl> Parser::parseVarDecl() {
  (void)getCurrentLocation(); // TODO: use loc for AST SourceRange
  bool isConst = CurrentToken.Kind == TokenKind::KW_const;
  if (isConst) advance();
  expect(TokenKind::KW_var);

  // Variable name - save before consuming
  if (CurrentToken.Kind != TokenKind::IDENTIFIER) {
    DiagEngine.error(getCurrentLocation(), "期望标识符");
    return nullptr;
  }
  llvm::StringRef name = CurrentToken.Spelling;
  advance();

  // Type (optional)
  std::unique_ptr<TypeNode> type;
  if (consumeIf(TokenKind::colon)) {
    type = parseType();
  }

  // Initializer
  std::unique_ptr<ExprNode> init;
  if (consumeIf(TokenKind::equal)) {
    init = parseExpression();
  }

  consumeIf(TokenKind::semi);

  return std::make_unique<VarDecl>(name, std::move(type), std::move(init),
                                    isConst);
}

std::unique_ptr<ParamDecl> Parser::parseParamDecl() {
  // Parameter name - save before consuming
  if (CurrentToken.Kind != TokenKind::IDENTIFIER) {
    DiagEngine.error(getCurrentLocation(), "期望参数名");
    return nullptr;
  }
  llvm::StringRef name = CurrentToken.Spelling;
  advance();

  // Type
  std::unique_ptr<TypeNode> type;
  if (consumeIf(TokenKind::colon)) {
    type = parseType();
  }

  // Default value
  std::unique_ptr<ExprNode> def;
  if (consumeIf(TokenKind::equal)) {
    def = parseExpression();
  }

  return std::make_unique<ParamDecl>(name, std::move(type), std::move(def));
}

std::unique_ptr<DeclNode> Parser::parseTypePrefixedDecl() {
  // Parse type first
  auto type = parseType();

  // Then identifier - save before consuming
  if (CurrentToken.Kind != TokenKind::IDENTIFIER) {
    DiagEngine.error(getCurrentLocation(), "期望标识符");
    return nullptr;
  }
  llvm::StringRef name = CurrentToken.Spelling;
  advance();

  // Check if this is a function declaration (has '(')
  if (CurrentToken.Kind == TokenKind::lparen) {
    // Function declaration
    advance();
    llvm::SmallVector<std::unique_ptr<ParamDecl>, 8> params;
    if (!consumeIf(TokenKind::rparen)) {
      do {
        auto param = parseParamDecl();
        if (param) params.push_back(std::move(param));
      } while (consumeIf(TokenKind::comma));
      expect(TokenKind::rparen);
    }

    std::unique_ptr<BlockStmt> body;
    if (CurrentToken.Kind == TokenKind::lbrace) {
      body = parseBlockStmt();
    } else {
      consumeIf(TokenKind::semi);
    }

    return std::make_unique<FuncDecl>(name, std::move(type),
                                       std::move(params), std::move(body));
  }

  // Variable declaration
  std::unique_ptr<ExprNode> init;
  if (consumeIf(TokenKind::equal)) {
    init = parseExpression();
  }
  consumeIf(TokenKind::semi);

  return std::make_unique<VarDecl>(name, std::move(type), std::move(init));
}

std::unique_ptr<StructDecl> Parser::parseStructDecl() {
  (void)getCurrentLocation(); // TODO: use loc for AST SourceRange
  expect(TokenKind::KW_struct);

  // Struct name
  if (CurrentToken.Kind != TokenKind::IDENTIFIER) {
    DiagEngine.error(getCurrentLocation(), "期望标识符");
    return nullptr;
  }
  llvm::StringRef name = CurrentToken.Spelling;
  advance();

  expect(TokenKind::lbrace);

  llvm::SmallVector<StructDecl::Field, 8> fields;
  while (!consumeIf(TokenKind::rbrace) && !CurrentToken.isEOF()) {
    // Field type
    auto fieldType = parseType();

    // Field name
    if (CurrentToken.Kind != TokenKind::IDENTIFIER) {
      DiagEngine.error(getCurrentLocation(), "期望标识符");
      break;
    }
    llvm::StringRef fieldName = CurrentToken.Spelling;
    advance();

    // Default value
    std::unique_ptr<ExprNode> def;
    if (consumeIf(TokenKind::equal)) {
      def = parseExpression();
    }

    consumeIf(TokenKind::comma);
    consumeIf(TokenKind::semi);

    fields.push_back({fieldName, std::move(fieldType), std::move(def)});
  }

  return std::make_unique<StructDecl>(name, std::move(fields));
}

std::unique_ptr<EnumDecl> Parser::parseEnumDecl() {
  (void)getCurrentLocation(); // TODO: use loc for AST SourceRange
  expect(TokenKind::KW_enum);

  // Enum name
  if (CurrentToken.Kind != TokenKind::IDENTIFIER) {
    DiagEngine.error(getCurrentLocation(), "期望标识符");
    return nullptr;
  }
  llvm::StringRef name = CurrentToken.Spelling;
  advance();

  expect(TokenKind::lbrace);

  llvm::SmallVector<EnumDecl::EnumConstant, 8> constants;
  while (!consumeIf(TokenKind::rbrace) && !CurrentToken.isEOF()) {
    if (CurrentToken.Kind != TokenKind::IDENTIFIER) {
      DiagEngine.error(getCurrentLocation(), "期望标识符");
      break;
    }
    llvm::StringRef constName = CurrentToken.Spelling;
    advance();

    std::unique_ptr<ExprNode> value;
    if (consumeIf(TokenKind::equal)) {
      value = parseExpression();
    }

    consumeIf(TokenKind::comma);

    constants.push_back({constName, std::move(value)});
  }

  return std::make_unique<EnumDecl>(name, std::move(constants));
}

std::unique_ptr<UnionDecl> Parser::parseUnionDecl() {
  // Note: 'union' is not a keyword; this is called via parseTypePrefixedDecl
  // or when the identifier 'union' is recognized
  (void)getCurrentLocation(); // TODO: use loc for AST SourceRange

  if (CurrentToken.Kind != TokenKind::IDENTIFIER) {
    DiagEngine.error(getCurrentLocation(), "期望标识符");
    return nullptr;
  }
  llvm::StringRef name = CurrentToken.Spelling;
  advance();

  expect(TokenKind::lbrace);

  llvm::SmallVector<UnionDecl::Field, 8> fields;
  while (!consumeIf(TokenKind::rbrace) && !CurrentToken.isEOF()) {
    auto fieldType = parseType();
    if (CurrentToken.Kind != TokenKind::IDENTIFIER) {
      DiagEngine.error(getCurrentLocation(), "期望标识符");
      break;
    }
    llvm::StringRef fieldName = CurrentToken.Spelling;
    advance();

    consumeIf(TokenKind::semi);

    fields.push_back({fieldName, std::move(fieldType)});
  }

  return std::make_unique<UnionDecl>(name, std::move(fields));
}

std::unique_ptr<TypedefDecl> Parser::parseTypedefDecl() {
  (void)getCurrentLocation(); // TODO: use loc for AST SourceRange
  expect(TokenKind::KW_typedef);

  auto underlyingType = parseType();

  if (CurrentToken.Kind != TokenKind::IDENTIFIER) {
    DiagEngine.error(getCurrentLocation(), "期望标识符");
    return nullptr;
  }
  llvm::StringRef name = CurrentToken.Spelling;
  advance();

  consumeIf(TokenKind::semi);

  return std::make_unique<TypedefDecl>(name, std::move(underlyingType));
}

std::unique_ptr<ModuleDecl> Parser::parseModuleDecl() {
  (void)getCurrentLocation(); // TODO: use loc for AST SourceRange
  expect(TokenKind::KW_module);

  if (CurrentToken.Kind != TokenKind::IDENTIFIER) {
    DiagEngine.error(getCurrentLocation(), "期望标识符");
    return nullptr;
  }
  llvm::StringRef name = CurrentToken.Spelling;
  advance();

  // TODO: parse exports, imports, body
  llvm::SmallVector<llvm::StringRef, 8> exports;
  llvm::SmallVector<llvm::StringRef, 8> imports;
  llvm::SmallVector<std::unique_ptr<ASTNode>, 8> body;
  return std::make_unique<ModuleDecl>(name, std::move(exports), 
                                       std::move(imports), std::move(body));
}

std::unique_ptr<ImportDecl> Parser::parseImportDecl() {
  (void)getCurrentLocation(); // TODO: use loc for AST SourceRange
  expect(TokenKind::KW_import);

  if (CurrentToken.Kind != TokenKind::IDENTIFIER) {
    DiagEngine.error(getCurrentLocation(), "期望标识符");
    return nullptr;
  }
  llvm::StringRef moduleName = CurrentToken.Spelling;
  advance();

  llvm::SmallVector<llvm::StringRef, 4> symbols;
  if (consumeIf(TokenKind::colon)) {
    // Import specific symbols
    do {
      if (CurrentToken.Kind != TokenKind::IDENTIFIER) {
        DiagEngine.error(getCurrentLocation(), "期望标识符");
        break;
      }
      symbols.push_back(CurrentToken.Spelling);
      advance();
    } while (consumeIf(TokenKind::comma));
  }

  consumeIf(TokenKind::semi);

  return std::make_unique<ImportDecl>(moduleName, std::move(symbols));
}

//===----------------------------------------------------------------------===//
// Statements
//===----------------------------------------------------------------------===//

std::unique_ptr<StmtNode> Parser::parseStatement() {
  switch (CurrentToken.Kind) {
    case TokenKind::lbrace:
      return parseBlockStmt();
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
    auto stmt = parseStatement();
    if (stmt) {
      block->Statements.push_back(std::move(stmt));
    } else {
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
      DiagEngine.error(getCurrentLocation(), "期望 'case' 或 'default'");
      synchronize();
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
         CurrentToken.Kind != TokenKind::rbrace) {
    auto stmt = parseStatement();
    if (stmt) body.push_back(std::move(stmt));
  }

  return std::make_unique<CaseStmt>(std::move(value), std::move(body));
}

std::unique_ptr<DefaultStmt> Parser::parseDefaultStmt() {
  expect(TokenKind::KW_default);
  consumeIf(TokenKind::colon);

  llvm::SmallVector<std::unique_ptr<ASTNode>, 8> body;
  while (CurrentToken.Kind != TokenKind::KW_case &&
         CurrentToken.Kind != TokenKind::KW_default &&
         CurrentToken.Kind != TokenKind::rbrace) {
    auto stmt = parseStatement();
    if (stmt) body.push_back(std::move(stmt));
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
  consumeIf(TokenKind::semi);
  return std::make_unique<ExprStmt>(std::move(expr));
}

//===----------------------------------------------------------------------===//
// Expressions (Pratt Parser)
//===----------------------------------------------------------------------===//

int Parser::getPrecedence(TokenKind kind) {
  switch (kind) {
    case TokenKind::equal:       return 2;   // Assignment
    case TokenKind::pluseq:
    case TokenKind::minuseq:
    case TokenKind::stareq:
    case TokenKind::slasheq:     return 2;
    case TokenKind::logical_or:  return 3;
    case TokenKind::logical_and: return 4;
    case TokenKind::eq:
    case TokenKind::neq:         return 5;
    case TokenKind::lt:
    case TokenKind::gt:
    case TokenKind::le:
    case TokenKind::ge:          return 6;
    case TokenKind::plus:
    case TokenKind::minus:       return 7;
    case TokenKind::star:
    case TokenKind::slash:
    case TokenKind::percent:     return 8;
    case TokenKind::amp:
    case TokenKind::pipe:
    case TokenKind::caret:       return 8;
    case TokenKind::shl:
    case TokenKind::shr:         return 9;
    default:                     return -1;
  }
}

std::unique_ptr<ExprNode> Parser::parseExpression(int minPrec) {
  auto left = parseUnaryExpr();

  while (true) {
    int prec = getPrecedence(CurrentToken.Kind);
    if (prec < minPrec) break;

    TokenKind op = CurrentToken.Kind;
    advance();

    // Handle assignment specially (right-associative)
    int nextPrec = prec;
    if (op == TokenKind::equal || op == TokenKind::pluseq ||
        op == TokenKind::minuseq || op == TokenKind::stareq ||
        op == TokenKind::slasheq) {
      nextPrec = prec;  // Right-associative
    } else {
      nextPrec = prec + 1;  // Left-associative
    }

    auto right = parseExpression(nextPrec);

    if (op == TokenKind::equal || op == TokenKind::pluseq ||
        op == TokenKind::minuseq || op == TokenKind::stareq ||
        op == TokenKind::slasheq) {
      left = std::make_unique<AssignExpr>(op, std::move(left), std::move(right));
    } else {
      left = std::make_unique<BinaryOperatorExpr>(op, std::move(left), std::move(right));
    }
  }

  return left;
}

std::unique_ptr<ExprNode> Parser::parseUnaryExpr() {
  // Prefix operators
  switch (CurrentToken.Kind) {
    case TokenKind::minus:
    case TokenKind::logical_not:
    case TokenKind::tilde:
    case TokenKind::plus: {
      TokenKind op = CurrentToken.Kind;
      advance();
      auto operand = parseUnaryExpr();
      return std::make_unique<UnaryExpr>(op, std::move(operand), true);
    }
    default:
      break;
  }

  return parsePostfixExpr();
}

std::unique_ptr<ExprNode> Parser::parsePostfixExpr() {
  auto expr = parsePrimaryExpr();

  while (true) {
    switch (CurrentToken.Kind) {
      case TokenKind::lparen: {
        // Function call
        advance();
        llvm::SmallVector<std::unique_ptr<ExprNode>, 4> args;
        if (!consumeIf(TokenKind::rparen)) {
          do {
            args.push_back(parseExpression());
          } while (consumeIf(TokenKind::comma));
          expect(TokenKind::rparen);
        }
        expr = std::make_unique<CallExpr>(std::move(expr), std::move(args));
        break;
      }
      case TokenKind::dot: {
        advance();
        if (CurrentToken.Kind != TokenKind::IDENTIFIER) {
          DiagEngine.error(getCurrentLocation(), "期望标识符");
          break;
        }
        llvm::StringRef member = CurrentToken.Spelling;
        advance();
        expr = std::make_unique<MemberExpr>(std::move(expr), member, false);
        break;
      }
      case TokenKind::arrow: {
        advance();
        if (CurrentToken.Kind != TokenKind::IDENTIFIER) {
          DiagEngine.error(getCurrentLocation(), "期望标识符");
          break;
        }
        llvm::StringRef member = CurrentToken.Spelling;
        advance();
        expr = std::make_unique<MemberExpr>(std::move(expr), member, true);
        break;
      }
      case TokenKind::lbracket: {
        advance();
        auto index = parseExpression();
        expect(TokenKind::rbracket);
        expr = std::make_unique<ArrayExpr>(std::move(expr), std::move(index));
        break;
      }
      default:
        return expr;
    }
  }
}

std::unique_ptr<ExprNode> Parser::parsePrimaryExpr() {
  switch (CurrentToken.Kind) {
    case TokenKind::INTEGER_LITERAL: {
      uint64_t val = CurrentToken.IntegerValue;
      auto lit = std::make_unique<IntegerLiteralExpr>(val);
      advance();
      return lit;
    }
    case TokenKind::FLOAT_LITERAL: {
      double val = CurrentToken.FloatValue;
      auto lit = std::make_unique<FloatLiteralExpr>(val);
      advance();
      return lit;
    }
    case TokenKind::STRING_LITERAL: {
      auto lit = std::make_unique<StringLiteralExpr>(CurrentToken.StringValue);
      advance();
      return lit;
    }
    case TokenKind::CHAR_LITERAL: {
      // TODO: parse actual Unicode code point from spelling
      uint32_t val = 0;
      auto lit = std::make_unique<CharLiteralExpr>(val);
      advance();
      return lit;
    }
    case TokenKind::BOOL_LITERAL: {
      bool val = CurrentToken.Spelling == "真";
      auto lit = std::make_unique<BoolLiteralExpr>(val);
      advance();
      return lit;
    }
    case TokenKind::NONE_LITERAL: {
      advance();
      return std::make_unique<NullLiteralExpr>();
    }
    case TokenKind::IDENTIFIER: {
      auto expr = std::make_unique<IdentifierExpr>(CurrentToken.Spelling);
      advance();
      return expr;
    }
    case TokenKind::lparen: {
      advance();
      auto expr = parseExpression();
      expect(TokenKind::rparen);
      return expr;
    }
    case TokenKind::lbrace: {
      // Array or struct initializer
      return parseInitializerExpr();
    }
    default:
      DiagEngine.error(getCurrentLocation(), "期望表达式");
      return nullptr;
  }
}

std::unique_ptr<ExprNode> Parser::parseInitializerExpr() {
  expect(TokenKind::lbrace);

  llvm::SmallVector<std::unique_ptr<ExprNode>, 8> elements;
  while (!consumeIf(TokenKind::rbrace) && !CurrentToken.isEOF()) {
    elements.push_back(parseExpression());
    consumeIf(TokenKind::comma);
  }

  return std::make_unique<ArrayInitExpr>(std::move(elements));
}

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

  DiagEngine.error(getCurrentLocation(), "期望类型");
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