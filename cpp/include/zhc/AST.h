//===--- AST.h - ZhC AST Node Definitions -------------------------------===//
//
// This file defines all AST node types for the ZhC compiler.
// Aligned with the Python v6.0 implementation (80 node types).
//
//===----------------------------------------------------------------------===//

#ifndef ZHC_AST_H
#define ZHC_AST_H

#include "zhc/Common.h"
#include "zhc/Lexer.h"
#include "zhc/Types.h"

#include "llvm/ADT/ArrayRef.h"
#include "llvm/ADT/SmallVector.h"
#include "llvm/ADT/StringRef.h"

#include <memory>
#include <vector>

namespace zhc {

// Forward declarations for visitor
class ASTVisitor;

//===----------------------------------------------------------------------===//
// AST Node Kind (matches Python ASTNodeType 1:1)
//===----------------------------------------------------------------------===//

enum class ASTNodeKind : uint8_t {
#define NODE(KIND) KIND,
  // Program structure
  NODE(PROGRAM)
  NODE(MODULE_DECL)
  NODE(IMPORT_DECL)

  // Declarations
  NODE(FUNCTION_DECL)
  NODE(STRUCT_DECL)
  NODE(VARIABLE_DECL)
  NODE(PARAM_DECL)
  NODE(ENUM_DECL)
  NODE(UNION_DECL)
  NODE(TYPEDEF_DECL)
  NODE(EXTERNAL_BLOCK)
  NODE(EXTERNAL_FUNCTION_DECL)

  // Statements
  NODE(BLOCK_STMT)
  NODE(IF_STMT)
  NODE(WHILE_STMT)
  NODE(FOR_STMT)
  NODE(DO_WHILE_STMT)
  NODE(BREAK_STMT)
  NODE(CONTINUE_STMT)
  NODE(RETURN_STMT)
  NODE(SWITCH_STMT)
  NODE(CASE_STMT)
  NODE(DEFAULT_STMT)
  NODE(EXPR_STMT)
  NODE(GOTO_STMT)
  NODE(LABEL_STMT)
  NODE(TRY_STMT)
  NODE(CATCH_CLAUSE)
  NODE(FINALLY_CLAUSE)
  NODE(THROW_STMT)

  // Expressions
  NODE(BINARY_EXPR)
  NODE(UNARY_EXPR)
  NODE(ASSIGN_EXPR)
  NODE(CALL_EXPR)
  NODE(MEMBER_EXPR)
  NODE(ARRAY_EXPR)
  NODE(IDENTIFIER_EXPR)
  NODE(INT_LITERAL)
  NODE(FLOAT_LITERAL)
  NODE(STRING_LITERAL)
  NODE(CHAR_LITERAL)
  NODE(BOOL_LITERAL)
  NODE(NULL_LITERAL)
  NODE(ARRAY_INIT)
  NODE(STRUCT_INIT)
  NODE(TERNARY_EXPR)
  NODE(SIZEOF_EXPR)
  NODE(CAST_EXPR)
  NODE(AS_EXPR)
  NODE(IS_EXPR)
  NODE(LAMBDA_EXPR)

  // Coroutine / async
  NODE(COROUTINE_DEF)
  NODE(AWAIT_EXPR)
  NODE(CHANNEL_EXPR)
  NODE(SPAWN_EXPR)
  NODE(YIELD_EXPR)

  // Pattern matching
  NODE(MATCH_EXPR)
  NODE(MATCH_CASE)

  // Type nodes
  NODE(PRIMITIVE_TYPE)
  NODE(POINTER_TYPE)
  NODE(ARRAY_TYPE)
  NODE(FUNCTION_TYPE)
  NODE(STRUCT_TYPE)
  NODE(AUTO_TYPE)
  NODE(WIDE_CHAR_TYPE)
  NODE(WIDE_STRING_TYPE)
  NODE(COMPLEX_TYPE)
  NODE(COMPLEX_LITERAL)
  NODE(FIXED_POINT_TYPE)

  // Wide char/string literals
  NODE(WIDE_CHAR_LITERAL)
  NODE(WIDE_STRING_LITERAL)

  // Memory management
  NODE(UNIQUE_PTR_DECL)
  NODE(SHARED_PTR_DECL)
  NODE(WEAK_PTR_DECL)
  NODE(SMART_PTR_TYPE)
  NODE(MOVE_EXPR)
  NODE(DESTRUCTOR_DECL)

  // Error recovery
  NODE(ERROR_NODE)
#undef NODE
};

/// Get the name string for an ASTNodeKind
llvm::StringRef getNodeKindName(ASTNodeKind kind);

//===----------------------------------------------------------------------===//
// AST Node Base Class
//===----------------------------------------------------------------------===//

class ASTNode {
public:
  virtual ~ASTNode() = default;

  /// Get the source range of this node
  SourceRange getRange() const { return Range; }
  SourceLocation getLocation() const { return Range.Start; }

  /// Get the node kind
  virtual ASTNodeKind getKind() const = 0;

  /// Get the kind name for debugging
  virtual const char* getKindName() const = 0;

  /// Visitor accept
  virtual void accept(ASTVisitor& visitor) = 0;

  /// Type annotation (set by semantic analysis)
  QualType getType() const { return CachedType; }
  void setType(QualType ty) { CachedType = ty; }

protected:
  SourceRange Range;
  QualType CachedType;
};

//===----------------------------------------------------------------------===//
// Type Nodes
//===----------------------------------------------------------------------===//

class TypeNode : public ASTNode {};

class PrimitiveTypeNode : public TypeNode {
public:
  TypeKind PrimKind;

