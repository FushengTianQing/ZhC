//===--- SourceManager.h - ZhC Source Manager ----------------------------===//
//
// This file defines the SourceManager for managing source file buffers.
// Provides complete UTF-8 aware source location and line lookup.
//
//===----------------------------------------------------------------------===//

#ifndef ZHC_SOURCEMANAGER_H
#define ZHC_SOURCEMANAGER_H

#include "zhc/Common.h"
#include "zhc/Lexer.h"

#include "llvm/ADT/StringMap.h"
#include "llvm/ADT/StringRef.h"
#include "llvm/Support/MemoryBuffer.h"
#include "llvm/Support/SourceMgr.h"

#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

namespace zhc {

/// Information about a loaded source file
struct FileInfo {
  uint32_t FileID = 0;
  std::string Path;
  std::string FileName;  // Just the filename part
  std::string Directory;  // Directory containing the file
  std::unique_ptr<llvm::MemoryBuffer> Buffer;
  std::vector<uint32_t> LineOffsets;  // Byte offset of each line start
  bool IsFile = false;  // true if loaded from file, false if from buffer
  
  /// Get line content (0-indexed line number)
  llvm::StringRef getLineContent(uint32_t line) const;
  
  /// Get the total number of lines
  uint32_t getNumLines() const { return (uint32_t)LineOffsets.size(); }
};

/// SourceManager - manages source file loading and position lookup
class SourceManager {
public:
  SourceManager();
  ~SourceManager();
  
  /// Load a source file. Returns FileID on success, 0 on failure.
  uint32_t loadFile(const std::string& path);
  
  /// Add an in-memory source buffer. Returns FileID.
  uint32_t addBuffer(std::unique_ptr<llvm::MemoryBuffer> buffer,
                     const std::string& name = "<stdin>");
  
  /// Add a string as a source buffer. Returns FileID.
  uint32_t addString(llvm::StringRef str, const std::string& name = "<string>");
  
  /// Get the source content for a FileID
  llvm::StringRef getSource(uint32_t fileID) const;
  
  /// Get file info for a FileID
  const FileInfo* getFileInfo(uint32_t fileID) const;
  
  /// Get FileID by filename (searches loaded files)
  uint32_t getFileID(llvm::StringRef path) const;
  
  /// Convert a SourceLocation to a human-readable string
  std::string getLocationString(SourceLocation loc) const;
  
  /// Get the line content at the given location
  llvm::StringRef getLine(SourceLocation loc) const;
  
  /// Get line content by FileID and line number (1-indexed)
  llvm::StringRef getLine(uint32_t fileID, uint32_t line) const;
  
  /// Get the column number (UTF-8 aware, counting characters not bytes)
  uint32_t getColumnUTF8(SourceLocation loc) const;
  
  /// Get byte offset for a SourceLocation
  size_t getByteOffset(SourceLocation loc) const;
  
  /// Create a SourceLocation from byte offset
  SourceLocation getLocation(uint32_t fileID, size_t byteOffset) const;
  
  /// Get the underlying LLVM SourceMgr (for LLVM diagnostics integration)
  llvm::SourceMgr& getLLVMSourceMgr() { return SM; }
  
  /// Get total number of loaded files
  uint32_t getNumFiles() const { return (uint32_t)Files.size() - 1; }
  
  /// Check if a file ID is valid
  bool isFileIDValid(uint32_t fileID) const {
    return fileID > 0 && fileID < Files.size();
  }

private:
  llvm::SourceMgr SM;
  std::vector<std::unique_ptr<FileInfo>> Files;
  std::unordered_map<std::string, uint32_t> PathToFileID;
  
  /// Compute line offsets for a buffer
  void computeLineOffsets(FileInfo& info);
  
  /// Common initialization for file and buffer
  uint32_t addFileInfo(std::unique_ptr<FileInfo> info);
};

} // namespace zhc

#endif // ZHC_SOURCEMANAGER_H
