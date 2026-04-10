# P7-IDE-JetBrains IDE插件 开发分析文档

## 基本信息

| 字段 | 内容 |
|------|------|
| **优先级** | P7 |
| **功能模块** | IDE (集成开发环境) |
| **功能名称** | JetBrains IDE 插件 |
| **文档版本** | 1.0.0 |
| **创建日期** | 2026-04-10 |
| **预计工时** | 约 3-4 周 |

---

## 1. 功能概述

为 JetBrains 系列 IDE (IntelliJ IDEA, PyCharm, WebStorm 等) 提供 ZhC 语言支持。JetBrains IDE 以其强大的代码分析功能著称，插件将充分利用这些能力。

### 1.1 核心目标

- 完整的语法高亮
- 智能代码补全
- 代码分析和重构
- 调试支持
- 框架集成

### 1.2 功能清单

| 功能 | 优先级 | 说明 |
|------|--------|------|
| 语法高亮 | P0 | 基于 Grammar-Kit |
| 文件类型 | P0 | 自定义文件图标 |
| 缩进 | P0 | 智能缩进 |
| 代码补全 | P1 | 关键词/类型/函数 |
| 错误检查 | P1 | 重型分析 |
| 导航 | P2 | 跳转到定义 |
| 重构 | P2 | 重命名等 |
| 调试 | P3 | 行断点等 |

---

## 2. 技术背景

### 2.1 JetBrains 插件架构

```
┌─────────────────────────────────────────────────────────────┐
│                  JetBrains 插件架构                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Parser    │  │  PSI Tree   │  │  Indexes   │        │
│  │  (Grammar)  │──│  (AST)      │──│  (Search)  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Language 相关的组件                      │   │
│  │  ├── SyntaxHighlighter                             │   │
│  │  ├── CodeStyleProvider                             │   │
│  │  ├── EnterHandler                                  │   │
│  │  ├── Commenter                                     │   │
│  │  ├── formatter                                    │   │
│  │  └── intention                                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              功能组件 (取决于语言)                     │   │
│  │  ├── CodeFoldingProvider                           │   │
│  │  ├── StructureViewProvider                         │   │
│  │  ├── GoToSymbolProvider                            │   │
│  │  └── RefactoringProvider                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 详细设计

### 3.1 项目结构

```
zhc-intellij/
├── src/
│   ├── main/
│   │   ├── kotlin/
│   │   │   └── com/zhc/
│   │   │       ├── ZhCPlugin.kt         # 插件入口
│   │   │       ├── parser/
│   │   │       │   ├── ZhCLexer.kt       # 词法分析器
│   │   │       │   ├── ZhCParser.kt      # 语法分析器
│   │   │       │   └── ZhCElementTypes.kt # 元素类型
│   │   │       ├── psi/
│   │   │       │   ├── ZhCFile.kt        # PSI 文件
│   │   │       │   ├── ZhCTokenType.kt   # Token 类型
│   │   │       │   └── nodes/            # PSI 节点
│   │   │       ├── lexer/
│   │   │       │   └── _ZhCLexer.flex    # Flex 词法定义
│   │   │       ├── grammar/
│   │   │       │   └── ZhC.bnf          # BNF 语法定义
│   │   │       ├── highlighting/
│   │   │       │   └── ZhCSyntaxHighlighter.kt
│   │   │       ├── completion/
│   │   │       │   └── ZhCCompletionContributor.kt
│   │   │       ├── inspection/
│   │   │       │   └── ZhCGlobalInspectionTool.kt
│   │   │       ├── formatter/
│   │   │       │   └── ZhCFormatter.kt
│   │   │       └── navigation/
│   │   │           └── ZhCGotoDeclarationHandler.kt
│   │   └── resources/
│   │       └── META-INF/
│   │           └── plugin.xml
│   └── test/
│       └── kotlin/
│           └── com/zhc/
│               └── ZhCParserTest.kt
├── build.gradle.kts
├── settings.gradle.kts
└── gradle.properties
```

### 3.2 语法定义 (BNF)

```bnf
// grammar/ZhC.bnf
{
  parserClass="com.zhc.parser.ZhCParser"
  extends="{FileElementImpl}"

  tokens=[
    IDENTIFIER="regexp:[\u4e00-\u9fa5_a-zA-Z][\u4e00-\u9fa5_a-zA-Z0-9]*"
    INTEGER="regexp:0x[0-9a-fA-F]+|\d+"
    FLOAT="regexp:\d+\.\d+"
    STRING="regexp:\"[^\"]*\""
    COMMENT="regexp://.*"
    WS="regexp:\s+"
  ]

  helpers=[
    expression
    type
    statement
  ]
}

