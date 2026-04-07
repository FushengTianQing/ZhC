"""
ZHC Language Server

提供完整的 Language Server Protocol 实现，支持代码补全、诊断、导航等功能。
"""

import json
import sys
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

        # 简单的语法检查
        try:
            # 调用词法分析器
            from zhc.parser.lexer import tokenize
            tokens, lexer_errors = tokenize(doc.text)

            # 基本的括号匹配检查
            stack = []
            lines = doc.text.split("\n")
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

        except Exception as e:
            # 编译错误
            diagnostics.append(Diagnostic(
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=0, character=1)
                ),
                severity=DiagnosticSeverity.ERROR,
                message=f"编译错误: {str(e)}"
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

        # 内置函数补全
        builtin_funcs = [
            ("打印", "void 打印(任意值)", "打印到标准输出"),
            ("读取", "字符串 读取()", "从标准输入读取"),
            ("长度", "整数型 长度(容器)", "获取容器长度"),
            ("获取", "元素 获取(容器, 整数型)", "获取容器元素"),
            ("设置", "空 设置(容器, 整数型, 元素)", "设置容器元素"),
        ]

        for func, signature, doc in builtin_funcs:
            if func.startswith(current_word):
                completions.append(CompletionItem(
                    label=func,
                    kind=CompletionItemKind.FUNCTION,
                    detail=signature,
                    documentation=doc,
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

            # 简单的符号识别
            word = self._get_word_at_position(line, char_num)

            # 关键字文档
            keyword_docs = {
                "整数型": "**整数型** (Integer)\n\n32 位有符号整数类型。\n\n示例: `整数型 x = 42;`",
                "浮点型": "**浮点型** (Float)\n\n64 位双精度浮点数类型。\n\n示例: `浮点型 x = 3.14;`",
                "字符串型": "**字符串型** (String)\n\n不可变字符串类型。\n\n示例: `字符串型 s = \"Hello\";`",
                "布尔型": "**布尔型** (Boolean)\n\n布尔值类型，值为 `真` 或 `假`。\n\n示例: `布尔型 flag = 真;`",
                "如果": "**如果** (If)\n\n条件语句。\n\n```zhc\n如果 (condition) {\n    // 代码\n}\n```",
                "当": "**当** (While)\n\n循环语句。\n\n```zhc\n当 (condition) {\n    // 代码\n}\n```",
                "函数": "**函数** (Function)\n\n声明一个函数。\n\n```zhc\n函数 函数名(参数) -> 返回类型 {\n    // 代码\n}\n```",
                "返回": "**返回** (Return)\n\n从函数返回值。\n\n```zhc\n返回 value;\n```",
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


def main():
    """主入口"""
    server = LanguageServer()
    server.run()


if __name__ == "__main__":
    main()
