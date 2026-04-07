"""
ZHC Language Server

提供完整的 Language Server Protocol 实现，支持代码补全、诊断、导航等功能。
"""

import json
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from threading import Lock

from .protocol import (
    Position, Range, Location, Diagnostic, DiagnosticSeverity,
    CompletionItem, CompletionItemKind, Hover, TextEdit,
    ServerCapabilities, ResponseError, SignatureHelp, SignatureInformation,
    DocumentSymbol, SymbolKind, SymbolInformation
)
from .jsonrpc import JSONRPCServer, StdinTransport, ErrorCode


class LanguageServer:
    """ZHC Language Server 实现"""

    # 服务器名称和版本
    SERVER_NAME = "zhc"
    SERVER_VERSION = "0.1.0"

    def __init__(self):
        self.server = JSONRPCServer()
        self.capabilities = ServerCapabilities()

        # 文档管理
        self.documents: Dict[str, "Document"] = {}
        self._lock = Lock()

        # 注册处理器
        self._register_handlers()

        # 设置能力
        self._setup_capabilities()

    def _setup_capabilities(self) -> None:
        """设置服务器能力"""
        self.capabilities.text_document_sync = 1  # 全量同步
        self.capabilities.completion_provider = {"triggerCharacters": [".", "("]}
        self.capabilities.hover_provider = True
        self.capabilities.signature_help_provider = {"triggerCharacters": ["(", ","]}
        self.capabilities.definition_provider = True
        self.capabilities.references_provider = True
        self.capabilities.document_symbol_provider = True
        self.capabilities.rename_provider = True
        self.server.set_capabilities(self.capabilities.to_dict())

    def _register_handlers(self) -> None:
        """注册请求处理器"""
        # 初始化
        self.server.register_handler("initialize", self._handle_initialize)
        self.server.register_handler("initialized", self._handle_initialized)

        # 文档同步
        self.server.register_handler("textDocument/didOpen", self._handle_text_document_did_open)
        self.server.register_handler("textDocument/didChange", self._handle_text_document_did_change)
        self.server.register_handler("textDocument/didClose", self._handle_text_document_did_close)
        self.server.register_handler("textDocument/didSave", self._handle_text_document_did_save)

        # 代码补全
        self.server.register_handler("textDocument/completion", self._handle_completion)
        self.server.register_handler("completionItem/resolve", self._handle_completion_resolve)

        # 悬停
        self.server.register_handler("textDocument/hover", self._handle_hover)

        # 签名帮助
        self.server.register_handler("textDocument/signatureHelp", self._handle_signature_help)

        # 定义和引用
        self.server.register_handler("textDocument/definition", self._handle_definition)
        self.server.register_handler("textDocument/references", self._handle_references)

        # 文档符号
        self.server.register_handler("textDocument/documentSymbol", self._handle_document_symbol)
        self.server.register_handler("workspace/symbol", self._handle_workspace_symbol)

        # 重命名
        self.server.register_handler("textDocument/rename", self._handle_rename)

        # 关闭
        self.server.register_handler("shutdown", self._handle_shutdown)
        self.server.register_handler("exit", self._handle_exit)

    def run(self) -> None:
        """运行服务器"""
        self.server.run()

    # ==================== 初始化 ====================

    def _handle_initialize(self, params: Optional[Dict]) -> Dict:
        """处理初始化请求"""
        capabilities = self.capabilities.to_dict()

        return {
            "capabilities": capabilities,
            "serverInfo": {
                "name": self.SERVER_NAME,
                "version": self.SERVER_VERSION
            }
        }

    def _handle_initialized(self, params: Optional[Dict]) -> None:
        """处理初始化完成通知"""
        # 发送欢迎消息（可选）
        pass

    # ==================== 文档同步 ====================

    def _handle_text_document_did_open(self, params: Optional[Dict]) -> None:
        """处理文档打开"""
        if not params:
            return

        text_doc = params.get("textDocument", {})
        uri = text_doc.get("uri", "")
        text = text_doc.get("text", "")

        with self._lock:
            self.documents[uri] = Document(uri=uri, text=text)

        # 发布初始诊断
        self._publish_diagnostics(uri)

    def _handle_text_document_did_change(self, params: Optional[Dict]) -> None:
        """处理文档更改"""
        if not params:
            return

        text_doc = params.get("textDocument", {})
        uri = text_doc.get("uri", "")
        changes = params.get("contentChanges", [])

        with self._lock:
            if uri in self.documents:
                doc = self.documents[uri]
                for change in changes:
                    if "text" in change:
                        doc.text = change["text"]
                        # 重新解析符号表
                        doc.symbols = {}
                        doc._parse_symbols()

        # 重新发布诊断
        self._publish_diagnostics(uri)

    def _handle_text_document_did_close(self, params: Optional[Dict]) -> None:
        """处理文档关闭"""
        if not params:
            return

        uri = params.get("textDocument", {}).get("uri", "")

        with self._lock:
            if uri in self.documents:
                del self.documents[uri]

    def _handle_text_document_did_save(self, params: Optional[Dict]) -> None:
        """处理文档保存"""
        # 可选：保存时执行额外操作
        pass

    def _publish_diagnostics(self, uri: str) -> None:
        """发布诊断信息"""
        diagnostics = self._compute_diagnostics(uri)

        # 发送诊断通知
        notification = {
            "method": "textDocument/publishDiagnostics",
            "params": {
                "uri": uri,
                "diagnostics": [d.to_dict() for d in diagnostics]
            }
        }

        # 输出到 stdout（由主循环处理）
        print(json.dumps(notification), flush=True)

    def _compute_diagnostics(self, uri: str) -> List[Diagnostic]:
        """计算文档诊断信息"""
        diagnostics = []

        with self._lock:
            doc = self.documents.get(uri)
            if not doc:
                return diagnostics

        # 词法分析检查
        try:
            from zhc.parser.lexer import tokenize
            tokens, lexer_errors = tokenize(doc.text)

            # 转换词法错误为诊断
            for error in lexer_errors:
                diagnostics.append(Diagnostic(
                    range=Range(
                        start=Position(line=error.line - 1 if hasattr(error, 'line') else 0,
                                       character=error.column - 1 if hasattr(error, 'column') else 0),
                        end=Position(line=error.line - 1 if hasattr(error, 'line') else 0,
                                     character=error.column if hasattr(error, 'column') else 1)
                    ),
                    severity=DiagnosticSeverity.ERROR,
                    message=f"词法错误: {str(error)}"
                ))

        except Exception as e:
            diagnostics.append(Diagnostic(
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=0, character=1)
                ),
                severity=DiagnosticSeverity.ERROR,
                message=f"词法分析错误: {str(e)}"
            ))

        # 括号匹配检查
        diagnostics.extend(self._check_bracket_matching(doc.text))

        # 语法结构检查
        diagnostics.extend(self._check_syntax_structure(doc.text))

        # 未使用变量检查（警告）
        diagnostics.extend(self._check_unused_symbols(doc))

        return diagnostics

    def _check_bracket_matching(self, text: str) -> List[Diagnostic]:
        """检查括号匹配"""
        diagnostics = []
        stack = []
        lines = text.split("\n")

        for line_num, line in enumerate(lines):
            for col, char in enumerate(line):
                if char in "({[":
                    stack.append((line_num, col, char))
                elif char in ")}]":
                    if not stack:
                        diagnostics.append(Diagnostic(
                            range=Range(
                                start=Position(line=line_num, character=col),
                                end=Position(line=line_num, character=col + 1)
                            ),
                            severity=DiagnosticSeverity.ERROR,
                            message=f"多余的 '{char}'"
                        ))
                    else:
                        open_pos = stack.pop()
                        expected = {"(": ")", "{": "}", "[": "]"}
                        if expected.get(open_pos[2]) != char:
                            diagnostics.append(Diagnostic(
                                range=Range(
                                    start=Position(line=line_num, character=col),
                                    end=Position(line=line_num, character=col + 1)
                                ),
                                severity=DiagnosticSeverity.ERROR,
                                message=f"不匹配的括号: 期望 '{expected[open_pos[2]]}'"
                            ))

        # 检查未闭合的括号
        for line_num, col, char in stack:
            diagnostics.append(Diagnostic(
                range=Range(
                    start=Position(line=line_num, character=col),
                    end=Position(line=line_num, character=col + 1)
                ),
                severity=DiagnosticSeverity.ERROR,
                message=f"未闭合的 '{char}'"
            ))

        return diagnostics

    def _check_syntax_structure(self, text: str) -> List[Diagnostic]:
        """检查语法结构"""
        diagnostics = []
        lines = text.split("\n")

        for line_num, line in enumerate(lines):
            stripped = line.strip()

            # 检查函数声明是否缺少返回类型
            if stripped.startswith("函数 ") and "->" not in stripped and "{" not in stripped:
                # 函数声明但没有返回类型和函数体
                if "(" in stripped and ")" in stripped:
                    diagnostics.append(Diagnostic(
                        range=Range(
                            start=Position(line=line_num, character=0),
                            end=Position(line=line_num, character=len(line))
                        ),
                        severity=DiagnosticSeverity.WARNING,
                        message="函数声明缺少返回类型，建议添加 '-> 返回类型'"
                    ))

            # 检查结构体/类是否缺少成员
            if stripped.startswith("结构体 ") or stripped.startswith("类 "):
                if stripped.endswith("{") and line_num + 1 < len(lines):
                    next_line = lines[line_num + 1].strip()
                    if next_line == "}":
                        diagnostics.append(Diagnostic(
                            range=Range(
                                start=Position(line=line_num, character=0),
                                end=Position(line=line_num, character=len(line))
                            ),
                            severity=DiagnosticSeverity.WARNING,
                            message="空的结构体/类定义"
                        ))

            # 检查未完成的条件语句
            if stripped == "如果":
                diagnostics.append(Diagnostic(
                    range=Range(
                        start=Position(line=line_num, character=0),
                        end=Position(line=line_num, character=len(line))
                    ),
                    severity=DiagnosticSeverity.ERROR,
                    message="未完成的条件语句: '如果' 后需要条件表达式"
                ))

            # 检查未完成的循环语句
            if stripped == "当":
                diagnostics.append(Diagnostic(
                    range=Range(
                        start=Position(line=line_num, character=0),
                        end=Position(line=line_num, character=len(line))
                    ),
                    severity=DiagnosticSeverity.ERROR,
                    message="未完成的循环语句: '当' 后需要条件表达式"
                ))

        return diagnostics

    def _check_unused_symbols(self, doc: "Document") -> List[Diagnostic]:
        """检查未使用的符号"""
        diagnostics = []

        # 获取文档中定义的所有符号
        defined_symbols = set(doc.symbols.keys())

        # 检查每个符号是否被使用
        for symbol_name, symbol_info in doc.symbols.items():
            # 跳过关键字和内置函数
            if symbol_name in ["打印", "读取", "长度", "获取", "设置"]:
                continue

            # 简单检查：符号是否在文档其他地方出现
            # 注意：这只是简单的文本匹配，实际应该使用语义分析
            lines = doc.text.split("\n")
            used = False

            for line_num, line in enumerate(lines):
                # 跳过定义行
                if line_num == symbol_info.line:
                    continue

                # 检查符号是否被使用
                if symbol_name in line:
                    used = True
                    break

            if not used and symbol_info.kind == SymbolKind.VARIABLE:
                diagnostics.append(Diagnostic(
                    range=Range(
                        start=Position(line=symbol_info.line, character=0),
                        end=Position(line=symbol_info.line, character=len(lines[symbol_info.line]) if symbol_info.line < len(lines) else 1)
                    ),
                    severity=DiagnosticSeverity.WARNING,
                    message=f"变量 '{symbol_name}' 可能未被使用"
                ))

        return diagnostics

    # ==================== 代码补全 ====================

    def _handle_completion(self, params: Optional[Dict]) -> Dict:
        """处理代码补全请求"""
        if not params:
            return {"isIncomplete": False, "items": []}

        text_doc = params.get("textDocument", {})
        position = params.get("position", {})
        uri = text_doc.get("uri", "")

        completions = self._get_completions(uri, position)

        return {
            "isIncomplete": False,
            "items": [item.to_dict() for item in completions]
        }

    def _get_completions(self, uri: str, position: Dict) -> List[CompletionItem]:
        """获取补全项"""
        completions = []

        with self._lock:
            doc = self.documents.get(uri)
            if not doc:
                return completions

            # 获取当前行
            lines = doc.text.split("\n")
            line_num = position.get("line", 0)
            char_num = position.get("character", 0)

            if line_num >= len(lines):
                return completions

            line = lines[line_num]
            prefix = line[:char_num] if char_num <= len(line) else line

            # 获取已输入的文本
            current_word = self._get_current_word(prefix)

            # 分析上下文
            context = self._analyze_completion_context(lines, line_num, char_num)

        # 根据上下文类型提供不同的补全
        if context == "type_declaration":
            # 类型声明上下文 - 补全类型关键字
            completions.extend(self._get_type_completions(current_word))
        elif context == "member_access":
            # 成员访问上下文 - 补全结构体/类成员
            completions.extend(self._get_member_completions(prefix, doc))
        elif context == "after_dot":
            # 点操作符后 - 补全方法和属性
            completions.extend(self._get_method_completions(current_word))
        else:
            # 默认上下文 - 关键字 + 符号
            completions.extend(self._get_default_completions(current_word, doc))

        return completions

    def _analyze_completion_context(self, lines: List[str], line_num: int, char_num: int) -> str:
        """分析补全上下文"""
        if line_num >= len(lines):
            return "default"

        line = lines[line_num]
        prefix = line[:char_num] if char_num <= len(line) else line

        # 类型声明: 类型关键字后
        type_keywords = ["整数型", "浮点型", "字符型", "字符串型", "布尔型", "空型", "字节型", "双精度浮点型", "长整数型", "短整数型", "逻辑型"]
        for kw in type_keywords:
            if prefix.endswith(kw):
                return "type_declaration"

        # 成员访问: 点操作符后
        if "." in prefix and not prefix.endswith("."):
            return "member_access"

        # 在括号中
        if "(" in prefix:
            return "argument"

        return "default"

    def _get_type_completions(self, current_word: str) -> List[CompletionItem]:
        """获取类型补全"""
        types = [
            ("整数型", "32位有符号整数", "INT"),
            ("浮点型", "64位双精度浮点数", "FLOAT"),
            ("双精度浮点型", "64位双精度浮点数", "DOUBLE"),
            ("字符型", "单个字符", "CHAR"),
            ("字符串型", "字符串", "STRING"),
            ("布尔型", "布尔值", "BOOL"),
            ("字节型", "单字节", "BYTE"),
            ("长整数型", "长整数", "LONG"),
            ("短整数型", "短整数", "SHORT"),
            ("逻辑型", "布尔值", "BOOL"),
            ("空型", "空类型", "VOID"),
        ]

        completions = []
        for name, detail, _ in types:
            if name.startswith(current_word):
                completions.append(CompletionItem(
                    label=name,
                    kind=CompletionItemKind.KEYWORD,
                    detail=detail,
                    insert_text=name
                ))
        return completions

    def _get_member_completions(self, prefix: str, doc: "Document") -> List[CompletionItem]:
        """获取成员补全"""
        completions = []
        # 提取前缀中的对象名
        obj_name = prefix.rsplit(".", 1)[-1] if "." in prefix else ""

        # 内置方法
        builtin_methods = [
            ("长度", "整数型", "获取长度"),
            ("获取", "元素", "获取元素"),
            ("设置", "空型", "设置元素"),
            ("添加", "空型", "添加元素"),
            ("删除", "布尔型", "删除元素"),
            ("清空", "空型", "清空容器"),
        ]

        for name, ret_type, doc_str in builtin_methods:
            if name.startswith(obj_name):
                completions.append(CompletionItem(
                    label=name,
                    kind=CompletionItemKind.METHOD,
                    detail=f"{ret_type} {name}()",
                    documentation=doc_str,
                    insert_text=name
                ))

        return completions

    def _get_method_completions(self, current_word: str) -> List[CompletionItem]:
        """获取方法补全"""
        methods = [
            ("长度", "整数型 长度()", "获取长度"),
            ("获取", "元素 获取(整数型 索引)", "获取元素"),
            ("设置", "空型 设置(整数型 索引, 元素)", "设置元素"),
            ("复制", "容器 复制()", "复制容器"),
            ("清空", "空型 清空()", "清空容器"),
            ("是否为空", "布尔型 是否为空()", "检查是否为空"),
            ("包含", "布尔型 包含(元素)", "检查是否包含元素"),
            ("转字符串", "字符串型 转字符串()", "转换为字符串"),
        ]

        completions = []
        for name, signature, doc_str in methods:
            if name.startswith(current_word):
                completions.append(CompletionItem(
                    label=name,
                    kind=CompletionItemKind.METHOD,
                    detail=signature,
                    documentation=doc_str,
                    insert_text=name
                ))
        return completions

    def _get_default_completions(self, current_word: str, doc: "Document") -> List[CompletionItem]:
        """获取默认补全（关键字 + 符号表）"""
        completions = []

        # 关键字补全
        keywords = [
            ("整数型", "整数类型", CompletionItemKind.KEYWORD),
            ("浮点型", "浮点数类型", CompletionItemKind.KEYWORD),
            ("字符型", "字符类型", CompletionItemKind.KEYWORD),
            ("字符串型", "字符串类型", CompletionItemKind.KEYWORD),
            ("布尔型", "布尔类型", CompletionItemKind.KEYWORD),
            ("空型", "空类型", CompletionItemKind.KEYWORD),
            ("如果", "条件语句", CompletionItemKind.KEYWORD),
            ("否则", "条件语句的 else 分支", CompletionItemKind.KEYWORD),
            ("当", "循环语句", CompletionItemKind.KEYWORD),
            ("匹配", "模式匹配", CompletionItemKind.KEYWORD),
            ("当", "匹配分支", CompletionItemKind.KEYWORD),
            ("返回", "返回语句", CompletionItemKind.KEYWORD),
            ("函数", "函数声明", CompletionItemKind.KEYWORD),
            ("结构体", "结构体声明", CompletionItemKind.KEYWORD),
            ("类", "类声明", CompletionItemKind.KEYWORD),
            ("枚举", "枚举声明", CompletionItemKind.KEYWORD),
            ("接口", "接口声明", CompletionItemKind.KEYWORD),
            ("公共", "公共访问修饰符", CompletionItemKind.KEYWORD),
            ("私有", "私有访问修饰符", CompletionItemKind.KEYWORD),
            ("保护", "保护访问修饰符", CompletionItemKind.KEYWORD),
            ("异步", "异步函数声明", CompletionItemKind.KEYWORD),
            ("等待", "等待异步操作", CompletionItemKind.KEYWORD),
            ("尝试", "异常捕获", CompletionItemKind.KEYWORD),
            ("捕获", "异常捕获", CompletionItemKind.KEYWORD),
            ("最终", "最终块", CompletionItemKind.KEYWORD),
            ("让出", "生成器让出", CompletionItemKind.KEYWORD),
        ]

        for keyword, detail, kind in keywords:
            if keyword.startswith(current_word):
                completions.append(CompletionItem(
                    label=keyword,
                    kind=kind,
                    detail=detail,
                    insert_text=keyword
                ))

        # 符号表补全
        for name, symbol_info in doc.symbols.items():
            if name.startswith(current_word) and name != current_word:
                # 将 SymbolKind 映射到 CompletionItemKind
                kind_map = {
                    SymbolKind.FUNCTION: CompletionItemKind.FUNCTION,
                    SymbolKind.CLASS: CompletionItemKind.CLASS,
                    SymbolKind.ENUM: CompletionItemKind.ENUM,
                    SymbolKind.VARIABLE: CompletionItemKind.VARIABLE,
                    SymbolKind.METHOD: CompletionItemKind.METHOD,
                    SymbolKind.PROPERTY: CompletionItemKind.PROPERTY,
                    SymbolKind.FIELD: CompletionItemKind.FIELD,
                }
                kind = kind_map.get(symbol_info.kind, CompletionItemKind.TEXT)
                completions.append(CompletionItem(
                    label=name,
                    kind=kind,
                    detail=symbol_info.detail,
                    insert_text=name
                ))

        # 内置函数补全
        builtin_funcs = [
            ("打印", "空型 打印(任意值)", "打印到标准输出"),
            ("读取", "字符串型 读取()", "从标准输入读取"),
            ("长度", "整数型 长度(容器)", "获取容器长度"),
            ("获取", "元素 获取(容器, 整数型)", "获取容器元素"),
            ("设置", "空型 设置(容器, 整数型, 元素)", "设置容器元素"),
            ("字符串", "字符串型 字符串(任意值)", "转换为字符串"),
            ("整数", "整数型 整数(任意值)", "转换为整数"),
            ("浮点", "浮点型 浮点(任意值)", "转换为浮点数"),
            ("是空", "布尔型 是空(容器)", "检查是否为空"),
            ("包含", "布尔型 包含(容器, 元素)", "检查是否包含元素"),
        ]

        for func, signature, doc_str in builtin_funcs:
            if func.startswith(current_word):
                completions.append(CompletionItem(
                    label=func,
                    kind=CompletionItemKind.FUNCTION,
                    detail=signature,
                    documentation=doc_str,
                    insert_text=func
                ))

        return completions

    def _get_current_word(self, line: str) -> str:
        """获取当前输入的单词"""
        word = ""
        for char in reversed(line):
            if char.isalnum() or char == "_":
                word = char + word
            else:
                break
        return word

    def _handle_completion_resolve(self, params: Optional[Dict]) -> Dict:
        """处理补全项解析"""
        # 提供补全项的详细信息
        if params and "data" in params:
            return params
        return params or {}

    # ==================== 悬停 ====================

    def _handle_hover(self, params: Optional[Dict]) -> Optional[Dict]:
        """处理悬停请求"""
        if not params:
            return None

        text_doc = params.get("textDocument", {})
        position = params.get("position", {})
        uri = text_doc.get("uri", "")

        hover_info = self._get_hover_info(uri, position)

        if hover_info:
            return hover_info.to_dict()
        return None

    def _get_hover_info(self, uri: str, position: Dict) -> Optional[Hover]:
        """获取悬停信息"""
        with self._lock:
            doc = self.documents.get(uri)
            if not doc:
                return None

            line_num = position.get("line", 0)
            char_num = position.get("character", 0)

            lines = doc.text.split("\n")
            if line_num >= len(lines):
                return None

            line = lines[line_num]
            if char_num >= len(line):
                return None

            # 获取当前单词
            word = self._get_word_at_position(line, char_num)

            # 首先检查符号表中的符号
            if word in doc.symbols:
                symbol = doc.symbols[word]
                kind_names = {
                    SymbolKind.FUNCTION: "函数",
                    SymbolKind.CLASS: "类",
                    SymbolKind.ENUM: "枚举",
                    SymbolKind.VARIABLE: "变量",
                    SymbolKind.METHOD: "方法",
                    SymbolKind.PROPERTY: "属性",
                }
                kind_name = kind_names.get(symbol.kind, "符号")
                return Hover(contents=f"**{kind_name}: {symbol.name}**\n\n类型: {symbol.detail}")

            # 关键字文档
            keyword_docs = {
                "整数型": "**整数型** (Integer)\n\n32 位有符号整数类型。\n\n示例: `整数型 x = 42;`",
                "浮点型": "**浮点型** (Float)\n\n64 位双精度浮点数类型。\n\n示例: `浮点型 x = 3.14;`",
                "双精度浮点型": "**双精度浮点型** (Double)\n\n64 位双精度浮点数类型。\n\n示例: `双精度浮点型 x = 3.1415926;`",
                "字符型": "**字符型** (Char)\n\n单个字符类型。\n\n示例: `字符型 c = 'A';`",
                "字符串型": "**字符串型** (String)\n\n不可变字符串类型。\n\n示例: `字符串型 s = \"Hello\";`",
                "布尔型": "**布尔型** (Boolean)\n\n布尔值类型，值为 `真` 或 `假`。\n\n示例: `布尔型 flag = 真;`",
                "字节型": "**字节型** (Byte)\n\n单字节无符号整数类型 (0-255)。\n\n示例: `字节型 b = 255;`",
                "长整数型": "**长整数型** (Long)\n\n64 位有符号整数类型。\n\n示例: `长整数型 x = 9223372036854775807;`",
                "短整数型": "**短整数型** (Short)\n\n16 位有符号整数类型。\n\n示例: `短整数型 x = 32767;`",
                "逻辑型": "**逻辑型** (Boolean)\n\n布尔值类型，同布尔型。\n\n示例: `逻辑型 flag = 假;`",
                "空型": "**空型** (Void)\n\n表示无返回值。\n\n示例: `函数 空型 无返回值() {}`",
                "如果": "**如果** (If)\n\n条件语句。\n\n```zhc\n如果 (condition) {\n    // 条件为真时执行\n} 否则 {\n    // 条件为假时执行\n}\n```",
                "否则": "**否则** (Else)\n\n条件语句的 else 分支。\n\n必须跟在 `如果` 块之后。",
                "当": "**当** (While/When)\n\n循环语句或模式匹配守卫。\n\n```zhc\n// 循环\n当 (condition) {\n    // 循环体\n}\n\n// 模式匹配\n匹配 value {\n    当 x > 10 -> // 守卫条件\n}\n```",
                "匹配": "**匹配** (Match)\n\n模式匹配语句。\n\n```zhc\n匹配 value {\n    模式1 -> 结果1\n    模式2 -> 结果2\n    _ -> 默认结果\n}\n```",
                "函数": "**函数** (Function)\n\n声明一个函数。\n\n```zhc\n函数 函数名(参数) -> 返回类型 {\n    // 函数体\n}\n```",
                "结构体": "**结构体** (Struct)\n\n声明一个结构体。\n\n```zhc\n结构体 结构体名 {\n    成员1: 类型1\n    成员2: 类型2\n}\n```",
                "类": "**类** (Class)\n\n声明一个类。\n\n```zhc\n类 类名 {\n    属性: 类型\n    函数 方法() {}\n}\n```",
                "枚举": "**枚举** (Enum)\n\n声明一个枚举类型。\n\n```zhc\n枚举 枚举名 {\n    选项1\n    选项2\n    选项3\n}\n```",
                "接口": "**接口** (Interface)\n\n声明一个接口。\n\n```zhc\n接口 接口名 {\n    方法1(): 返回类型\n    属性: 类型\n}\n```",
                "公共": "**公共** (Public)\n\n公共访问修饰符。\n\n可以被任何代码访问。",
                "私有": "**私有** (Private)\n\n私有访问修饰符。\n\n只能在定义它的类内部访问。",
                "保护": "**保护** (Protected)\n\n保护访问修饰符。\n\n可以在定义它的类及其子类中访问。",
                "异步": "**异步** (Async)\n\n异步函数声明。\n\n```zhc\n异步 函数 异步操作() -> Future[结果类型] {\n    // 异步操作\n}\n```",
                "等待": "**等待** (Await)\n\n等待异步操作完成。\n\n```zhc\n结果 = 等待 异步操作()\n```",
                "返回": "**返回** (Return)\n\n从函数返回值。\n\n```zhc\n返回 value;\n```",
                "尝试": "**尝试** (Try)\n\n异常捕获的开始。\n\n```zhc\n尝试 {\n    // 可能抛出异常的代码\n} 捕获 异常类型 e {\n    // 处理异常\n} 最终 {\n    // 总是执行的代码\n}\n```",
                "捕获": "**捕获** (Catch)\n\n异常捕获处理。\n\n跟在 `尝试` 块之后。",
                "最终": "**最终** (Finally)\n\n最终块。\n\n无论是否发生异常都会执行。",
                "让出": "**让出** (Yield)\n\n生成器让出语句。\n\n```zhc\n函数 生成器() -> 元素类型 {\n    让出 value1\n    让出 value2\n}\n```",
            }

            if word in keyword_docs:
                return Hover(contents=keyword_docs[word])

        return None

    def _get_word_at_position(self, line: str, char_num: int) -> str:
        """获取指定位置的单词"""
        start = char_num
        end = char_num

        while start > 0 and (line[start - 1].isalnum() or line[start - 1] == "_"):
            start -= 1

        while end < len(line) and (line[end].isalnum() or line[end] == "_"):
            end += 1

        return line[start:end]

    # ==================== 签名帮助 ====================

    def _handle_signature_help(self, params: Optional[Dict]) -> Optional[Dict]:
        """处理签名帮助请求"""
        if not params:
            return None

        text_doc = params.get("textDocument", {})
        position = params.get("position", {})
        uri = text_doc.get("uri", "")

        signature = self._get_signature_help(uri, position)

        if signature:
            return signature.to_dict()
        return None

    def _get_signature_help(self, uri: str, position: Dict) -> Optional[SignatureHelp]:
        """获取签名帮助"""
        with self._lock:
            doc = self.documents.get(uri)
            if not doc:
                return None

        # 简单的签名帮助实现
        # 实际应该分析函数调用上下文
        signatures = [
            SignatureInformation(
                label="打印(值)",
                documentation="打印值到标准输出",
                parameters=[]
            ),
            SignatureInformation(
                label="读取()",
                documentation="从标准输入读取一行",
                parameters=[]
            ),
            SignatureInformation(
                label="长度(容器)",
                documentation="获取容器长度",
                parameters=[]
            ),
        ]

        return SignatureHelp(signatures=signatures)

    # ==================== 定义和引用 ====================

    def _handle_definition(self, params: Optional[Dict]) -> Optional[List[Dict]]:
        """处理转到定义请求"""
        if not params:
            return None

        text_doc = params.get("textDocument", {})
        position = params.get("position", {})
        uri = text_doc.get("uri", "")

        locations = self._find_definition(uri, position)

        return [loc.to_dict() for loc in locations] if locations else None

    def _find_definition(self, uri: str, position: Dict) -> List[Location]:
        """查找定义位置"""
        # 简化实现
        # 实际应该使用符号表查找
        return []

    def _handle_references(self, params: Optional[Dict]) -> Optional[List[Dict]]:
        """处理查找引用请求"""
        if not params:
            return None

        text_doc = params.get("textDocument", {})
        position = params.get("position", {})
        uri = text_doc.get("uri", "")

        locations = self._find_references(uri, position)

        return [loc.to_dict() for loc in locations] if locations else None

    def _find_references(self, uri: str, position: Dict) -> List[Location]:
        """查找引用位置"""
        # 简化实现
        return []

    # ==================== 文档符号 ====================

    def _handle_document_symbol(self, params: Optional[Dict]) -> Optional[List[Dict]]:
        """处理文档符号请求"""
        if not params:
            return None

        uri = params.get("textDocument", {}).get("uri", "")

        symbols = self._get_document_symbols(uri)

        return [sym.to_dict() for sym in symbols] if symbols else None

    def _get_document_symbols(self, uri: str) -> List[DocumentSymbol]:
        """获取文档符号"""
        symbols = []

        with self._lock:
            doc = self.documents.get(uri)
            if not doc:
                return symbols

            # 简单的符号提取
            # 实际应该使用 AST
            lines = doc.text.split("\n")
            for line_num, line in enumerate(lines):
                stripped = line.strip()

                # 函数定义
                if stripped.startswith("函数 "):
                    parts = stripped.split("(")[0].replace("函数 ", "").split("->")
                    name = parts[0].strip()
                    return_type = parts[1].strip() if len(parts) > 1 else "空型"

                    symbols.append(DocumentSymbol(
                        name=name,
                        kind=SymbolKind.FUNCTION,
                        range=Range(
                            start=Position(line=line_num, character=0),
                            end=Position(line=line_num, character=len(line))
                        ),
                        selection_range=Range(
                            start=Position(line=line_num, character=2),
                            end=Position(line=line_num, character=2 + len(name))
                        ),
                        detail=return_type
                    ))

                # 结构体定义
                elif stripped.startswith("结构体 "):
                    name = stripped.replace("结构体 ", "").split("{")[0].strip()

                    symbols.append(DocumentSymbol(
                        name=name,
                        kind=SymbolKind.CLASS,
                        range=Range(
                            start=Position(line=line_num, character=0),
                            end=Position(line=line_num, character=len(line))
                        ),
                        selection_range=Range(
                            start=Position(line=line_num, character=3),
                            end=Position(line=line_num, character=3 + len(name))
                        )
                    ))

                # 类定义
                elif stripped.startswith("类 "):
                    name = stripped.replace("类 ", "").split("{")[0].strip()

                    symbols.append(DocumentSymbol(
                        name=name,
                        kind=SymbolKind.CLASS,
                        range=Range(
                            start=Position(line=line_num, character=0),
                            end=Position(line=line_num, character=len(line))
                        ),
                        selection_range=Range(
                            start=Position(line=line_num, character=1),
                            end=Position(line=line_num, character=1 + len(name))
                        )
                    ))

        return symbols

    def _handle_workspace_symbol(self, params: Optional[Dict]) -> Optional[List[Dict]]:
        """处理工作区符号请求"""
        if not params:
            return None

        query = params.get("query", "")

        # 简化实现
        symbols = []

        with self._lock:
            for uri, doc in self.documents.items():
                doc_symbols = self._get_document_symbols(uri)
                for sym in doc_symbols:
                    if query.lower() in sym.name.lower():
                        symbols.append(SymbolInformation(
                            name=sym.name,
                            kind=sym.kind,
                            location=Location(
                                uri=uri,
                                range=sym.range
                            )
                        ).to_dict())

        return symbols

    # ==================== 重命名 ====================

    def _handle_rename(self, params: Optional[Dict]) -> Optional[Dict]:
        """处理重命名请求"""
        if not params:
            return None

        # 简化实现
        return {
            "changes": {}
        }

    # ==================== 关闭 ====================

    def _handle_shutdown(self, params: Optional[Dict]) -> None:
        """处理关闭请求"""
        return None

    def _handle_exit(self, params: Optional[Dict]) -> None:
        """处理退出请求"""
        sys.exit(0)