  PrimitiveTypeNode(TypeKind kind) : PrimKind(kind) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::PRIMITIVE_TYPE; }
  const char* getKindName() const override { return "PrimitiveType"; }
  void accept(ASTVisitor& v) override;
};

class PointerTypeNode : public TypeNode {
public:
  std::unique_ptr<TypeNode> Pointee;

  PointerTypeNode(std::unique_ptr<TypeNode> pointee)
      : Pointee(std::move(pointee)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::POINTER_TYPE; }
  const char* getKindName() const override { return "PointerType"; }
  void accept(ASTVisitor& v) override;
};

class ArrayTypeNode : public TypeNode {
public:
  std::unique_ptr<TypeNode> ElementType;
  std::unique_ptr<ASTNode> Size;  // nullptr for unsized

  ArrayTypeNode(std::unique_ptr<TypeNode> elem, std::unique_ptr<ASTNode> sz)
      : ElementType(std::move(elem)), Size(std::move(sz)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::ARRAY_TYPE; }
  const char* getKindName() const override { return "ArrayType"; }
  void accept(ASTVisitor& v) override;
};

class FunctionTypeNode : public TypeNode {
public:
  std::unique_ptr<TypeNode> ReturnType;
  llvm::SmallVector<std::unique_ptr<TypeNode>, 4> ParamTypes;

  FunctionTypeNode(std::unique_ptr<TypeNode> ret,
                   llvm::SmallVector<std::unique_ptr<TypeNode>, 4> params)
      : ReturnType(std::move(ret)), ParamTypes(std::move(params)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::FUNCTION_TYPE; }
  const char* getKindName() const override { return "FunctionType"; }
  void accept(ASTVisitor& v) override;
};

class StructTypeNode : public TypeNode {
public:
  llvm::StringRef Name;

  StructTypeNode(llvm::StringRef name) : Name(name) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::STRUCT_TYPE; }
  const char* getKindName() const override { return "StructType"; }
  void accept(ASTVisitor& v) override;
};

class AutoTypeNode : public TypeNode {
public:
  AutoTypeNode() = default;

  ASTNodeKind getKind() const override { return ASTNodeKind::AUTO_TYPE; }
  const char* getKindName() const override { return "AutoType"; }
  void accept(ASTVisitor& v) override;
};

//===----------------------------------------------------------------------===//
// Expression Nodes
//===----------------------------------------------------------------------===//

class ExprNode : public ASTNode {};

// --- Literals ---

class IntegerLiteralExpr : public ExprNode {
public:
  uint64_t Value;
  bool IsSigned;

  IntegerLiteralExpr(uint64_t val, bool isSigned = true)
      : Value(val), IsSigned(isSigned) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::INT_LITERAL; }
  const char* getKindName() const override { return "IntLiteral"; }
  void accept(ASTVisitor& v) override;
};

class FloatLiteralExpr : public ExprNode {
public:
  double Value;

  FloatLiteralExpr(double val) : Value(val) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::FLOAT_LITERAL; }
  const char* getKindName() const override { return "FloatLiteral"; }
  void accept(ASTVisitor& v) override;
};

class StringLiteralExpr : public ExprNode {
public:
  std::string Value;

  StringLiteralExpr(std::string val) : Value(std::move(val)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::STRING_LITERAL; }
  const char* getKindName() const override { return "StringLiteral"; }
  void accept(ASTVisitor& v) override;
};

class CharLiteralExpr : public ExprNode {
public:
  uint32_t Value;  // Unicode code point

  CharLiteralExpr(uint32_t val) : Value(val) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::CHAR_LITERAL; }
  const char* getKindName() const override { return "CharLiteral"; }
  void accept(ASTVisitor& v) override;
};

class BoolLiteralExpr : public ExprNode {
public:
  bool Value;

  BoolLiteralExpr(bool val) : Value(val) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::BOOL_LITERAL; }
  const char* getKindName() const override { return "BoolLiteral"; }
  void accept(ASTVisitor& v) override;
};

class NullLiteralExpr : public ExprNode {
public:
  NullLiteralExpr() = default;

  ASTNodeKind getKind() const override { return ASTNodeKind::NULL_LITERAL; }
  const char* getKindName() const override { return "NullLiteral"; }
  void accept(ASTVisitor& v) override;
};

class WideCharLiteralExpr : public ExprNode {
public:
  uint32_t Value;

  WideCharLiteralExpr(uint32_t val) : Value(val) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::WIDE_CHAR_LITERAL; }
  const char* getKindName() const override { return "WideCharLiteral"; }
  void accept(ASTVisitor& v) override;
};

class WideStringLiteralExpr : public ExprNode {
public:
  std::string Value;

  WideStringLiteralExpr(std::string val) : Value(std::move(val)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::WIDE_STRING_LITERAL; }
  const char* getKindName() const override { return "WideStringLiteral"; }
  void accept(ASTVisitor& v) override;
};

class ComplexLiteralExpr : public ExprNode {
public:
  double Real;
  double Imag;

  ComplexLiteralExpr(double r, double i) : Real(r), Imag(i) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::COMPLEX_LITERAL; }
  const char* getKindName() const override { return "ComplexLiteral"; }
  void accept(ASTVisitor& v) override;
};

// --- Identifiers & Access ---

class IdentifierExpr : public ExprNode {
public:
  llvm::StringRef Name;

  IdentifierExpr(llvm::StringRef name) : Name(name) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::IDENTIFIER_EXPR; }
  const char* getKindName() const override { return "IdentifierExpr"; }
  void accept(ASTVisitor& v) override;
};

