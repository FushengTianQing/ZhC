"""
中文C语言包管理器模块
Package Manager for ZHC Language

提供包的安装、发布、搜索等管理功能
支持语音交互（语音识别、命令解析、语音反馈）
"""

__version__ = "1.2.0"
__author__ = "中文C编译器团队"

from .pkg_manager import (
    PackageManager,
    PackageInfo,
    PackageRegistry,
    PackageDependency,
    PackageType,
    PackageStatus,
    CommandMapper,
    AliasManager,
)

# 语音支持（可选导入）
try:
    from .voice import (  # noqa: F401
        SpeechRecognizer,
        VoiceCommandParser,
        VoiceFeedback,
    )

    VOICE_SUPPORT = True
except ImportError:
    VOICE_SUPPORT = False

__all__ = [
    "PackageManager",
    "PackageInfo",
    "PackageRegistry",
    "PackageDependency",
    "PackageType",
    "PackageStatus",
    "CommandMapper",
    "AliasManager",
]

# 如果语音支持可用，添加到导出列表
if VOICE_SUPPORT:
    __all__.extend(["SpeechRecognizer", "VoiceCommandParser", "VoiceFeedback"])
