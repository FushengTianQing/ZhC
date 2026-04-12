//===--- Diagnostics.h - ZhC Diagnostic Engine --------------------------===//
//
// This file defines the diagnostic engine for the ZhC compiler.
// It supports Chinese error messages and source location highlighting.
//
//===----------------------------------------------------------------------===//

#ifndef ZHC_DIAGNOSTICS_H
#define ZHC_DIAGNOSTICS_H

#include "zhc/Common.h"
#include "llvm/ADT/StringRef.h"
#include "llvm/Support/SourceMgr.h"
#include "llvm/Support/raw_ostream.h"

#include <string>
#include <vector>

namespace zhc {

/// Diagnostic severity level
enum class DiagnosticLevel {
  Note,
  Warning,
  Error,
  Fatal
};

/// A single diagnostic message
struct Diagnostic {
  DiagnosticLevel Level;
  SourceLocation Loc;
  std::string Message;
  std::string Hint;  // Optional fix-it hint
  
  Diagnostic(DiagnosticLevel level, SourceLocation loc, std::string message)
      : Level(level), Loc(loc), Message(std::move(message)) {}
};

/// Diagnostic engine - collects and reports diagnostics
class DiagnosticsEngine {
public:
  DiagnosticsEngine() = default;
  
  /// Report an error at the given location
  void error(SourceLocation loc, const std::string& msg);
  
  /// Report a warning at the given location
  void warning(SourceLocation loc, const std::string& msg);
  
  /// Report a note at the given location
  void note(SourceLocation loc, const std::string& msg);
  
  /// Report a fatal error (compilation stops)
  void fatal(SourceLocation loc, const std::string& msg);
  
  /// Get all collected diagnostics
  const std::vector<Diagnostic>& getDiagnostics() const { return Diags; }
  
  /// Get the number of errors
  unsigned getErrorCount() const { return ErrorCount; }
  
  /// Get the number of warnings
  unsigned getWarningCount() const { return WarningCount; }
  
  /// Check if any errors occurred
  bool hasErrors() const { return ErrorCount > 0; }
  
  /// Clear all diagnostics
  void clear();
  
  /// Print all diagnostics to the given stream
  void printAll(llvm::raw_ostream& os) const;
  
private:
  std::vector<Diagnostic> Diags;
  unsigned ErrorCount = 0;
  unsigned WarningCount = 0;
  
  void addDiagnostic(DiagnosticLevel level, SourceLocation loc, 
                     const std::string& msg);
  
  /// Get the severity prefix string (Chinese)
  llvm::StringRef getLevelPrefix(DiagnosticLevel level) const;
};

} // namespace zhc

#endif // ZHC_DIAGNOSTICS_H