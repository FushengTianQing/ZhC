//===--- Driver.h - ZhC Compiler Driver ----------------------------------===//
//
// This file defines the compiler driver for the ZhC compiler.
//
//===----------------------------------------------------------------------===//

#ifndef ZHC_DRIVER_H
#define ZHC_DRIVER_H

#include "zhc/SourceManager.h"
#include "zhc/Diagnostics.h"

#include <string>

namespace zhc {

/// Compiler invocation options
struct CompileOptions {
  bool PrintAST = false;        // -fsyntax-only
  bool PrintIR = false;         // -emit-llvm
  bool PrintTokens = false;     // -dump-tokens
  bool PrintParseTree = false;  // -ast-print
  std::string OutputFile;       // -o <file>
  std::vector<std::string> IncludePaths;
  std::vector<std::string> Defines;
};

/// Compiler driver - orchestrates the compilation pipeline
class Driver {
public:
  Driver(const CompileOptions& opts);
  
  /// Compile a source file
  bool compile(const std::string& inputPath);
  
  /// Get diagnostics from the last compilation
  const DiagnosticsEngine& getDiagnostics() const { return DiagEngine; }
  
private:
  CompileOptions Opts;
  DiagnosticsEngine DiagEngine;
  SourceManager SourceMgr;
  
  bool compileSource(const std::string& path);
};

} // namespace zhc

#endif // ZHC_DRIVER_H