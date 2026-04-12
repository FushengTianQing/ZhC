//===--- Diagnostics.h - ZhC Diagnostic Engine --------------------------===//
//
// This file defines the diagnostic engine for the ZhC compiler.
// It supports Chinese error messages, source location highlighting,
// colorized output, and fix-it hints.
//
//===----------------------------------------------------------------------===//

#ifndef ZHC_DIAGNOSTICS_H
#define ZHC_DIAGNOSTICS_H

#include "zhc/Common.h"
#include "llvm/ADT/StringRef.h"
#include "llvm/ADT/SmallVector.h"
#include "llvm/Support/SourceMgr.h"
#include "llvm/Support/raw_ostream.h"

#include <string>
#include <vector>

namespace zhc {

class SourceManager;

/// Diagnostic severity level
enum class DiagnosticLevel {
  Note,
  Warning,
  Error,
  Fatal
};

/// A fix-it hint: replace the text at [Start, End) with Replacement
struct FixItHint {
  SourceLocation Start;
  SourceLocation End;
  std::string Replacement;
  
  FixItHint(SourceLocation start, SourceLocation end, std::string replacement)
      : Start(start), End(end), Replacement(std::move(replacement)) {}
  
  /// Create a simple insertion hint
  static FixItHint insert(SourceLocation loc, std::string text) {
    return FixItHint(loc, loc, std::move(text));
  }
  
  /// Create a removal hint
  static FixItHint remove(SourceLocation start, SourceLocation end) {
    return FixItHint(start, end, "");
  }
};

/// A single diagnostic message
struct Diagnostic {
  DiagnosticLevel Level;
  SourceLocation Loc;
  std::string Message;
  std::vector<FixItHint> Hints;
  
  Diagnostic(DiagnosticLevel level, SourceLocation loc, std::string message)
      : Level(level), Loc(loc), Message(std::move(message)) {}
  
  /// Add a fix-it hint
  Diagnostic& addFixIt(FixItHint hint) {
    Hints.push_back(std::move(hint));
    return *this;
  }
};

/// Diagnostic engine - collects and reports diagnostics
class DiagnosticsEngine {
public:
  DiagnosticsEngine();
  
  /// Report an error at the given location
  Diagnostic& error(SourceLocation loc, const std::string& msg);
  
  /// Report a warning at the given location
  Diagnostic& warning(SourceLocation loc, const std::string& msg);
  
  /// Report a note at the given location
  Diagnostic& note(SourceLocation loc, const std::string& msg);
  
  /// Report a fatal error (compilation stops)
  Diagnostic& fatal(SourceLocation loc, const std::string& msg);
  
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
  
  /// Print a single diagnostic with source context
  void printDiagnostic(llvm::raw_ostream& os, const Diagnostic& diag) const;
  
  /// Set the source manager for source line display
  void setSourceManager(SourceManager* sm) { SrcMgr = sm; }
  
  /// Enable/disable color output
  void setColorOutput(bool enable) { UseColor = enable; }
  
  /// Set max errors before stopping (0 = unlimited)
  void setMaxErrors(unsigned max) { MaxErrors = max; }

private:
  std::vector<Diagnostic> Diags;
  unsigned ErrorCount = 0;
  unsigned WarningCount = 0;
  SourceManager* SrcMgr = nullptr;
  bool UseColor = true;
  unsigned MaxErrors = 0;  // 0 = unlimited
  
  Diagnostic& addDiagnostic(DiagnosticLevel level, SourceLocation loc, 
                            const std::string& msg);
  
  /// Get the severity prefix string (Chinese)
  llvm::StringRef getLevelPrefix(DiagnosticLevel level) const;
  
  /// Get ANSI color code for severity
  const char* getLevelColor(DiagnosticLevel level) const;
  
  /// Get ANSI reset code
  const char* getResetColor() const;
};

} // namespace zhc

#endif // ZHC_DIAGNOSTICS_H
