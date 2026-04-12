//===--- Preprocessor.cpp - ZhC Preprocessor Implementation -------------===//
//
// Implementation of the ZhC preprocessor.
// Supports #define, #ifdef, #ifndef, #if, #elif, #else, #endif,
// #include, #pragma once, and built-in macros.
//
//===----------------------------------------------------------------------===//

#include "zhc/Preprocessor.h"

#include "llvm/ADT/SmallString.h"
#include "llvm/Support/FileSystem.h"
#include "llvm/Support/Path.h"
#include "llvm/Support/raw_ostream.h"

#include <algorithm>
#include <cctype>
#include <chrono>
#include <ctime>
#include <fstream>
#include <regex>
#include <sstream>

namespace zhc {

namespace {

/// Trim whitespace from both ends of a string
static std::string trimString(const std::string& s) {
  size_t start = s.find_first_not_of(" \t\r\n");
  if (start == std::string::npos) return "";
  size_t end = s.find_last_not_of(" \t\r\n");
  return s.substr(start, end - start + 1);
}

} // anonymous namespace

//===----------------------------------------------------------------------===//
// Constructor and Initialization
//===----------------------------------------------------------------------===//

Preprocessor::Preprocessor(const PreprocessorConfig& config,
                           SourceManager& sm,
                           DiagnosticsEngine& diags)
    : Config(config), SrcMgr(sm), Diags(diags) {
  initBuiltinMacros();
  
  // Initialize user-defined macros from config
  for (auto& entry : Config.PredefinedMacros) {
    defineObjectMacro(std::string(entry.getKey()), std::string(entry.getValue()));
  }
}

void Preprocessor::initBuiltinMacros() {
  // ZhC version macros
  defineObjectMacro("__ZHC__", "1");
  defineObjectMacro("__ZHC_VERSION__", "\"0.1.0\"");
  defineObjectMacro("__ZHC_MAJOR__", "0");
  defineObjectMacro("__ZHC_MINOR__", "1");
  defineObjectMacro("__ZHC_PATCH__", "0");
  
  // Standard preprocessor macros (will be updated during processing)
  defineObjectMacro("__FILE__", "\"<input>\"");
  defineObjectMacro("__LINE__", "0");
  
  // Date and time macros
  auto now = std::chrono::system_clock::now();
  auto time = std::chrono::system_clock::to_time_t(now);
  std::tm* tm = std::localtime(&time);
  
  char dateBuf[32];
  char timeBuf[32];
  std::strftime(dateBuf, sizeof(dateBuf), "\"%Y-%m-%d\"", tm);
  std::strftime(timeBuf, sizeof(timeBuf), "\"%H:%M:%S\"", tm);
  
  defineObjectMacro("__DATE__", dateBuf);
  defineObjectMacro("__TIME__", timeBuf);
}

//===----------------------------------------------------------------------===//
// Macro Definition
//===----------------------------------------------------------------------===//

void Preprocessor::defineMacro(const std::string& name, const std::string& value) {
  defineObjectMacro(name, value);
}

void Preprocessor::defineObjectMacro(const std::string& name, 
                                      const std::string& value,
                                      SourceLocation loc) {
  auto macro = std::make_unique<Macro>(name, value, MacroType::Object);
  macro->DefinitionLoc = loc;
  Macros[name] = std::move(macro);
}

void Preprocessor::defineFunctionMacro(const std::string& name,
                                        const std::vector<std::string>& params,
                                        const std::string& body,
                                        bool isVariadic,
                                        SourceLocation loc) {
  auto macro = std::make_unique<Macro>(name, body, MacroType::Function);
  macro->Parameters = params;
  macro->IsVariadic = isVariadic;
  macro->DefinitionLoc = loc;
  Macros[name] = std::move(macro);
}

void Preprocessor::undefMacro(const std::string& name) {
  Macros.erase(name);
}

bool Preprocessor::isMacroDefined(const std::string& name) const {
  return Macros.find(name) != Macros.end();
}

const Macro* Preprocessor::getMacro(const std::string& name) const {
  auto it = Macros.find(name);
  return it != Macros.end() ? it->second.get() : nullptr;
}

//===----------------------------------------------------------------------===//
// #define Parsing
//===----------------------------------------------------------------------===//

std::unique_ptr<Macro> Preprocessor::parseDefine(llvm::StringRef content) {
  // Remove trailing comments
  content = content.take_until([](char c) { return c == '/' && c == '/'; });
  content = content.trim();
  
  // Check for function macro: NAME(args) body
  size_t parenPos = content.find('(');
  if (parenPos != llvm::StringRef::npos) {
    // Check if '(' is immediately after the name (no space)
    size_t nameEnd = parenPos;
    llvm::StringRef namePart = content.take_front(nameEnd);
    
    // If there's a space before '(', it's an object macro with '(' in body
    if (namePart.rfind(' ') != llvm::StringRef::npos) {
      // Object macro with '(' in body
      size_t spacePos = content.find(' ');
      std::string name = content.take_front(spacePos).str();
      std::string body = content.drop_front(spacePos).trim().str();
      return std::make_unique<Macro>(name, body, MacroType::Object);
    }
    
    // Function macro
    std::string name = content.take_front(parenPos).str();
    
    // Find closing paren
    size_t endParen = content.find(')', parenPos);
    if (endParen == llvm::StringRef::npos) {
      Diags.error(SourceLocation(CurrentLine, 1, CurrentFileID), 
                  "宏定义缺少右括号: " + name);
      return nullptr;
    }
    
    // Parse parameters
    llvm::StringRef paramsStr = content.slice(parenPos + 1, endParen).trim();
    std::vector<std::string> params;
    bool isVariadic = false;
    
    if (!paramsStr.empty()) {
      // Split by comma
      llvm::SmallVector<llvm::StringRef, 8> paramParts;
      paramsStr.split(paramParts, ',', -1, false);
      
      for (auto& part : paramParts) {
        std::string param = part.trim().str();
        if (param == "...") {
          isVariadic = true;
        } else if (param.ends_with("...")) {
          // Named variadic parameter (e.g., args...)
          isVariadic = true;
          param = param.substr(0, param.size() - 3);
          params.push_back(param);
        } else {
          params.push_back(param);
        }
      }
    }
    
    // Body is everything after ')'
    std::string body = content.drop_front(endParen + 1).trim().str();
    
    auto macro = std::make_unique<Macro>(name, body, MacroType::Function);
    macro->Parameters = params;
    macro->IsVariadic = isVariadic;
    return macro;
  }
  
  // Object macro: NAME value
  size_t spacePos = content.find(' ');
  if (spacePos == llvm::StringRef::npos) {
    // Macro without body
    return std::make_unique<Macro>(content.str(), "", MacroType::Object);
  }
  
  std::string name = content.take_front(spacePos).str();
  std::string body = content.drop_front(spacePos).trim().str();
  return std::make_unique<Macro>(name, body, MacroType::Object);
}

//===----------------------------------------------------------------------===//
// Macro Expansion
//===----------------------------------------------------------------------===//

std::string Preprocessor::expandMacro(const std::string& name,
                                       const std::vector<std::string>& args,
                                       unsigned depth) {
  if (depth > Config.MaxMacroDepth) {
    Diags.error(SourceLocation(CurrentLine, 1, CurrentFileID),
                "宏展开深度超过限制: " + name);
    return name;
  }
  
  const Macro* macro = getMacro(name);
  if (!macro) {
    return name;
  }
  
  if (macro->Type == MacroType::Object) {
    // Object macro: direct substitution with recursive expansion
    return expandText(macro->Body, depth + 1);
  }
  
  if (macro->Type == MacroType::Function) {
    if (args.empty()) {
      // Function macro without arguments - return as-is
      return name;
    }
    
    // Function macro: parameter substitution
    std::string body = macro->Body;
    
    // Build parameter map
    llvm::StringMap<std::string> paramMap;
    for (size_t i = 0; i < macro->Parameters.size() && i < args.size(); ++i) {
      paramMap[macro->Parameters[i]] = args[i];
    }
    
    // Handle variadic arguments
    if (macro->IsVariadic && args.size() > macro->Parameters.size()) {
      std::string vaArgs;
      for (size_t i = macro->Parameters.size(); i < args.size(); ++i) {
        if (i > macro->Parameters.size()) vaArgs += ", ";
        vaArgs += args[i];
      }
      paramMap["__VA_ARGS__"] = vaArgs;
    }
    
    // Substitute parameters (word boundary matching)
    std::string result;
    size_t i = 0;
    while (i < body.size()) {
      // Check for identifier
      if (std::isalpha(body[i]) || body[i] == '_') {
        size_t start = i;
        while (i < body.size() && (std::isalnum(body[i]) || body[i] == '_')) {
          ++i;
        }
        std::string ident = body.substr(start, i - start);
        
        // Check if it's a parameter
        auto it = paramMap.find(ident);
        if (it != paramMap.end()) {
          result += it->second;
        } else {
          result += ident;
        }
      } else {
        result += body[i];
        ++i;
      }
    }
    
    // Recursive expansion
    return expandText(result, depth + 1);
  }
  
  return name;
}

std::string Preprocessor::expandText(llvm::StringRef text, unsigned depth) {
  if (depth > Config.MaxMacroDepth) {
    return text.str();
  }
  
  std::string result;
  size_t i = 0;
  
  while (i < text.size()) {
    // Check for string literal (don't expand macros inside strings)
    if (text[i] == '"' || text[i] == '\'') {
      char quote = text[i];
      result += quote;
      ++i;
      while (i < text.size() && text[i] != quote) {
        if (text[i] == '\\' && i + 1 < text.size()) {
          result += text[i];
          result += text[i + 1];
          i += 2;
        } else {
          result += text[i];
          ++i;
        }
      }
      if (i < text.size()) {
        result += text[i];  // Closing quote
        ++i;
      }
      continue;
    }
    
    // Check for identifier
    if (std::isalpha(text[i]) || text[i] == '_') {
      size_t start = i;
      while (i < text.size() && (std::isalnum(text[i]) || text[i] == '_')) {
        ++i;
      }
      std::string ident = text.substr(start, i - start).str();
      
      // Check if it's a macro
      const Macro* macro = getMacro(ident);
      if (macro) {
        if (macro->Type == MacroType::Function) {
          // Check for argument list
          if (i < text.size() && text[i] == '(') {
            std::vector<std::string> args;
            size_t endPos;
            args = parseMacroArgs(text, i, endPos);
            std::string expanded = expandMacro(ident, args, depth);
            result += expanded;
            i = endPos;
          } else {
            // Function macro without args - keep as-is
            result += ident;
          }
        } else {
          // Object macro
          std::string expanded = expandMacro(ident, {}, depth);
          result += expanded;
        }
      } else {
        result += ident;
      }
    } else {
      result += text[i];
      ++i;
    }
  }
  
  return result;
}

std::vector<std::string> Preprocessor::parseMacroArgs(llvm::StringRef text,
                                                       size_t start,
                                                       size_t& endPos) {
  assert(text[start] == '(');
  
  std::vector<std::string> args;
  std::string currentArg;
  int parenDepth = 1;
  size_t i = start + 1;
  
  while (i < text.size() && parenDepth > 0) {
    char c = text[i];
    
    if (c == '(') {
      ++parenDepth;
      currentArg += c;
    } else if (c == ')') {
      --parenDepth;
      if (parenDepth > 0) {
        currentArg += c;
      }
    } else if (c == ',' && parenDepth == 1) {
      args.push_back(trimString(currentArg));
      currentArg.clear();
    } else {
      currentArg += c;
    }
    
    ++i;
  }
  
  // Add last argument
  if (!currentArg.empty() || !args.empty()) {
    args.push_back(trimString(currentArg));
  }
  
  endPos = i;
  return args;
}

//===----------------------------------------------------------------------===//
// Condition Evaluation
//===----------------------------------------------------------------------===//

bool Preprocessor::evaluateCondition(llvm::StringRef condition) {
  condition = condition.trim();
  
  // Handle defined() operator
  std::string processed;
  size_t i = 0;
  while (i < condition.size()) {
    if (condition.substr(i).starts_with("defined")) {
      i += 7;  // Skip "defined"
      
      // Skip whitespace
      while (i < condition.size() && std::isspace(condition[i])) ++i;
      
      // Expect '('
      if (i < condition.size() && condition[i] == '(') {
        ++i;
        // Skip whitespace
        while (i < condition.size() && std::isspace(condition[i])) ++i;
        
        // Read identifier
        size_t start = i;
        while (i < condition.size() && (std::isalnum(condition[i]) || condition[i] == '_')) {
          ++i;
        }
        std::string name = condition.substr(start, i - start).str();
        
        // Skip whitespace
        while (i < condition.size() && std::isspace(condition[i])) ++i;
        
        // Expect ')'
        if (i < condition.size() && condition[i] == ')') {
          ++i;
          processed += isMacroDefined(name) ? "1" : "0";
          continue;
        }
      }
      
      // defined without parens - read identifier directly
      size_t start = i;
      while (i < condition.size() && (std::isalnum(condition[i]) || condition[i] == '_')) {
        ++i;
      }
      std::string name = condition.substr(start, i - start).str();
      processed += isMacroDefined(name) ? "1" : "0";
      continue;
    }
    
    processed += condition[i];
    ++i;
  }
  
  // Expand macros in the condition
  processed = expandText(processed);
  
  // Evaluate the expression
  try {
    int result = evaluateSimpleExpression(processed);
    return result != 0;
  } catch (...) {
    return false;
  }
}

int Preprocessor::evaluateSimpleExpression(llvm::StringRef expr) {
  expr = expr.trim();
  
  // Remove all whitespace for easier parsing
  std::string compact;
  for (char c : expr) {
    if (!std::isspace(c)) {
      compact += c;
    }
  }
  
  // Handle C preprocessor !0 = 1, !1 = 0
  {
    std::string temp;
    size_t i = 0;
    while (i < compact.size()) {
      if (compact[i] == '!' && i + 1 < compact.size() && 
          (compact[i + 1] == '0' || compact[i + 1] == '1')) {
        temp += (compact[i + 1] == '1') ? '0' : '1';
        i += 2;
      } else {
        temp += compact[i];
        ++i;
      }
    }
    compact = temp;
  }
  
  // Convert C operators to Python-style for evaluation
  // && -> and, || -> or
  compact = std::regex_replace(compact, std::regex("&&"), " and ");
  compact = std::regex_replace(compact, std::regex("\\|\\|"), " or ");
  
  // Add spaces around comparison operators
  compact = std::regex_replace(compact, std::regex("=="), " == ");
  compact = std::regex_replace(compact, std::regex("!="), " != ");
  compact = std::regex_replace(compact, std::regex("<="), " <= ");
  compact = std::regex_replace(compact, std::regex(">="), " >= ");
  compact = std::regex_replace(compact, std::regex("<([^<=])"), " < $1");
  compact = std::regex_replace(compact, std::regex(">([^>=])"), " > $1");
  
  // Safety check: only allow safe characters
  std::string safeChars = "0123456789 +-*/%<>=!&|()andor";
  for (char c : compact) {
    if (safeChars.find(c) == std::string::npos && c != ' ') {
      throw std::runtime_error("Unsafe expression");
    }
  }
  
  // Simple expression evaluation
  // For now, use a basic recursive descent parser
  // This is safer than using eval
  
  // Handle parentheses first
  // For simplicity, we'll use a stack-based evaluator
  
  std::istringstream iss(compact);
  std::vector<std::string> tokens;
  std::string token;
  while (iss >> token) {
    tokens.push_back(token);
  }
  
  // Very simple expression evaluator
  // Handles: numbers, comparisons, logical ops
  // For a full implementation, we'd need a proper parser
  
  // For now, just handle simple numeric expressions
  if (tokens.empty()) return 0;
  
  // Try to parse as a simple number
  if (tokens.size() == 1) {
    try {
      return std::stoi(tokens[0]);
    } catch (...) {
      return 0;
    }
  }
  
  // Handle comparison operators
  for (size_t i = 0; i < tokens.size() - 2; ++i) {
    if (tokens[i + 1] == "==") {
      int left = std::stoi(tokens[i]);
      int right = std::stoi(tokens[i + 2]);
      return left == right ? 1 : 0;
    }
    if (tokens[i + 1] == "!=") {
      int left = std::stoi(tokens[i]);
      int right = std::stoi(tokens[i + 2]);
      return left != right ? 1 : 0;
    }
    if (tokens[i + 1] == "<") {
      int left = std::stoi(tokens[i]);
      int right = std::stoi(tokens[i + 2]);
      return left < right ? 1 : 0;
    }
    if (tokens[i + 1] == ">") {
      int left = std::stoi(tokens[i]);
      int right = std::stoi(tokens[i + 2]);
      return left > right ? 1 : 0;
    }
    if (tokens[i + 1] == "<=") {
      int left = std::stoi(tokens[i]);
      int right = std::stoi(tokens[i + 2]);
      return left <= right ? 1 : 0;
    }
    if (tokens[i + 1] == ">=") {
      int left = std::stoi(tokens[i]);
      int right = std::stoi(tokens[i + 2]);
      return left >= right ? 1 : 0;
    }
  }
  
  // Handle logical operators
  for (size_t i = 0; i < tokens.size() - 2; ++i) {
    if (tokens[i + 1] == "and") {
      int left = std::stoi(tokens[i]);
      int right = std::stoi(tokens[i + 2]);
      return (left && right) ? 1 : 0;
    }
    if (tokens[i + 1] == "or") {
      int left = std::stoi(tokens[i]);
      int right = std::stoi(tokens[i + 2]);
      return (left || right) ? 1 : 0;
    }
  }
  
  // Handle arithmetic operators
  for (size_t i = 0; i < tokens.size() - 2; ++i) {
    if (tokens[i + 1] == "+") {
      return std::stoi(tokens[i]) + std::stoi(tokens[i + 2]);
    }
    if (tokens[i + 1] == "-") {
      return std::stoi(tokens[i]) - std::stoi(tokens[i + 2]);
    }
    if (tokens[i + 1] == "*") {
      return std::stoi(tokens[i]) * std::stoi(tokens[i + 2]);
    }
    if (tokens[i + 1] == "/") {
      int right = std::stoi(tokens[i + 2]);
      if (right == 0) return 0;
      return std::stoi(tokens[i]) / right;
    }
  }
  
  return 0;
}

//===----------------------------------------------------------------------===//
// #include Processing
//===----------------------------------------------------------------------===//

std::pair<std::string, bool> Preprocessor::parseIncludePath(llvm::StringRef content) {
  content = content.trim();
  
  // #include <file> - system header
  if (content.starts_with("<") && content.ends_with(">")) {
    return {content.drop_front(1).drop_back().str(), true};
  }
  
  // #include "file" - local header
  if (content.starts_with("\"") && content.ends_with("\"")) {
    return {content.drop_front(1).drop_back().str(), false};
  }
  
  Diags.error(SourceLocation(CurrentLine, 1, CurrentFileID),
              "无效的 #include 语法: " + content.str());
  return {"", false};
}

std::string Preprocessor::findIncludeFile(const std::string& filename, 
                                           bool isSystem) {
  std::vector<std::string> searchPaths;
  
  if (!isSystem) {
    // Local header: search current file's directory first
    if (!CurrentFile.empty() && CurrentFile != "<input>") {
      llvm::SmallString<256> currentDir(CurrentFile);
      llvm::sys::path::remove_filename(currentDir);
      searchPaths.push_back(std::string(currentDir.str()));
    }
  }
  
  // Add -I paths
  searchPaths.insert(searchPaths.end(), 
                     Config.IncludePaths.begin(), 
                     Config.IncludePaths.end());
  
  // Add stdlib path
  if (!Config.StdlibPath.empty()) {
    searchPaths.push_back(Config.StdlibPath);
  }
  
  // Search for file
  for (const std::string& path : searchPaths) {
    llvm::SmallString<256> fullPath(path);
    llvm::sys::path::append(fullPath, filename);
    
    if (llvm::sys::fs::exists(fullPath)) {
      return std::string(fullPath.str());
    }
  }
  
  return "";  // Not found
}

bool Preprocessor::checkPragmaOnce(const std::string& filepath) {
  // Check if file is already in IncludedFiles set
  return IncludedFiles.find(filepath) != IncludedFiles.end();
}

std::string Preprocessor::processInclude(llvm::StringRef content) {
  // Check include depth
  if (IncludeStack.size() >= Config.MaxIncludeDepth) {
    Diags.error(SourceLocation(CurrentLine, 1, CurrentFileID),
                "#include 嵌套深度超过限制");
    return "";
  }
  
  // Parse path
  auto [filename, isSystem] = parseIncludePath(content);
  if (filename.empty()) {
    return "";
  }
  
  // Find file
  std::string filepath = findIncludeFile(filename, isSystem);
  if (filepath.empty()) {
    Diags.error(SourceLocation(CurrentLine, 1, CurrentFileID),
                "找不到头文件: " + filename);
    return "";
  }
  
  // Check for circular include
  if (std::find(IncludeStack.begin(), IncludeStack.end(), filepath) 
      != IncludeStack.end()) {
    Diags.error(SourceLocation(CurrentLine, 1, CurrentFileID),
                "循环包含: " + filename);
    return "";
  }
  
  // Check #pragma once
  if (checkPragmaOnce(filepath)) {
    return "";  // Already included, skip
  }
  
  // Mark as included
  IncludedFiles.insert(filepath);
  IncludeStack.push_back(filepath);
  
  // Save current state
  std::string oldFile = CurrentFile;
  uint32_t oldLine = CurrentLine;
  uint32_t oldFileID = CurrentFileID;
  
  // Load and process file
  uint32_t fileID = SrcMgr.loadFile(filepath);
  if (fileID == 0) {
    Diags.error(SourceLocation(CurrentLine, 1, CurrentFileID),
                "无法读取头文件: " + filename);
    IncludeStack.pop_back();
    CurrentFile = oldFile;
    CurrentLine = oldLine;
    CurrentFileID = oldFileID;
    return "";
  }
  
  std::string result = process(fileID);
  
  // Restore state
  IncludeStack.pop_back();
  CurrentFile = oldFile;
  CurrentLine = oldLine;
  CurrentFileID = oldFileID;
  
  return result;
}

//===----------------------------------------------------------------------===//
// Main Processing
//===----------------------------------------------------------------------===//

std::vector<llvm::StringRef> Preprocessor::splitLines(llvm::StringRef source) {
  std::vector<llvm::StringRef> lines;
  size_t start = 0;
  size_t end = source.find('\n');
  
  while (end != llvm::StringRef::npos) {
    lines.push_back(source.slice(start, end));
    start = end + 1;
    end = source.find('\n', start);
  }
  
  // Last line (without trailing newline)
  if (start < source.size()) {
    lines.push_back(source.substr(start));
  }
  
  return lines;
}

std::string Preprocessor::process(uint32_t fileID) {
  llvm::StringRef source = SrcMgr.getSource(fileID);
  const FileInfo* info = SrcMgr.getFileInfo(fileID);
  
  CurrentFileID = fileID;
  CurrentFile = info ? info->Path : "<unknown>";
  CurrentLine = 0;
  
  // Update __FILE__ macro
  std::string fileMacroValue = "\"" + CurrentFile + "\"";
  defineObjectMacro("__FILE__", fileMacroValue);
  
  // Condition compilation stack: (isActive, hasSatisfied)
  std::stack<std::pair<bool, bool>> conditionStack;
  
  std::vector<llvm::StringRef> lines = splitLines(source);
  std::ostringstream output;
  
  for (size_t i = 0; i < lines.size(); ++i) {
    CurrentLine = static_cast<uint32_t>(i + 1);
    
    // Update __LINE__ macro
    defineObjectMacro("__LINE__", std::to_string(CurrentLine));
    
    llvm::StringRef line = lines[i];
    llvm::StringRef stripped = line.trim();
    
    // Check if in active branch
    bool inActiveBranch = true;
    std::stack<std::pair<bool, bool>> tempStack = conditionStack;
    while (!tempStack.empty()) {
      if (!tempStack.top().first) {
        inActiveBranch = false;
        break;
      }
      tempStack.pop();
    }
    
    // Handle preprocessor directives
    if (stripped.starts_with("#")) {
      llvm::StringRef directive = stripped.drop_front(1).trim();
      
      // #define
      if (directive.starts_with("define")) {
        if (inActiveBranch) {
          llvm::StringRef defineContent = directive.drop_front(6).trim();
          auto macro = parseDefine(defineContent);
          if (macro) {
            macro->DefinitionLoc = SourceLocation(CurrentLine, 1, CurrentFileID);
            Macros[macro->Name] = std::move(macro);
          }
        }
        continue;
      }
      
      // #undef
      if (directive.starts_with("undef")) {
        if (inActiveBranch) {
          llvm::StringRef name = directive.drop_front(5).trim();
          undefMacro(name.str());
        }
        continue;
      }
      
      // #if (not #ifdef or #ifndef)
      if (directive.starts_with("if") && 
          !directive.starts_with("ifdef") && 
          !directive.starts_with("ifndef")) {
        llvm::StringRef condition = directive.drop_front(2).trim();
        bool isTrue = inActiveBranch && evaluateCondition(condition);
        conditionStack.push({isTrue, isTrue});
        continue;
      }
      
      // #ifdef
      if (directive.starts_with("ifdef")) {
        llvm::StringRef name = directive.drop_front(5).trim();
        bool isDefined = inActiveBranch && isMacroDefined(name.str());
        conditionStack.push({isDefined, isDefined});
        continue;
      }
      
      // #ifndef
      if (directive.starts_with("ifndef")) {
        llvm::StringRef name = directive.drop_front(6).trim();
        bool isNotDefined = inActiveBranch && !isMacroDefined(name.str());
        conditionStack.push({isNotDefined, isNotDefined});
        continue;
      }
      
      // #else
      if (directive.starts_with("else")) {
        if (!conditionStack.empty()) {
          auto [current, satisfied] = conditionStack.top();
          conditionStack.pop();
          
          // Check parent conditions
          bool parentActive = true;
          std::stack<std::pair<bool, bool>> temp = conditionStack;
          while (!temp.empty()) {
            if (!temp.top().first) {
              parentActive = false;
              break;
            }
            temp.pop();
          }
          
          bool newCondition = !satisfied && parentActive;
          conditionStack.push({newCondition, satisfied || newCondition});
        }
        continue;
      }
      
      // #elif
      if (directive.starts_with("elif")) {
        if (!conditionStack.empty()) {
          auto [current, satisfied] = conditionStack.top();
          conditionStack.pop();
          
          if (!satisfied) {
            llvm::StringRef condition = directive.drop_front(4).trim();
            bool isTrue = evaluateCondition(condition);
            
            // Check parent conditions
            bool parentActive = true;
            std::stack<std::pair<bool, bool>> temp = conditionStack;
            while (!temp.empty()) {
              if (!temp.top().first) {
                parentActive = false;
                break;
              }
              temp.pop();
            }
            
            bool newCondition = isTrue && parentActive;
            conditionStack.push({newCondition, satisfied || isTrue});
          } else {
            conditionStack.push({false, satisfied});
          }
        }
        continue;
      }
      
      // #endif
      if (directive.starts_with("endif")) {
        if (!conditionStack.empty()) {
          conditionStack.pop();
        }
        continue;
      }
      
      // #include
      if (directive.starts_with("include")) {
        if (inActiveBranch) {
          llvm::StringRef includeContent = directive.drop_front(7).trim();
          std::string included = processInclude(includeContent);
          if (!included.empty()) {
            output << included << "\n";
          }
        }
        continue;
      }
      
      // #pragma once
      if (directive.starts_with("pragma")) {
        llvm::StringRef pragmaContent = directive.drop_front(6).trim();
        if (pragmaContent == "once") {
          // Mark current file as included
          IncludedFiles.insert(CurrentFile);
        }
        continue;
      }
      
      // Unknown directive - ignore
      continue;
    }
    
    // Non-directive line: expand macros if in active branch
    if (inActiveBranch) {
      std::string expanded = expandText(line);
      output << expanded << "\n";
    }
  }
  
  return output.str();
}

std::string Preprocessor::processText(llvm::StringRef source,
                                       const std::string& filename) {
  uint32_t fileID = SrcMgr.addString(source, filename);
  return process(fileID);
}

} // namespace zhc