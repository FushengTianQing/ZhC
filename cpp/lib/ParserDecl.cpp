//===--- ParserDecl.cpp - Declaration Parsing --------------------------------===//
//
// This file implements declaration parsing for the ZhC parser.
//
//===----------------------------------------------------------------------===//

#include "zhc/Parser.h"
#include "zhc/ASTContext.h"

#include "llvm/Support/raw_ostream.h"

namespace zhc {

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

  DiagEngine.report(getCurrentLocation(), DiagID::err_expected_declaration);
  return nullptr;
}

std::unique_ptr<FuncDecl> Parser::parseFunctionDecl() {
  (void)getCurrentLocation(); // TODO: use loc for AST SourceRange
  expect(TokenKind::KW_func);

  // Function name - save before consuming
  if (CurrentToken.Kind != TokenKind::IDENTIFIER) {
    DiagEngine.report(getCurrentLocation(), DiagID::err_expected_identifier);
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
    DiagEngine.report(getCurrentLocation(), DiagID::err_expected_identifier);
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
    DiagEngine.report(getCurrentLocation(), DiagID::err_expected_parameter_name);
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
    DiagEngine.report(getCurrentLocation(), DiagID::err_expected_identifier);
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
    DiagEngine.report(getCurrentLocation(), DiagID::err_expected_identifier);
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
      DiagEngine.report(getCurrentLocation(), DiagID::err_expected_identifier);
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
    DiagEngine.report(getCurrentLocation(), DiagID::err_expected_identifier);
    return nullptr;
  }
  llvm::StringRef name = CurrentToken.Spelling;
  advance();

  expect(TokenKind::lbrace);

  llvm::SmallVector<EnumDecl::EnumConstant, 8> constants;
  while (!consumeIf(TokenKind::rbrace) && !CurrentToken.isEOF()) {
    if (CurrentToken.Kind != TokenKind::IDENTIFIER) {
      DiagEngine.report(getCurrentLocation(), DiagID::err_expected_identifier);
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
    DiagEngine.report(getCurrentLocation(), DiagID::err_expected_identifier);
    return nullptr;
  }
  llvm::StringRef name = CurrentToken.Spelling;
  advance();

  expect(TokenKind::lbrace);

  llvm::SmallVector<UnionDecl::Field, 8> fields;
  while (!consumeIf(TokenKind::rbrace) && !CurrentToken.isEOF()) {
    auto fieldType = parseType();
    if (CurrentToken.Kind != TokenKind::IDENTIFIER) {
      DiagEngine.report(getCurrentLocation(), DiagID::err_expected_identifier);
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
    DiagEngine.report(getCurrentLocation(), DiagID::err_expected_identifier);
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
    DiagEngine.report(getCurrentLocation(), DiagID::err_expected_identifier);
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
    DiagEngine.report(getCurrentLocation(), DiagID::err_expected_identifier);
    return nullptr;
  }
  llvm::StringRef moduleName = CurrentToken.Spelling;
  advance();

  llvm::SmallVector<llvm::StringRef, 4> symbols;
  if (consumeIf(TokenKind::colon)) {
    // Import specific symbols
    do {
      if (CurrentToken.Kind != TokenKind::IDENTIFIER) {
        DiagEngine.report(getCurrentLocation(), DiagID::err_expected_identifier);
        break;
      }
      symbols.push_back(CurrentToken.Spelling);
      advance();
    } while (consumeIf(TokenKind::comma));
  }

  consumeIf(TokenKind::semi);

  return std::make_unique<ImportDecl>(moduleName, std::move(symbols));
}

} // namespace zhc
