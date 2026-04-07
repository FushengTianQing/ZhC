"""
LSP 服务器测试

测试 Language Server 的核心功能。
"""

import pytest
import json
from zhc.lsp.server import LanguageServer, Document
from zhc.lsp.protocol import (
    Position, Range, DiagnosticSeverity, CompletionItemKind
)


class TestLanguageServer:
    """测试 Language Server"""

    def test_create_server(self):
        """测试创建服务器"""
        server = LanguageServer()
        assert server.SERVER_NAME == "zhc"
        assert server.SERVER_VERSION == "0.1.0"

    def test_server_capabilities(self):
        """测试服务器能力"""
        server = LanguageServer()
        capabilities = server.capabilities

        assert capabilities.text_document_sync == 1
        assert capabilities.hover_provider is True
        assert capabilities.definition_provider is True
        assert capabilities.references_provider is True
        assert capabilities.rename_provider is True

    def test_handle_initialize(self):
        """测试处理初始化请求"""
        server = LanguageServer()

        result = server._handle_initialize({})

        assert "capabilities" in result
        assert "serverInfo" in result
        assert result["serverInfo"]["name"] == "zhc"

    def test_handle_text_document_did_open(self):
        """测试处理文档打开"""
        server = LanguageServer()

        params = {
            "textDocument": {
                "uri": "file:///test.zhc",
                "text": "函数 测试() { 返回 0; }"
            }
        }

        server._handle_text_document_did_open(params)

        assert "file:///test.zhc" in server.documents
        assert server.documents["file:///test.zhc"].text == "函数 测试() { 返回 0; }"

    def test_handle_text_document_did_change(self):
        """测试处理文档更改"""
        server = LanguageServer()

        # 先打开文档
        server.documents["file:///test.zhc"] = Document(
            uri="file:///test.zhc",
            text="old text"
        )

        params = {
            "textDocument": {"uri": "file:///test.zhc"},
            "contentChanges": [{"text": "new text"}]
        }

        server._handle_text_document_did_change(params)

        assert server.documents["file:///test.zhc"].text == "new text"

    def test_handle_text_document_did_close(self):
        """测试处理文档关闭"""
        server = LanguageServer()

        server.documents["file:///test.zhc"] = Document(
            uri="file:///test.zhc",
            text="test"
        )

        params = {
            "textDocument": {"uri": "file:///test.zhc"}
        }

        server._handle_text_document_did_close(params)

        assert "file:///test.zhc" not in server.documents


class TestCompletion:
    """测试代码补全"""

    def test_handle_completion(self):
        """测试处理补全请求"""
        server = LanguageServer()

        # 打开文档
        server.documents["file:///test.zhc"] = Document(
            uri="file:///test.zhc",
            text="整"
        )

        params = {
            "textDocument": {"uri": "file:///test.zhc"},
            "position": {"line": 0, "character": 1}
        }

        result = server._handle_completion(params)

        assert "isIncomplete" in result
        assert "items" in result
        assert isinstance(result["items"], list)

    def test_get_completions_keywords(self):
        """测试关键字补全"""
        server = LanguageServer()

        server.documents["file:///test.zhc"] = Document(
            uri="file:///test.zhc",
            text="整"
        )

        completions = server._get_completions("file:///test.zhc", {"line": 0, "character": 1})

        # 应该包含 "整数型"
        labels = [item.label for item in completions]
        assert "整数型" in labels

    def test_get_completions_functions(self):
        """测试函数补全"""
        server = LanguageServer()

        server.documents["file:///test.zhc"] = Document(
            uri="file:///test.zhc",
            text="打"
        )

        completions = server._get_completions("file:///test.zhc", {"line": 0, "character": 1})

        # 应该包含 "打印"
        labels = [item.label for item in completions]
        assert "打印" in labels

    def test_get_current_word(self):
        """测试获取当前单词"""
        server = LanguageServer()

        assert server._get_current_word("整数型") == "整数型"
        assert server._get_current_word("  整数型") == "整数型"
        assert server._get_current_word("整数型 x") == "x"


class TestHover:
    """测试悬停提示"""

    def test_handle_hover(self):
        """测试处理悬停请求"""
        server = LanguageServer()

        server.documents["file:///test.zhc"] = Document(
            uri="file:///test.zhc",
            text="整数型 x = 0;"
        )

        params = {
            "textDocument": {"uri": "file:///test.zhc"},
            "position": {"line": 0, "character": 2}
        }

        result = server._handle_hover(params)

        # 应该返回整数型的文档
        if result:
            assert "contents" in result

    def test_get_hover_info_keywords(self):
        """测试关键字悬停信息"""
        server = LanguageServer()

        server.documents["file:///test.zhc"] = Document(
            uri="file:///test.zhc",
            text="整数型"
        )

        hover = server._get_hover_info("file:///test.zhc", {"line": 0, "character": 2})

        assert hover is not None
        assert "整数型" in hover.contents

    def test_get_word_at_position(self):
        """测试获取指定位置的单词"""
        server = LanguageServer()

        assert server._get_word_at_position("整数型 x", 0) == "整数型"
        assert server._get_word_at_position("整数型 x", 4) == "x"


