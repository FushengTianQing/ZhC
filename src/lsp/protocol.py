"""
LSP 协议类型定义

定义 Language Server Protocol 规范中使用的核心数据类型。
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict, List, Optional, Union


class DiagnosticSeverity(IntEnum):
    """诊断信息严重程度"""

    ERROR = 1
    WARNING = 2
    INFORMATION = 3
    HINT = 4


class CompletionItemKind(IntEnum):
    """补全项类型"""

    TEXT = 1
    METHOD = 2
    FUNCTION = 3
    CONSTRUCTOR = 4
    FIELD = 5
    VARIABLE = 6
    CLASS = 7
    INTERFACE = 8
    MODULE = 9
    PROPERTY = 10
    UNIT = 11
    VALUE = 12
    ENUM = 13
    KEYWORD = 14
    SNIPPET = 15
    COLOR = 16
    FILE = 17
    REFERENCE = 18
    FOLDER = 19
    ENUM_MEMBER = 20
    CONSTANT = 21
    STRUCT = 22
    EVENT = 23
    OPERATOR = 24
    TYPE_PARAMETER = 25


class SymbolKind(IntEnum):
    """符号类型"""

    FILE = 1
    MODULE = 2
    NAMESPACE = 3
    PACKAGE = 4
    CLASS = 5
    METHOD = 6
    PROPERTY = 7
    FIELD = 8
    CONSTRUCTOR = 9
    ENUM = 10
    INTERFACE = 11
    FUNCTION = 12
    VARIABLE = 13
    CONSTANT = 14
    STRING = 15
    NUMBER = 16
    BOOLEAN = 17
    ARRAY = 18
    OBJECT = 19
    KEY = 20
    NULL = 21
    ENUM_MEMBER = 22
    PROPERTY_KEY = 23
    CONSTANT_KEY = 24


@dataclass
class Position:
    """位置（行/列）"""

    line: int  # 从 0 开始的行号
    character: int  # 从 0 开始的列号

    def to_dict(self) -> Dict[str, int]:
        return {"line": self.line, "character": self.character}

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> "Position":
        return cls(line=data.get("line", 0), character=data.get("character", 0))


@dataclass
class Range:
    """范围（起始位置到结束位置）"""

    start: Position
    end: Position

    def to_dict(self) -> Dict[str, Dict[str, int]]:
        return {"start": self.start.to_dict(), "end": self.end.to_dict()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Range":
        return cls(
            start=Position.from_dict(data.get("start", {})),
            end=Position.from_dict(data.get("end", {})),
        )


@dataclass
class Location:
    """位置信息（URI + 范围）"""

    uri: str
    range: Range

    def to_dict(self) -> Dict[str, Any]:
        return {"uri": self.uri, "range": self.range.to_dict()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Location":
        return cls(
            uri=data.get("uri", ""), range=Range.from_dict(data.get("range", {}))
        )


@dataclass
class Diagnostic:
    """诊断信息（错误、警告等）"""

    range: Range
    severity: Optional[DiagnosticSeverity] = None
    code: Optional[Union[int, str]] = None
    source: str = "zhc"
    message: str = ""
    related_information: List["DiagnosticRelatedInformation"] = field(
        default_factory=list
    )

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "range": self.range.to_dict(),
            "message": self.message,
        }
        if self.severity is not None:
            result["severity"] = self.severity
        if self.code is not None:
            result["code"] = self.code
        result["source"] = self.source
        return result


@dataclass
class DiagnosticRelatedInformation:
    """诊断相关信息"""

    location: Location
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return {"location": self.location.to_dict(), "message": self.message}


@dataclass
class CompletionItem:
    """补全项"""

    label: str  # 显示文本
    kind: Optional[CompletionItemKind] = None
    detail: Optional[str] = None
    documentation: Optional[str] = None
    insert_text: Optional[str] = None
    insert_text_format: int = 1  # 1=PlainText, 2=Snippet
    text_edit: Optional["TextEdit"] = None
    filter_text: Optional[str] = None
    preselect: bool = False
    sort_text: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {"label": self.label}
        if self.kind is not None:
            result["kind"] = self.kind
        if self.detail is not None:
            result["detail"] = self.detail
        if self.documentation is not None:
            result["documentation"] = self.documentation
        if self.insert_text is not None:
            result["insertText"] = self.insert_text
        result["insertTextFormat"] = self.insert_text_format
        if self.text_edit is not None:
            result["textEdit"] = self.text_edit.to_dict()
        if self.filter_text is not None:
            result["filterText"] = self.filter_text
        result["preselect"] = self.preselect
        if self.sort_text is not None:
            result["sortText"] = self.sort_text
        if self.data is not None:
            result["data"] = self.data
        return result


@dataclass
class TextEdit:
    """文本编辑"""

    range: Range
    new_text: str

    def to_dict(self) -> Dict[str, Any]:
        return {"range": self.range.to_dict(), "newText": self.new_text}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TextEdit":
        return cls(
            range=Range.from_dict(data.get("range", {})),
            new_text=data.get("newText", ""),
        )


@dataclass
class Hover:
    """悬停信息"""

    contents: str  # Markdown 格式的文档
    range: Optional[Range] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {"contents": {"kind": "markdown", "value": self.contents}}
        if self.range is not None:
            result["range"] = self.range.to_dict()
        return result


@dataclass
class SignatureInformation:
    """函数签名信息"""

    label: str  # 函数签名
    documentation: Optional[str] = None
    parameters: List["ParameterInformation"] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"label": self.label}
        if self.documentation is not None:
            result["documentation"] = self.documentation
        if self.parameters:
            result["parameters"] = [p.to_dict() for p in self.parameters]
        return result


@dataclass
class ParameterInformation:
    """参数信息"""

    label: str  # 参数名
    documentation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"label": self.label}
        if self.documentation is not None:
            result["documentation"] = self.documentation
        return result


@dataclass
class SignatureHelp:
    """签名帮助"""

    signatures: List[SignatureInformation]
    active_signature: int = 0
    active_parameter: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signatures": [s.to_dict() for s in self.signatures],
            "activeSignature": self.active_signature,
            "activeParameter": self.active_parameter,
        }


@dataclass
class DocumentSymbol:
    """文档符号"""

    name: str
    kind: SymbolKind
    range: Range
    selection_range: Range
    detail: Optional[str] = None
    children: List["DocumentSymbol"] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "name": self.name,
            "kind": self.kind,
            "range": self.range.to_dict(),
            "selectionRange": self.selection_range.to_dict(),
        }
        if self.detail is not None:
            result["detail"] = self.detail
        if self.children:
            result["children"] = [c.to_dict() for c in self.children]
        return result


@dataclass
class WorkspaceEdit:
    """工作区编辑"""

    changes: Dict[str, List[TextEdit]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "changes": {
                uri: [te.to_dict() for te in edits]
                for uri, edits in self.changes.items()
            }
        }


@dataclass
class SymbolInformation:
    """符号信息"""

    name: str
    kind: SymbolKind
    location: Location
    container_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "name": self.name,
            "kind": self.kind,
            "location": self.location.to_dict(),
        }
        if self.container_name is not None:
            result["containerName"] = self.container_name
        return result


# JSON-RPC 消息类型
@dataclass
class Message:
    """JSON-RPC 消息基类"""

    jsonrpc: str = field(default="2.0", init=False)


@dataclass
class Request(Message):
    """JSON-RPC 请求"""

    id: Union[int, str] = 0
    method: str = ""
    params: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": self.id,
            "method": self.method,
        }
        if self.params is not None:
            result["params"] = self.params
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Request":
        return cls(
            id=data.get("id", 0),
            method=data.get("method", ""),
            params=data.get("params"),
        )


@dataclass
class Response(Message):
    """JSON-RPC 响应"""

    id: Union[int, str, None] = None
    result: Any = None
    error: Optional["ResponseError"] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"jsonrpc": "2.0"}
        if self.id is not None:
            result["id"] = self.id
        if self.error is not None:
            result["error"] = self.error.to_dict()
        else:
            result["result"] = self.result
        return result


@dataclass
class ResponseError:
    """JSON-RPC 错误"""

    code: int = 0
    message: str = ""
    data: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"code": self.code, "message": self.message}
        if self.data is not None:
            result["data"] = self.data
        return result


@dataclass
class Notification(Message):
    """JSON-RPC 通知（无响应的消息）"""

    method: str = ""
    params: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"jsonrpc": "2.0", "method": self.method}
        if self.params is not None:
            result["params"] = self.params
        return result


# 服务器能力
@dataclass
class ServerCapabilities:
    """服务器能力"""

    text_document_sync: int = 1  # 1=Full, 2=Incremental
    completion_provider: Optional[Dict[str, Any]] = None
    hover_provider: bool = False
    signature_help_provider: Optional[Dict[str, Any]] = None
    definition_provider: bool = False
    references_provider: bool = False
    document_highlight_provider: bool = False
    document_symbol_provider: bool = False
    workspace_symbol_provider: bool = False
    code_action_provider: bool = False
    code_lens_provider: Optional[Dict[str, Any]] = None
    document_formatting_provider: bool = False
    document_range_formatting_provider: bool = False
    rename_provider: bool = False
    execute_command_provider: Optional[Dict[str, Any]] = None
    workspace: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"textDocumentSync": self.text_document_sync}
        if self.completion_provider is not None:
            result["completionProvider"] = self.completion_provider
        if self.hover_provider:
            result["hoverProvider"] = self.hover_provider
        if self.signature_help_provider is not None:
            result["signatureHelpProvider"] = self.signature_help_provider
        if self.definition_provider:
            result["definitionProvider"] = self.definition_provider
        if self.references_provider:
            result["referencesProvider"] = self.references_provider
        if self.document_highlight_provider:
            result["documentHighlightProvider"] = self.document_highlight_provider
        if self.document_symbol_provider:
            result["documentSymbolProvider"] = self.document_symbol_provider
        if self.workspace_symbol_provider:
            result["workspaceSymbolProvider"] = self.workspace_symbol_provider
        if self.code_action_provider:
            result["codeActionProvider"] = self.code_action_provider
        if self.code_lens_provider is not None:
            result["codeLensProvider"] = self.code_lens_provider
        if self.document_formatting_provider:
            result["documentFormattingProvider"] = self.document_formatting_provider
        if self.document_range_formatting_provider:
            result["documentRangeFormattingProvider"] = (
                self.document_range_formatting_provider
            )
        if self.rename_provider:
            result["renameProvider"] = self.rename_provider
        if self.execute_command_provider is not None:
            result["executeCommandProvider"] = self.execute_command_provider
        if self.workspace is not None:
            result["workspace"] = self.workspace
        return result