class MemberExpr : public ExprNode {
public:
  std::unique_ptr<ExprNode> Base;
  llvm::StringRef MemberName;
  bool IsArrow;  // true for ->, false for .

  MemberExpr(std::unique_ptr<ExprNode> base, llvm::StringRef member, bool arrow)
      : Base(std::move(base)), MemberName(member), IsArrow(arrow) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::MEMBER_EXPR; }
  const char* getKindName() const override { return "MemberExpr"; }
  void accept(ASTVisitor& v) override;
};

class ArrayExpr : public ExprNode {
public:
  std::unique_ptr<ExprNode> Base;
  std::unique_ptr<ExprNode> Index;

  ArrayExpr(std::unique_ptr<ExprNode> base, std::unique_ptr<ExprNode> idx)
      : Base(std::move(base)), Index(std::move(idx)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::ARRAY_EXPR; }
  const char* getKindName() const override { return "ArrayExpr"; }
  void accept(ASTVisitor& v) override;
};

// --- Operators ---

class BinaryOperatorExpr : public ExprNode {
public:
  TokenKind Op;
  std::unique_ptr<ExprNode> LHS;
  std::unique_ptr<ExprNode> RHS;

  BinaryOperatorExpr(TokenKind op, std::unique_ptr<ExprNode> lhs,
                     std::unique_ptr<ExprNode> rhs)
      : Op(op), LHS(std::move(lhs)), RHS(std::move(rhs)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::BINARY_EXPR; }
  const char* getKindName() const override { return "BinaryExpr"; }
  void accept(ASTVisitor& v) override;
};

class UnaryExpr : public ExprNode {
public:
  TokenKind Op;
  std::unique_ptr<ExprNode> Operand;
  bool IsPrefix;  // true for prefix (++x), false for postfix (x++)

  UnaryExpr(TokenKind op, std::unique_ptr<ExprNode> operand, bool prefix)
      : Op(op), Operand(std::move(operand)), IsPrefix(prefix) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::UNARY_EXPR; }
  const char* getKindName() const override { return "UnaryExpr"; }
  void accept(ASTVisitor& v) override;
};

class AssignExpr : public ExprNode {
public:
  TokenKind Op;  // equal, pluseq, minuseq, etc.
  std::unique_ptr<ExprNode> Target;
  std::unique_ptr<ExprNode> Value;

  AssignExpr(TokenKind op, std::unique_ptr<ExprNode> target,
             std::unique_ptr<ExprNode> value)
      : Op(op), Target(std::move(target)), Value(std::move(value)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::ASSIGN_EXPR; }
  const char* getKindName() const override { return "AssignExpr"; }
  void accept(ASTVisitor& v) override;
};

class CallExpr : public ExprNode {
public:
  std::unique_ptr<ExprNode> Callee;
  llvm::SmallVector<std::unique_ptr<ExprNode>, 4> Args;

  CallExpr(std::unique_ptr<ExprNode> callee,
           llvm::SmallVector<std::unique_ptr<ExprNode>, 4> args)
      : Callee(std::move(callee)), Args(std::move(args)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::CALL_EXPR; }
  const char* getKindName() const override { return "CallExpr"; }
  void accept(ASTVisitor& v) override;
};

class TernaryExpr : public ExprNode {
public:
  std::unique_ptr<ExprNode> Condition;
  std::unique_ptr<ExprNode> TrueExpr;
  std::unique_ptr<ExprNode> FalseExpr;

  TernaryExpr(std::unique_ptr<ExprNode> cond, std::unique_ptr<ExprNode> trueE,
              std::unique_ptr<ExprNode> falseE)
      : Condition(std::move(cond)), TrueExpr(std::move(trueE)),
        FalseExpr(std::move(falseE)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::TERNARY_EXPR; }
  const char* getKindName() const override { return "TernaryExpr"; }
  void accept(ASTVisitor& v) override;
};

class SizeofExpr : public ExprNode {
public:
  std::unique_ptr<ASTNode> Operand;  // ExprNode or TypeNode

  explicit SizeofExpr(std::unique_ptr<ASTNode> operand)
      : Operand(std::move(operand)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::SIZEOF_EXPR; }
  const char* getKindName() const override { return "SizeofExpr"; }
  void accept(ASTVisitor& v) override;
};

class CastExpr : public ExprNode {
public:
  std::unique_ptr<TypeNode> TargetType;
  std::unique_ptr<ExprNode> Operand;

  CastExpr(std::unique_ptr<TypeNode> ty, std::unique_ptr<ExprNode> operand)
      : TargetType(std::move(ty)), Operand(std::move(operand)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::CAST_EXPR; }
  const char* getKindName() const override { return "CastExpr"; }
  void accept(ASTVisitor& v) override;
};

class AsExpr : public ExprNode {
public:
  std::unique_ptr<ExprNode> Operand;
  std::unique_ptr<TypeNode> TargetType;
  bool IsSafe;  // true for 'as' (safe), false for unsafe

  AsExpr(std::unique_ptr<ExprNode> operand, std::unique_ptr<TypeNode> ty,
         bool safe)
      : Operand(std::move(operand)), TargetType(std::move(ty)), IsSafe(safe) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::AS_EXPR; }
  const char* getKindName() const override { return "AsExpr"; }
  void accept(ASTVisitor& v) override;
};

class IsExpr : public ExprNode {
public:
  std::unique_ptr<ExprNode> Operand;
  std::unique_ptr<TypeNode> CheckType;