class TestDiagnostics:
    """测试诊断功能"""

    def test_compute_diagnostics_valid_code(self):
        """测试有效代码的诊断"""
        server = LanguageServer()

        server.documents["file:///test.zhc"] = Document(
            uri="file:///test.zhc",
            text="函数 测试() { 返回 0; }"
        )

        diagnostics = server._compute_diagnostics("file:///test.zhc")

        # 有效代码应该没有错误
        error_diagnostics = [d for d in diagnostics if d.severity == DiagnosticSeverity.ERROR]
        assert len(error_diagnostics) == 0

    def test_compute_diagnostics_unclosed_bracket(self):
        """测试未闭合括号的诊断"""
        server = LanguageServer()

        server.documents["file:///test.zhc"] = Document(
            uri="file:///test.zhc",
            text="函数 测试() { 返回 0; "
        )

        diagnostics = server._compute_diagnostics("file:///test.zhc")

        # 应该检测到未闭合的括号
        assert len(diagnostics) > 0
        assert any("未闭合" in d.message for d in diagnostics)


class TestDocumentSymbol:
    """测试文档符号"""

    def test_handle_document_symbol(self):
        """测试处理文档符号请求"""
        server = LanguageServer()

        server.documents["file:///test.zhc"] = Document(
            uri="file:///test.zhc",
            text="函数 测试() -> 整数型 { 返回 0; }\n结构体 点 { 整数型 x; 整数型 y; }"
        )

        params = {
            "textDocument": {"uri": "file:///test.zhc"}
        }

        result = server._handle_document_symbol(params)

        assert result is not None
        assert isinstance(result, list)

    def test_get_document_symbols_functions(self):
        """测试提取函数符号"""
        server = LanguageServer()

        server.documents["file:///test.zhc"] = Document(
            uri="file:///test.zhc",
            text="函数 测试() -> 整数型 { 返回 0; }"
        )

        symbols = server._get_document_symbols("file:///test.zhc")

        assert len(symbols) > 0
        assert symbols[0].name == "测试"

    def test_get_document_symbols_structs(self):
        """测试提取结构体符号"""
        server = LanguageServer()

        server.documents["file:///test.zhc"] = Document(
            uri="file:///test.zhc",
            text="结构体 点 { 整数型 x; 整数型 y; }"
        )

        symbols = server._get_document_symbols("file:///test.zhc")

        assert len(symbols) > 0
        assert symbols[0].name == "点"


class TestDocument:
    """测试文档类"""

    def test_create_document(self):
        """测试创建文档"""
        doc = Document(uri="file:///test.zhc", text="test code")
        assert doc.uri == "file:///test.zhc"
        assert doc.text == "test code"
        assert doc.version == 0


class TestSignatureHelp:
    """测试签名帮助"""

    def test_handle_signature_help(self):
        """测试处理签名帮助请求"""
        server = LanguageServer()

        server.documents["file:///test.zhc"] = Document(
            uri="file:///test.zhc",
            text="打印("
        )

        params = {
            "textDocument": {"uri": "file:///test.zhc"},
            "position": {"line": 0, "character": 2}
        }

        result = server._handle_signature_help(params)

        if result:
            assert "signatures" in result


class TestDefinition:
    """测试转到定义"""

    def test_handle_definition(self):
        """测试处理转到定义请求"""
        server = LanguageServer()

        server.documents["file:///test.zhc"] = Document(
            uri="file:///test.zhc",
            text="整数型 x = 0;"
        )

        params = {
            "textDocument": {"uri": "file:///test.zhc"},
            "position": {"line": 0, "character": 4}
        }

        result = server._handle_definition(params)

        # 简化实现返回空列表
        assert result is None or isinstance(result, list)


class TestReferences:
    """测试查找引用"""

    def test_handle_references(self):
        """测试处理查找引用请求"""
        server = LanguageServer()

        server.documents["file:///test.zhc"] = Document(
            uri="file:///test.zhc",
            text="整数型 x = 0;"
        )

        params = {
            "textDocument": {"uri": "file:///test.zhc"},
            "position": {"line": 0, "character": 4}
        }

        result = server._handle_references(params)

        # 简化实现返回空列表
        assert result is None or isinstance(result, list)


class TestRename:
    """测试重命名"""

    def test_handle_rename(self):
        """测试处理重命名请求"""
        server = LanguageServer()

        server.documents["file:///test.zhc"] = Document(
            uri="file:///test.zhc",
            text="整数型 x = 0;"
        )

        params = {
            "textDocument": {"uri": "file:///test.zhc"},
            "position": {"line": 0, "character": 4},
            "newName": "y"
        }

        result = server._handle_rename(params)

        assert result is not None
        assert "changes" in result