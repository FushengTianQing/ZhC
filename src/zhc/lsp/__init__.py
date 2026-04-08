"""
Language Server Protocol (LSP) 实现

提供 IDE 集成支持，包括代码补全、诊断、导航等功能。
"""

from .protocol import (
    Position,
    Range,
    Location,
    Diagnostic,
    DiagnosticSeverity,
    CompletionItem,
    CompletionItemKind,
    Hover,
    TextEdit,
    Message,
    Request,
    Response,
    Notification,
)
from .jsonrpc import JSONRPCClient, JSONRPCServer
from .server import LanguageServer

__all__ = [
    # 协议类型
    "Position",
    "Range",
    "Location",
    "Diagnostic",
    "DiagnosticSeverity",
    "CompletionItem",
    "CompletionItemKind",
    "Hover",
    "TextEdit",
    "Message",
    "Request",
    "Response",
    "Notification",
    # JSON-RPC
    "JSONRPCClient",
    "JSONRPCServer",
    # LSP 服务器
    "LanguageServer",
]