  IsExpr(std::unique_ptr<ExprNode> operand, std::unique_ptr<TypeNode> ty)
      : Operand(std::move(operand)), CheckType(std::move(ty)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::IS_EXPR; }
  const char* getKindName() const override { return "IsExpr"; }
  void accept(ASTVisitor& v) override;
};

class ArrayInitExpr : public ExprNode {
public:
  llvm::SmallVector<std::unique_ptr<ExprNode>, 8> Elements;

  ArrayInitExpr(llvm::SmallVector<std::unique_ptr<ExprNode>, 8> elems)
      : Elements(std::move(elems)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::ARRAY_INIT; }
  const char* getKindName() const override { return "ArrayInit"; }
  void accept(ASTVisitor& v) override;
};

class StructInitExpr : public ExprNode {
public:
  struct FieldInit {
    llvm::StringRef Name;
    std::unique_ptr<ExprNode> Value;
  };

  llvm::StringRef StructName;
  llvm::SmallVector<FieldInit, 8> Fields;

  StructInitExpr(llvm::StringRef name,
                 llvm::SmallVector<FieldInit, 8> fields)
      : StructName(name), Fields(std::move(fields)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::STRUCT_INIT; }
  const char* getKindName() const override { return "StructInit"; }
  void accept(ASTVisitor& v) override;
};

class LambdaExpr : public ExprNode {
public:
  llvm::SmallVector<std::pair<llvm::StringRef, std::unique_ptr<TypeNode>>, 4> Params;
  std::unique_ptr<TypeNode> ReturnType;
  std::unique_ptr<class BlockStmt> Body;
  llvm::SmallVector<llvm::StringRef, 4> Captures;

  ASTNodeKind getKind() const override { return ASTNodeKind::LAMBDA_EXPR; }
  const char* getKindName() const override { return "LambdaExpr"; }
  void accept(ASTVisitor& v) override;
};

class MoveExpr : public ExprNode {
public:
  std::unique_ptr<ExprNode> Operand;

  explicit MoveExpr(std::unique_ptr<ExprNode> operand)
      : Operand(std::move(operand)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::MOVE_EXPR; }
  const char* getKindName() const override { return "MoveExpr"; }
  void accept(ASTVisitor& v) override;
};

// --- Coroutine / Async Expressions ---

class AwaitExpr : public ExprNode {
public:
  std::unique_ptr<ExprNode> Operand;

  explicit AwaitExpr(std::unique_ptr<ExprNode> operand)
      : Operand(std::move(operand)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::AWAIT_EXPR; }
  const char* getKindName() const override { return "AwaitExpr"; }
  void accept(ASTVisitor& v) override;
};

class YieldExpr : public ExprNode {
public:
  std::unique_ptr<ExprNode> Value;

  explicit YieldExpr(std::unique_ptr<ExprNode> val) : Value(std::move(val)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::YIELD_EXPR; }
  const char* getKindName() const override { return "YieldExpr"; }
  void accept(ASTVisitor& v) override;
};

class SpawnExpr : public ExprNode {
public:
  std::unique_ptr<ExprNode> Target;

  explicit SpawnExpr(std::unique_ptr<ExprNode> target)
      : Target(std::move(target)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::SPAWN_EXPR; }
  const char* getKindName() const override { return "SpawnExpr"; }
  void accept(ASTVisitor& v) override;
};

class ChannelExpr : public ExprNode {
public:
  enum class Direction { Send, Receive };
  Direction Dir;
  std::unique_ptr<ExprNode> Value;

  ChannelExpr(Direction dir, std::unique_ptr<ExprNode> val)
      : Dir(dir), Value(std::move(val)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::CHANNEL_EXPR; }
  const char* getKindName() const override { return "ChannelExpr"; }
  void accept(ASTVisitor& v) override;
};

// --- Pattern Matching ---

class MatchCase {
public:
  std::unique_ptr<ASTNode> Pattern;  // Pattern node (expression)
  std::unique_ptr<ExprNode> Guard;   // Optional guard expression
  std::unique_ptr<class BlockStmt> Body;
};

class MatchExpr : public ExprNode {
public:
  std::unique_ptr<ExprNode> Subject;
  llvm::SmallVector<MatchCase, 4> Cases;

  MatchExpr(std::unique_ptr<ExprNode> subject,
            llvm::SmallVector<MatchCase, 4> cases)
      : Subject(std::move(subject)), Cases(std::move(cases)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::MATCH_EXPR; }
  const char* getKindName() const override { return "MatchExpr"; }
  void accept(ASTVisitor& v) override;
};

//===----------------------------------------------------------------------===//
// Statement Nodes
//===----------------------------------------------------------------------===//

class StmtNode : public ASTNode {};

class BlockStmt : public StmtNode {
public:
  llvm::SmallVector<std::unique_ptr<ASTNode>, 8> Statements;

  BlockStmt() = default;

  ASTNodeKind getKind() const override { return ASTNodeKind::BLOCK_STMT; }
  const char* getKindName() const override { return "BlockStmt"; }
  void accept(ASTVisitor& v) override;
};

class ExprStmt : public StmtNode {
public:
  std::unique_ptr<ExprNode> Expr;

  ExprStmt(std::unique_ptr<ExprNode> expr) : Expr(std::move(expr)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::EXPR_STMT; }
  const char* getKindName() const override { return "ExprStmt"; }
  void accept(ASTVisitor& v) override;
};

class ReturnStmt : public StmtNode {
public:
  std::unique_ptr<ExprNode> Value;  // nullptr for void return

