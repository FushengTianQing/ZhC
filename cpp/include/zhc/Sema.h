//===--- Sema.h - ZhC Semantic Analysis Interface ------------------------===//
//
// This file defines the semantic analyzer for the ZhC compiler.
//
//===----------------------------------------------------------------------===//

#ifndef ZHC_SEMA_H
#define ZHC_SEMA_H

#include "zhc/AST.h"
#include "zhc/Diagnostics.h"

#include <unordered_map>

namespace zhc {

/// Symbol table entry
struct SymbolInfo {
  enum class Kind { Variable, Function, Type };
  Kind Kind;
  std::string Name;
  SourceLocation DeclLoc;
};

/// Semantic analyzer - type checking, symbol resolution
class Sema {
public:
  Sema(DiagnosticsEngine& diag);
  
  /// Perform semantic analysis on a translation unit
  bool analyze(TranslationUnit* unit);
  
private:
  DiagnosticsEngine& DiagEngine;
  std::unordered_map<std::string, SymbolInfo> SymbolTable;
  
  void pushScope();
  void popScope();
  bool addSymbol(const std::string& name, SymbolInfo::Kind kind, SourceLocation loc);
  SymbolInfo* lookupSymbol(const std::string& name);
};

} // namespace zhc

#endif // ZHC_SEMA_H