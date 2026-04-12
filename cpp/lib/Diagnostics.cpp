//===--- Diagnostics.cpp - ZhC Diagnostic Engine Implementation ----------===//
//
// This file implements the diagnostic engine for the ZhC compiler.
//
//===----------------------------------------------------------------------===//

#include "zhc/Diagnostics.h"

#include "llvm/Support/raw_ostream.h"

namespace zhc {

void DiagnosticsEngine::error(SourceLocation loc, const std::string& msg) {
  addDiagnostic(DiagnosticLevel::Error, loc, msg);
}

void DiagnosticsEngine::warning(SourceLocation loc, const std::string& msg) {
  addDiagnostic(DiagnosticLevel::Warning, loc, msg);
}

void DiagnosticsEngine::note(SourceLocation loc, const std::string& msg) {
  addDiagnostic(DiagnosticLevel::Note, loc, msg);
}

void DiagnosticsEngine::fatal(SourceLocation loc, const std::string& msg) {
  addDiagnostic(DiagnosticLevel::Fatal, loc, msg);
}

void DiagnosticsEngine::addDiagnostic(DiagnosticLevel level, 
                                       SourceLocation loc, 
                                       const std::string& msg) {
  Diags.emplace_back(level, loc, msg);
  
  switch (level) {
    case DiagnosticLevel::Error:
      ErrorCount++;
      break;
    case DiagnosticLevel::Warning:
      WarningCount++;
      break;
    case DiagnosticLevel::Fatal:
      ErrorCount++;
      break;
    default:
      break;
  }
}

llvm::StringRef DiagnosticsEngine::getLevelPrefix(DiagnosticLevel level) const {
  switch (level) {
    case DiagnosticLevel::Note:    return "提示";
    case DiagnosticLevel::Warning: return "警告";
    case DiagnosticLevel::Error:   return "错误";
    case DiagnosticLevel::Fatal:   return "致命错误";
    default:                       return "未知";
  }
}

void DiagnosticsEngine::clear() {
  Diags.clear();
  ErrorCount = 0;
  WarningCount = 0;
}

void DiagnosticsEngine::printAll(llvm::raw_ostream& os) const {
  for (const auto& diag : Diags) {
    os << getLevelPrefix(diag.Level) << ": ";
    if (diag.Loc.isValid()) {
      os << "第 " << diag.Loc.Line << " 行，第 " << diag.Loc.Column << " 列: ";
    }
    os << diag.Message << "\n";
    
    if (!diag.Hint.empty()) {
      os << "  建议: " << diag.Hint << "\n";
    }
  }
}

} // namespace zhc