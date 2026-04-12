//===--- preprocessor_test.cpp - Preprocessor Unit Tests -----------------===//
//
// Unit tests for the ZhC Preprocessor.
// Tests #define, #ifdef, #ifndef, #if, #elif, #else, #endif,
// #include, #pragma once, macro expansion, and built-in macros.
//
//===----------------------------------------------------------------------===//

#include "zhc/Preprocessor.h"
#include "zhc/Diagnostics.h"
#include "zhc/SourceManager.h"

#include "gtest/gtest.h"

#include <string>

using namespace zhc;

namespace {

/// Test helper class
class PreprocessorTest : public ::testing::Test {
protected:
  SourceManager SM;
  DiagnosticsEngine Diags;
  PreprocessorConfig Config;
  std::unique_ptr<Preprocessor> PP;
  
  void SetUp() override {
    PP = std::make_unique<Preprocessor>(Config, SM, Diags);
  }
  
  std::string preprocess(const std::string& source) {
    return PP->processText(source);
  }
  
  std::string stripTrailingNewlines(const std::string& s) {
    size_t end = s.find_last_not_of('\n');
    return end == std::string::npos ? "" : s.substr(0, end + 1);
  }
};

//===----------------------------------------------------------------------===//
// Object Macro Tests
//===----------------------------------------------------------------------===//

TEST_F(PreprocessorTest, SimpleObjectMacro) {
  std::string source = "#define PI 3.14\nPI";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "3.14");
}

TEST_F(PreprocessorTest, ObjectMacroEmptyBody) {
  std::string source = "#define DEBUG\nint x = 1;";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "int x = 1;");
}

TEST_F(PreprocessorTest, ObjectMacroWithExpression) {
  std::string source = "#define SIZE 100\nint arr[SIZE];";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "int arr[100];");
}

TEST_F(PreprocessorTest, ObjectMacroRedefine) {
  std::string source = "#define X 1\n#define X 2\nX";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "2");
}

TEST_F(PreprocessorTest, ObjectMacroUndef) {
  std::string source = "#define X 10\nX\n#undef X\nX";
  std::string result = preprocess(source);
  // After undef, X should not be expanded
  EXPECT_EQ(stripTrailingNewlines(result), "10\nX");
}

TEST_F(PreprocessorTest, MultipleObjectMacros) {
  std::string source = "#define A 1\n#define B 2\n#define C 3\nA + B + C";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "1 + 2 + 3");
}

TEST_F(PreprocessorTest, MacroInStringLiteralNotExpanded) {
  std::string source = "#define NAME world\n\"hello NAME\"";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "\"hello NAME\"");
}

TEST_F(PreprocessorTest, MacroExpansionRecursive) {
  std::string source = "#define A B\n#define B 42\nA";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "42");
}

TEST_F(PreprocessorTest, MacroExpansionChained) {
  std::string source = "#define A B\n#define B C\n#define C 99\nA";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "99");
}

//===----------------------------------------------------------------------===//
// Function Macro Tests
//===----------------------------------------------------------------------===//

TEST_F(PreprocessorTest, SimpleFunctionMacro) {
  std::string source = "#define ADD(a, b) (a + b)\nADD(1, 2)";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "(1 + 2)");
}

TEST_F(PreprocessorTest, FunctionMacroSingleArg) {
  std::string source = "#define SQUARE(x) (x * x)\nSQUARE(5)";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "(5 * 5)");
}

TEST_F(PreprocessorTest, FunctionMacroMultipleUses) {
  std::string source = "#define MAX(a, b) ((a) > (b) ? (a) : (b))\nMAX(1, 2) + MAX(3, 4)";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "((1) > (2) ? (1) : (2)) + ((3) > (4) ? (3) : (4))");
}

TEST_F(PreprocessorTest, FunctionMacroNoArgsNotExpanded) {
  std::string source = "#define FOO(x) (x)\nFOO";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "FOO");
}

TEST_F(PreprocessorTest, FunctionMacroVariadic) {
  std::string source = "#define LOG(fmt, ...) printf(fmt, __VA_ARGS__)\nLOG(\"%d %d\", 1, 2)";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "printf(\"%d %d\", 1, 2)");
}

