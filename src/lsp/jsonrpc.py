"""
JSON-RPC 通信层

实现 JSON-RPC 2.0 协议的客户端和服务器端。
支持请求、响应和通知三种消息类型。
"""

import json
import sys
from typing import Any, Callable, Dict, Optional, Protocol
from threading import Lock

from .protocol import Message, Request, Response, Notification, ResponseError


# JSON-RPC 错误码
class ErrorCode:
    """JSON-RPC 错误码"""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    SERVER_NOT_INITIALIZED = -32002
    REQUEST_CANCELLED = -32800


class Transport(Protocol):
    """传输层协议"""
    def send(self, data: bytes) -> None: ...
    def receive(self) -> bytes: ...


class StdinTransport:
    """标准输入/输出传输"""

    def __init__(self):
        self._lock = Lock()

    def send(self, data: bytes) -> None:
        """发送数据到标准输出"""
        with self._lock:
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.write(b"\r\n")
            sys.stdout.flush()

    def receive(self) -> bytes:
        """从标准输入接收数据"""
        line = sys.stdin.buffer.readline()
        if not line:
            return b""
        return line.strip()


class JSONRPCClient:
    """JSON-RPC 客户端"""

    def __init__(self, transport: Optional[Transport] = None):
        self.transport = transport or StdinTransport()
        self._request_id = 0
        self._pending_requests: Dict[int, Callable] = {}
        self._pending_results: Dict[int, Any] = {}
        self._error_results: Dict[int, ResponseError] = {}

    def _next_id(self) -> int:
        """生成下一个请求 ID"""
        self._request_id += 1
        return self._request_id

    def send_request(self, method: str, params: Optional[Any] = None) -> Any:
        """发送请求并等待响应"""
        request_id = self._next_id()
        request = Request(id=request_id, method=method, params=params)

        # 发送请求
        data = json.dumps(request.to_dict()).encode("utf-8")
        self.transport.send(data)

        # 接收响应（简化实现，实际应该异步处理）
        response_data = self.transport.receive()
        if not response_data:
            raise ConnectionError("No response received")

        response = json.loads(response_data.decode("utf-8"))

        # 检查错误
        if "error" in response:
            error = ResponseError(
                code=response["error"].get("code", ErrorCode.INTERNAL_ERROR),
                message=response["error"].get("message", "Unknown error"),
                data=response["error"].get("data")
            )
            raise JSONRPCError(error)

        return response.get("result")

    def send_notification(self, method: str, params: Optional[Any] = None) -> None:
        """发送通知（无响应）"""
        notification = Notification(method=method, params=params)
        data = json.dumps(notification.to_dict()).encode("utf-8")
        self.transport.send(data)

    def handle_response(self, response_data: bytes) -> Optional[Any]:
        """处理收到的响应数据"""
        try:
            response = json.loads(response_data.decode("utf-8"))
        except json.JSONDecodeError as e:
            raise JSONRPCError(ResponseError(
                code=ErrorCode.PARSE_ERROR,
                message=f"Invalid JSON: {str(e)}"
            ))

        # 检查是否为错误响应
        if "error" in response:
            error = ResponseError(
                code=response["error"].get("code", ErrorCode.INTERNAL_ERROR),
                message=response["error"].get("message", "Unknown error"),
                data=response["error"].get("data")
            )
            self._error_results[response["id"]] = error
            return None

        return response.get("result")

    def handle_message(self, message_data: bytes) -> Optional[bytes]:
        """处理收到的消息，返回响应数据（如需要）"""
        try:
            message = json.loads(message_data.decode("utf-8"))
        except json.JSONDecodeError as e:
            error_response = Response(
                id=None,
                error=ResponseError(
                    code=ErrorCode.PARSE_ERROR,
                    message=f"Invalid JSON: {str(e)}"
                )
            )
            return json.dumps(error_response.to_dict()).encode("utf-8")

        # 检查消息类型
        if "id" not in message:
            # 通知消息，无需响应
            return None

        # 请求消息，需要响应
        return None  # 由服务器处理


class JSONRPCError(Exception):
    """JSON-RPC 错误异常"""

    def __init__(self, error: ResponseError):
        self.error = error
        super().__init__(f"JSON-RPC Error {error.code}: {error.message}")


class RequestHandler:
    """请求处理器接口"""

    def handle_request(self, method: str, params: Optional[Any]) -> Any:
        """处理请求"""
        raise NotImplementedError