ZhCFile ::= shebang? HeaderComment? Item*

shebang ::= "#!/.*"
HeaderComment ::= "/**" DOC_TEXT "*/"

Item ::= Function | Struct | Enum | Import | Namespace | GlobalVariable

Function ::= "函数" Type? IDENTIFIER "(" ParameterList? ")" ("->" Type)? Block
ParameterList ::= Parameter ("," Parameter)*
Parameter ::= IDENTIFIER ":" Type

Struct ::= "结构体" IDENTIFIER ("实现" TypeList)? "{" StructMember* "}"
StructMember ::= IDENTIFIER ":" Type ("=" Expression)? ";"

Enum ::= "枚举" IDENTIFIER "{" EnumMember ("," EnumMember)* "}"
EnumMember ::= IDENTIFIER ("=" Expression)?

Type ::= BaseType | PointerType | ArrayType | FunctionType
BaseType ::= "整数型" | "长整数型" | "浮点型" | "双精度型" | "字符型" | "布尔型" | "字符串型"
PointerType ::= Type "*"
ArrayType ::= Type "[" Expression? "]"
FunctionType ::= Type "(" TypeList? ")"

Block ::= "{" Statement* "}"
Statement ::=
    IfStatement
  | WhileStatement
  | ForStatement
  | ReturnStatement
  | ExpressionStatement
  | LocalVariableDeclaration
  | Assignment
  | BreakStatement
  | ContinueStatement

IfStatement ::= "如果" Expression "则" Block ("否则" Block)? "结束"
WhileStatement ::= "当" Expression Block "结束"
ForStatement ::= "对于" IDENTIFIER "从" Expression "到" Expression Block "结束"
ReturnStatement ::= "返回" Expression? ";"
BreakStatement ::= "中断" ";"
ContinueStatement ::= "继续" ";"
LocalVariableDeclaration ::= ("变量" | "常量") IDENTIFIER ":" Type ("=" Expression)? ";"
Assignment ::= Expression "=" Expression ";"

Expression ::= BinaryExpression | UnaryExpression | PrimaryExpression

BinaryExpression ::= Expression BinaryOp Expression
BinaryOp ::= "+" | "-" | "*" | "/" | "%" | "==" | "!=" | "<" | ">" | "<=" | ">=" | "&&" | "||"

UnaryExpression ::= UnaryOp Expression
UnaryOp ::= "+" | "-" | "!" | "*" | "&"

PrimaryExpression ::=
    Identifier
  | Literal
  | FunctionCall
  | ArrayAccess
  | MemberAccess
  | "(" Expression ")"

