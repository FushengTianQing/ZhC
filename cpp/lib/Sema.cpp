//===--- Sema.cpp - Semantic Analysis Implementation ------------------------===//
//
// This file implements semantic analysis for the ZhC compiler.
// Includes unused variable detection with _ and ! support.
//
//===----------------------------------------------------------------------===//

#include "zhc/Sema.h"

#include "llvm/ADT/StringSet.h"

namespace zhc {

namespace {

/// Helper class to collect variable references from expressions and statements
class VariableUsageCollector {
public:
  /// Collect all identifier references in an expression
  static void collectUses(ExprNode* expr, llvm::StringSet<>& usedVars) {
    if (!expr) return;
    
    switch (expr->getKind()) {
    case ASTNodeKind::IDENTIFIER_EXPR: {
      auto* ident = static_cast<IdentifierExpr*>(expr);
      usedVars.insert(ident->Name);
      break;
    }
    case ASTNodeKind::BINARY_EXPR: {
      auto* bin = static_cast<BinaryOperatorExpr*>(expr);
      collectUses(bin->LHS.get(), usedVars);
      collectUses(bin->RHS.get(), usedVars);
      break;
    }
    case ASTNodeKind::UNARY_EXPR: {
      auto* unary = static_cast<UnaryExpr*>(expr);
      collectUses(unary->Operand.get(), usedVars);
      break;
    }
    case ASTNodeKind::ASSIGN_EXPR: {
      auto* assign = static_cast<AssignExpr*>(expr);
      collectUses(assign->Target.get(), usedVars);
      collectUses(assign->Value.get(), usedVars);
      break;
    }
    case ASTNodeKind::CALL_EXPR: {
      auto* call = static_cast<CallExpr*>(expr);
      for (auto& arg : call->Args) {
        collectUses(arg.get(), usedVars);
      }
      break;
    }
    case ASTNodeKind::TERNARY_EXPR: {
      auto* ternary = static_cast<TernaryExpr*>(expr);
      collectUses(ternary->Condition.get(), usedVars);
      collectUses(ternary->TrueExpr.get(), usedVars);
      collectUses(ternary->FalseExpr.get(), usedVars);
      break;
    }
    case ASTNodeKind::MEMBER_EXPR: {
      auto* member = static_cast<MemberExpr*>(expr);
      collectUses(member->Base.get(), usedVars);
      break;
    }
    case ASTNodeKind::ARRAY_EXPR: {
      auto* array = static_cast<ArrayExpr*>(expr);
      collectUses(array->Base.get(), usedVars);
      collectUses(array->Index.get(), usedVars);
      break;
    }
    case ASTNodeKind::CAST_EXPR: {
      auto* cast = static_cast<CastExpr*>(expr);
      collectUses(cast->Operand.get(), usedVars);
      break;
    }
    case ASTNodeKind::SIZEOF_EXPR: {
      // sizeof doesn't "use" a variable in the traditional sense
      break;
    }
    default:
      break;
    }
  }
  
