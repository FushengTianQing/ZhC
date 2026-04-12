//===--- Types.h - ZhC Type System ---------------------------------------===//
//
// Basic type definitions for the ZhC compiler.
//
//===----------------------------------------------------------------------===//

#ifndef ZHC_TYPES_H
#define ZHC_TYPES_H

#include "zhc/Common.h"
#include "llvm/ADT/StringRef.h"

namespace zhc {

/// Type kind enumeration
enum class TypeKind {
  Void,
  Bool,
  Int8,
  Int16,
  Int32,
  Int64,
  UInt8,
  UInt16,
  UInt32,
  UInt64,
  Float32,
  Float64,
  String,
  Char,
  Pointer,
  Array,
  Struct,
  Enum,
  Function,
  Generic,
  UserDefined
};

/// QualType - a type with qualifiers (const, volatile, etc.)
class QualType {
public:
  QualType() : Kind(TypeKind::Void), IsConst(false), IsVolatile(false) {}
  
  explicit QualType(TypeKind kind, bool isConst = false, bool isVolatile = false)
      : Kind(kind), IsConst(isConst), IsVolatile(isVolatile) {}
  
  TypeKind getKind() const { return Kind; }
  bool isConst() const { return IsConst; }
  bool isVolatile() const { return IsVolatile; }
  
  bool isVoid() const { return Kind == TypeKind::Void; }
  bool isBool() const { return Kind == TypeKind::Bool; }
  bool isInteger() const {
    return Kind >= TypeKind::Int8 && Kind <= TypeKind::UInt64;
  }
  bool isFloat() const {
    return Kind == TypeKind::Float32 || Kind == TypeKind::Float64;
  }
  bool isNumeric() const { return isInteger() || isFloat(); }
  bool isPointer() const { return Kind == TypeKind::Pointer; }
  bool isArray() const { return Kind == TypeKind::Array; }
  bool isStruct() const { return Kind == TypeKind::Struct; }
  bool isFunction() const { return Kind == TypeKind::Function; }
  
  QualType withConst() const { return QualType(Kind, true, IsVolatile); }
  QualType withoutConst() const { return QualType(Kind, false, IsVolatile); }
  
  /// Get the type name as a string
  llvm::StringRef getTypeName() const;
  
private:
  TypeKind Kind;
  bool IsConst;
  bool IsVolatile;
};

/// Built-in type singletons (managed by ASTContext)
struct BuiltinTypes {
  QualType VoidTy;
  QualType BoolTy;
  QualType Int8Ty;
  QualType Int16Ty;
  QualType Int32Ty;
  QualType Int64Ty;
  QualType UInt8Ty;
  QualType UInt16Ty;
  QualType UInt32Ty;
  QualType UInt64Ty;
  QualType Float32Ty;
  QualType Float64Ty;
  QualType StringTy;
  QualType CharTy;
};

} // namespace zhc

#endif // ZHC_TYPES_H