TEST_F(PreprocessorTest, FunctionMacroWithNestedCall) {
  std::string source = "#define DOUBLE(x) ((x) * 2)\n#define TRIPLE(x) ((x) * 3)\nDOUBLE(TRIPLE(5))";
  std::string result = preprocess(source);
  // DOUBLE(TRIPLE(5)) -> ((TRIPLE(5)) * 2) -> (((5) * 3) * 2)
  EXPECT_NE(result.find("5"), std::string::npos);
  EXPECT_NE(result.find("* 2"), std::string::npos);
  EXPECT_NE(result.find("* 3"), std::string::npos);
}

//===----------------------------------------------------------------------===//
// Conditional Compilation Tests
//===----------------------------------------------------------------------===//

TEST_F(PreprocessorTest, IfdefDefined) {
  std::string source = "#define X\n#ifdef X\nyes\n#endif";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "yes");
}

TEST_F(PreprocessorTest, IfdefNotDefined) {
  std::string source = "#ifdef X\nyes\n#endif\nno";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "no");
}

TEST_F(PreprocessorTest, IfndefNotDefined) {
  std::string source = "#ifndef X\nyes\n#endif";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "yes");
}

TEST_F(PreprocessorTest, IfndefDefined) {
  std::string source = "#define X\n#ifndef X\nno\n#endif\nyes";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "yes");
}

TEST_F(PreprocessorTest, IfdefElseTrue) {
  std::string source = "#define X\n#ifdef X\nthen\n#else\nelse\n#endif";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "then");
}

TEST_F(PreprocessorTest, IfdefElseFalse) {
  std::string source = "#ifdef X\nthen\n#else\nelse\n#endif";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "else");
}

TEST_F(PreprocessorTest, NestedIfdef) {
  std::string source = "#define A\n#define B\n#ifdef A\n#ifdef B\nboth\n#endif\n#endif";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "both");
}

TEST_F(PreprocessorTest, NestedIfdefInnerFalse) {
  std::string source = "#define A\n#ifdef A\n#ifdef B\ninner\n#else\nelse_inner\n#endif\n#endif";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "else_inner");
}

TEST_F(PreprocessorTest, IfdefElifTrue) {
  std::string source = "#define V 2\n#ifdef X\nfirst\n#elif V\nsecond\n#endif";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "second");
}

TEST_F(PreprocessorTest, IfdefElifChain) {
  std::string source = "#define V 3\n#if V == 1\none\n#elif V == 2\ntwo\n#elif V == 3\nthree\n#else\nother\n#endif";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "three");
}

TEST_F(PreprocessorTest, IfdefElifElseNone) {
  std::string source = "#if 0\nfirst\n#elif 0\nsecond\n#else\nfallback\n#endif";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "fallback");
}

TEST_F(PreprocessorTest, IfdefElifAllFalse) {
  std::string source = "#if 0\nfirst\n#elif 0\nsecond\n#endif";
  std::string result = preprocess(source);
  EXPECT_TRUE(stripTrailingNewlines(result).empty());
}

//===----------------------------------------------------------------------===//
// #if Condition Tests
//===----------------------------------------------------------------------===//

TEST_F(PreprocessorTest, IfTrue) {
  std::string source = "#if 1\nyes\n#endif";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "yes");
}

TEST_F(PreprocessorTest, IfFalse) {
  std::string source = "#if 0\nno\n#endif\nafter";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "after");
}

TEST_F(PreprocessorTest, IfDefined) {
  std::string source = "#define X\n#if defined(X)\nyes\n#endif";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "yes");
}

TEST_F(PreprocessorTest, IfNotDefined) {
  std::string source = "#if !defined(X)\nyes\n#endif";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "yes");
}

TEST_F(PreprocessorTest, IfComparison) {
  std::string source = "#define V 5\n#if V == 5\nyes\n#endif";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "yes");
}

TEST_F(PreprocessorTest, IfComparisonNotEqual) {
  std::string source = "#define V 3\n#if V == 5\nno\n#else\nyes\n#endif";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "yes");
}

