//===--- Diagnostics.h - ZhC Diagnostic Engine --------------------------===//
//
// This file defines the diagnostic engine for the ZhC compiler.
// It supports Chinese error messages, source location highlighting,
// colorized output, fix-it hints, and diagnostic IDs for maintainability.
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

/// Diagnostic ID - unique identifier for each diagnostic message
/// Defined in DiagnosticKinds.def
enum class DiagID {
#define DIAG(ID, LEVEL, MESSAGE) ID,
#include "zhc/DiagnosticKinds.def"
};

/// Get the severity level for a diagnostic ID
DiagnosticLevel getDiagLevel(DiagID ID);

/// Get the message template for a diagnostic ID
llvm::StringRef getDiagMessage(DiagID ID);

/// Format a diagnostic message with placeholders
std::string formatDiagMessage(DiagID ID, llvm::ArrayRef<std::string> args);

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
  DiagID ID;  // Diagnostic ID for tracking
  SourceLocation Loc;
  std::string Message;
  std::vector<FixItHint> Hints;
  
  Diagnostic(DiagnosticLevel level, DiagID id, SourceLocation loc, std::string message)
      : Level(level), ID(id), Loc(loc), Message(std::move(message)) {}
  
  /// Legacy constructor for backward compatibility
  Diagnostic(DiagnosticLevel level, SourceLocation loc, std::string message)
      : Level(level), ID(DiagID::err_expected), Loc(loc), Message(std::move(message)) {}
  
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
  
  /// Report a diagnostic by ID (preferred method)
  Diagnostic& report(SourceLocation loc, DiagID ID, llvm::ArrayRef<std::string> args = {});
  
  /// Report an error at the given location (legacy method)
  Diagnostic& error(SourceLocation loc, const std::string& msg);
  
  /// Report a warning at the given location (legacy method)
  Diagnostic& warning(SourceLocation loc, const std::string& msg);
  
  /// Report a note at the given location (legacy method)
  Diagnostic& note(SourceLocation loc, const std::string& msg);
  
  /// Report a fatal error (compilation stops) (legacy method)
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
  
  Diagnostic& addDiagnostic(DiagnosticLevel level, DiagID id, SourceLocation loc,
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