Identifier ::= IDENTIFIER
Literal ::= IntegerLiteral | FloatLiteral | StringLiteral | CharLiteral | BooleanLiteral
FunctionCall ::= IDENTIFIER "(" ArgumentList? ")"
ArgumentList ::= Expression ("," Expression)*
ArrayAccess ::= Expression "[" Expression "]"
MemberAccess ::= Expression "." IDENTIFIER
```

### 3.3 插件配置

```xml
<!-- src/main/resources/META-INF/plugin.xml -->
<idea-plugin>
    <id>com.zhc.intellij</id>
    <name>ZhC Language Support</name>
    <version>0.1.0</version>
    <vendor>ZhC Team</vendor>
    <description>Language support for ZhC programming language</description>

    <depends>com.intellij.modules.platform</depends>

    <extensions defaultExtensionNs="com.intellij">
        <!-- 文件类型 -->
        <fileType name="ZhC"
                  language="ZhC"
                  extension="zhc"
                  fieldName="ZhCFileType.INSTANCE"
                  factoryClass="com.zhc.ZhCFileTypeFactory"/>

        <!-- 语言 -->
        <languageName name="ZhC"
                      implementationClass="com.zhc.language.ZhCLanguage"/>

        <!-- 语法高亮 -->
        <syntaxHighlighter key="ZhC"
                           implementationClass="com.zhc.highlighting.ZhCSyntaxHighlighter"/>

        <!-- 代码风格 -->
        <codeStyleSettingsProvider implementation="com.zhc.formatter.ZhCCodeStyleSettingsProvider"/>
        <indentOptionsProvider implementation="com.zhc.formatter.ZhCIndentOptionsProvider"/>

        <!-- 格式化器 -->
        <formatterBlockExtension implementation="com.zhc.formatter.ZhCFormattingModelBuilder"/>

        <!-- 补全 -->
        <completion.contributor language="ZhC"
                               implementationClass="com.zhc.completion.ZhCCompletionContributor"/>

        <!-- 引用贡献 -->
        <contributor.language.xml.file.bundle name="messages.ZhCBundle"
                                             path="messages/ZhCBundle.properties"/>
    </extensions>

    <actions>
        <action id="ZhC.FormatCode"
                class="com.zhc.actions.ZhCFormatAction"
                text="Format ZhC Code"
                description="Format ZhC source code">
            <keyboard-shortcut keymap="$default" first-keystroke="ctrl shift F"/>
        </action>
    </actions>
</idea-plugin>
```

### 3.4 语法高亮器

```kotlin
// highlighting/ZhCSyntaxHighlighter.kt
package com.zhc.highlighting

import com.intellij.lexer.Lexer
import com.intellij.openapi.editor.DefaultLanguageHighlighterColors as Colors
import com.intellij.openapi.editor.HighlighterColors
import com.intellij.openapi.editor.colors.TextAttributesKey
import com.intellij.openapi.editor.colors.TextAttributesKey.createTextAttributesKey
import com.intellij.openapi.fileTypes.SyntaxHighlighterBase
import com.intellij.psi.tree.IElementType
import com.zhc.parser.ZhCElementTypes

class ZhCSyntaxHighlighter : SyntaxHighlighterBase() {

    companion object {
        val KEYWORD = createTextAttributesKey("ZHc_KEYWORD", Colors.KEYWORD)
        val TYPE = createTextAttributesKey("ZHc_TYPE", Colors.CLASS_NAME)
        val FUNCTION = createTextAttributesKey("ZHc_FUNCTION", Colors.FUNCTION_DECLARATION)
        val STRING = createTextAttributesKey("ZHc_STRING", Colors.STRING)
        val NUMBER = createTextAttributesKey("ZHc_NUMBER", Colors.NUMBER)
        val COMMENT = createTextAttributesKey("ZHc_COMMENT", Colors.LINE_COMMENT)
        val IDENTIFIER = createTextAttributesKey("ZHc_IDENTIFIER", Colors.IDENTIFIER)
        val OPERATOR = createTextAttributesKey("ZHc_OPERATOR", Colors.OPERATION_SIGN)
        val BRACES = createTextAttributesKey("ZHc_BRACES", Colors.BRACES)
    }

    override fun getHighlightingLexer(): Lexer = ZhCLexerAdapter()

    override fun getTokenHighlights(tokenType: IElementType?): Array<TextAttributesKey> {
        return when (tokenType) {
            ZhCElementTypes.KEYWORD -> arrayOf(KEYWORD)
            ZhCElementTypes.TYPE -> arrayOf(TYPE)
            ZhCElementTypes.FUNCTION_CALL,
            ZhCElementTypes.FUNCTION_DECL -> arrayOf(FUNCTION)
            ZhCElementTypes.STRING_LITERAL -> arrayOf(STRING)
            ZhCElementTypes.INTEGER_LITERAL,
            ZhCElementTypes.FLOAT_LITERAL -> arrayOf(NUMBER)
            ZhCElementTypes.LINE_COMMENT,
            ZhCElementTypes.BLOCK_COMMENT -> arrayOf(COMMENT)
            ZhCElementTypes.IDENTIFIER -> arrayOf(IDENTIFIER)
            ZhCElementTypes.OPERATOR -> arrayOf(OPERATOR)
            ZhCElementTypes.LBRACE, ZhCElementTypes.RBRACE,
            ZhCElementTypes.LPAREN, ZhCElementTypes.RPAREN,
            ZhCElementTypes.LBRACKET, ZhCElementTypes.RBRACKET -> arrayOf(BRACES)
            else -> TextAttributesKey.EMPTY_ARRAY
        }
    }
}
```

### 3.5 代码补全

```kotlin
// completion/ZhCCompletionContributor.kt
package com.zhc.completion