  /// Collect all variable uses in a statement
  static void collectUsesInStmt(ASTNode* node, llvm::StringSet<>& usedVars) {
    if (!node) return;
    
    switch (node->getKind()) {
    case ASTNodeKind::EXPR_STMT: {
      auto* exprStmt = static_cast<ExprStmt*>(node);
      collectUses(exprStmt->Expr.get(), usedVars);
      break;
    }
    case ASTNodeKind::RETURN_STMT: {
      auto* ret = static_cast<ReturnStmt*>(node);
      collectUses(ret->Value.get(), usedVars);
      break;
    }
    case ASTNodeKind::IF_STMT: {
      auto* ifStmt = static_cast<IfStmt*>(node);
      collectUses(ifStmt->Condition.get(), usedVars);
      collectUsesInStmt(ifStmt->ThenBranch.get(), usedVars);
      collectUsesInStmt(ifStmt->ElseBranch.get(), usedVars);
      break;
    }
    case ASTNodeKind::WHILE_STMT: {
      auto* whileStmt = static_cast<WhileStmt*>(node);
      collectUses(whileStmt->Condition.get(), usedVars);
      collectUsesInStmt(whileStmt->Body.get(), usedVars);
      break;
    }
    case ASTNodeKind::DO_WHILE_STMT: {
      auto* doStmt = static_cast<DoWhileStmt*>(node);
      collectUses(doStmt->Condition.get(), usedVars);
      collectUsesInStmt(doStmt->Body.get(), usedVars);
      break;
    }
    case ASTNodeKind::FOR_STMT: {
      auto* forStmt = static_cast<ForStmt*>(node);
      // Init might be a VarDecl or ExprStmt
      if (forStmt->Init) {
        if (forStmt->Init->getKind() == ASTNodeKind::VARIABLE_DECL) {
          auto* varInit = static_cast<VarDecl*>(forStmt->Init.get());
          if (varInit->Init) {
            collectUses(varInit->Init.get(), usedVars);
          }
        } else {
          collectUsesInStmt(forStmt->Init.get(), usedVars);
        }
      }
      collectUses(forStmt->Condition.get(), usedVars);
      collectUses(forStmt->Increment.get(), usedVars);
      collectUsesInStmt(forStmt->Body.get(), usedVars);
      break;
    }
    case ASTNodeKind::SWITCH_STMT: {
      auto* switchStmt = static_cast<SwitchStmt*>(node);
      collectUses(switchStmt->Subject.get(), usedVars);
      for (auto& caseNode : switchStmt->Cases) {
        collectUsesInStmt(caseNode.get(), usedVars);
      }
      break;
    }
    case ASTNodeKind::BLOCK_STMT: {
      auto* block = static_cast<BlockStmt*>(node);
      for (auto& s : block->Statements) {
        collectUsesInStmt(s.get(), usedVars);
      }
      break;
    }
    case ASTNodeKind::TRY_STMT: {
      auto* tryStmt = static_cast<TryStmt*>(node);
      collectUsesInStmt(tryStmt->Body.get(), usedVars);
      for (auto& catchClause : tryStmt->CatchClauses) {
        collectUsesInStmt(catchClause.get(), usedVars);
      }
      if (tryStmt->FinallyBlock) {
        collectUsesInStmt(tryStmt->FinallyBlock.get(), usedVars);
      }
      break;
    }
    case ASTNodeKind::CATCH_CLAUSE: {
      auto* cc = static_cast<CatchClause*>(node);
      collectUsesInStmt(cc->Body.get(), usedVars);
      break;
    }
    case ASTNodeKind::THROW_STMT: {
      auto* throwStmt = static_cast<ThrowStmt*>(node);
      collectUses(throwStmt->Exception.get(), usedVars);
      break;
    }
    case ASTNodeKind::VARIABLE_DECL: {
      auto* varDecl = static_cast<VarDecl*>(node);
      if (varDecl->Init) {
        collectUses(varDecl->Init.get(), usedVars);
      }
      break;
    }
    default:
      break;
    }
  }
  