//===----------------------------------------------------------------------===//
// Built-in Macro Tests
//===----------------------------------------------------------------------===//

TEST_F(PreprocessorTest, BuiltinZhcMacro) {
  EXPECT_TRUE(PP->isMacroDefined("__ZHC__"));
  auto* macro = PP->getMacro("__ZHC__");
  ASSERT_NE(macro, nullptr);
  EXPECT_EQ(macro->Body, "1");
}

TEST_F(PreprocessorTest, BuiltinZhcVersionMacro) {
  EXPECT_TRUE(PP->isMacroDefined("__ZHC_VERSION__"));
  auto* macro = PP->getMacro("__ZHC_VERSION__");
  ASSERT_NE(macro, nullptr);
  EXPECT_EQ(macro->Body, "\"0.1.0\"");
}

TEST_F(PreprocessorTest, BuiltinFileMacro) {
  std::string source = "__FILE__";
  std::string result = preprocess(source);
  // Should expand to quoted filename
  EXPECT_TRUE(result.find("test_string") != std::string::npos || 
              result.find("<") != std::string::npos);
}

TEST_F(PreprocessorTest, BuiltinLineMacro) {
  std::string source = "line1\n__LINE__";
  std::string result = preprocess(source);
  // __LINE__ on the second line should be "2"
  EXPECT_TRUE(result.find("2") != std::string::npos);
}

TEST_F(PreprocessorTest, BuiltinDateMacro) {
  EXPECT_TRUE(PP->isMacroDefined("__DATE__"));
  auto* macro = PP->getMacro("__DATE__");
  ASSERT_NE(macro, nullptr);
  EXPECT_TRUE(macro->Body.starts_with("\""));
}

TEST_F(PreprocessorTest, BuiltinTimeMacro) {
  EXPECT_TRUE(PP->isMacroDefined("__TIME__"));
}

//===----------------------------------------------------------------------===//
// Programmatic API Tests
//===----------------------------------------------------------------------===//

TEST_F(PreprocessorTest, DefineMacroProgrammatically) {
  PP->defineMacro("MY_MACRO", "42");
  EXPECT_TRUE(PP->isMacroDefined("MY_MACRO"));
  
  std::string source = "MY_MACRO";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "42");
}

TEST_F(PreprocessorTest, UndefMacroProgrammatically) {
  PP->defineMacro("MY_MACRO", "42");
  EXPECT_TRUE(PP->isMacroDefined("MY_MACRO"));
  
  PP->undefMacro("MY_MACRO");
  EXPECT_FALSE(PP->isMacroDefined("MY_MACRO"));
}

TEST_F(PreprocessorTest, GetMacroReturnsNullForUndefined) {
  EXPECT_EQ(PP->getMacro("NONEXISTENT"), nullptr);
}

TEST_F(PreprocessorTest, PredefinedMacrosFromConfig) {
  PreprocessorConfig config;
  config.PredefinedMacros["CUSTOM"] = "123";
  
  auto pp = std::make_unique<Preprocessor>(config, SM, Diags);
  EXPECT_TRUE(pp->isMacroDefined("CUSTOM"));
  
  std::string source = "CUSTOM";
  std::string result = pp->processText(source);
  EXPECT_EQ(stripTrailingNewlines(result), "123");
}

//===----------------------------------------------------------------------===//
// Integration / Multi-feature Tests
//===----------------------------------------------------------------------===//

TEST_F(PreprocessorTest, DefineAndUseInConditional) {
  std::string source = 
    "#define DEBUG 1\n"
    "#if DEBUG\n"
    "debug_code();\n"
    "#endif\n"
    "release_code();";
  std::string result = preprocess(source);
  EXPECT_NE(result.find("debug_code();"), std::string::npos);
  EXPECT_NE(result.find("release_code();"), std::string::npos);
}

TEST_F(PreprocessorTest, UndefThenIfdef) {
  std::string source = 
    "#define X\n"
    "#ifdef X\n"
    "first\n"
    "#endif\n"
    "#undef X\n"
    "#ifdef X\n"
    "second\n"
    "#endif\n"
    "done";
  std::string result = preprocess(source);
  EXPECT_NE(result.find("first"), std::string::npos);
  EXPECT_EQ(result.find("second"), std::string::npos);
  EXPECT_NE(result.find("done"), std::string::npos);
}

