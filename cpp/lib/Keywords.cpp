//===--- Keywords.cpp - ZhC Keyword Table Implementation -----------------===//
//
// This file implements the keyword lookup table for the ZhC compiler.
//
//===----------------------------------------------------------------------===//

#include "zhc/Keywords.h"

namespace zhc {

KeywordTable::KeywordTable() {
  //===--- Control Flow Keywords -----------------------------------------===//
  addBilingual("如果", "if", TokenKind::KW_if);
  addBilingual("否则", "else", TokenKind::KW_else);
  addBilingual("循环", "while", TokenKind::KW_while);
  addBilingual("当", "while", TokenKind::KW_while);  // Alternative
  addBilingual("对于", "for", TokenKind::KW_for);
  addBilingual("选择", "switch", TokenKind::KW_switch);
  addBilingual("当", "case", TokenKind::KW_case);    // Context-dependent
  addBilingual("默认", "default", TokenKind::KW_default);
  addBilingual("返回", "return", TokenKind::KW_return);
  addBilingual("跳出", "break", TokenKind::KW_break);
  addBilingual("继续", "continue", TokenKind::KW_continue);
  addBilingual("产出", "yield", TokenKind::KW_yield);
  
  //===--- Type Definition Keywords --------------------------------------===//
  addBilingual("函数", "func", TokenKind::KW_func);
  addBilingual("变量", "var", TokenKind::KW_var);
  addBilingual("常量", "const", TokenKind::KW_const);
  addBilingual("结构体", "struct", TokenKind::KW_struct);
  addBilingual("枚举", "enum", TokenKind::KW_enum);
  addBilingual("类型定义", "typedef", TokenKind::KW_typedef);
  addBilingual("类", "class", TokenKind::KW_class);
  addBilingual("接口", "interface", TokenKind::KW_interface);
  addBilingual("实现", "implements", TokenKind::KW_implements);
  addBilingual("继承", "extends", TokenKind::KW_extends);
  
  //===--- Type Keywords -------------------------------------------------===//
  addBilingual("整数型", "int", TokenKind::KW_int);
  addBilingual("浮点型", "float", TokenKind::KW_float);
  addBilingual("字符型", "char", TokenKind::KW_char);
  addBilingual("布尔型", "bool", TokenKind::KW_bool);
  addBilingual("空型", "void", TokenKind::KW_void);
  addBilingual("字符串型", "string", TokenKind::KW_string);
  
  //===--- Access Control Keywords ---------------------------------------===//
  addBilingual("公有", "public", TokenKind::KW_public);
  addBilingual("私有", "private", TokenKind::KW_private);
  addBilingual("保护", "protected", TokenKind::KW_protected);
  addBilingual("静态", "static", TokenKind::KW_static);
  addBilingual("外部", "extern", TokenKind::KW_extern);
  
  //===--- Memory Management Keywords ------------------------------------===//
  addBilingual("新建", "new", TokenKind::KW_new);
  addBilingual("删除", "delete", TokenKind::KW_delete);
  addBilingual("大小", "sizeof", TokenKind::KW_sizeof);
  addBilingual("类型", "typeof", TokenKind::KW_typeof);
  addBilingual("对齐", "alignof", TokenKind::KW_alignof);
  
  //===--- Smart Pointer Keywords ----------------------------------------===//
  addBilingual("独享指针", "unique_ptr", TokenKind::KW_unique_ptr);
  addBilingual("共享指针", "shared_ptr", TokenKind::KW_shared_ptr);
  addBilingual("弱指针", "weak_ptr", TokenKind::KW_weak_ptr);
  addBilingual("移动", "move", TokenKind::KW_move);
  
  //===--- Exception Handling Keywords -----------------------------------===//
  addBilingual("尝试", "try", TokenKind::KW_try);
  addBilingual("捕获", "catch", TokenKind::KW_catch);
  addBilingual("最终", "finally", TokenKind::KW_finally);
  addBilingual("抛出", "throw", TokenKind::KW_throw);
  
  //===--- Coroutine/Async Keywords --------------------------------------===//
  addBilingual("异步", "async", TokenKind::KW_async);
  addBilingual("等待", "await", TokenKind::KW_await);
  
  //===--- Module System Keywords ----------------------------------------===//
  addBilingual("导入", "import", TokenKind::KW_import);
  addBilingual("模块", "module", TokenKind::KW_module);
  addBilingual("从", "from", TokenKind::KW_from);
  addBilingual("伴随", "with", TokenKind::KW_with);
  
  //===--- Generic Keywords ----------------------------------------------===//
  addBilingual("泛型", "generic", TokenKind::KW_generic);
  addBilingual("约束", "where", TokenKind::KW_where);
  
  //===--- Safety Keywords -----------------------------------------------===//
  addBilingual("共享型", "shared", TokenKind::KW_shared);
  addBilingual("线程独享型", "thread_local", TokenKind::KW_thread_local);
  addBilingual("结果型", "result", TokenKind::KW_result);
  addBilingual("可空型", "nullable", TokenKind::KW_nullable);
  addBilingual("溢出检查", "overflow_check", TokenKind::KW_overflow_check);
  addBilingual("边界检查", "bounds_check", TokenKind::KW_bounds_check);
  
  //===--- Pattern Matching Keywords -------------------------------------===//
  addBilingual("匹配", "match", TokenKind::KW_match);
  addBilingual("模式", "pattern", TokenKind::KW_pattern);
  addBilingual("守卫", "guard", TokenKind::KW_guard);
  addBilingual("范围", "range", TokenKind::KW_range);
  addBilingual("解构", "destructure", TokenKind::KW_destructure);
  
  //===--- Closure Keywords ----------------------------------------------===//
  addBilingual("闭包", "closure", TokenKind::KW_closure);
  addBilingual("上值", "upvalue", TokenKind::KW_upvalue);
  
  //===--- Exception Class Keywords --------------------------------------===//
  addBilingual("异常类", "exception", TokenKind::KW_exception);
  
  //===--- Destructor Keywords -------------------------------------------===//
  addBilingual("析构函数", "destructor", TokenKind::KW_destructor);
  
  //===--- Other Modifier Keywords ---------------------------------------===//
  addBilingual("运算符", "operator", TokenKind::KW_operator);
  addBilingual("覆盖", "override", TokenKind::KW_override);
  addBilingual("虚函数", "virtual", TokenKind::KW_virtual);
  addBilingual("抽象", "abstract", TokenKind::KW_abstract);
  addBilingual("封闭", "sealed", TokenKind::KW_sealed);
  addBilingual("可变", "mutable", TokenKind::KW_mutable);
  addBilingual("易变", "volatile", TokenKind::KW_volatile);
  addBilingual("内联", "inline", TokenKind::KW_inline);
}

void KeywordTable::addBilingual(const char* chinese, const char* english, 
                                 TokenKind kind) {
  Keywords[chinese] = kind;
  Keywords[english] = kind;
}

std::optional<TokenKind> KeywordTable::lookup(llvm::StringRef text) const {
  auto it = Keywords.find(text);
  if (it != Keywords.end()) {
    return it->second;
  }
  return std::nullopt;
}

bool KeywordTable::isKeyword(llvm::StringRef text) const {
  return Keywords.find(text) != Keywords.end();
}

const KeywordTable& getKeywordTable() {
  static KeywordTable table;
  return table;
}

} // namespace zhc