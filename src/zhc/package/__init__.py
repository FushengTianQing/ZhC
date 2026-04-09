"""
中文C语言包管理器模块
Package Manager for ZHC Language

提供包的安装、发布、搜索等管理功能
支持语音交互（语音识别、命令解析、语音反馈）
支持依赖管理、版本约束、锁定文件等
"""

__version__ = "1.3.0"
__author__ = "中文C编译器团队"

# 原有包管理器
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

# 依赖管理模块
from .version import (
    Version,
    VersionConstraint,
    PrereleaseType,
    Prerelease,
    parse_version,
    parse_constraint,
    satisfies,
)
from .config import (
    ProjectConfig,
    DependencySpec,
    find_project_root,
    load_project_config,
)
from .dependency import (
    ResolvedDependency,
    DependencyResolver,
    MockRepository,
)

# 仓库接口（新的模块化实现）
from .repository import (
    PackageRepository,
    PackageMetadata,
    PackageSearchResult,
    RepositoryRegistry,
    AuthManager,
    AuthConfig,
    AuthType,
    PackageIndex,
    IndexEntry,
    LocalRepository,
    RemoteRepository,
)
from .cache import (
    PackageCache,
    CacheEntry,
)
from .lockfile import (
    Lockfile,
    LockedPackage,
)
from .errors import (
    PackageError,
    PackageNotFoundError,
    VersionNotFoundError,
    DependencyConflictError,
    CyclicDependencyError,
    NetworkError,
    CacheError,
    LockfileError,
    ConfigError,
    InvalidVersionError,
    InvalidConstraintError,
    PackageIntegrityError,
    OfflineModeError,
)

# 版本控制模块
from .version_control import (
    VersionControl,
    VersionError,
)
from .changelog import (
    ChangelogGenerator,
)
from .git_utils import (
    GitUtils,
    GitError,
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
    # 原有包管理器
    "PackageManager",
    "PackageInfo",
    "PackageRegistry",
    "PackageDependency",
    "PackageType",
    "PackageStatus",
    "CommandMapper",
    "AliasManager",
    # 版本管理
    "Version",
    "VersionConstraint",
    "PrereleaseType",
    "Prerelease",
    "parse_version",
    "parse_constraint",
    "satisfies",
    # 配置管理
    "ProjectConfig",
    "DependencySpec",
    "find_project_root",
    "load_project_config",
    # 依赖解析
    "ResolvedDependency",
    "DependencyResolver",
    "MockRepository",
    # 仓库接口
    "PackageRepository",
    "PackageMetadata",
    "PackageSearchResult",
    "RepositoryRegistry",
    "AuthManager",
    "AuthConfig",
    "AuthType",
    "PackageIndex",
    "IndexEntry",
    "LocalRepository",
    "RemoteRepository",
    # 缓存管理
    "PackageCache",
    "CacheEntry",
    # 锁定文件
    "Lockfile",
    "LockedPackage",
    # 版本控制
    "VersionControl",
    "VersionError",
    "ChangelogGenerator",
    "GitUtils",
    "GitError",
    # 错误定义
    "PackageError",
    "PackageNotFoundError",
    "VersionNotFoundError",
    "DependencyConflictError",
    "CyclicDependencyError",
    "NetworkError",
    "CacheError",
    "LockfileError",
    "ConfigError",
    "InvalidVersionError",
    "InvalidConstraintError",
    "PackageIntegrityError",
    "OfflineModeError",
]

# 如果语音支持可用，添加到导出列表
if VOICE_SUPPORT:
    __all__.extend(["SpeechRecognizer", "VoiceCommandParser", "VoiceFeedback"])
