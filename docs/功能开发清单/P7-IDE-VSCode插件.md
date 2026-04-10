# P7-IDE-VSCode插件完善 开发分析文档

## 基本信息

| 字段 | 内容 |
|------|------|
| **优先级** | P7 |
| **功能模块** | IDE (集成开发环境) |
| **功能名称** | VS Code 插件完善 |
| **文档版本** | 1.0.0 |
| **创建日期** | 2026-04-10 |
| **预计工时** | 约 3-4 周 |

---

## 1. 功能概述

VS Code 是最流行的代码编辑器之一。完善的 VS Code 插件可以为 ZhC 开发者提供优秀的编程体验，包括语法高亮、代码补全、错误诊断、格式化等功能。

### 1.1 核心目标

- 实现完整的语法高亮
- 提供智能代码补全
- 显示实时错误诊断
- 支持代码格式化
- 集成调试功能

### 1.2 插件功能清单

| 功能 | 优先级 | 状态 |
|------|--------|------|
| 语法高亮 | P0 | 基础已有 |
| 代码补全 | P0 | 待完善 |
| 错误诊断 | P1 | 待实现 |
| 代码格式化 | P1 | 待实现 |
| 悬停提示 | P1 | 待实现 |
| 跳转到定义 | P2 | 待实现 |
| 查找引用 | P2 | 待实现 |
| 重命名符号 | P2 | 待实现 |
| 代码折叠 | P2 | 待实现 |
| 调试支持 | P3 | 待实现 |

---

## 2. 技术背景

### 2.1 VS Code 扩展架构

```
┌─────────────────────────────────────────────────────────────┐
│                    VS Code 扩展架构                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 Extension Host (Node.js)               │   │
│  │                                                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │   │
│  │  │  Language   │  │   Debug     │  │   Tools     │   │   │
│  │  │   Server    │  │  Adapter    │  │             │   │   │
│  │  │  (LSP)     │  │             │  │  Formatter  │   │   │
│  │  │             │  │             │  │             │   │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘   │   │
│  └─────────┼────────────────┼────────────────┼───────────┘   │
│            │                │                │               │
│            ▼                ▼                ▼               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  zhclang Language Server              │   │
│  │              (通过 Language Server Protocol)           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 LSP (Language Server Protocol)

LSP 是 VS Code 和语言服务器之间的通信协议，支持：
- 文本同步
- 诊断信息
- 代码补全
- 悬停信息
- 跳转到定义
- 查找引用
- 格式化

---

## 3. 详细设计

### 3.1 插件架构

```
zhc-vscode/
├── package.json                # 插件配置
├── tsconfig.json              # TypeScript 配置
├── src/
│   ├── extension.ts           # 插件入口
│   ├── language-configuration.ts # 语言配置
│   ├── syntaxes/
│   │   └── zhc.tmLanguage.json  # 语法高亮定义
│   ├── lsp/
│   │   ├── client.ts          # LSP 客户端
│   │   └── server.ts          # LSP 服务器
│   ├── commands/
│   │   └── formatter.ts       # 格式化命令
│   ├── providers/
│   │   ├── completion.ts      # 补全提供者
│   │   ├── hover.ts           # 悬停提供者
│   │   ├── definition.ts      # 定义跳转
│   │   └── reference.ts       # 引用查找
│   └── utils/
│       ├── parser.ts           # 语法解析
│       └── analyzer.ts         # 语义分析
└── README.md
```

### 3.2 语法高亮定义

```jsonc
// syntaxes/zhc.tmLanguage.json
{
  "$schema": "https://raw.githubusercontent.com/martinring/tmlanguage/master/tmlanguage.json",
  "name": "ZhC",
  "patterns": [
    {
      "name": "comment.line.zhc",
      "match": "//.*$"
    },
    {
      "name": "comment.block.zhc",
      "begin": "/\\*",
      "end": "\\*/"
    },
    {
      "name": "keyword.control.zhc",
      "match": "\\b(如果|则|否则|结束|对于|从|到|执行|当|返回|函数|结构体|枚举|导入|命名空间|常量的|变量的)\\b"
    },
    {
      "name": "keyword.type.zhc",
      "match": "\\b(整数型|长整数型|浮点型|双精度型|字符型|布尔型|字符串型|空类型|指针型)\\b"
    },
    {
      "name": "string.quoted.zhc",
      "begin": "\"",
      "end": "\"",
      "patterns": [
        {
          "name": "constant.character.escape.zhc",
          "match": "\\\\[nrt\\\\\"\"]"
        },
        {
          "name": "constant.character.unicode.zhc",
          "match": "\\\\u[0-9a-fA-F]{4}"
        }
      ]
    },
    {
      "name": "constant.numeric.zhc",
      "match": "\\b(\\d+\\.\\d+(f|F)?|\\d+(i|I|l|L)?|0x[0-9a-fA-F]+)\\b"
    },
    {
      "name": "entity.name.function.zhc",
      "match": "\\b([\\u4e00-\\u9fa5_a-zA-Z][\\u4e00-\\u9fa5_a-zA-Z0-9]*)\\s*(?=\\()"
    },
    {
      "name": "variable.parameter.zhc",
      "match": "(?<=[(,])\\s*([\\u4e00-\\u9fa5_a-zA-Z][\\u4e00-\\u9fa5_a-zA-Z0-9]*)\\s*(?=[,)])"
    }
  ],
  "scopeName": "source.zhc"
}
```

### 3.3 Language Server 实现

```typescript
// src/lsp/server.ts
import {
    createConnection,
    TextDocuments,
    ProposedFeatures,
    InitializeParams,
    InitializeResult,
    TextDocumentSyncKind,
    CompletionItem,
    CompletionItemKind,
    Hover,
    Definition,
    Diagnostic,
    Range,
    Position
} from 'vscode-languageserver/node';