  explicit ReturnStmt(std::unique_ptr<ExprNode> val = nullptr)
      : Value(std::move(val)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::RETURN_STMT; }
  const char* getKindName() const override { return "ReturnStmt"; }
  void accept(ASTVisitor& v) override;
};

class IfStmt : public StmtNode {
public:
  std::unique_ptr<ExprNode> Condition;
  std::unique_ptr<StmtNode> ThenBranch;
  std::unique_ptr<StmtNode> ElseBranch;  // nullptr if no else

  IfStmt(std::unique_ptr<ExprNode> cond, std::unique_ptr<StmtNode> then,
         std::unique_ptr<StmtNode> elseS = nullptr)
      : Condition(std::move(cond)), ThenBranch(std::move(then)),
        ElseBranch(std::move(elseS)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::IF_STMT; }
  const char* getKindName() const override { return "IfStmt"; }
  void accept(ASTVisitor& v) override;
};

class WhileStmt : public StmtNode {
public:
  std::unique_ptr<ExprNode> Condition;
  std::unique_ptr<StmtNode> Body;

  WhileStmt(std::unique_ptr<ExprNode> cond, std::unique_ptr<StmtNode> body)
      : Condition(std::move(cond)), Body(std::move(body)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::WHILE_STMT; }
  const char* getKindName() const override { return "WhileStmt"; }
  void accept(ASTVisitor& v) override;
};

class ForStmt : public StmtNode {
public:
  std::unique_ptr<ASTNode> Init;       // VarDecl or ExprStmt
  std::unique_ptr<ExprNode> Condition;
  std::unique_ptr<ExprNode> Increment;
  std::unique_ptr<StmtNode> Body;

  ForStmt(std::unique_ptr<ASTNode> init, std::unique_ptr<ExprNode> cond,
          std::unique_ptr<ExprNode> incr, std::unique_ptr<StmtNode> body)
      : Init(std::move(init)), Condition(std::move(cond)),
        Increment(std::move(incr)), Body(std::move(body)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::FOR_STMT; }
  const char* getKindName() const override { return "ForStmt"; }
  void accept(ASTVisitor& v) override;
};

class DoWhileStmt : public StmtNode {
public:
  std::unique_ptr<StmtNode> Body;
  std::unique_ptr<ExprNode> Condition;

  DoWhileStmt(std::unique_ptr<StmtNode> body, std::unique_ptr<ExprNode> cond)
      : Body(std::move(body)), Condition(std::move(cond)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::DO_WHILE_STMT; }
  const char* getKindName() const override { return "DoWhileStmt"; }
  void accept(ASTVisitor& v) override;
};

class BreakStmt : public StmtNode {
public:
  BreakStmt() = default;

  ASTNodeKind getKind() const override { return ASTNodeKind::BREAK_STMT; }
  const char* getKindName() const override { return "BreakStmt"; }
  void accept(ASTVisitor& v) override;
};

class ContinueStmt : public StmtNode {
public:
  ContinueStmt() = default;

  ASTNodeKind getKind() const override { return ASTNodeKind::CONTINUE_STMT; }
  const char* getKindName() const override { return "ContinueStmt"; }
  void accept(ASTVisitor& v) override;
};

class SwitchStmt : public StmtNode {
public:
  std::unique_ptr<ExprNode> Subject;
  llvm::SmallVector<std::unique_ptr<ASTNode>, 8> Cases;  // CaseStmt/DefaultStmt

  SwitchStmt(std::unique_ptr<ExprNode> subject,
             llvm::SmallVector<std::unique_ptr<ASTNode>, 8> cases)
      : Subject(std::move(subject)), Cases(std::move(cases)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::SWITCH_STMT; }
  const char* getKindName() const override { return "SwitchStmt"; }
  void accept(ASTVisitor& v) override;
};

class CaseStmt : public StmtNode {
public:
  std::unique_ptr<ExprNode> Value;
  llvm::SmallVector<std::unique_ptr<ASTNode>, 8> Body;

  CaseStmt(std::unique_ptr<ExprNode> val,
           llvm::SmallVector<std::unique_ptr<ASTNode>, 8> body)
      : Value(std::move(val)), Body(std::move(body)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::CASE_STMT; }
  const char* getKindName() const override { return "CaseStmt"; }
  void accept(ASTVisitor& v) override;
};

class DefaultStmt : public StmtNode {
public:
  llvm::SmallVector<std::unique_ptr<ASTNode>, 8> Body;

  DefaultStmt(llvm::SmallVector<std::unique_ptr<ASTNode>, 8> body)
      : Body(std::move(body)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::DEFAULT_STMT; }
  const char* getKindName() const override { return "DefaultStmt"; }
  void accept(ASTVisitor& v) override;
};

class GotoStmt : public StmtNode {
public:
  llvm::StringRef Label;

  GotoStmt(llvm::StringRef label) : Label(label) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::GOTO_STMT; }
  const char* getKindName() const override { return "GotoStmt"; }
  void accept(ASTVisitor& v) override;
};

class LabelStmt : public StmtNode {
public:
  llvm::StringRef Name;
  std::unique_ptr<StmtNode> Body;

  LabelStmt(llvm::StringRef name, std::unique_ptr<StmtNode> body)
      : Name(name), Body(std::move(body)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::LABEL_STMT; }
  const char* getKindName() const override { return "LabelStmt"; }
  void accept(ASTVisitor& v) override;
};

// --- Exception Handling ---

class TryStmt : public StmtNode {
public:
  std::unique_ptr<BlockStmt> Body;
  llvm::SmallVector<std::unique_ptr<ASTNode>, 2> CatchClauses;
  std::unique_ptr<BlockStmt> FinallyBlock;  // optional

