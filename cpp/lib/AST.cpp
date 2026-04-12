//===--- AST.cpp - ZhC AST Node Implementations --------------------------===//
//
// This file implements the AST node methods for the ZhC compiler.
//
//===----------------------------------------------------------------------===//

#include "zhc/AST.h"

namespace zhc {

//===----------------------------------------------------------------------===//
// getNodeKindName
//===----------------------------------------------------------------------===//

llvm::StringRef getNodeKindName(ASTNodeKind kind) {
  switch (kind) {
#define NODE(KIND) case ASTNodeKind::KIND: return #KIND;
    NODE(PROGRAM)
    NODE(MODULE_DECL)
    NODE(IMPORT_DECL)
    NODE(FUNCTION_DECL)
    NODE(STRUCT_DECL)
    NODE(VARIABLE_DECL)
    NODE(PARAM_DECL)
    NODE(ENUM_DECL)
    NODE(UNION_DECL)
    NODE(TYPEDEF_DECL)
    NODE(EXTERNAL_BLOCK)
    NODE(EXTERNAL_FUNCTION_DECL)
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
    NODE(COROUTINE_DEF)
    NODE(AWAIT_EXPR)
    NODE(CHANNEL_EXPR)
    NODE(SPAWN_EXPR)
    NODE(YIELD_EXPR)
    NODE(MATCH_EXPR)
    NODE(MATCH_CASE)
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
    NODE(WIDE_CHAR_LITERAL)
    NODE(WIDE_STRING_LITERAL)
    NODE(UNIQUE_PTR_DECL)
    NODE(SHARED_PTR_DECL)
    NODE(WEAK_PTR_DECL)
    NODE(SMART_PTR_TYPE)
    NODE(MOVE_EXPR)
    NODE(DESTRUCTOR_DECL)
    NODE(ERROR_NODE)
#undef NODE
  }
  return "Unknown";
}

//===----------------------------------------------------------------------===//
// Type Nodes - accept() implementations
//===----------------------------------------------------------------------===//

void PrimitiveTypeNode::accept(ASTVisitor& v) { v.visitPrimitiveType(this); }
void PointerTypeNode::accept(ASTVisitor& v) { v.visitPointerType(this); }
void ArrayTypeNode::accept(ASTVisitor& v) { v.visitArrayType(this); }
void FunctionTypeNode::accept(ASTVisitor& v) { v.visitFunctionType(this); }
void StructTypeNode::accept(ASTVisitor& v) { v.visitStructType(this); }
void AutoTypeNode::accept(ASTVisitor& v) { v.visitAutoType(this); }
void SmartPointerTypeNode::accept(ASTVisitor& v) { v.visitSmartPtrType(this); }

//===----------------------------------------------------------------------===//
// Literal Nodes
//===----------------------------------------------------------------------===//

void IntegerLiteralExpr::accept(ASTVisitor& v) { v.visitIntLiteral(this); }
void FloatLiteralExpr::accept(ASTVisitor& v) { v.visitFloatLiteral(this); }
void StringLiteralExpr::accept(ASTVisitor& v) { v.visitStringLiteral(this); }
void CharLiteralExpr::accept(ASTVisitor& v) { v.visitCharLiteral(this); }
void BoolLiteralExpr::accept(ASTVisitor& v) { v.visitBoolLiteral(this); }
void NullLiteralExpr::accept(ASTVisitor& v) { v.visitNullLiteral(this); }
void WideCharLiteralExpr::accept(ASTVisitor& v) { v.visitWideCharLiteral(this); }
void WideStringLiteralExpr::accept(ASTVisitor& v) { v.visitWideStringLiteral(this); }
void ComplexLiteralExpr::accept(ASTVisitor& v) { v.visitComplexLiteral(this); }

//===----------------------------------------------------------------------===//
// Expression Nodes
//===----------------------------------------------------------------------===//

void IdentifierExpr::accept(ASTVisitor& v) { v.visitIdentifierExpr(this); }
void BinaryOperatorExpr::accept(ASTVisitor& v) { v.visitBinaryExpr(this); }
void UnaryExpr::accept(ASTVisitor& v) { v.visitUnaryExpr(this); }
void AssignExpr::accept(ASTVisitor& v) { v.visitAssignExpr(this); }
void CallExpr::accept(ASTVisitor& v) { v.visitCallExpr(this); }
void MemberExpr::accept(ASTVisitor& v) { v.visitMemberExpr(this); }
void ArrayExpr::accept(ASTVisitor& v) { v.visitArrayExpr(this); }
void TernaryExpr::accept(ASTVisitor& v) { v.visitTernaryExpr(this); }
void SizeofExpr::accept(ASTVisitor& v) { v.visitSizeofExpr(this); }
void CastExpr::accept(ASTVisitor& v) { v.visitCastExpr(this); }
void AsExpr::accept(ASTVisitor& v) { v.visitAsExpr(this); }
void IsExpr::accept(ASTVisitor& v) { v.visitIsExpr(this); }
void ArrayInitExpr::accept(ASTVisitor& v) { v.visitArrayInit(this); }
void StructInitExpr::accept(ASTVisitor& v) { v.visitStructInit(this); }
void LambdaExpr::accept(ASTVisitor& v) { v.visitLambdaExpr(this); }
void MoveExpr::accept(ASTVisitor& v) { v.visitMoveExpr(this); }
void AwaitExpr::accept(ASTVisitor& v) { v.visitAwaitExpr(this); }
void YieldExpr::accept(ASTVisitor& v) { v.visitYieldExpr(this); }
void SpawnExpr::accept(ASTVisitor& v) { v.visitSpawnExpr(this); }
void ChannelExpr::accept(ASTVisitor& v) { v.visitChannelExpr(this); }
void MatchExpr::accept(ASTVisitor& v) { v.visitMatchExpr(this); }

//===----------------------------------------------------------------------===//
// Statement Nodes
//===----------------------------------------------------------------------===//

void BlockStmt::accept(ASTVisitor& v) { v.visitBlockStmt(this); }
void ExprStmt::accept(ASTVisitor& v) { v.visitExprStmt(this); }
void ReturnStmt::accept(ASTVisitor& v) { v.visitReturnStmt(this); }
void IfStmt::accept(ASTVisitor& v) { v.visitIfStmt(this); }
void WhileStmt::accept(ASTVisitor& v) { v.visitWhileStmt(this); }
void ForStmt::accept(ASTVisitor& v) { v.visitForStmt(this); }
void DoWhileStmt::accept(ASTVisitor& v) { v.visitDoWhileStmt(this); }
void BreakStmt::accept(ASTVisitor& v) { v.visitBreakStmt(this); }
void ContinueStmt::accept(ASTVisitor& v) { v.visitContinueStmt(this); }
void SwitchStmt::accept(ASTVisitor& v) { v.visitSwitchStmt(this); }
void CaseStmt::accept(ASTVisitor& v) { v.visitCaseStmt(this); }
void DefaultStmt::accept(ASTVisitor& v) { v.visitDefaultStmt(this); }
void GotoStmt::accept(ASTVisitor& v) { v.visitGotoStmt(this); }
void LabelStmt::accept(ASTVisitor& v) { v.visitLabelStmt(this); }
void TryStmt::accept(ASTVisitor& v) { v.visitTryStmt(this); }
void CatchClause::accept(ASTVisitor& v) { v.visitCatchClause(this); }
void FinallyClause::accept(ASTVisitor& v) { v.visitFinallyClause(this); }
void ThrowStmt::accept(ASTVisitor& v) { v.visitThrowStmt(this); }

//===----------------------------------------------------------------------===//
// Declaration Nodes
//===----------------------------------------------------------------------===//

void VarDecl::accept(ASTVisitor& v) { v.visitVarDecl(this); }
void FuncDecl::accept(ASTVisitor& v) { v.visitFuncDecl(this); }
void ParamDecl::accept(ASTVisitor& v) { v.visitParamDecl(this); }
void StructDecl::accept(ASTVisitor& v) { v.visitStructDecl(this); }
void EnumDecl::accept(ASTVisitor& v) { v.visitEnumDecl(this); }
void UnionDecl::accept(ASTVisitor& v) { v.visitUnionDecl(this); }
void TypedefDecl::accept(ASTVisitor& v) { v.visitTypedefDecl(this); }
void ExternalFunctionDecl::accept(ASTVisitor& v) { v.visitExternalFunctionDecl(this); }
void ExternalBlock::accept(ASTVisitor& v) { v.visitExternalBlock(this); }
void ModuleDecl::accept(ASTVisitor& v) { v.visitModuleDecl(this); }
void ImportDecl::accept(ASTVisitor& v) { v.visitImportDecl(this); }
void DestructorDecl::accept(ASTVisitor& v) { v.visitDestructorDecl(this); }
void CoroutineDef::accept(ASTVisitor& v) { v.visitCoroutineDef(this); }

//===----------------------------------------------------------------------===//
// Top-level Nodes
//===----------------------------------------------------------------------===//

void TranslationUnit::accept(ASTVisitor& v) { v.visitTranslationUnit(this); }
void ErrorNode::accept(ASTVisitor& v) { v.visitErrorNode(this); }

} // namespace zhc