import { ZhCAnalyzer } from '../utils/analyzer';
import { ZhCParser } from '../utils/parser';

const connection = createConnection(ProposedFeatures.all);
const documents = new TextDocuments();

const analyzer = new ZhCAnalyzer();
const parser = new ZhCParser();

// 初始化
connection.onInitialize((params: InitializeParams): InitializeResult => {
    return {
        capabilities: {
            textDocumentSync: TextDocumentSyncKind.Incremental,
            completionProvider: {
                resolveProvider: true,
                triggerCharacters: ['.', '(', ' ', ':']
            },
            hoverProvider: true,
            definitionProvider: true,
            referencesProvider: true,
            documentFormattingProvider: true,
            documentRangeFormattingProvider: true,
        }
    };
});

// 文档变化时更新分析
documents.onDidChangeContent(change => {
    const text = change.document.getText();
    const diagnostics = analyzeDocument(change.document.uri, text);
    connection.sendDiagnostics({ uri: change.document.uri, diagnostics });
});

function analyzeDocument(uri: string, text: string): Diagnostic[] {
    const diagnostics: Diagnostic[] = [];

    try {
        const ast = parser.parse(text);
        const symbols = analyzer.analyze(ast);

        // 检查语法和语义错误
        for (const error of analyzer.errors) {
            diagnostics.push({
                severity: DiagnosticSeverity.Error,
                range: {
                    start: Position.create(error.line - 1, error.column - 1),
                    end: Position.create(error.line - 1, error.column + error.length)
                },
                message: error.message,
                source: 'zhc'
            });
        }
    } catch (e) {
        // 解析错误处理
    }

    return diagnostics;
}

// 代码补全
connection.onCompletion((params): CompletionItem[] => {
    const doc = documents.get(params.textDocument.uri);
    if (!doc) return [];

    const position = params.position;
    const text = doc.getText();
    const context = getCompletionContext(text, position);

    const items: CompletionItem[] = [];

    // 关键词补全
    for (const keyword of KEYWORDS) {
        if (keyword.startsWith(context.prefix)) {
            items.push({
                label: keyword,
                kind: CompletionItemKind.Keyword,
                detail: KEYWORD_DESCRIPTIONS[keyword]
            });
        }
    }

    // 类型补全
    for (const type of TYPES) {
        if (type.startsWith(context.prefix)) {
            items.push({
                label: type,
                kind: CompletionItemKind.Class,
                detail: '类型'
            });
        }
    }

    // 函数补全
    for (const func of getVisibleFunctions(text, position)) {
        items.push({
            label: func.name,
            kind: CompletionItemKind.Function,
            detail: func.signature,
            documentation: func.doc,
            insertText: func.insertText,
            insertTextFormat: InsertTextFormat.Snippet
        });
    }

    return items;
});

// 悬停信息
connection.onHover((params): Hover | null => {
    const doc = documents.get(params.textDocument.uri);
    if (!doc) return null;

    const position = params.position;
    const text = doc.getText();
    const symbol = getSymbolAtPosition(text, position);

    if (symbol) {
        const info = analyzer.getSymbolInfo(symbol);
        if (info) {
            return {
                contents: {
                    kind: MarkupKind.Markdown,
                    value: `**${info.name}**\n\n${info.type}\n\n${info.description}`
                }
            };
        }
    }

    return null;
});

documents.listen(connection);
connection.listen();
```

### 3.4 代码格式化器

```typescript
// src/commands/formatter.ts
import {
    DocumentFormattingParams,
    TextEdit,
    Range,
    Position
} from 'vscode-languageserver/node';

export class ZhCFormatter {
    formatDocument(params: DocumentFormattingParams, text: string): TextEdit[] {
        const options = params.options;
        const edits: TextEdit[] = [];

        try {
            const ast = this.parse(text);

            // 1. 缩进规范化
            edits.push(...this.normalizeIndentation(text, options.tabSize));

            // 2. 空行规范化
            edits.push(...this.normalizeBlankLines(text));

            // 3. 括号空格
            edits.push(...this.formatBrackets(text));

            // 4. 操作符空格
            edits.push(...this.formatOperators(text));

            // 5. 尾随空格移除
            edits.push(...this.removeTrailingWhitespace(text));

        } catch (e) {
            console.error('Formatting error:', e);
        }

        return edits;
    }

