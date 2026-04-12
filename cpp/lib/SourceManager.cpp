//===--- SourceManager.cpp - ZhC Source Manager Implementation -----------===//
//
// This file implements the enhanced SourceManager for managing source file buffers.
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

SourceManager::~SourceManager() = default;

uint32_t SourceManager::loadFile(const std::string& path) {
  // Check if already loaded
  auto it = PathToFileID.find(path);
  if (it != PathToFileID.end()) {
    return it->second;
  }
  
  auto buffer = llvm::MemoryBuffer::getFile(path);
  if (!buffer) {
    return 0;  // Invalid FileID
  }
  
  auto info = std::make_unique<FileInfo>();
  info->FileID = static_cast<uint32_t>(Files.size());
  info->Path = path;
  
  // Extract directory and filename
  size_t lastSlash = path.find_last_of("/\\");
  if (lastSlash != std::string::npos) {
    info->Directory = path.substr(0, lastSlash);
    info->FileName = path.substr(lastSlash + 1);
  } else {
    info->FileName = path;
  }
  
  info->Buffer = std::move(*buffer);
  info->IsFile = true;
  
  computeLineOffsets(*info);
  
  uint32_t fileID = info->FileID;
  PathToFileID[path] = fileID;
  Files.push_back(std::move(info));
  
  // Also add to LLVM SourceMgr
  SM.AddNewSourceBuffer(std::move(*buffer), llvm::SMLoc());
  
  return fileID;
}

uint32_t SourceManager::addBuffer(std::unique_ptr<llvm::MemoryBuffer> buffer,
                                  const std::string& name) {
  auto info = std::make_unique<FileInfo>();
  info->FileID = static_cast<uint32_t>(Files.size());
  info->Path = name;
  info->FileName = name;
  info->Buffer = std::move(buffer);
  info->IsFile = false;
  
  computeLineOffsets(*info);
  
  uint32_t fileID = info->FileID;
  Files.push_back(std::move(info));
  
  return fileID;
}

uint32_t SourceManager::addString(llvm::StringRef str, const std::string& name) {
  auto buffer = llvm::MemoryBuffer::getMemBuffer(str, name);
  return addBuffer(std::move(buffer), name);
}

uint32_t SourceManager::addFileInfo(std::unique_ptr<FileInfo> info) {
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

uint32_t SourceManager::getFileID(llvm::StringRef path) const {
  auto it = PathToFileID.find(path.str());
  if (it != PathToFileID.end()) {
    return it->second;
  }
  return 0;
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
  return getLine(loc.FileID, loc.Line);
}

llvm::StringRef SourceManager::getLine(uint32_t fileID, uint32_t line) const {
  if (fileID == 0 || fileID >= Files.size()) {
    return "";
  }

  const FileInfo* info = Files[fileID].get();
  return info->getLineContent(line);
}

llvm::StringRef FileInfo::getLineContent(uint32_t line) const {
  if (line == 0 || line > LineOffsets.size()) {
    return "";
  }

  size_t lineStart = LineOffsets[line - 1];
  size_t lineEnd = (line < LineOffsets.size()) ?
                   LineOffsets[line] :
                   Buffer->getBufferSize();

  return Buffer->getBuffer().slice(lineStart, lineEnd - lineStart);
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

size_t SourceManager::getByteOffset(SourceLocation loc) const {
  if (!loc.isValid() || loc.FileID == 0 || loc.FileID >= Files.size()) {
    return 0;
  }

  const FileInfo* info = Files[loc.FileID].get();
  if (loc.Line == 0 || loc.Line > info->LineOffsets.size()) {
    return 0;
  }

  size_t lineStart = info->LineOffsets[loc.Line - 1];
  return lineStart + loc.Column - 1;
}

SourceLocation SourceManager::getLocation(uint32_t fileID, size_t byteOffset) const {
  if (fileID == 0 || fileID >= Files.size()) {
    return SourceLocation();
  }

  const FileInfo* info = Files[fileID].get();
  const auto& offsets = info->LineOffsets;

  // Binary search for the line
  uint32_t lo = 0;
  uint32_t hi = (uint32_t)offsets.size();

  while (lo < hi) {
    uint32_t mid = (lo + hi) / 2;
    if (offsets[mid] <= byteOffset) {
      lo = mid + 1;
    } else {
      hi = mid;
    }
  }

  uint32_t line = lo;
  size_t lineStart = (line > 0) ? offsets[line - 1] : 0;
  uint32_t column = (uint32_t)(byteOffset - lineStart) + 1;

  return SourceLocation(line, column, fileID);
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
