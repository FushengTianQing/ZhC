"""
JSON-RPC 通信层测试

测试 JSON-RPC 协议的实现。
"""

import pytest
import json
from zhc.lsp.jsonrpc import (
    JSONRPCClient, JSONRPCServer, JSONRPCError,
    RequestHandler, ErrorCode, ResponseError
)
from zhc.lsp.protocol import Request, Response


class MockTransport:
    """模拟传输层"""

    def __init__(self):
        self.sent_data = []
        self.receive_data = []

    def send(self, data: bytes) -> None:
        self.sent_data.append(data)

    def receive(self) -> bytes:
        if self.receive_data:
            return self.receive_data.pop(0)
        return b""

    def add_receive_data(self, data: bytes) -> None:
        self.receive_data.append(data)


class TestJSONRPCClient:
    """测试 JSON-RPC 客户端"""

    def test_create_client(self):
        """测试创建客户端"""
        transport = MockTransport()
        client = JSONRPCClient(transport)
        assert client.transport == transport

    def test_send_notification(self):
        """测试发送通知"""
        transport = MockTransport()
        client = JSONRPCClient(transport)

        client.send_notification("test", {"key": "value"})

        assert len(transport.sent_data) == 1
        data = json.loads(transport.sent_data[0].decode("utf-8"))
        assert data["method"] == "test"
        assert data["params"] == {"key": "value"}
        assert "id" not in data

    def test_handle_response(self):
        """测试处理响应"""
        transport = MockTransport()
        client = JSONRPCClient(transport)

        response_data = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"status": "ok"}
        }).encode("utf-8")

        result = client.handle_response(response_data)
        assert result == {"status": "ok"}

    def test_handle_error_response(self):
        """测试处理错误响应"""
        transport = MockTransport()
        client = JSONRPCClient(transport)

        response_data = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": -32600,
                "message": "Invalid Request"
            }
        }).encode("utf-8")

        result = client.handle_response(response_data)
        assert result is None


class TestJSONRPCServer:
    """测试 JSON-RPC 服务器"""

    def test_create_server(self):
        """测试创建服务器"""
        transport = MockTransport()
        server = JSONRPCServer(transport)
        assert server.transport == transport

    def test_register_handler(self):
        """测试注册处理器"""
        transport = MockTransport()
        server = JSONRPCServer(transport)

        def handler(params):
            return {"result": "ok"}

        server.register_handler("test", handler)
        assert "test" in server._handlers

    def test_handle_valid_request(self):
        """测试处理有效请求"""
        transport = MockTransport()
        server = JSONRPCServer(transport)

        def handler(params):
            return {"result": "ok"}

        server.register_handler("test", handler)

        request_data = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "test",
            "params": {}
        }).encode("utf-8")

        response_data = server.handle_message(request_data)
        assert response_data is not None

        response = json.loads(response_data.decode("utf-8"))
        assert response["id"] == 1
        assert response["result"] == {"result": "ok"}

    def test_handle_unknown_method(self):
        """测试处理未知方法"""
        transport = MockTransport()
        server = JSONRPCServer(transport)

        request_data = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "unknown"
        }).encode("utf-8")

        response_data = server.handle_message(request_data)
        assert response_data is not None

        response = json.loads(response_data.decode("utf-8"))
        assert response["error"]["code"] == ErrorCode.METHOD_NOT_FOUND

    def test_handle_invalid_json(self):
        """测试处理无效 JSON"""
        transport = MockTransport()
        server = JSONRPCServer(transport)

        response_data = server.handle_message(b"invalid json")
        assert response_data is not None

        response = json.loads(response_data.decode("utf-8"))
        assert response["error"]["code"] == ErrorCode.PARSE_ERROR

    def test_handle_notification(self):
        """测试处理通知"""
        transport = MockTransport()
        server = JSONRPCServer(transport)

        notification_handled = []

        def handler(params):
            notification_handled.append(params)

        server.register_handler("test", handler)

        notification_data = json.dumps({
            "jsonrpc": "2.0",
            "method": "test",
            "params": {"key": "value"}
        }).encode("utf-8")

        response_data = server.handle_message(notification_data)
        assert response_data is None  # 通知无响应
        assert len(notification_handled) == 1

    def test_handle_handler_exception(self):
        """测试处理器抛出异常"""
        transport = MockTransport()
        server = JSONRPCServer(transport)

        def handler(params):
            raise ValueError("Test error")

        server.register_handler("test", handler)

        request_data = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "test"
        }).encode("utf-8")

        response_data = server.handle_message(request_data)
        assert response_data is not None

        response = json.loads(response_data.decode("utf-8"))
        assert response["error"]["code"] == ErrorCode.INTERNAL_ERROR


class TestErrorCode:
    """测试错误码"""

    def test_error_codes(self):
        """测试错误码定义"""
        assert ErrorCode.PARSE_ERROR == -32700
        assert ErrorCode.INVALID_REQUEST == -32600
        assert ErrorCode.METHOD_NOT_FOUND == -32601
        assert ErrorCode.INVALID_PARAMS == -32602
        assert ErrorCode.INTERNAL_ERROR == -32603


class TestResponseError:
    """测试响应错误"""

    def test_create_response_error(self):
        """测试创建响应错误"""
        error = ResponseError(code=-32600, message="Invalid Request")
        assert error.code == -32600
        assert error.message == "Invalid Request"

    def test_response_error_to_dict(self):
        """测试响应错误转换为字典"""
        error = ResponseError(code=-32600, message="Invalid Request", data={"extra": "info"})
        result = error.to_dict()
        assert result["code"] == -32600
        assert result["message"] == "Invalid Request"
        assert result["data"] == {"extra": "info"}


class TestJSONRPCError:
    """测试 JSON-RPC 错误异常"""

    def test_create_jsonrpc_error(self):
        """测试创建 JSON-RPC 错误"""
        error = ResponseError(code=-32600, message="Invalid Request")
        exception = JSONRPCError(error)
        assert exception.error == error
        assert "Invalid Request" in str(exception)


class TestRequestHandler:
    """测试请求处理器"""

    def test_handle_request(self):
        """测试处理请求"""
        class TestHandler(RequestHandler):
            def handle_request(self, method, params):
                if method == "test":
                    return {"result": "ok"}
                return None

        handler = TestHandler()
        result = handler.handle_request("test", {})
        assert result == {"result": "ok"}