  /// Collect all variable uses in a function body
  static void collectUsesInFunction(FuncDecl* func, llvm::StringSet<>& usedVars) {
    if (!func || !func->Body) return;
    collectUsesInStmt(func->Body.get(), usedVars);
  }
};

} // anonymous namespace

//===----------------------------------------------------------------------===//
// Sema Implementation
//===----------------------------------------------------------------------===//

Sema::Sema(DiagnosticsEngine& diag) : DiagEngine(diag) {}

bool Sema::analyze(TranslationUnit* unit) {
  if (!unit) return false;
  
  bool success = true;
  
  // Analyze all top-level declarations
  for (auto& decl : unit->Decls) {
    if (decl->getKind() == ASTNodeKind::FUNCTION_DECL) {
      auto* func = static_cast<FuncDecl*>(decl.get());
      success &= analyzeFunction(func);
    }
  }
  
  return success && !DiagEngine.hasErrors();
}

bool Sema::analyzeFunction(FuncDecl* func) {
  if (!func) return true;
  
  // Collect all local variable declarations in the function
  llvm::SmallVector<TrackedVar, 32> localVars;
  collectLocalVars(func->Body.get(), localVars);
  
  // Collect variable uses
  llvm::StringSet<> usedVars;
  VariableUsageCollector::collectUsesInFunction(func, usedVars);
  
  // Check for unused variables
  for (const TrackedVar& info : localVars) {
    // Skip discarded variables (name="_" or IsDiscarded flag)
    if (info.Decl->shouldSuppressUnusedWarning()) {
      continue;
    }
    
    // Skip static/extern variables
    if (info.Decl->IsStatic || info.Decl->IsExtern) {
      continue;
    }
    
    // Check if the variable is used
    if (!usedVars.contains(info.Decl->Name)) {
      DiagEngine.report(info.DeclLoc, DiagID::warn_unused_variable,
                   {std::string(info.Decl->Name)});
    }
  }
  
  // Check for uninitialized variable usage (S02 framework)
  checkInitialization(func);
  
  return true;
}

void Sema::collectLocalVars(ASTNode* node, llvm::SmallVector<TrackedVar, 32>& vars) {
  if (!node) return;
  
  switch (node->getKind()) {
  case ASTNodeKind::BLOCK_STMT: {
    auto* block = static_cast<BlockStmt*>(node);
    for (auto& s : block->Statements) {
      if (s->getKind() == ASTNodeKind::VARIABLE_DECL) {
        auto* varDecl = static_cast<VarDecl*>(s.get());
        vars.emplace_back(varDecl, varDecl->getLocation());
      }
      collectLocalVars(s.get(), vars);
    }
    break;
  }
  case ASTNodeKind::IF_STMT: {
    auto* ifStmt = static_cast<IfStmt*>(node);
    collectLocalVars(ifStmt->ThenBranch.get(), vars);
    collectLocalVars(ifStmt->ElseBranch.get(), vars);
    break;
  }
  case ASTNodeKind::WHILE_STMT: {
    auto* whileStmt = static_cast<WhileStmt*>(node);
    collectLocalVars(whileStmt->Body.get(), vars);
    break;
  }
  case ASTNodeKind::DO_WHILE_STMT: {
    auto* doStmt = static_cast<DoWhileStmt*>(node);
    collectLocalVars(doStmt->Body.get(), vars);
    break;
  }
  case ASTNodeKind::FOR_STMT: {
    auto* forStmt = static_cast<ForStmt*>(node);
    if (forStmt->Init && forStmt->Init->getKind() == ASTNodeKind::VARIABLE_DECL) {
      auto* varInit = static_cast<VarDecl*>(forStmt->Init.get());
      vars.emplace_back(varInit, varInit->getLocation());
    }
    collectLocalVars(forStmt->Body.get(), vars);
    break;
  }
  case ASTNodeKind::SWITCH_STMT: {
    auto* switchStmt = static_cast<SwitchStmt*>(node);
    for (auto& caseNode : switchStmt->Cases) {
      collectLocalVars(caseNode.get(), vars);
    }
    break;
  }
  case ASTNodeKind::TRY_STMT: {
    auto* tryStmt = static_cast<TryStmt*>(node);
    collectLocalVars(tryStmt->Body.get(), vars);
    for (auto& catchClause : tryStmt->CatchClauses) {
      collectLocalVars(catchClause.get(), vars);
    }
    if (tryStmt->FinallyBlock) {
      collectLocalVars(tryStmt->FinallyBlock.get(), vars);
    }
    break;
  }
  case ASTNodeKind::CATCH_CLAUSE: {
    auto* cc = static_cast<CatchClause*>(node);
    collectLocalVars(cc->Body.get(), vars);
    break;
  }
  default:
    break;
  }
}

//===----------------------------------------------------------------------===//
// Initialization Tracking (S02 Framework - Phase 1 Scaffolding)
//===----------------------------------------------------------------------===//

void Sema::markInitialized(const std::string& name) {
  auto it = LocalVars.find(name);
  if (it != LocalVars.end()) {
    it->second.IsInitialized = true;
  }
}

void Sema::markUsed(const std::string& name) {
  auto it = LocalVars.find(name);
  if (it != LocalVars.end()) {
    it->second.IsUsed = true;
  }
}

bool Sema::isInitialized(const std::string& name) const {
  auto it = LocalVars.find(name);
  if (it != LocalVars.end()) {
    return it->second.IsInitialized;
  }
  // Unknown variables are considered initialized (error will be caught by other checks)
  return true;
}

void Sema::checkInitialization(FuncDecl* func) {
  if (!func || !func->Body) return;
  
  // Clear any previous state
  LocalVars.clear();
  
  // Build initialization map by scanning function body
  std::unordered_map<std::string, bool> initMap;
  scanForInitialization(func->Body.get(), initMap);
  
  // Check for uninitialized uses (Phase 1: simple forward scan, no control flow)
  // This is a framework - full control flow analysis in Phase 2
  for (const auto& [name, info] : LocalVars) {
    if (info.IsUsed && !info.IsInitialized) {
      DiagEngine.report(info.DeclLoc, DiagID::err_uninitialized_var, {name});
    }
  }
}

void Sema::scanForInitialization(ASTNode* node, std::unordered_map<std::string, bool>& initMap) {
  if (!node) return;
  
  switch (node->getKind()) {
  case ASTNodeKind::VARIABLE_DECL: {
    auto* varDecl = static_cast<VarDecl*>(node);
    std::string name = std::string(varDecl->Name);
    
    // Track this variable
    LocalVarInfo info;
    info.DeclLoc = varDecl->getLocation();
    info.IsInitialized = (varDecl->Init != nullptr);
    LocalVars[name] = info;
    initMap[name] = info.IsInitialized;
    break;
  }
  case ASTNodeKind::IDENTIFIER_EXPR: {
    auto* ident = static_cast<IdentifierExpr*>(node);
    std::string name = std::string(ident->Name);
    
    // Mark as used
    markUsed(name);
    
    // If this is a known local var, mark as potentially used uninitialized
    auto it = LocalVars.find(name);
    if (it != LocalVars.end()) {
      it->second.IsUsed = true;
    }
    break;
  }
  case ASTNodeKind::ASSIGN_EXPR: {
    auto* assign = static_cast<AssignExpr*>(node);
    // Left side of assignment initializes the variable
    if (assign->Target->getKind() == ASTNodeKind::IDENTIFIER_EXPR) {
      auto* target = static_cast<IdentifierExpr*>(assign->Target.get());
      markInitialized(std::string(target->Name));
    }
    scanForInitialization(assign->Value.get(), initMap);
    break;
  }
  case ASTNodeKind::BLOCK_STMT: {
    auto* block = static_cast<BlockStmt*>(node);
    for (auto& stmt : block->Statements) {
      scanForInitialization(stmt.get(), initMap);
    }
    break;
  }
  case ASTNodeKind::IF_STMT: {
    auto* ifStmt = static_cast<IfStmt*>(node);
    // Don't analyze condition for init state - conditions can use uninitialized vars
    scanForInitialization(ifStmt->ThenBranch.get(), initMap);
    scanForInitialization(ifStmt->ElseBranch.get(), initMap);
    break;
  }
  case ASTNodeKind::WHILE_STMT: {
    auto* whileStmt = static_cast<WhileStmt*>(node);
    scanForInitialization(whileStmt->Body.get(), initMap);
    break;
  }
  case ASTNodeKind::FOR_STMT: {
    auto* forStmt = static_cast<ForStmt*>(node);
    if (forStmt->Init) {
      scanForInitialization(forStmt->Init.get(), initMap);
    }
    scanForInitialization(forStmt->Body.get(), initMap);
    break;
  }
  case ASTNodeKind::RETURN_STMT: {
    auto* ret = static_cast<ReturnStmt*>(node);
    if (ret->Value) {
      scanForInitialization(ret->Value.get(), initMap);
    }
    break;
  }
  case ASTNodeKind::EXPR_STMT: {
    auto* exprStmt = static_cast<ExprStmt*>(node);
    scanForInitialization(exprStmt->Expr.get(), initMap);
    break;
  }
  case ASTNodeKind::BINARY_EXPR:
  case ASTNodeKind::UNARY_EXPR:
  case ASTNodeKind::CALL_EXPR:
  case ASTNodeKind::TERNARY_EXPR:
  case ASTNodeKind::CAST_EXPR:
  case ASTNodeKind::ARRAY_EXPR:
  case ASTNodeKind::MEMBER_EXPR:
  case ASTNodeKind::SIZEOF_EXPR: {
    // These expressions may contain identifier uses
    // Delegate to VariableUsageCollector pattern
    llvm::StringSet<> usedVars;
    VariableUsageCollector::collectUses(
        static_cast<ExprNode*>(node), usedVars);
    for (const auto& var : usedVars) {
      markUsed(std::string(var.getKey()));
    }
    break;
  }
  default:
    break;
  }
}

void Sema::pushScope() {
  ScopeStack.push_back(std::make_unique<Scope>());
}

void Sema::popScope() {
  if (!ScopeStack.empty()) {
    ScopeStack.pop_back();
  }
}

bool Sema::addSymbol(const std::string& name, SymbolInfo::SymbolKind kind, 
                     SourceLocation loc) {
  Scope* scope = ScopeStack.empty() ? nullptr : ScopeStack.back().get();
  
  if (scope) {
    if (scope->Symbols.find(name) != scope->Symbols.end()) {
      return false;
    }
    SymbolInfo info{kind, name, loc};
    scope->Symbols[name] = info;
  } else {
    if (GlobalSymbols.find(name) != GlobalSymbols.end()) {
      return false;
    }
    SymbolInfo info{kind, name, loc};
    GlobalSymbols[name] = info;
  }
  
  return true;
}

SymbolInfo* Sema::lookupSymbol(const std::string& name) {
  for (auto it = ScopeStack.rbegin(); it != ScopeStack.rend(); ++it) {
    auto findIt = (*it)->Symbols.find(name);
    if (findIt != (*it)->Symbols.end()) {
      return &findIt->second;
    }
  }
  
  auto globalIt = GlobalSymbols.find(name);
  if (globalIt != GlobalSymbols.end()) {
    return &globalIt->second;
  }
  
  return nullptr;
}

} // namespace zhc
