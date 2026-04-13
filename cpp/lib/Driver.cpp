//===--- Driver.cpp - ZhC Compiler Driver Implementation -----------------===//
//
// This file implements the compiler driver for the ZhC compiler.
//
//===----------------------------------------------------------------------===//

#include "zhc/Driver.h"
#include "zhc/Lexer.h"
#include "zhc/Diagnostics.h"
#include "zhc/SourceManager.h"

#include "llvm/Support/raw_ostream.h"

namespace zhc {

Driver::Driver(const CompileOptions& opts) : Opts(opts) {}

bool Driver::compile(const std::string& inputPath) {
  return compileSource(inputPath);
}

bool Driver::compileSource(const std::string& path) {
  // Load source file
  uint32_t fileID = SourceMgr.loadFile(path);
  if (fileID == 0) {
    DiagEngine.report(SourceLocation(), DiagID::fatal_cannot_open_file, {path});
    return false;
  }
  
  llvm::StringRef source = SourceMgr.getSource(fileID);
  
  // Create lexer
  Lexer lexer(source, fileID);
  
  // If -dump-tokens, just dump tokens
  if (Opts.PrintTokens) {
    while (true) {
      Token tok = lexer.lexNext();
      llvm::outs() << getTokenKindName(tok.Kind);
      if (!tok.Spelling.empty()) {
        llvm::outs() << " '" << tok.Spelling << "'";
      }
      llvm::outs() << "\n";
      if (tok.isEOF()) break;
    }
    return true;
  }
  
  // TODO: Parser, Semantic Analysis, IR Generation, Backend
  // For now, just lex and report success if no errors
  
  while (true) {
    Token tok = lexer.lexNext();
    if (tok.isEOF()) break;
    
    if (tok.Kind == TokenKind::unknown) {
DiagEngine.report(lexer.getCurrentLocation(), DiagID::err_unknown_character,
                     {tok.Spelling.str()});
    }
  }
  
  return !DiagEngine.hasErrors();
}

} // namespace zhc