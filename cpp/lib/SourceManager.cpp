//===--- SourceManager.cpp - ZhC Source Manager Implementation -----------===//
//
// This file implements the SourceManager for managing source file buffers.
//
//===----------------------------------------------------------------------===//

#include "zhc/SourceManager.h"

#include "llvm/Support/MemoryBuffer.h"
#include "llvm/Support/raw_ostream.h"

#include <fstream>

namespace zhc {

SourceManager::SourceManager() {
  // Reserve FileID 0 for invalid/unknown
  Files.push_back(nullptr);
}

uint32_t SourceManager::loadFile(const std::string& path) {
  auto buffer = llvm::MemoryBuffer::getFile(path);
  if (!buffer) {
    return 0;  // Invalid FileID
  }
  
  auto info = std::make_unique<FileInfo>();
  info->FileID = static_cast<uint32_t>(Files.size());
  info->Path = path;
  info->FileName = path.substr(path.find_last_of('/') + 1);
  info->Buffer = std::move(*buffer);
  
  computeLineOffsets(*info);
  
  uint32_t fileID = info->FileID;
  Files.push_back(std::move(info));
  
  return fileID;
}

uint32_t SourceManager::addBuffer(std::unique_ptr<llvm::MemoryBuffer> buffer,
                                   const std::string& name) {
  auto info = std::make_unique<FileInfo>();
  info->FileID = static_cast<uint32_t>(Files.size());
  info->Path = name;
  info->FileName = name;
  info->Buffer = std::move(buffer);
  
  computeLineOffsets(*info);
  
  uint32_t fileID = info->FileID;
  Files.push_back(std::move(info));
  
  return fileID;
}

llvm::StringRef SourceManager::getSource(uint32_t fileID) const {
  if (fileID == 0 || fileID >= Files.size()) {
    return "";
  }
  return Files[fileID]->Buffer->getBuffer();
}

const FileInfo* SourceManager::getFileInfo(uint32_t fileID) const {
  if (fileID == 0 || fileID >= Files.size()) {
    return nullptr;
  }
  return Files[fileID].get();
}

std::string SourceManager::getLocationString(SourceLocation loc) const {
  if (!loc.isValid() || loc.FileID == 0 || loc.FileID >= Files.size()) {
    return "<unknown>";
  }
  
  const FileInfo* info = Files[loc.FileID].get();
  return info->FileName + ":" + std::to_string(loc.Line) + ":" + 
         std::to_string(loc.Column);
}

llvm::StringRef SourceManager::getLine(SourceLocation loc) const {
  if (!loc.isValid() || loc.FileID == 0 || loc.FileID >= Files.size()) {
    return "";
  }
  
  const FileInfo* info = Files[loc.FileID].get();
  if (loc.Line == 0 || loc.Line > info->LineOffsets.size()) {
    return "";
  }
  
  size_t lineStart = info->LineOffsets[loc.Line - 1];
  size_t lineEnd = (loc.Line < info->LineOffsets.size()) ?
                   info->LineOffsets[loc.Line] :
                   info->Buffer->getBufferSize();
  
  return info->Buffer->getBuffer().slice(lineStart, lineEnd - lineStart);
}

uint32_t SourceManager::getColumnUTF8(SourceLocation loc) const {
  if (!loc.isValid()) {
    return 0;
  }
  
  llvm::StringRef line = getLine(loc);
  if (line.empty()) {
    return loc.Column;
  }
  
  // Convert byte column to character column
  size_t bytePos = 0;
  size_t charPos = 0;
  
  while (bytePos < line.size() && charPos < loc.Column - 1) {
    uint8_t b = static_cast<uint8_t>(line[bytePos]);
    bytePos += utf8::charLength(b);
    if (utf8::isLeadByte(b)) {
      charPos++;
    }
  }
  
  return static_cast<uint32_t>(charPos + 1);
}

void SourceManager::computeLineOffsets(FileInfo& info) {
  info.LineOffsets.clear();
  info.LineOffsets.push_back(0);  // Line 1 starts at byte 0
  
  llvm::StringRef buffer = info.Buffer->getBuffer();
  for (size_t i = 0; i < buffer.size(); ++i) {
    if (buffer[i] == '\n') {
      info.LineOffsets.push_back(i + 1);
    }
  }
}

} // namespace zhc