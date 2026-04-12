//===--- Parser.h - ZhC Parser Interface ---------------------------------===//
//
// This file defines the recursive descent parser for the ZhC compiler.
// Uses Pratt parsing (precedence climbing) for expressions.
//
//===----------------------------------------------------------------------===//

#ifndef ZHC_PARSER_H
#define ZHC_PARSER_H

#include "zhc/Lexer.h"
#include "zhc/Diagnostics.h"
#include "zhc/AST.h"
#include "zhc/ASTContext.h"

#include <memory>

namespace zhc {

/// Recursive descent parser for ZhC
/// 
/// Parsing strategy:
/// - Expressions: Pratt parser (precedence climbing)
/// - Statements: Recursive descent
/// - Declarations: Recursive descent
/// - Error recovery: Synchronization at statement boundaries
class Parser {
public:
  /// Construct a parser with the given lexer, diagnostics engine, and AST context
  Parser(Lexer& lex, DiagnosticsEngine& diag, ASTContext& ctx);
  
  /// Parse a translation unit (top-level declarations)
  std::unique_ptr<TranslationUnit> parseTranslationUnit();
  
  /// Check if any parse errors occurred
  bool hasErrors() const { return DiagEngine.hasErrors(); }
  
  //===----------------------------------------------------------------------===//
  // Declarations (public for recursive descent and testing)
  //===----------------------------------------------------------------------===//
  
  /// Parse any top-level declaration
  std::unique_ptr<DeclNode> parseDeclaration();
  
  /// Parse function declaration: 'func' name(params) [: type] { body }
  std::unique_ptr<FuncDecl> parseFunctionDecl();
  
  /// Parse variable declaration: 'var' name [: type] [= init]
  std::unique_ptr<VarDecl> parseVarDecl();
  
  /// Parse parameter declaration: name [: type] [= default]
  std::unique_ptr<ParamDecl> parseParamDecl();
  
  /// Parse type-prefixed declaration: type name [= init] or type name(params) { body }
  std::unique_ptr<DeclNode> parseTypePrefixedDecl();
  
  /// Parse struct declaration: 'struct' name { fields }
  std::unique_ptr<StructDecl> parseStructDecl();
  
  /// Parse enum declaration: 'enum' name { constants }
  std::unique_ptr<EnumDecl> parseEnumDecl();
  
  /// Parse union declaration: 'union' name { fields }
  std::unique_ptr<UnionDecl> parseUnionDecl();
  
  /// Parse typedef declaration: 'typedef' type name
  std::unique_ptr<TypedefDecl> parseTypedefDecl();
  
  /// Parse module declaration: 'module' name { exports imports body }
  std::unique_ptr<ModuleDecl> parseModuleDecl();
  
  /// Parse import declaration: 'import' module [: symbols]
  std::unique_ptr<ImportDecl> parseImportDecl();
  
  //===----------------------------------------------------------------------===//
  // Statements (public for recursive descent and testing)
  //===----------------------------------------------------------------------===//
  
  /// Parse any statement
  std::unique_ptr<StmtNode> parseStatement();
  
  /// Parse block statement: { statements }
  std::unique_ptr<BlockStmt> parseBlockStmt();
  
  /// Parse if statement: 'if' (cond) then ['else' else]
  std::unique_ptr<IfStmt> parseIfStmt();
  
  /// Parse while statement: 'while' (cond) body
  std::unique_ptr<WhileStmt> parseWhileStmt();
  
  /// Parse for statement: 'for' (init; cond; incr) body
  std::unique_ptr<ForStmt> parseForStmt();
  
  /// Parse return statement: 'return' [value]
  std::unique_ptr<ReturnStmt> parseReturnStmt();
  
  /// Parse break statement: 'break'
  std::unique_ptr<BreakStmt> parseBreakStmt();
  
  /// Parse continue statement: 'continue'
  std::unique_ptr<ContinueStmt> parseContinueStmt();
  
  /// Parse switch statement: 'switch' (subject) { cases }
  std::unique_ptr<SwitchStmt> parseSwitchStmt();
  
  /// Parse case statement: 'case' value: body
  std::unique_ptr<CaseStmt> parseCaseStmt();
  
  /// Parse default statement: 'default': body
  std::unique_ptr<DefaultStmt> parseDefaultStmt();
  
  /// Parse try statement: 'try' body catch-clauses [finally]
  std::unique_ptr<TryStmt> parseTryStmt();
  
  /// Parse catch clause: 'catch' [(type var)] body
  std::unique_ptr<CatchClause> parseCatchClause();
  
  /// Parse throw statement: 'throw' [exception | "message"]
  std::unique_ptr<ThrowStmt> parseThrowStmt();
  
  /// Parse expression statement: expr;
  std::unique_ptr<ExprStmt> parseExprStmt();
  
  //===----------------------------------------------------------------------===//
  // Expressions (Pratt Parser) (public for testing)
  //===----------------------------------------------------------------------===//
  
  /// Get precedence for an operator token
  static int getPrecedence(TokenKind kind);
  
  /// Parse expression with minimum precedence (Pratt parser)
  std::unique_ptr<ExprNode> parseExpression(int minPrec = 0);
  
  /// Parse unary expression: prefix operators + postfix
  std::unique_ptr<ExprNode> parseUnaryExpr();
  
  /// Parse postfix expression: primary + postfix operators
  std::unique_ptr<ExprNode> parsePostfixExpr();
  
  /// Parse primary expression: literals, identifiers, parenthesized
  std::unique_ptr<ExprNode> parsePrimaryExpr();
  
  /// Parse initializer expression: { elements }
  std::unique_ptr<ExprNode> parseInitializerExpr();
  
  //===----------------------------------------------------------------------===//
  // Types (public for recursive descent and testing)
  //===----------------------------------------------------------------------===//
  
  /// Parse type: primitive | identifier | pointer | array
  std::unique_ptr<TypeNode> parseType();
  
  /// Parse base type (without pointer/array modifiers)
  std::unique_ptr<TypeNode> parseBaseType();
  
  /// Convert type keyword to TypeKind
  static TypeKind keywordToTypeKind(TokenKind kind);
  
  /// Check if token is a type keyword
  static bool isTypeKeyword(TokenKind kind);
  
private:
  Lexer& Lex;
  DiagnosticsEngine& DiagEngine;
  ASTContext& Context;
  
  /// Current token
  Token CurrentToken;
  
  //===----------------------------------------------------------------------===//
  // Token Management (private)
  //===----------------------------------------------------------------------===//
  
  /// Advance to the next token
  void advance();
  
  /// Consume a token of the expected kind, report error if mismatch
  bool expect(TokenKind kind);
  
  /// Consume a token if it matches, otherwise don't advance
  bool consumeIf(TokenKind kind);
  
  /// Get the current source location
  SourceLocation getCurrentLocation() const;
  
  //===----------------------------------------------------------------------===//
  // Error Recovery (private)
  //===----------------------------------------------------------------------===//
  
  /// Synchronize to a known statement boundary after an error
  void synchronize();
};

} // namespace zhc

#endif // ZHC_PARSER_H