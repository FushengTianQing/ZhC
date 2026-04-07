"""
LSP 协议类型测试

测试 LSP 协议中定义的各种数据类型。
"""

import pytest
from zhc.lsp.protocol import (
    Position, Range, Location, Diagnostic, DiagnosticSeverity,
    CompletionItem, CompletionItemKind, Hover, TextEdit,
    Request, Response, Notification, ResponseError, ServerCapabilities
)


class TestPosition:
    """测试 Position 类型"""

    def test_create_position(self):
        """测试创建位置"""
        pos = Position(line=10, character=5)
        assert pos.line == 10
        assert pos.character == 5

    def test_position_to_dict(self):
        """测试位置转换为字典"""
        pos = Position(line=10, character=5)
        result = pos.to_dict()
        assert result == {"line": 10, "character": 5}

    def test_position_from_dict(self):
        """测试从字典创建位置"""
        data = {"line": 10, "character": 5}
        pos = Position.from_dict(data)
        assert pos.line == 10
        assert pos.character == 5


class TestRange:
    """测试 Range 类型"""

    def test_create_range(self):
        """测试创建范围"""
        start = Position(line=0, character=0)
        end = Position(line=10, character=5)
        range_obj = Range(start=start, end=end)
        assert range_obj.start.line == 0
        assert range_obj.end.line == 10

    def test_range_to_dict(self):
        """测试范围转换为字典"""
        start = Position(line=0, character=0)
        end = Position(line=10, character=5)
        range_obj = Range(start=start, end=end)
        result = range_obj.to_dict()
        assert result == {
            "start": {"line": 0, "character": 0},
            "end": {"line": 10, "character": 5}
        }

    def test_range_from_dict(self):
        """测试从字典创建范围"""
        data = {
            "start": {"line": 0, "character": 0},
            "end": {"line": 10, "character": 5}
        }
        range_obj = Range.from_dict(data)
        assert range_obj.start.line == 0
        assert range_obj.end.line == 10


class TestLocation:
    """测试 Location 类型"""

    def test_create_location(self):
        """测试创建位置信息"""
        start = Position(line=0, character=0)
        end = Position(line=10, character=5)
        range_obj = Range(start=start, end=end)
        location = Location(uri="file:///test.zhc", range=range_obj)
        assert location.uri == "file:///test.zhc"
        assert location.range.start.line == 0

    def test_location_to_dict(self):
        """测试位置信息转换为字典"""
        start = Position(line=0, character=0)
        end = Position(line=10, character=5)
        range_obj = Range(start=start, end=end)
        location = Location(uri="file:///test.zhc", range=range_obj)
        result = location.to_dict()
        assert result["uri"] == "file:///test.zhc"
        assert "range" in result


class TestDiagnostic:
    """测试 Diagnostic 类型"""

    def test_create_diagnostic(self):
        """测试创建诊断信息"""
        start = Position(line=0, character=0)
        end = Position(line=0, character=10)
        range_obj = Range(start=start, end=end)
        diagnostic = Diagnostic(
            range=range_obj,
            severity=DiagnosticSeverity.ERROR,
            message="Test error"
        )
        assert diagnostic.message == "Test error"
        assert diagnostic.severity == DiagnosticSeverity.ERROR

    def test_diagnostic_to_dict(self):
        """测试诊断信息转换为字典"""
        start = Position(line=0, character=0)
        end = Position(line=0, character=10)
        range_obj = Range(start=start, end=end)
        diagnostic = Diagnostic(
            range=range_obj,
            severity=DiagnosticSeverity.ERROR,
            message="Test error"
        )
        result = diagnostic.to_dict()
        assert result["message"] == "Test error"
        assert result["severity"] == 1
        assert "range" in result


class TestCompletionItem:
    """测试 CompletionItem 类型"""

    def test_create_completion_item(self):
        """测试创建补全项"""
        item = CompletionItem(
            label="test",
            kind=CompletionItemKind.FUNCTION,
            detail="Test function"
        )
        assert item.label == "test"
        assert item.kind == CompletionItemKind.FUNCTION

    def test_completion_item_to_dict(self):
        """测试补全项转换为字典"""
        item = CompletionItem(
            label="test",
            kind=CompletionItemKind.FUNCTION,
            detail="Test function"
        )
        result = item.to_dict()
        assert result["label"] == "test"
        assert result["kind"] == 3
        assert result["detail"] == "Test function"


