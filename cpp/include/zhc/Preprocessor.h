//===--- Preprocessor.h - ZhC Preprocessor Interface --------------------===//
//
// This file defines the Preprocessor interface for the ZhC compiler.
// Supports #define, #ifdef, #ifndef, #if, #elif, #else, #endif,
// #include, #pragma once, and built-in macros.
//
//===----------------------------------------------------------------------===//

#ifndef ZHC_PREPROCESSOR_H
#define ZHC_PREPROCESSOR_H

#include "zhc/Common.h"
#include "zhc/Diagnostics.h"
#include "zhc/SourceManager.h"

#include "llvm/ADT/StringMap.h"
#include "llvm/ADT/StringRef.h"

#include <memory>
#include <set>
#include <stack>
#include <string>
#include <vector>

namespace zhc {

/// Macro type enumeration
enum class MacroType {
  Object,    // #define NAME value
  Function   // #define NAME(args) body
};

/// Macro definition
struct Macro {
  std::string Name;
  std::string Body;
  MacroType Type = MacroType::Object;
  std::vector<std::string> Parameters;
  bool IsVariadic = false;
  SourceLocation DefinitionLoc;
  
  Macro() = default;
  Macro(std::string name, std::string body, MacroType type = MacroType::Object)
      : Name(std::move(name)), Body(std::move(body)), Type(type) {}
};

/// Preprocessor configuration
struct PreprocessorConfig {
  std::vector<std::string> IncludePaths;      // -I paths
  std::string StdlibPath;                      // Standard library path
  llvm::StringMap<std::string> PredefinedMacros;  // -D macros
  unsigned MaxIncludeDepth = 100;              // Maximum #include nesting
  unsigned MaxMacroDepth = 100;                // Maximum macro expansion depth
};

/// Preprocessor - handles preprocessing directives
class Preprocessor {
public:
  /// Construct a preprocessor with the given configuration
  Preprocessor(const PreprocessorConfig& config, 
               SourceManager& sm, 
               DiagnosticsEngine& diags);
  
  /// Process a source file and return the preprocessed content
  std::string process(uint32_t fileID);
  
  /// Process source text directly (for testing)
  std::string processText(llvm::StringRef source, 
                          const std::string& filename = "<input>");
  
  /// Define a macro programmatically
  void defineMacro(const std::string& name, const std::string& value);
  
  /// Undefine a macro
  void undefMacro(const std::string& name);
  
  /// Check if a macro is defined
  bool isMacroDefined(const std::string& name) const;
  
  /// Get a macro definition (returns nullptr if not defined)
  const Macro* getMacro(const std::string& name) const;
  
  /// Get all defined macros
  const llvm::StringMap<std::unique_ptr<Macro>>& getMacros() const { 
    return Macros; 
  }
  
  /// Get the set of included files (absolute paths)
  const std::set<std::string>& getIncludedFiles() const { 
    return IncludedFiles; 
  }

private:
  PreprocessorConfig Config;
  SourceManager& SrcMgr;
  DiagnosticsEngine& Diags;
  
  // Macro table
  llvm::StringMap<std::unique_ptr<Macro>> Macros;
  
  // Include tracking
  std::set<std::string> IncludedFiles;     // Files already included (#pragma once)
  std::vector<std::string> IncludeStack;   // Current include stack
  
  // Current processing state
  std::string CurrentFile;
  uint32_t CurrentLine = 0;
  uint32_t CurrentFileID = 0;
  
  // Initialize built-in macros
  void initBuiltinMacros();
  
  // Define an object macro
  void defineObjectMacro(const std::string& name, const std::string& value,
                         SourceLocation loc = SourceLocation());
  
  // Define a function macro
  void defineFunctionMacro(const std::string& name, 
                           const std::vector<std::string>& params,
                           const std::string& body,
                           bool isVariadic = false,
                           SourceLocation loc = SourceLocation());
  
  // Parse a #define directive
  std::unique_ptr<Macro> parseDefine(llvm::StringRef content);
  
  // Expand a macro
  std::string expandMacro(const std::string& name, 
                          const std::vector<std::string>& args = {},
                          unsigned depth = 0);
  
  // Expand all macros in text
  std::string expandText(llvm::StringRef text, unsigned depth = 0);
  
  // Parse macro arguments from text starting at '('
  std::vector<std::string> parseMacroArgs(llvm::StringRef text, size_t start, 
                                           size_t& endPos);
  
  // Evaluate a preprocessor condition (#if, #elif)
  bool evaluateCondition(llvm::StringRef condition);
  
  // Evaluate a simple integer expression
  int evaluateSimpleExpression(llvm::StringRef expr);
  
  // Process an #include directive
  std::string processInclude(llvm::StringRef content);
  
  // Parse include path from directive content
  std::pair<std::string, bool> parseIncludePath(llvm::StringRef content);
  
  // Find an include file in search paths
  std::string findIncludeFile(const std::string& filename, bool isSystem);
  
  // Check if file has #pragma once
  bool checkPragmaOnce(const std::string& filepath);
  
  // Process a single line
  std::string processLine(llvm::StringRef line);
  
  // Split source into lines
  std::vector<llvm::StringRef> splitLines(llvm::StringRef source);
};

} // namespace zhc

#endif // ZHC_PREPROCESSOR_H
