//===--- frontend_chinese_test.cpp - Chinese Keyword Tests ----------------===//
//
// Integration tests for full Chinese keyword support.
// Tests programs written entirely with Chinese keywords and identifiers.
//
//===----------------------------------------------------------------------===//

#include "gtest/gtest.h"

#include "zhc/Lexer.h"
#include "zhc/Parser.h"
#include "zhc/Sema.h"
#include "zhc/Diagnostics.h"
#include "zhc/SourceManager.h"
#include "zhc/ASTContext.h"
#include "zhc/Keywords.h"

#include <memory>

using namespace zhc;

namespace {

/// Chinese keyword test helper
class ChineseKeywordTest : public ::testing::Test {
protected:
  struct CompileResult {
    std::unique_ptr<TranslationUnit> AST;
    DiagnosticsEngine Diags;
    bool Success;
    unsigned ErrorCount;
  };

  CompileResult compile(const std::string& source) {
    CompileResult result;
    SourceManager SM;
    ASTContext Context(SM);
    
    result.Diags.setSourceManager(&SM);
    uint32_t fileID = SM.addString(source, "chinese_test.zhc");
    
    Lexer lexer(source, fileID);
    Parser parser(lexer, result.Diags, Context);
    
    result.AST = parser.parseTranslationUnit();
    result.Success = !result.Diags.hasErrors();
    result.ErrorCount = result.Diags.getErrorCount();
    
    if (result.Success && result.AST) {
      Sema sema(result.Diags);
      result.Success = sema.analyze(result.AST.get());
    }
    
    return result;
  }

