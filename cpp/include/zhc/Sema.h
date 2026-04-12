//===--- Sema.h - ZhC Semantic Analysis Interface ------------------------===//
//
// This file defines the semantic analyzer for the ZhC compiler.
// Includes unused variable detection.
//
//===----------------------------------------------------------------------===//

#ifndef ZHC_SEMA_H
#define ZHC_SEMA_H

#include "zhc/AST.h"
#include "zhc/Diagnostics.h"

#include "llvm/ADT/SmallVector.h"
#include "llvm/ADT/StringMap.h"
#include "llvm/ADT/StringRef.h"

#include <memory>
#include <unordered_map>
#include <vector>

namespace zhc {

/// Symbol table entry
struct SymbolInfo {
  enum class SymbolKind { Variable, Function, Type };
  SymbolKind SymKind;
  std::string Name;
  SourceLocation DeclLoc;
};

/// Scope - a symbol table for a single scope level
struct Scope {
  llvm::StringMap<SymbolInfo> Symbols;
};

/// Information about a tracked local variable
struct TrackedVar {
  VarDecl* Decl;
  SourceLocation DeclLoc;
  
  TrackedVar(VarDecl* decl, SourceLocation loc)
      : Decl(decl), DeclLoc(loc) {}
};

/// Local variable info for initialization tracking (S02 framework)
struct LocalVarInfo {
  QualType Type;
  bool IsInitialized = false;
  bool IsUsed = false;
  SourceLocation DeclLoc;
  
  LocalVarInfo() = default;
  LocalVarInfo(QualType type, SourceLocation loc)
      : Type(type), DeclLoc(loc) {}
};

/// Semantic analyzer - type checking, symbol resolution, unused variable detection
class Sema {
public:
  Sema(DiagnosticsEngine& diag);
  
  /// Perform semantic analysis on a translation unit
  bool analyze(TranslationUnit* unit);

private:
  DiagnosticsEngine& DiagEngine;
  
  // Symbol table
  std::vector<std::unique_ptr<Scope>> ScopeStack;
  llvm::StringMap<SymbolInfo> GlobalSymbols;
  
  // Tracked local variables for unused detection
  llvm::SmallVector<TrackedVar, 32> TrackedVars;
  
  // Initialization tracking (S02 framework - Phase 1 scaffolding)
  std::unordered_map<std::string, LocalVarInfo> LocalVars;
  
  /// Analyze a function for unused variables
  bool analyzeFunction(FuncDecl* func);
  
  /// Collect all local variable declarations in a statement
  void collectLocalVars(ASTNode* stmt, llvm::SmallVector<TrackedVar, 32>& vars);
  
  // Initialization tracking methods (S02 framework)
  void markInitialized(const std::string& name);
  void markUsed(const std::string& name);
  bool isInitialized(const std::string& name) const;
  
  /// Check for use of uninitialized variables in a function
  void checkInitialization(FuncDecl* func);
  
  /// Scan statements for initialization state tracking
  void scanForInitialization(ASTNode* node, std::unordered_map<std::string, bool>& initMap);
  
  void pushScope();
  void popScope();
  bool addSymbol(const std::string& name, SymbolInfo::SymbolKind kind, SourceLocation loc);
  SymbolInfo* lookupSymbol(const std::string& name);
};

} // namespace zhc

#endif // ZHC_SEMA_H