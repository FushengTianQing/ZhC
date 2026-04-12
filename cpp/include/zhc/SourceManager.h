//===--- SourceManager.h - ZhC Source Manager ----------------------------===//
//
// This file defines the SourceManager for managing source file buffers.
//
//===----------------------------------------------------------------------===//

#ifndef ZHC_SOURCEMANAGER_H
#define ZHC_SOURCEMANAGER_H

#include "zhc/Common.h"
#include "llvm/ADT/StringMap.h"
#include "llvm/ADT/StringRef.h"
#include "llvm/Support/MemoryBuffer.h"
#include "llvm/Support/SourceMgr.h"

#include <memory>
#include <string>
#include <vector>

namespace zhc {

/// Information about a loaded source file
struct FileInfo {
  uint32_t FileID = 0;
  std::string Path;
  std::string FileName;  // Just the filename part
  std::unique_ptr<llvm::MemoryBuffer> Buffer;
  std::vector<uint32_t> LineOffsets;  // Byte offset of each line start
};

/// SourceManager - manages source file loading and position lookup
class SourceManager {
public:
  SourceManager();
  
  /// Load a source file. Returns FileID on success.
  uint32_t loadFile(const std::string& path);
  
  /// Add an in-memory source buffer. Returns FileID.
  uint32_t addBuffer(std::unique_ptr<llvm::MemoryBuffer> buffer, 
                     const std::string& name = "<stdin>");
  
  /// Get the source content for a FileID
  llvm::StringRef getSource(uint32_t fileID) const;
  
  /// Get file info for a FileID
  const FileInfo* getFileInfo(uint32_t fileID) const;
  
  /// Convert a SourceLocation to a human-readable string
  std::string getLocationString(SourceLocation loc) const;
  
  /// Get the line content at the given location
  llvm::StringRef getLine(SourceLocation loc) const;
  
  /// Get the column number (UTF-8 aware, counting characters not bytes)
  uint32_t getColumnUTF8(SourceLocation loc) const;
  
  /// Get the underlying LLVM SourceMgr (for LLVM diagnostics integration)
  llvm::SourceMgr& getLLVMSourceMgr() { return SM; }
  
private:
  llvm::SourceMgr SM;
  std::vector<std::unique_ptr<FileInfo>> Files;
  
  /// Compute line offsets for a buffer
  void computeLineOffsets(FileInfo& info);
};

} // namespace zhc

#endif // ZHC_SOURCEMANAGER_H