//===--- main.cpp - ZhC Compiler Driver Entry Point ----------------------===//
//
// This file implements the main entry point for the ZhC compiler.
//
//===----------------------------------------------------------------------===//

#include "zhc/Driver.h"
#include "zhc/Lexer.h"
#include "zhc/Diagnostics.h"
#include "zhc/SourceManager.h"

#include "llvm/Support/CommandLine.h"
#include "llvm/Support/InitLLVM.h"
#include "llvm/Support/raw_ostream.h"

using namespace zhc;

static llvm::cl::opt<std::string> InputFilename(
    llvm::cl::Positional, llvm::cl::desc("<input file>"), llvm::cl::Required);

static llvm::cl::opt<std::string> OutputFilename(
    "o", llvm::cl::desc("Output filename"), llvm::cl::value_desc("filename"));

static llvm::cl::opt<bool> DumpTokens(
    "dump-tokens", llvm::cl::desc("Dump lexer tokens"));

static llvm::cl::opt<bool> PrintAST(
    "ast-print", llvm::cl::desc("Print the AST"));

static llvm::cl::opt<bool> EmitLLVM(
    "emit-llvm", llvm::cl::desc("Emit LLVM IR"));

int main(int argc, const char** argv) {
  llvm::InitLLVM X(argc, argv);
  
  llvm::cl::ParseCommandLineOptions(argc, argv, "ZhC - 中文C编译器\n");
  
  CompileOptions opts;
  opts.OutputFile = OutputFilename;
  opts.PrintTokens = DumpTokens;
  opts.PrintAST = PrintAST;
  opts.PrintIR = EmitLLVM;
  
  // Quick test: if -dump-tokens, just lex and dump
  if (DumpTokens) {
    SourceManager srcMgr;
    uint32_t fileID = srcMgr.loadFile(InputFilename);
    
    if (fileID == 0) {
      llvm::errs() << "错误: 无法打开文件 '" << InputFilename << "'\n";
      return 1;
    }
    
    Lexer lexer(srcMgr.getSource(fileID), fileID);
    
    while (true) {
      Token tok = lexer.lexNext();
      
      llvm::outs() << getTokenKindName(tok.Kind);
      
      if (!tok.Spelling.empty()) {
        llvm::outs() << " '" << tok.Spelling << "'";
      }
      
      SourceLocation loc = lexer.getCurrentLocation();
      llvm::outs() << " 第" << loc.Line << "行 第" << loc.Column << "列\n";
      
      if (tok.isEOF()) break;
    }
    
    return 0;
  }
  
  // Full compilation
  Driver driver(opts);
  bool success = driver.compile(InputFilename);
  
  driver.getDiagnostics().printAll(llvm::errs());
  
  return success ? 0 : 1;
}