import com.intellij.codeInsight.completion.CompletionContributor
import com.intellij.codeInsight.completion.CompletionParameters
import com.intellij.codeInsight.completion.CompletionResultSet
import com.intellij.codeInsight.completion.KeywordCompletionContributor
import com.intellij.patterns.PlatformPatterns

class ZhCCompletionContributor : CompletionContributor() {

    init {
        // 关键词补全
        extend(CompletionType.BASIC,
            PlatformPatterns.psiElement(),
            ZhCKeywordCompletionProvider)
    }
}

object ZhCKeywordCompletionProvider : CompletionProvider<CompletionParameters>() {

    private val KEYWORDS = listOf(
        // 控制流
        "如果", "则", "否则", "结束",
        "对于", "从", "到", "执行",
        "当", "返回", "中断", "继续",

        // 声明
        "函数", "结构体", "枚举", "导入", "命名空间",
        "变量", "常量", "新建", "空",

        // 类型
        "整数型", "长整数型", "浮点型", "双精度型",
        "字符型", "布尔型", "字符串型", "空类型", "指针型"
    )

    private val TYPE_KEYWORDS = listOf(
        "整数型", "长整数型", "浮点型", "双精度型",
        "字符型", "布尔型", "字符串型", "空类型", "指针型"
    )

    override fun addCompletions(
        parameters: CompletionParameters,
        context: ProcessingContext,
        result: CompletionResultSet
    ) {
        val position = parameters.position
        val text = position.text

        // 根据上下文提供补全
        KEYWORDS.filter { it.startsWith(text) }.forEach {
            result.addElement(
                LookupElementBuilder.create(it)
                    .withPresentableText(it)
                    .withTypeText(if (it in TYPE_KEYWORDS) "类型" else "关键词")
                    .bold()
            )
        }
    }
}
```

### 3.6 构建配置

```kotlin
// build.gradle.kts
plugins {
    id("org.jetbrains.kotlin") version "1.9.0"
    id("org.jetbrains.intellij") version "1.15.0"
}

group = "com.zhc"
version = "0.1.0"

repositories {
    mavenCentral()
}

intellij {
    pluginName = "ZhC Language Support"
    plugins.set(listOf("com.intellij.java"))
    version.set("2023.1")
    type.set("IC")
}

tasks {
    patchPluginXml {
        version.set(project.version.toString())
    }

    runIde {
        version.set("2023.1")
    }
}
```

---

## 4. 实现方案

### 4.1 第一阶段：基础支持

1. **Grammar-Kit 配置**
   - 定义 BNF 语法
   - 生成 Parser
   - 生成 PSI 节点

2. **语法高亮**
   - Token 类型定义
   - 高亮颜色配置

3. **文件类型**
   - .zhc 文件关联
   - 图标设置

### 4.2 第二阶段：编辑支持

1. **智能缩进**
2. **代码折叠**
3. **注释处理**
4. **格式化**

### 4.3 第三阶段：代码分析

1. **代码补全**
2. **错误检查**
3. **意图行动**

### 4.4 第四阶段：高级功能

1. **重构支持**
2. **调试集成**
3. **单元测试**

---

## 5. 参考资料

- [IntelliJ SDK Documentation](https://plugins.jetbrains.com/docs/intellij/)
- [Grammar-Kit](https://github.com/JetBrains/Grammar-Kit)
- [Custom Language Support Tutorial](https://plugins.jetbrains.com/docs/intellij/custom-language-support.html)
- [IntelliJ Platform SDK](https://github.com/JetBrains/intellij-sdk-docs)
