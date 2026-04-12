//===--- ASTContext.h - AST Memory Management ----------------------------===//
//
// Manages memory lifetime for AST nodes using BumpPtrAllocator.
// Design principles:
// 1. Most AST nodes use arena allocation (bulk deallocation)
// 2. Nodes requiring destructors (e.g., with std::string) are tracked separately
// 3. Built-in types are singletons (VoidTy, Int32Ty, etc.)
// 4. Not thread-safe (single-threaded per compilation)
//
//===----------------------------------------------------------------------===//

#ifndef ZHC_ASTCONTEXT_H
#define ZHC_ASTCONTEXT_H

#include "zhc/Common.h"
#include "llvm/Support/Allocator.h"
#include "llvm/ADT/StringMap.h"
#include "llvm/ADT/ArrayRef.h"

#include <functional>
#include <vector>

namespace zhc {

class SourceManager;

/// ASTContext - manages memory for all AST nodes in a compilation
class ASTContext {
public:
  explicit ASTContext(SourceManager& sm);
  ~ASTContext();
  
  //===--- Arena Allocation ---===//
  
  /// Create an object in the arena (no destructor called)
  /// Use for POD/trivially-destructible AST nodes
  template<typename T, typename... Args>
  T* create(Args&&... args) {
    return new (Allocator.Allocate(sizeof(T), alignof(T)))
        T(std::forward<Args>(args)...);
  }
  
  /// Create an object that needs destructor call
  /// Use for nodes with std::string/std::vector members
  template<typename T, typename... Args>
  T* createWithDtor(Args&&... args) {
    void* mem = Allocator.Allocate(sizeof(T), alignof(T));
    T* obj = new (mem) T(std::forward<Args>(args)...);
    TrackedAllocations.push_back([obj]() { obj->~T(); });
    return obj;
  }
  
  //===--- String Allocation ---===//
  
  /// Copy a string into the arena and return a StringRef
  /// The string data lives for the duration of the context
  llvm::StringRef copyString(llvm::StringRef str);
  
  /// Copy a C string into the arena
  const char* copyCString(const char* str);
  
  //===--- Memory Stats ---===//
  
  /// Get total bytes allocated
  size_t getTotalMemory() const;
  
  /// Get number of tracked allocations
  size_t getTrackedCount() const { return TrackedAllocations.size(); }
  
  //===--- Source Manager Access ---===//
  
  SourceManager& getSourceManager() { return SM; }
  const SourceManager& getSourceManager() const { return SM; }
  
private:
  SourceManager& SM;
  llvm::BumpPtrAllocator Allocator;
  std::vector<std::function<void()>> TrackedAllocations;
  
  // String interning table
  llvm::StringMap<const char*> InternedStrings;
};

} // namespace zhc

#endif // ZHC_ASTCONTEXT_H