//===--- ASTContext.cpp - AST Memory Management Implementation -----------===//
//
// Implementation of ASTContext for managing AST node memory.
//
//===----------------------------------------------------------------------===//

#include "zhc/ASTContext.h"
#include "zhc/SourceManager.h"

#include <cstring>

namespace zhc {

ASTContext::ASTContext(SourceManager& sm) : SM(sm) {}

ASTContext::~ASTContext() {
  // Call destructors for tracked allocations in reverse order
  for (auto it = TrackedAllocations.rbegin(); it != TrackedAllocations.rend(); ++it) {
    (*it)();
  }
  // BumpPtrAllocator automatically frees all memory
}

llvm::StringRef ASTContext::copyString(llvm::StringRef str) {
  // Check if already interned
  auto it = InternedStrings.find(str);
  if (it != InternedStrings.end()) {
    return llvm::StringRef(it->second, str.size());
  }
  
  // Allocate and copy
  char* mem = Allocator.Allocate<char>(str.size() + 1);
  std::memcpy(mem, str.data(), str.size());
  mem[str.size()] = '\0';
  
  // Intern the string
  InternedStrings[str] = mem;
  
  return llvm::StringRef(mem, str.size());
}

const char* ASTContext::copyCString(const char* str) {
  if (!str) return nullptr;
  
  size_t len = std::strlen(str);
  
  // Check if already interned
  auto it = InternedStrings.find(llvm::StringRef(str, len));
  if (it != InternedStrings.end()) {
    return it->second;
  }
  
  // Allocate and copy
  char* mem = Allocator.Allocate<char>(len + 1);
  std::memcpy(mem, str, len + 1);
  
  // Intern the string
  InternedStrings[llvm::StringRef(str, len)] = mem;
  
  return mem;
}

size_t ASTContext::getTotalMemory() const {
  return Allocator.getTotalMemory();
}

} // namespace zhc