class TestHover:
    """测试 Hover 类型"""

    def test_create_hover(self):
        """测试创建悬停信息"""
        hover = Hover(contents="Test documentation")
        assert hover.contents == "Test documentation"

    def test_hover_to_dict(self):
        """测试悬停信息转换为字典"""
        hover = Hover(contents="Test documentation")
        result = hover.to_dict()
        assert result["contents"]["value"] == "Test documentation"


class TestTextEdit:
    """测试 TextEdit 类型"""

    def test_create_text_edit(self):
        """测试创建文本编辑"""
        start = Position(line=0, character=0)
        end = Position(line=0, character=10)
        range_obj = Range(start=start, end=end)
        edit = TextEdit(range=range_obj, new_text="new text")
        assert edit.new_text == "new text"

    def test_text_edit_to_dict(self):
        """测试文本编辑转换为字典"""
        start = Position(line=0, character=0)
        end = Position(line=0, character=10)
        range_obj = Range(start=start, end=end)
        edit = TextEdit(range=range_obj, new_text="new text")
        result = edit.to_dict()
        assert result["newText"] == "new text"
        assert "range" in result


class TestRequest:
    """测试 Request 类型"""

    def test_create_request(self):
        """测试创建请求"""
        request = Request(id=1, method="test", params={"key": "value"})
        assert request.id == 1
        assert request.method == "test"

    def test_request_to_dict(self):
        """测试请求转换为字典"""
        request = Request(id=1, method="test", params={"key": "value"})
        result = request.to_dict()
        assert result["id"] == 1
        assert result["method"] == "test"
        assert result["params"] == {"key": "value"}

    def test_request_from_dict(self):
        """测试从字典创建请求"""
        data = {"id": 1, "method": "test", "params": {"key": "value"}}
        request = Request.from_dict(data)
        assert request.id == 1
        assert request.method == "test"


class TestResponse:
    """测试 Response 类型"""

    def test_create_success_response(self):
        """测试创建成功响应"""
        response = Response(id=1, result={"status": "ok"})
        assert response.id == 1
        assert response.result == {"status": "ok"}
        assert response.error is None

    def test_create_error_response(self):
        """测试创建错误响应"""
        error = ResponseError(code=-32600, message="Invalid Request")
        response = Response(id=1, error=error)
        assert response.error.code == -32600
        assert response.error.message == "Invalid Request"

    def test_response_to_dict(self):
        """测试响应转换为字典"""
        response = Response(id=1, result={"status": "ok"})
        result = response.to_dict()
        assert result["id"] == 1
        assert result["result"] == {"status": "ok"}


class TestNotification:
    """测试 Notification 类型"""

    def test_create_notification(self):
        """测试创建通知"""
        notification = Notification(method="test", params={"key": "value"})
        assert notification.method == "test"
        assert notification.params == {"key": "value"}

    def test_notification_to_dict(self):
        """测试通知转换为字典"""
        notification = Notification(method="test", params={"key": "value"})
        result = notification.to_dict()
        assert result["method"] == "test"
        assert result["params"] == {"key": "value"}


class TestServerCapabilities:
    """测试 ServerCapabilities 类型"""

    def test_create_capabilities(self):
        """测试创建服务器能力"""
        capabilities = ServerCapabilities(
            text_document_sync=1,
            hover_provider=True,
            completion_provider={"triggerCharacters": ["."]}
        )
        assert capabilities.text_document_sync == 1
        assert capabilities.hover_provider is True

    def test_capabilities_to_dict(self):
        """测试服务器能力转换为字典"""
        capabilities = ServerCapabilities(
            text_document_sync=1,
            hover_provider=True,
            completion_provider={"triggerCharacters": ["."]}
        )
        result = capabilities.to_dict()
        assert result["textDocumentSync"] == 1
        assert result["hoverProvider"] is True
        assert "completionProvider" in result