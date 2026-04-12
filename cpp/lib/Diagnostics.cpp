//===--- Diagnostics.cpp - ZhC Diagnostic Engine Implementation ----------===//
//
// This file implements the enhanced diagnostic engine for the ZhC compiler.
//
//===----------------------------------------------------------------------===//

#include "zhc/Diagnostics.h"
#include "zhc/SourceManager.h"

#include "llvm/Support/raw_ostream.h"

namespace zhc {

DiagnosticsEngine::DiagnosticsEngine() = default;

Diagnostic& DiagnosticsEngine::error(SourceLocation loc, const std::string& msg) {
  return addDiagnostic(DiagnosticLevel::Error, loc, msg);
}

Diagnostic& DiagnosticsEngine::warning(SourceLocation loc, const std::string& msg) {
  return addDiagnostic(DiagnosticLevel::Warning, loc, msg);
}

Diagnostic& DiagnosticsEngine::note(SourceLocation loc, const std::string& msg) {
  return addDiagnostic(DiagnosticLevel::Note, loc, msg);
}

Diagnostic& DiagnosticsEngine::fatal(SourceLocation loc, const std::string& msg) {
  return addDiagnostic(DiagnosticLevel::Fatal, loc, msg);
}

Diagnostic& DiagnosticsEngine::addDiagnostic(DiagnosticLevel level,
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

  return Diags.back();
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

const char* DiagnosticsEngine::getLevelColor(DiagnosticLevel level) const {
  if (!UseColor) return "";
  switch (level) {
    case DiagnosticLevel::Note:    return "\033[36m";    // Cyan
    case DiagnosticLevel::Warning: return "\033[33m";    // Yellow
    case DiagnosticLevel::Error:   return "\033[31m";    // Red
    case DiagnosticLevel::Fatal:   return "\033[1;31m";  // Bold Red
    default:                       return "";
  }
}

const char* DiagnosticsEngine::getResetColor() const {
  return UseColor ? "\033[0m" : "";
}

void DiagnosticsEngine::clear() {
  Diags.clear();
  ErrorCount = 0;
  WarningCount = 0;
}

void DiagnosticsEngine::printAll(llvm::raw_ostream& os) const {
  for (const auto& diag : Diags) {
    printDiagnostic(os, diag);
  }

  // Summary
  if (ErrorCount > 0 || WarningCount > 0) {
    os << "\n";
    if (ErrorCount > 0) {
      os << ErrorCount << " 个错误";
      if (WarningCount > 0) os << "，";
    }
    if (WarningCount > 0) {
      os << WarningCount << " 个警告";
    }
    os << "。\n";
  }
}

void DiagnosticsEngine::printDiagnostic(llvm::raw_ostream& os,
                                         const Diagnostic& diag) const {
  // Print location and severity
  os << getLevelColor(diag.Level);

  if (diag.Loc.isValid() && SrcMgr) {
    os << SrcMgr->getLocationString(diag.Loc) << ": ";
  }

  os << getLevelPrefix(diag.Level) << ": " << diag.Message;
  os << getResetColor() << "\n";

  // Print source line if available
  if (diag.Loc.isValid() && SrcMgr) {
    llvm::StringRef line = SrcMgr->getLine(diag.Loc);
    if (!line.empty()) {
      // Trim trailing newline
      auto trimmed = line.rtrim("\r\n");
      os << "  " << trimmed << "\n";

      // Print caret pointing to the column
      uint32_t col = SrcMgr->getColumnUTF8(diag.Loc);
      if (col > 0) {
        os << "  ";
        for (uint32_t i = 1; i < col; ++i) {
          os << " ";
        }
        os << getLevelColor(diag.Level) << "^" << getResetColor() << "\n";
      }
    }
  }

  // Print fix-it hints
  for (const auto& hint : diag.Hints) {
    os << "  建议: ";
    if (hint.Start == hint.End) {
      // Insertion
      os << "在 第 " << hint.Start.Line << " 行，第 " << hint.Start.Column
         << " 列 插入 '" << hint.Replacement << "'";
    } else if (hint.Replacement.empty()) {
      // Removal
      os << "删除 第 " << hint.Start.Line << " 行，第 " << hint.Start.Column
         << " 列 到 第 " << hint.End.Column << " 列";
    } else {
      // Replacement
      os << "将 第 " << hint.Start.Line << " 行，第 " << hint.Start.Column
         << " 列 替换为 '" << hint.Replacement << "'";
    }
    os << "\n";
  }
}

} // namespace zhc