class JSONRPCServer:
    """JSON-RPC 服务器"""

    def __init__(self, transport: Optional[Transport] = None):
        self.transport = transport or StdinTransport()
        self._handlers: Dict[str, Callable] = {}
        self._capabilities: Dict[str, Any] = {}

    def register_handler(self, method: str, handler: Callable) -> None:
        """注册请求处理器"""
        self._handlers[method] = handler

    def set_capabilities(self, capabilities: Dict[str, Any]) -> None:
        """设置服务器能力"""
        self._capabilities = capabilities

    def handle_message(self, message_data: bytes) -> Optional[bytes]:
        """处理收到的消息"""
        # 解析消息
        try:
            message = json.loads(message_data.decode("utf-8"))
        except json.JSONDecodeError as e:
            return self._create_error_response(
                None,
                ErrorCode.PARSE_ERROR,
                f"Invalid JSON: {str(e)}"
            )

        # 检查消息格式
        if not isinstance(message, dict):
            return self._create_error_response(
                message.get("id"),
                ErrorCode.INVALID_REQUEST,
                "Message must be a JSON object"
            )

        # 检查 JSON-RPC 版本
        if message.get("jsonrpc") != "2.0":
            return self._create_error_response(
                message.get("id"),
                ErrorCode.INVALID_REQUEST,
                "Invalid JSON-RPC version"
            )

        # 获取方法名
        method = message.get("method")
        if not method:
            return self._create_error_response(
                message.get("id"),
                ErrorCode.INVALID_REQUEST,
                "Missing method name"
            )

        # 获取 ID
        msg_id = message.get("id")

        # 检查是否为通知（无 ID）
        if msg_id is None:
            # 通知消息，只需处理
            self._handle_notification(method, message.get("params"))
            return None

        # 请求消息，需要响应
        return self._handle_request(msg_id, method, message.get("params"))

    def _handle_request(self, msg_id: Any, method: str, params: Optional[Any]) -> bytes:
        """处理请求"""
        handler = self._handlers.get(method)

        if handler is None:
            return self._create_error_response(
                msg_id,
                ErrorCode.METHOD_NOT_FOUND,
                f"Method not found: {method}"
            )

        try:
            result = handler(params)
            return self._create_success_response(msg_id, result)
        except Exception as e:
            return self._create_error_response(
                msg_id,
                ErrorCode.INTERNAL_ERROR,
                f"Internal error: {str(e)}"
            )

    def _handle_notification(self, method: str, params: Optional[Any]) -> None:
        """处理通知"""
        handler = self._handlers.get(method)
        if handler:
            try:
                handler(params)
            except Exception:
                pass  # 通知错误不影响服务器

    def _create_success_response(self, msg_id: Any, result: Any) -> bytes:
        """创建成功响应"""
        response = Response(id=msg_id, result=result)
        return json.dumps(response.to_dict()).encode("utf-8")

    def _create_error_response(self, msg_id: Any, code: int, message: str) -> bytes:
        """创建错误响应"""
        response = Response(
            id=msg_id,
            error=ResponseError(code=code, message=message)
        )
        return json.dumps(response.to_dict()).encode("utf-8")

    def run(self) -> None:
        """运行服务器主循环"""
        while True:
            try:
                message_data = self.transport.receive()
                if not message_data:
                    break

                response_data = self.handle_message(message_data)
                if response_data:
                    self.transport.send(response_data)

            except Exception as e:
                error_response = self._create_error_response(
                    None,
                    ErrorCode.INTERNAL_ERROR,
                    f"Server error: {str(e)}"
                )
                self.transport.send(error_response)


class MessageDispatcher:
    """消息分发器"""

    def __init__(self):
        self._handlers: Dict[str, Callable] = {}
        self._middleware: list[Callable] = []

    def register(self, method: str, handler: Callable) -> None:
        """注册处理器"""
        self._handlers[method] = handler

    def add_middleware(self, middleware: Callable) -> None:
        """添加中间件"""
        self._middleware.append(middleware)

    def dispatch(self, message: Message) -> Optional[Any]:
        """分发消息"""
        if isinstance(message, Request):
            # 应用中间件
            for mw in self._middleware:
                message = mw(message)
                if message is None:
                    return None

            handler = self._handlers.get(message.method)
            if handler:
                return handler(message.params)

        return None
