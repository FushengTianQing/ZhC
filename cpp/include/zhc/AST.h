//===--- AST.h - ZhC AST Node Definitions -------------------------------===//
//
// This file defines the AST node types for the ZhC compiler.
//
//===----------------------------------------------------------------------===//

#ifndef ZHC_AST_H
#define ZHC_AST_H

#include "zhc/Common.h"
#include "llvm/ADT/ArrayRef.h"
#include "llvm/ADT/SmallVector.h"
#include "llvm/ADT/StringRef.h"

namespace zhc {

/// Base class for all AST nodes
class ASTNode {
public:
  virtual ~ASTNode() = default;
  
  /// Get the source range of this node
  SourceRange getRange() const { return Range; }
  
  /// Get the kind name for debugging
  virtual const char* getKindName() const = 0;
  
protected:
  SourceRange Range;
};

/// Expression AST nodes
class ExprNode : public ASTNode {};
class IntegerLiteralExpr : public ExprNode {
public:
  uint64_t Value;
  const char* getKindName() const override { return "IntegerLiteralExpr"; }
};
class FloatLiteralExpr : public ExprNode {
public:
  double Value;
  const char* getKindName() const override { return "FloatLiteralExpr"; }
};
class StringLiteralExpr : public ExprNode {
public:
  std::string Value;
  const char* getKindName() const override { return "StringLiteralExpr"; }
};
class IdentifierExpr : public ExprNode {
public:
  llvm::StringRef Name;
  const char* getKindName() const override { return "IdentifierExpr"; }
};

/// Binary expression (for operators)
class BinaryOperatorExpr : public ExprNode {
public:
  TokenKind Op;  // Operator token
  std::unique_ptr<ExprNode> LHS;
  std::unique_ptr<ExprNode> RHS;
  const char* getKindName() const override { return "BinaryOperatorExpr"; }
};

/// Statement AST nodes
class StmtNode : public ASTNode {};
class ReturnStmt : public StmtNode {
public:
  std::unique_ptr<ExprNode> Value;
  const char* getKindName() const override { return "ReturnStmt"; }
};
class ExprStmt : public StmtNode {
public:
  std::unique_ptr<ExprNode> Expr;
  const char* getKindName() const override { return "ExprStmt"; }
};

/// Declaration AST nodes
class DeclNode : public ASTNode {};
class VarDecl : public DeclNode {
public:
  llvm::StringRef Name;
  std::unique_ptr<ExprNode> Init;
  const char* getKindName() const override { return "VarDecl"; }
};
class FuncDecl : public DeclNode {
public:
  llvm::StringRef Name;
  llvm::SmallVector<llvm::StringRef, 8> Params;  // Parameter names
  llvm::SmallVector<std::unique_ptr<DeclNode>, 8> Body;  // Statements
  const char* getKindName() const override { return "FuncDecl"; }
};

/// Translation Unit (top-level)
class TranslationUnit : public ASTNode {
public:
  llvm::SmallVector<std::unique_ptr<DeclNode>, 16> Decls;
  const char* getKindName() const override { return "TranslationUnit"; }
};

} // namespace zhc

#endif // ZHC_AST_H