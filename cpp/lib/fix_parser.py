import re

with open("Parser.cpp", "r") as f:
    content = f.read()

# Pattern: if (!expect(TokenKind::IDENTIFIER)) ...; llvm::StringRef name = CurrentToken.Spelling;
# Replace with: check, save, advance pattern

# Fix pattern 1: "if (!expect(TokenKind::IDENTIFIER)) return nullptr;\n  llvm::StringRef name = CurrentToken.Spelling;"
pattern1 = r"if \(!expect\(TokenKind::IDENTIFIER\)\) return nullptr;\n  llvm::StringRef (\w+) = CurrentToken\.Spelling;"
replacement1 = r"""if (CurrentToken.Kind != TokenKind::IDENTIFIER) {
    DiagEngine.error(getCurrentLocation(), "期望标识符");
    return nullptr;
  }
  llvm::StringRef \1 = CurrentToken.Spelling;
  advance();"""

content = re.sub(pattern1, replacement1, content)

# Fix pattern 2: "if (!expect(TokenKind::IDENTIFIER)) break;\n    llvm::StringRef fieldName = CurrentToken.Spelling;"
pattern2 = r"if \(!expect\(TokenKind::IDENTIFIER\)\) break;\n    llvm::StringRef (\w+) = CurrentToken\.Spelling;"
replacement2 = r"""if (CurrentToken.Kind != TokenKind::IDENTIFIER) {
      DiagEngine.error(getCurrentLocation(), "期望标识符");
      break;
    }
    llvm::StringRef \1 = CurrentToken.Spelling;
    advance();"""

content = re.sub(pattern2, replacement2, content)

# Fix pattern 3: "if (!expect(TokenKind::IDENTIFIER)) break;\n  llvm::StringRef fieldName = CurrentToken.Spelling;"
pattern3 = r"if \(!expect\(TokenKind::IDENTIFIER\)\) break;\n  llvm::StringRef (\w+) = CurrentToken\.Spelling;"
replacement3 = r"""if (CurrentToken.Kind != TokenKind::IDENTIFIER) {
      DiagEngine.error(getCurrentLocation(), "期望标识符");
      break;
    }
    llvm::StringRef \1 = CurrentToken.Spelling;
    advance();"""

content = re.sub(pattern3, replacement3, content)

with open("Parser.cpp", "w") as f:
    f.write(content)

print("Fixed!")