  ASTNodeKind getKind() const override { return ASTNodeKind::TRY_STMT; }
  const char* getKindName() const override { return "TryStmt"; }
  void accept(ASTVisitor& v) override;
};

class CatchClause : public ASTNode {
public:
  std::unique_ptr<TypeNode> ExceptionType;  // optional
  llvm::StringRef VariableName;             // optional
  std::unique_ptr<BlockStmt> Body;
  bool IsDefault;

  CatchClause(std::unique_ptr<TypeNode> ty, llvm::StringRef var,
              std::unique_ptr<BlockStmt> body, bool isDefault)
      : ExceptionType(std::move(ty)), VariableName(var), Body(std::move(body)),
        IsDefault(isDefault) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::CATCH_CLAUSE; }
  const char* getKindName() const override { return "CatchClause"; }
  void accept(ASTVisitor& v) override;
};

class FinallyClause : public ASTNode {
public:
  std::unique_ptr<BlockStmt> Body;

  explicit FinallyClause(std::unique_ptr<BlockStmt> body)
      : Body(std::move(body)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::FINALLY_CLAUSE; }
  const char* getKindName() const override { return "FinallyClause"; }
  void accept(ASTVisitor& v) override;
};

class ThrowStmt : public StmtNode {
public:
  std::unique_ptr<ExprNode> Exception;
  std::string Message;  // For simple string throws

  ThrowStmt(std::unique_ptr<ExprNode> exc, std::string msg)
      : Exception(std::move(exc)), Message(std::move(msg)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::THROW_STMT; }
  const char* getKindName() const override { return "ThrowStmt"; }
  void accept(ASTVisitor& v) override;
};

//===----------------------------------------------------------------------===//
// Declaration Nodes
//===----------------------------------------------------------------------===//

class DeclNode : public ASTNode {};

class ParamDecl : public DeclNode {
public:
  llvm::StringRef Name;
  std::unique_ptr<TypeNode> Type;
  std::unique_ptr<ExprNode> DefaultValue;  // optional

  ParamDecl(llvm::StringRef name, std::unique_ptr<TypeNode> type,
            std::unique_ptr<ExprNode> def = nullptr)
      : Name(name), Type(std::move(type)), DefaultValue(std::move(def)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::PARAM_DECL; }
  const char* getKindName() const override { return "ParamDecl"; }
  void accept(ASTVisitor& v) override;
};

class VarDecl : public DeclNode {
public:
  llvm::StringRef Name;
  std::unique_ptr<TypeNode> Type;   // nullptr for type inference
  std::unique_ptr<ExprNode> Init;   // optional initializer
  bool IsConst;
  bool IsStatic;
  bool IsExtern;
  bool IsDiscarded;  // Marked with ! suffix - suppress unused warning

  VarDecl(llvm::StringRef name, std::unique_ptr<TypeNode> type,
          std::unique_ptr<ExprNode> init = nullptr, bool isConst = false,
          bool isStatic = false, bool isExtern = false, bool isDiscarded = false)
      : Name(name), Type(std::move(type)), Init(std::move(init)),
        IsConst(isConst), IsStatic(isStatic), IsExtern(isExtern), 
        IsDiscarded(isDiscarded) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::VARIABLE_DECL; }
  const char* getKindName() const override { return "VarDecl"; }
  void accept(ASTVisitor& v) override;
  
  /// Check if this variable should suppress unused warnings
  /// Returns true if name is "_" or IsDiscarded is true
  bool shouldSuppressUnusedWarning() const {
    return Name == "_" || IsDiscarded;
  }
};

class FuncDecl : public DeclNode {
public:
  llvm::StringRef Name;
  std::unique_ptr<TypeNode> ReturnType;
  llvm::SmallVector<std::unique_ptr<ParamDecl>, 8> Params;
  std::unique_ptr<BlockStmt> Body;  // nullptr for extern/forward decl
  bool IsAsync;

  FuncDecl(llvm::StringRef name, std::unique_ptr<TypeNode> retType,
           llvm::SmallVector<std::unique_ptr<ParamDecl>, 8> params,
           std::unique_ptr<BlockStmt> body = nullptr, bool isAsync = false)
      : Name(name), ReturnType(std::move(retType)), Params(std::move(params)),
        Body(std::move(body)), IsAsync(isAsync) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::FUNCTION_DECL; }
  const char* getKindName() const override { return "FuncDecl"; }
  void accept(ASTVisitor& v) override;
};

class StructDecl : public DeclNode {
public:
  llvm::StringRef Name;
  struct Field {
    llvm::StringRef Name;
    std::unique_ptr<TypeNode> Type;
    std::unique_ptr<ExprNode> Default;  // optional
  };
  llvm::SmallVector<Field, 8> Fields;

  StructDecl(llvm::StringRef name, llvm::SmallVector<Field, 8> fields)
      : Name(name), Fields(std::move(fields)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::STRUCT_DECL; }
  const char* getKindName() const override { return "StructDecl"; }
  void accept(ASTVisitor& v) override;
};

class EnumDecl : public DeclNode {
public:
  llvm::StringRef Name;
  struct EnumConstant {
    llvm::StringRef Name;
    std::unique_ptr<ExprNode> Value;  // optional explicit value
  };
  llvm::SmallVector<EnumConstant, 8> Constants;
  std::unique_ptr<TypeNode> BaseType;  // optional underlying type

  EnumDecl(llvm::StringRef name,
           llvm::SmallVector<EnumConstant, 8> constants,
           std::unique_ptr<TypeNode> base = nullptr)
      : Name(name), Constants(std::move(constants)),
        BaseType(std::move(base)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::ENUM_DECL; }
  const char* getKindName() const override { return "EnumDecl"; }
  void accept(ASTVisitor& v) override;
};