    private normalizeIndentation(text: string, tabSize: number): TextEdit[] {
        const edits: TextEdit[] = [];
        const lines = text.split('\n');
        const indent = ' '.repeat(tabSize);

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const match = line.match(/^(\s*)/);
            if (match) {
                const spaces = match[1];
                const expectedSpaces = this.calculateIndentation(i, lines);

                if (spaces !== expectedSpaces) {
                    edits.push({
                        range: Range.create(
                            Position.create(i, 0),
                            Position.create(i, spaces.length)
                        ),
                        newText: expectedSpaces
                    });
                }
            }
        }

        return edits;
    }

    private formatBrackets(text: string): TextEdit[] {
        const edits: TextEdit[] = [];
        // 添加花括号前后的空格
        const patterns = [
            { before: /(\S)\{/g, after: '$1 {', desc: '开括号前空格' },
            { before: /\{(\S)/g, after: '{ $1', desc: '开括号后空格' },
            { before: /\{(\s)/g, after: '{ $1', desc: '开括号后保留空格' },
            { before: /\{(\s*\n)/g, after: '{\n', desc: '开括号后换行' },
            { before: /(\s*)\}/g, after: '\n$1}', desc: '闭括号单独一行' },
        ];

        // ... 实现格式化逻辑
        return edits;
    }
}
```

### 3.5 包配置

```json
{
  "name": "zhc-vscode",
  "displayName": "ZhC Language Support",
  "description": "Language support for ZhC programming language",
  "version": "0.1.0",
  "publisher": "zhc-team",
  "engines": {
    "vscode": "^1.75.0"
  },
  "categories": [
    "Programming Languages",
    "IntelliSense",
    "Formatters",
    "Debuggers"
  ],
  "contributes": {
    "languages": [
      {
        "id": "zhc",
        "aliases": ["ZhC", "zhc"],
        "extensions": [".zhc"],
        "configuration": "./language-configuration.json"
      }
    ],
    "grammars": [
      {
        "language": "zhc",
        "scopeName": "source.zhc",
        "path": "./syntaxes/zhc.tmLanguage.json"
      }
    ],
    "configuration": {
      "type": "object",
      "title": "ZhC Configuration",
      "properties": {
        "zhc.server.path": {
          "type": "string",
          "default": "zhclang",
          "description": "Path to zhclang language server"
        },
        "zhc.format.tabSize": {
          "type": "number",
          "default": 4,
          "description": "Tab size for formatting"
        },
        "zhc.format.insertSpaces": {
          "type": "boolean",
          "default": true,
          "description": "Insert spaces instead of tabs"
        }
      }
    },
    "commands": [
      {
        "command": "zhc.formatDocument",
        "title": "Format Document",
        "category": "ZhC"
      }
    ]
  }
}
```

---

## 4. 实现方案

### 4.1 第一阶段：语法和补全

1. **完善语法高亮**
   - 添加更多 token 类型
   - 支持嵌套注释
   - 字符串转义序列

2. **实现代码补全**
   - 关键词补全
   - 类型补全
   - 函数签名补全

### 4.2 第二阶段：LSP 功能

1. **错误诊断**
   - 语法错误
   - 类型错误
   - 未定义变量

2. **悬停信息**
   - 类型信息
   - 函数签名
   - 文档注释

### 4.3 第三阶段：导航功能

1. **跳转到定义**
2. **查找引用**
3. **符号大纲**

### 4.4 第四阶段：调试

1. **调试适配器**
2. **断点支持**
3. **变量查看**

---

## 5. 测试策略

### 5.1 单元测试

```typescript
// src/test/completion.test.ts
import * as assert from 'assert';
import { getCompletionItems } from '../providers/completion';

suite('Completion Tests', () => {
    test('Should complete keywords', () => {
        const text = '如';
        const items = getCompletionItems(text, 0);
        assert.ok(items.some(i => i.label === '如果'));
        assert.ok(items.some(i => i.label === '否则'));
    });

    test('Should complete types', () => {
        const text = '变量 x: 整';
        const items = getCompletionItems(text, text.length);
        assert.ok(items.some(i => i.label === '整数型'));
    });

    test('Should show function signature', () => {
        const text = '打印行(';
        const items = getCompletionItems(text, text.length);
        const print = items.find(i => i.label === '打印行');
        assert.ok(print?.detail?.includes('函数'));
    });
});
```

---

## 6. 参考资料

- [VS Code Extension API](https://code.visualstudio.com/api)
- [Language Server Protocol](https://microsoft.github.io/language-server-protocol/)
- [VS Code Extension Samples](https://github.com/microsoft/vscode-extension-samples)
- [TextMate Grammar](https://macromates.com/manual/en/language_grammars)