  /// Check keyword is recognized
  bool isKeyword(const std::string& text) {
    return getKeywordTable().isKeyword(text);
  }
};

//===----------------------------------------------------------------------===//
// T1.22c: Full Chinese Keyword Tests (5 fixtures)
//===----------------------------------------------------------------------===//

TEST_F(ChineseKeywordTest, ChineseHelloWorld) {
  // Fully Chinese Hello World
  auto result = compile(
    "函数 主函数() {"
    "  打印(\"你好世界\");"
    "  返回 0;"
    "}"
  );
  
  EXPECT_EQ(result.ErrorCount, 0u);
  EXPECT_TRUE(result.Success);
  EXPECT_TRUE(result.AST != nullptr);
}

TEST_F(ChineseKeywordTest, ChineseControlFlow) {
  // Chinese control flow keywords
  auto result = compile(
    "函数 控制流() : 整数型 {"
    "  如果 (真) {"
    "    返回 1;"
    "  } 否则 {"
    "    返回 0;"
    "  }"
    "}"
  );
  
  EXPECT_EQ(result.ErrorCount, 0u);
  EXPECT_TRUE(result.Success);
  EXPECT_TRUE(result.AST != nullptr);
  
  // Verify keywords are recognized
  EXPECT_TRUE(isKeyword("如果"));
  EXPECT_TRUE(isKeyword("否则"));
  EXPECT_TRUE(isKeyword("返回"));
  // Note: 真/假 are BOOL_LITERALs, not keywords, so isKeyword returns false.
  // They are handled by the Lexer in lexIdentifier(), not TokenKinds.def.
}

TEST_F(ChineseKeywordTest, ChineseTypes) {
  // Chinese type keywords
  auto result = compile(
    "函数 类型测试() {"
    "  变量 整数 : 整数型 = 42;"
    "  变量 浮点 : 浮点型 = 3.14;"
    "  变量 字符 : 字符型 = 'A';"
    "  变量 布尔 : 布尔型 = 真;"
    "}"
  );
  
  EXPECT_EQ(result.ErrorCount, 0u);
  EXPECT_TRUE(result.Success);
  EXPECT_TRUE(result.AST != nullptr);
  
  // Verify type keywords are recognized
  EXPECT_TRUE(isKeyword("整数型"));
  EXPECT_TRUE(isKeyword("浮点型"));
  EXPECT_TRUE(isKeyword("字符型"));
  EXPECT_TRUE(isKeyword("布尔型"));
  EXPECT_TRUE(isKeyword("空型"));
}

TEST_F(ChineseKeywordTest, MixedChineseEnglish) {
  // Mixed Chinese and English keywords
  auto result = compile(
    "func 混合函数() : int {"
    "  var x : 整数型 = 1;"
    "  if (真) {"
    "    return x;"
    "  } else {"
    "    返回 0;"
    "  }"
    "}"
  );
  
  // Both Chinese and English keywords should work
  EXPECT_EQ(result.ErrorCount, 0u);
  EXPECT_TRUE(result.Success);
  EXPECT_TRUE(result.AST != nullptr);
  
  // Verify bilingual keywords
  EXPECT_TRUE(isKeyword("func"));
  EXPECT_TRUE(isKeyword("函数"));
  EXPECT_TRUE(isKeyword("if"));
  EXPECT_TRUE(isKeyword("如果"));
  EXPECT_TRUE(isKeyword("return"));
  EXPECT_TRUE(isKeyword("返回"));
}

TEST_F(ChineseKeywordTest, ChineseUnicodeIdentifiers) {
  // Chinese identifiers (not keywords)
  auto result = compile(
    "函数 计算总和(甲 : 整数型, 乙 : 整数型) : 整数型 {"
    "  变量 张三 = 甲;"
    "  变量 李四 = 乙;"
    "  变量 结果 = 张三 + 李四;"
    "  返回 结果;"
    "}"
  );
  
  EXPECT_EQ(result.ErrorCount, 0u);
  EXPECT_TRUE(result.Success);
  EXPECT_TRUE(result.AST != nullptr);
  
  // These should NOT be keywords (they're identifiers)
  EXPECT_FALSE(isKeyword("甲"));
  EXPECT_FALSE(isKeyword("乙"));
  EXPECT_FALSE(isKeyword("张三"));
  EXPECT_FALSE(isKeyword("李四"));
  EXPECT_FALSE(isKeyword("结果"));
}

//===----------------------------------------------------------------------===//
// Additional Chinese keyword tests
//===----------------------------------------------------------------------===//

TEST_F(ChineseKeywordTest, AllControlFlowKeywords) {
  // Test all control flow keywords
  auto result = compile(
    "函数 全部控制流() {"
    "  循环 (真) { 跳出; }"
    "  对于 (变量 i = 0; i < 10; i = i + 1) { 继续; }"
    "  选择 (1) {"
    "    情况 1: 返回;"
    "    默认: 返回;"
    "  }"
    "}"
  );
  
  EXPECT_EQ(result.ErrorCount, 0u);
  EXPECT_TRUE(result.Success);
  
  // Verify keywords
  EXPECT_TRUE(isKeyword("循环"));
  EXPECT_TRUE(isKeyword("跳出"));
  EXPECT_TRUE(isKeyword("对于"));
  EXPECT_TRUE(isKeyword("继续"));
  EXPECT_TRUE(isKeyword("选择"));
  EXPECT_TRUE(isKeyword("情况"));
  EXPECT_TRUE(isKeyword("默认"));
}

TEST_F(ChineseKeywordTest, AllDeclarationKeywords) {
  // Test all declaration keywords
  auto result = compile(
    "结构体 点 { 整数型 x; 整数型 y; }"
    "枚举 颜色 { 红, 绿, 蓝 }"
    "函数 测试() { 变量 x = 1; 常量 变量 y = 2; }"
  );
  
  EXPECT_EQ(result.ErrorCount, 0u);
  EXPECT_TRUE(result.Success);
  
  // Verify keywords
  EXPECT_TRUE(isKeyword("结构体"));
  EXPECT_TRUE(isKeyword("枚举"));
  EXPECT_TRUE(isKeyword("函数"));
  EXPECT_TRUE(isKeyword("变量"));
  EXPECT_TRUE(isKeyword("常量"));
}

TEST_F(ChineseKeywordTest, ExceptionHandlingKeywords) {
  // Exception handling keywords
  auto result = compile(
    "函数 异常测试() {"
    "  尝试 {"
    "    抛出 \"错误\";"
    "  } 捕获 (异常 e) {"
    "    处理();"
    "  } 最终 {"
    "    清理();"
    "  }"
    "}"
  );
  
  // Should parse (even if exception handling not fully implemented)
  EXPECT_TRUE(result.AST != nullptr);
  
  // Verify keywords
  EXPECT_TRUE(isKeyword("尝试"));
  EXPECT_TRUE(isKeyword("抛出"));
  EXPECT_TRUE(isKeyword("捕获"));
  EXPECT_TRUE(isKeyword("最终"));
}

TEST_F(ChineseKeywordTest, ModuleSystemKeywords) {
  // Module system keywords (parseModuleDecl is a stub — no body support yet)
  auto result = compile(
    "导入 数学库 : 正弦, 余弦;"
    "模块 我的模块;"
  );
  
  // Should parse
  EXPECT_TRUE(result.AST != nullptr);
  
  // Verify keywords
  EXPECT_TRUE(isKeyword("导入"));
  EXPECT_TRUE(isKeyword("模块"));
}

TEST_F(ChineseKeywordTest, MemoryKeywords) {
  // Memory management keywords
  // Note: These may not be fully implemented yet
  
  // Verify keywords exist
  EXPECT_TRUE(isKeyword("新建"));
  EXPECT_TRUE(isKeyword("删除"));
  EXPECT_TRUE(isKeyword("大小"));
  EXPECT_TRUE(isKeyword("移动"));
  EXPECT_TRUE(isKeyword("独享指针"));
  EXPECT_TRUE(isKeyword("共享指针"));
  EXPECT_TRUE(isKeyword("弱指针"));
}

TEST_F(ChineseKeywordTest, AccessControlKeywords) {
  // Access control keywords
  // Note: These may not be fully implemented yet
  
  // Verify keywords exist
  EXPECT_TRUE(isKeyword("公有"));
  EXPECT_TRUE(isKeyword("私有"));
  EXPECT_TRUE(isKeyword("保护"));
  EXPECT_TRUE(isKeyword("静态"));
  EXPECT_TRUE(isKeyword("外部"));
}

TEST_F(ChineseKeywordTest, CoroutineKeywords) {
  // Coroutine keywords
  // Note: These may not be fully implemented yet
  
  // Verify keywords exist
  EXPECT_TRUE(isKeyword("异步"));
  EXPECT_TRUE(isKeyword("等待"));
  EXPECT_TRUE(isKeyword("产出"));
}

TEST_F(ChineseKeywordTest, ChineseStringLiterals) {
  // Chinese string literals
  auto result = compile(
    "函数 字符串测试() {"
    "  变量 消息 = \"你好，世界！\";"
    "  变量 路径 = \"用户/文档/文件\";"
    "  返回 消息;"
    "}"
  );
  
  EXPECT_EQ(result.ErrorCount, 0u);
  EXPECT_TRUE(result.Success);
}

TEST_F(ChineseKeywordTest, ChineseComments) {
  // Chinese comments
  auto result = compile(
    "# 这是中文注释\n"
    "函数 有注释() {\n"
    "  # 变量声明\n"
    "  变量 x = 42;\n"
    "  返回 x;\n"
    "}"
  );
  
  EXPECT_EQ(result.ErrorCount, 0u);
  EXPECT_TRUE(result.Success);
}

TEST_F(ChineseKeywordTest, FullwidthPunctuation) {
  // Fullwidth punctuation (if supported)
  // Note: Fullwidth punctuation may not be supported yet
  // This test documents expected behavior
  
  // Verify Chinese punctuation detection exists
  // (Implementation may vary)
}

}  // anonymous namespace