class UnionDecl : public DeclNode {
public:
  llvm::StringRef Name;
  struct Field {
    llvm::StringRef Name;
    std::unique_ptr<TypeNode> Type;
  };
  llvm::SmallVector<Field, 8> Fields;

  UnionDecl(llvm::StringRef name, llvm::SmallVector<Field, 8> fields)
      : Name(name), Fields(std::move(fields)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::UNION_DECL; }
  const char* getKindName() const override { return "UnionDecl"; }
  void accept(ASTVisitor& v) override;
};

class TypedefDecl : public DeclNode {
public:
  llvm::StringRef Name;
  std::unique_ptr<TypeNode> UnderlyingType;

  TypedefDecl(llvm::StringRef name, std::unique_ptr<TypeNode> type)
      : Name(name), UnderlyingType(std::move(type)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::TYPEDEF_DECL; }
  const char* getKindName() const override { return "TypedefDecl"; }
  void accept(ASTVisitor& v) override;
};

class ExternalFunctionDecl : public DeclNode {
public:
  llvm::StringRef Name;
  std::unique_ptr<TypeNode> ReturnType;
  llvm::SmallVector<std::unique_ptr<ParamDecl>, 8> Params;
  std::string CName;    // Optional C name
  std::string Library;  // Optional library name

  ExternalFunctionDecl(llvm::StringRef name,
                       std::unique_ptr<TypeNode> retType,
                       llvm::SmallVector<std::unique_ptr<ParamDecl>, 8> params,
                       std::string cName = "", std::string library = "")
      : Name(name), ReturnType(std::move(retType)), Params(std::move(params)),
        CName(std::move(cName)), Library(std::move(library)) {}

  ASTNodeKind getKind() const override {
    return ASTNodeKind::EXTERNAL_FUNCTION_DECL;
  }
  const char* getKindName() const override { return "ExternalFunctionDecl"; }
  void accept(ASTVisitor& v) override;
};

class ExternalBlock : public DeclNode {
public:
  std::string Language;
  llvm::SmallVector<std::unique_ptr<ExternalFunctionDecl>, 4> Declarations;

  ExternalBlock(std::string lang,
                llvm::SmallVector<std::unique_ptr<ExternalFunctionDecl>, 4> decls)
      : Language(std::move(lang)), Declarations(std::move(decls)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::EXTERNAL_BLOCK; }
  const char* getKindName() const override { return "ExternalBlock"; }
  void accept(ASTVisitor& v) override;
};

// --- Module System ---

class ModuleDecl : public DeclNode {
public:
  llvm::StringRef Name;
  llvm::SmallVector<llvm::StringRef, 8> Exports;
  llvm::SmallVector<llvm::StringRef, 8> Imports;
  llvm::SmallVector<std::unique_ptr<ASTNode>, 8> Body;

  ModuleDecl(llvm::StringRef name,
             llvm::SmallVector<llvm::StringRef, 8> exports,
             llvm::SmallVector<llvm::StringRef, 8> imports,
             llvm::SmallVector<std::unique_ptr<ASTNode>, 8> body)
      : Name(name), Exports(std::move(exports)), Imports(std::move(imports)),
        Body(std::move(body)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::MODULE_DECL; }
  const char* getKindName() const override { return "ModuleDecl"; }
  void accept(ASTVisitor& v) override;
};

class ImportDecl : public DeclNode {
public:
  llvm::StringRef ModuleName;
  llvm::SmallVector<llvm::StringRef, 4> Symbols;  // empty = import all

  ImportDecl(llvm::StringRef module,
             llvm::SmallVector<llvm::StringRef, 4> syms = {})
      : ModuleName(module), Symbols(std::move(syms)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::IMPORT_DECL; }
  const char* getKindName() const override { return "ImportDecl"; }
  void accept(ASTVisitor& v) override;
};

// --- Memory Management ---

class SmartPointerTypeNode : public TypeNode {
public:
  enum class PtrKind { Unique, Shared, Weak };
  PtrKind Kind;
  std::unique_ptr<TypeNode> Pointee;

  SmartPointerTypeNode(PtrKind kind, std::unique_ptr<TypeNode> pointee)
      : Kind(kind), Pointee(std::move(pointee)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::SMART_PTR_TYPE; }
  const char* getKindName() const override { return "SmartPtrType"; }
  void accept(ASTVisitor& v) override;
};

class DestructorDecl : public DeclNode {
public:
  llvm::StringRef StructName;
  std::unique_ptr<BlockStmt> Body;

  DestructorDecl(llvm::StringRef name, std::unique_ptr<BlockStmt> body)
      : StructName(name), Body(std::move(body)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::DESTRUCTOR_DECL; }
  const char* getKindName() const override { return "DestructorDecl"; }
  void accept(ASTVisitor& v) override;
};

// --- Coroutine Definition ---

class CoroutineDef : public DeclNode {
public:
  llvm::StringRef Name;
  std::unique_ptr<TypeNode> ReturnType;
  llvm::SmallVector<std::unique_ptr<ParamDecl>, 8> Params;
  std::unique_ptr<BlockStmt> Body;

  CoroutineDef(llvm::StringRef name, std::unique_ptr<TypeNode> retType,
               llvm::SmallVector<std::unique_ptr<ParamDecl>, 8> params,
               std::unique_ptr<BlockStmt> body)
      : Name(name), ReturnType(std::move(retType)), Params(std::move(params)),
        Body(std::move(body)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::COROUTINE_DEF; }
  const char* getKindName() const override { return "CoroutineDef"; }
  void accept(ASTVisitor& v) override;
};

