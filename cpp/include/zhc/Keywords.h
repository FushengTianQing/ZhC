//===--- Keywords.h - ZhC Keyword Table ---------------------------------===//
//
// This file defines the keyword lookup table for the ZhC compiler.
// It maps both Chinese and English keywords to their TokenKind values.
//
//===----------------------------------------------------------------------===//

#ifndef ZHC_KEYWORDS_H
#define ZHC_KEYWORDS_H

#include "zhc/Lexer.h"
#include "llvm/ADT/StringMap.h"

namespace zhc {

/// Keyword lookup table - maps keyword strings to TokenKind
class KeywordTable {
public:
  /// Initialize the keyword table with all Chinese and English keywords
  KeywordTable();
  
  /// Look up a keyword. Returns the TokenKind or std::nullopt if not found.
  std::optional<TokenKind> lookup(llvm::StringRef text) const;
  
  /// Check if a string is a keyword
  bool isKeyword(llvm::StringRef text) const;
  
private:
  llvm::StringMap<TokenKind> Keywords;
  
  /// Add a Chinese-English keyword pair
  void addBilingual(const char* chinese, const char* english, TokenKind kind);
};

/// Get the global keyword table instance
const KeywordTable& getKeywordTable();

} // namespace zhc

#endif // ZHC_KEYWORDS_H