class Document:
    """文档"""

    def __init__(self, uri: str, text: str = ""):
        self.uri = uri
        self.text = text
        self.version = 0
        # 符号表
        self.symbols: Dict[str, "SymbolInfo"] = {}
        self._parse_symbols()

    def _parse_symbols(self) -> None:
        """解析文档中的符号"""
        lines = self.text.split("\n")

        for line_num, line in enumerate(lines):
            stripped = line.strip()

            # 函数定义: 函数 函数名(...) -> 返回类型
            if stripped.startswith("函数 "):
                self._parse_function(line, line_num)

            # 结构体定义: 结构体 结构体名
            elif stripped.startswith("结构体 "):
                self._parse_struct(line, line_num)

            # 类定义: 类 类名
            elif stripped.startswith("类 "):
                self._parse_class(line, line_num)

            # 枚举定义: 枚举 枚举名
            elif stripped.startswith("枚举 "):
                self._parse_enum(line, line_num)

            # 变量声明: 变量类型 变量名 = ...
            else:
                self._parse_variables(line, line_num)

    def _parse_function(self, line: str, line_num: int) -> None:
        """解析函数定义"""
        # 函数 函数名(...) -> 返回类型 或 函数 函数名(...)
        if "->" in line:
            parts = line.split("->")
            sig_part = parts[0]
            return_type = parts[1].strip().split("{")[0].strip()
        else:
            sig_part = line
            return_type = "空型"

        # 提取函数名
        func_match = sig_part.replace("函数 ", "").split("(")[0].strip()
        if func_match:
            self.symbols[func_match] = SymbolInfo(
                name=func_match,
                kind=SymbolKind.FUNCTION,
                detail=return_type,
                line=line_num
            )

    def _parse_struct(self, line: str, line_num: int) -> None:
        """解析结构体定义"""
        name = line.replace("结构体 ", "").split("{")[0].strip()
        if name:
            self.symbols[name] = SymbolInfo(
                name=name,
                kind=SymbolKind.CLASS,
                detail="结构体",
                line=line_num
            )

    def _parse_class(self, line: str, line_num: int) -> None:
        """解析类定义"""
        name = line.replace("类 ", "").split("{")[0].strip()
        if name:
            self.symbols[name] = SymbolInfo(
                name=name,
                kind=SymbolKind.CLASS,
                detail="类",
                line=line_num
            )

    def _parse_enum(self, line: str, line_num: int) -> None:
        """解析枚举定义"""
        name = line.replace("枚举 ", "").split("{")[0].strip()
        if name:
            self.symbols[name] = SymbolInfo(
                name=name,
                kind=SymbolKind.ENUM,
                detail="枚举",
                line=line_num
            )

    def _parse_variables(self, line: str, line_num: int) -> None:
        """解析变量声明"""
        # 匹配: 类型名 变量名 = 或 类型名 变量名;
        import re
        # 变量声明模式
        type_patterns = ["整数型", "浮点型", "字符型", "字符串型", "布尔型", "空型", "字节型", "双精度浮点型"]

        for type_kw in type_patterns:
            if line.strip().startswith(type_kw):
                # 提取变量名
                rest = line.strip()[len(type_kw):].strip()
                # 变量名是第一个标识符
                match = re.match(r'^(\w+)\s*', rest)
                if match:
                    var_name = match.group(1)
                    if var_name and var_name not in ("=", "{", "}", "(", ")"):
                        self.symbols[var_name] = SymbolInfo(
                            name=var_name,
                            kind=SymbolKind.VARIABLE,
                            detail=type_kw,
                            line=line_num
                        )
                break


@dataclass
class SymbolInfo:
    """符号信息"""
    name: str
    kind: SymbolKind
    detail: str = ""
    line: int = 0


def main():
    """主入口"""
    server = LanguageServer()
    server.run()


if __name__ == "__main__":
    main()