//===----------------------------------------------------------------------===//
// Translation Unit (top-level)
//===----------------------------------------------------------------------===//

class TranslationUnit : public ASTNode {
public:
  llvm::SmallVector<std::unique_ptr<ASTNode>, 16> Decls;

  TranslationUnit() = default;

  ASTNodeKind getKind() const override { return ASTNodeKind::PROGRAM; }
  const char* getKindName() const override { return "TranslationUnit"; }
  void accept(ASTVisitor& v) override;
};

//===----------------------------------------------------------------------===//
// Error Node (for error recovery)
//===----------------------------------------------------------------------===//

class ErrorNode : public ASTNode {
public:
  std::string Message;

  explicit ErrorNode(std::string msg) : Message(std::move(msg)) {}

  ASTNodeKind getKind() const override { return ASTNodeKind::ERROR_NODE; }
  const char* getKindName() const override { return "ErrorNode"; }
  void accept(ASTVisitor& v) override;
};

//===----------------------------------------------------------------------===//
// AST Visitor (abstract base)
//===----------------------------------------------------------------------===//

class ASTVisitor {
public:
  virtual ~ASTVisitor() = default;

#define VISIT(KIND, CLASS) virtual void visit##KIND(CLASS*) = 0;
  // Types
  VISIT(PrimitiveType, PrimitiveTypeNode)
  VISIT(PointerType, PointerTypeNode)
  VISIT(ArrayType, ArrayTypeNode)
  VISIT(FunctionType, FunctionTypeNode)
  VISIT(StructType, StructTypeNode)
  VISIT(AutoType, AutoTypeNode)
  VISIT(SmartPtrType, SmartPointerTypeNode)

  // Literals
  VISIT(IntLiteral, IntegerLiteralExpr)
  VISIT(FloatLiteral, FloatLiteralExpr)
  VISIT(StringLiteral, StringLiteralExpr)
  VISIT(CharLiteral, CharLiteralExpr)
  VISIT(BoolLiteral, BoolLiteralExpr)
  VISIT(NullLiteral, NullLiteralExpr)
  VISIT(WideCharLiteral, WideCharLiteralExpr)
  VISIT(WideStringLiteral, WideStringLiteralExpr)
  VISIT(ComplexLiteral, ComplexLiteralExpr)

  // Expressions
  VISIT(IdentifierExpr, IdentifierExpr)
  VISIT(BinaryExpr, BinaryOperatorExpr)
  VISIT(UnaryExpr, UnaryExpr)
  VISIT(AssignExpr, AssignExpr)
  VISIT(CallExpr, CallExpr)
  VISIT(MemberExpr, MemberExpr)
  VISIT(ArrayExpr, ArrayExpr)
  VISIT(TernaryExpr, TernaryExpr)
  VISIT(SizeofExpr, SizeofExpr)
  VISIT(CastExpr, CastExpr)
  VISIT(AsExpr, AsExpr)
  VISIT(IsExpr, IsExpr)
  VISIT(ArrayInit, ArrayInitExpr)
  VISIT(StructInit, StructInitExpr)
  VISIT(LambdaExpr, LambdaExpr)
  VISIT(MoveExpr, MoveExpr)
  VISIT(AwaitExpr, AwaitExpr)
  VISIT(YieldExpr, YieldExpr)
  VISIT(SpawnExpr, SpawnExpr)
  VISIT(ChannelExpr, ChannelExpr)
  VISIT(MatchExpr, MatchExpr)

  // Statements
  VISIT(BlockStmt, BlockStmt)
  VISIT(ExprStmt, ExprStmt)
  VISIT(ReturnStmt, ReturnStmt)
  VISIT(IfStmt, IfStmt)
  VISIT(WhileStmt, WhileStmt)
  VISIT(ForStmt, ForStmt)
  VISIT(DoWhileStmt, DoWhileStmt)
  VISIT(BreakStmt, BreakStmt)
  VISIT(ContinueStmt, ContinueStmt)
  VISIT(SwitchStmt, SwitchStmt)
  VISIT(CaseStmt, CaseStmt)
  VISIT(DefaultStmt, DefaultStmt)
  VISIT(GotoStmt, GotoStmt)
  VISIT(LabelStmt, LabelStmt)
  VISIT(TryStmt, TryStmt)
  VISIT(CatchClause, CatchClause)
  VISIT(FinallyClause, FinallyClause)
  VISIT(ThrowStmt, ThrowStmt)

  // Declarations
  VISIT(VarDecl, VarDecl)
  VISIT(FuncDecl, FuncDecl)
  VISIT(ParamDecl, ParamDecl)
  VISIT(StructDecl, StructDecl)
  VISIT(EnumDecl, EnumDecl)
  VISIT(UnionDecl, UnionDecl)
  VISIT(TypedefDecl, TypedefDecl)
  VISIT(ExternalFunctionDecl, ExternalFunctionDecl)
  VISIT(ExternalBlock, ExternalBlock)
  VISIT(ModuleDecl, ModuleDecl)
  VISIT(ImportDecl, ImportDecl)
  VISIT(DestructorDecl, DestructorDecl)
  VISIT(CoroutineDef, CoroutineDef)

  // Top-level
  VISIT(TranslationUnit, TranslationUnit)
  VISIT(ErrorNode, ErrorNode)
#undef VISIT
};

} // namespace zhc

#endif // ZHC_AST_H