TEST_F(PreprocessorTest, MacroExpansionInCode) {
  std::string source = 
    "#define BUFFER_SIZE 1024\n"
    "#define MAX_ITEMS 100\n"
    "char buffer[BUFFER_SIZE];\n"
    "int items[MAX_ITEMS];";
  std::string result = preprocess(source);
  EXPECT_NE(result.find("char buffer[1024];"), std::string::npos);
  EXPECT_NE(result.find("int items[100];"), std::string::npos);
}

TEST_F(PreprocessorTest, FunctionMacroInConditional) {
  std::string source = 
    "#define PLATFORM 2\n"
    "#define WRAP(x) (x)\n"
    "#if PLATFORM == 2\n"
    "WRAP(42)\n"
    "#endif";
  std::string result = preprocess(source);
  EXPECT_NE(result.find("(42)"), std::string::npos);
}

TEST_F(PreprocessorTest, HeaderGuardPattern) {
  std::string source = 
    "#ifndef MY_HEADER_H\n"
    "#define MY_HEADER_H\n"
    "int foo();\n"
    "#endif";
  std::string result = preprocess(source);
  EXPECT_NE(result.find("int foo();"), std::string::npos);
  
  // Processing the same content again should still work
  // (MY_HEADER_H is now defined, so content would be skipped)
  EXPECT_TRUE(PP->isMacroDefined("MY_HEADER_H"));
}

TEST_F(PreprocessorTest, PragmaOnce) {
  std::string source = 
    "#pragma once\n"
    "int bar();";
  std::string result = preprocess(source);
  EXPECT_NE(result.find("int bar();"), std::string::npos);
}

TEST_F(PreprocessorTest, EmptyInput) {
  std::string source = "";
  std::string result = preprocess(source);
  EXPECT_TRUE(result.empty());
}

TEST_F(PreprocessorTest, NoDirectives) {
  std::string source = "int main() {\n  return 0;\n}";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "int main() {\n  return 0;\n}");
}

TEST_F(PreprocessorTest, CommentStrippingInDefine) {
  std::string source = "#define X 42 // this is a comment\nX";
  std::string result = preprocess(source);
  // The macro body should not include the comment
  EXPECT_EQ(stripTrailingNewlines(result), "42");
}

TEST_F(PreprocessorTest, MultipleDefineUndef) {
  std::string source = 
    "#define A 1\n"
    "A\n"
    "#undef A\n"
    "#define A 2\n"
    "A";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "1\n2");
}

TEST_F(PreprocessorTest, ConditionalWithMacroExpansion) {
  std::string source = 
    "#define VER 3\n"
    "#if VER == 3\n"
    "v3_code\n"
    "#elif VER == 2\n"
    "v2_code\n"
    "#else\n"
    "other_code\n"
    "#endif";
  std::string result = preprocess(source);
  EXPECT_NE(result.find("v3_code"), std::string::npos);
  EXPECT_EQ(result.find("v2_code"), std::string::npos);
  EXPECT_EQ(result.find("other_code"), std::string::npos);
}

// Edge case: deeply nested conditionals
TEST_F(PreprocessorTest, DeeplyNestedConditionals) {
  std::string source = 
    "#if 1\n"
    "#if 1\n"
    "#if 1\n"
    "deep\n"
    "#endif\n"
    "#endif\n"
    "#endif";
  std::string result = preprocess(source);
  EXPECT_NE(result.find("deep"), std::string::npos);
}

// Edge case: macro expanding to another macro
TEST_F(PreprocessorTest, MacroChainExpansion) {
  std::string source = 
    "#define LEVEL3 999\n"
    "#define LEVEL2 LEVEL3\n"
    "#define LEVEL1 LEVEL2\n"
    "LEVEL1";
  std::string result = preprocess(source);
  EXPECT_EQ(stripTrailingNewlines(result), "999");
}

}  // anonymous namespace
