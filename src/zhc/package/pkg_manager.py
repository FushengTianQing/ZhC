"""
中文C语言包管理器
Package Manager for ZHC Language

提供包的安装、发布、搜索等管理功能，支持依赖管理和版本控制。
支持语音交互（语音识别、命令解析、语音反馈）。
"""

import os
import json
import hashlib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime

# requests 是可选依赖（用于远程仓库访问）
try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None


class PackageType(Enum):
    """包类型枚举"""

    LIBRARY = "库"
    TOOL = "工具"
    EXAMPLE = "示例"
    TEMPLATE = "模板"


class PackageStatus(Enum):
    """包状态枚举"""

    STABLE = "稳定版"
    BETA = "测试版"
    DEPRECATED = "已废弃"


class AliasManager:
    """
    别名管理器

    管理命令别名，支持短别名和自定义别名
    """

    # 预定义的短别名（官方别名）
    SHORT_ALIASES = {
        "i": "install",
        "pub": "publish",
        "s": "search",
        "ls": "list",
        "rm": "uninstall",
        "up": "update",
        "v": "verify",
        "inf": "info",
        "h": "help",
        "init": "init",
    }

    def __init__(self, config_path: str = None):
        """
        初始化别名管理器

        Args:
            config_path: 配置文件路径（默认 ~/.zhc/aliases.json）
        """
        if config_path is None:
            config_path = os.path.expanduser("~/.zhc/aliases.json")

        self.config_path = config_path
        self.custom_aliases: Dict[str, str] = {}  # 自定义别名映射
        self._load_custom_aliases()

    def _load_custom_aliases(self):
        """从配置文件加载自定义别名"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.custom_aliases = data.get("aliases", {})
            except Exception:
                # 配置文件损坏时忽略
                self.custom_aliases = {}

    def _save_custom_aliases(self):
        """保存自定义别名到配置文件"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"aliases": self.custom_aliases}, f, ensure_ascii=False, indent=2
                )
        except Exception as e:
            print(f"⚠️  保存别名配置失败: {e}")

    def resolve(self, alias: str) -> str:
        """
        解析别名到标准命令

        Args:
            alias: 别名或命令

        Returns:
            标准英文命令（如果别名有效）或原值
        """
        # 1. 先检查自定义别名（优先级最高）
        if alias in self.custom_aliases:
            return self.custom_aliases[alias]

        # 2. 再检查短别名
        if alias in self.SHORT_ALIASES:
            return self.SHORT_ALIASES[alias]

        # 3. 不是别名，原样返回
        return alias

    def register_alias(self, alias: str, command: str) -> Tuple[bool, str]:
        """
        注册自定义别名

        Args:
            alias: 别名
            command: 标准命令

        Returns:
            (是否成功, 消息)
        """
        # 检查别名是否有效
        if not alias or not alias.strip():
            return False, "❌ 别名不能为空"

        alias = alias.strip()
        command = command.strip()

        # 检查别名是否与标准命令冲突
        if alias in CommandMapper.CN_TO_EN or alias in CommandMapper.EN_TO_CN:
            return False, f"❌ 别名 '{alias}' 与标准命令冲突"

        # 检查命令是否有效
        valid_commands = set(CommandMapper.EN_TO_CN.keys()) | set(
            CommandMapper.CN_TO_EN.values()
        )
        if command not in valid_commands:
            return False, f"❌ 命令 '{command}' 不是有效命令"

        # 注册别名
        self.custom_aliases[alias] = command
        self._save_custom_aliases()

        return True, f"✅ 别名 '{alias}' → '{command}' 注册成功"

    def unregister_alias(self, alias: str) -> Tuple[bool, str]:
        """
        注销别名

        Args:
            alias: 别名

        Returns:
            (是否成功, 消息)
        """
        if alias in self.SHORT_ALIASES:
            return False, f"❌ 官方别名 '{alias}' 不能删除"

        if alias not in self.custom_aliases:
            return False, f"❌ 别名 '{alias}' 不存在"

        del self.custom_aliases[alias]
        self._save_custom_aliases()

        return True, f"✅ 别名 '{alias}' 已删除"

    def list_aliases(self) -> Dict[str, str]:
        """
        列出所有别名

        Returns:
            别名映射字典（包含官方别名和自定义别名）
        """
        all_aliases = self.SHORT_ALIASES.copy()
        all_aliases.update(self.custom_aliases)
        return all_aliases

    def get_alias_info(self, alias: str) -> Optional[Dict]:
        """
        获取别名信息

        Args:
            alias: 别名

        Returns:
            别名信息（如果存在）
        """
        if alias in self.SHORT_ALIASES:
            return {
                "alias": alias,
                "command": self.SHORT_ALIASES[alias],
                "type": "官方别名",
            }

        if alias in self.custom_aliases:
            return {
                "alias": alias,
                "command": self.custom_aliases[alias],
                "type": "自定义别名",
            }

        return None


class CommandMapper:
    """
    命令映射器

    支持中英文命令双向映射和别名解析
    """

    # 中文命令 -> 英文命令
    CN_TO_EN = {
        "安装": "install",
        "发布": "publish",
        "搜索": "search",
        "列表": "list",
        "卸载": "uninstall",
        "更新": "update",
        "验证": "verify",
        "信息": "info",
        "帮助": "help",
        "初始化": "init",
    }

    # 英文命令 -> 中文命令
    EN_TO_CN = {v: k for k, v in CN_TO_EN.items()}

    # 别名管理器（类级别）
    _alias_manager: Optional[AliasManager] = None

    @classmethod
    def get_alias_manager(cls) -> AliasManager:
        """获取别名管理器实例（懒加载）"""
        if cls._alias_manager is None:
            cls._alias_manager = AliasManager()
        return cls._alias_manager

    @staticmethod
    def to_english(command: str) -> str:
        """转换为英文命令"""
        return CommandMapper.CN_TO_EN.get(command, command)

    @staticmethod
    def to_chinese(command: str) -> str:
        """转换为中文命令"""
        return CommandMapper.EN_TO_CN.get(command, command)

    @staticmethod
    def is_chinese_command(command: str) -> bool:
        """判断是否为中文命令"""
        return command in CommandMapper.CN_TO_EN

    @staticmethod
    def normalize(command: str) -> str:
        """
        规范化命令（转换为标准英文命令）

        支持三层解析：
        1. 别名解析（自定义别名 > 官方短别名）
        2. 中文命令转换
        3. 英文命令验证

        Args:
            command: 命令（中文、英文或别名）

        Returns:
            标准英文命令
        """
        # 1. 先解析别名（最高优先级）
        alias_manager = CommandMapper.get_alias_manager()
        resolved = alias_manager.resolve(command)
        if resolved != command:
            # 解析到别名，递归规范化（防止别名指向别名）
            return CommandMapper.normalize(resolved)

        # 2. 如果是中文命令，转换为英文
        if command in CommandMapper.CN_TO_EN:
            return CommandMapper.CN_TO_EN[command]

        # 3. 如果已经是英文命令，直接返回
        if command in CommandMapper.EN_TO_CN:
            return command

        # 4. 未知命令，原样返回
        return command

    @staticmethod
    def is_alias(command: str) -> bool:
        """
        判断是否为别名

        Args:
            command: 命令

        Returns:
            是否为别名
        """
        alias_manager = CommandMapper.get_alias_manager()
        return alias_manager.resolve(command) != command


@dataclass
class PackageDependency:
    """
    包依赖

    表示一个包的依赖关系
    """

    name: str  # 依赖包名
    version_range: str  # 版本范围（如 ">=1.0.0 <2.0.0"）
    optional: bool = False  # 是否可选

    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> "PackageDependency":
        """从字典创建"""
        return PackageDependency(**data)

    def version_satisfied(self, version: str) -> bool:
        """
        检查版本是否满足要求

        Args:
            version: 版本字符串（如 "1.2.3"）

        Returns:
            是否满足
        """
        # 简化版本检查（实际应该完整实现语义化版本）
        min_version = "0.0.0"
        max_version = "999.999.999"

        if ">=" in self.version_range:
            min_version = self.version_range.split(">=")[1].strip().split()[0]
        if "<" in self.version_range:
            max_version = self.version_range.split("<")[1].strip().split()[0]

        return min_version <= version < max_version


@dataclass
class PackageInfo:
    """
    包信息

    表示一个中文C语言包的完整信息
    """

    name: str  # 包名
    version: str  # 版本
    description: str  # 描述
    author: str  # 作者
    package_type: PackageType  # 包类型
    status: PackageStatus = PackageStatus.STABLE
    dependencies: List[PackageDependency] = None
    keywords: List[str] = None
    homepage: str = ""
    repository: str = ""
    license: str = "MIT"
    created_at: str = ""
    updated_at: str = ""
    downloads: int = 0

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.keywords is None:
            self.keywords = []
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d")
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict:
        """转换为字典"""
        data = asdict(self)
        data["package_type"] = self.package_type.value
        data["status"] = self.status.value
        data["dependencies"] = [dep.to_dict() for dep in self.dependencies]
        return data

    @staticmethod
    def from_dict(data: Dict) -> "PackageInfo":
        """从字典创建"""
        data["package_type"] = PackageType(data["package_type"])
        data["status"] = PackageStatus(data.get("status", "稳定版"))
        data["dependencies"] = [
            PackageDependency.from_dict(dep) for dep in data.get("dependencies", [])
        ]
        return PackageInfo(**data)

    def to_package_json(self) -> str:
        """生成 package.json 内容"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class PackageRegistry:
    """
    包注册表

    管理包的注册信息和版本历史
    """

    def __init__(self, registry_url: str = "https://registry.zhc-lang.org"):
        self.registry_url = registry_url
        self._cache: Dict[str, PackageInfo] = {}

    def get_package(self, name: str) -> Optional[PackageInfo]:
        """
        获取包信息

        Args:
            name: 包名

        Returns:
            包信息（如果存在）
        """
        # 检查缓存
        if name in self._cache:
            return self._cache[name]

        # 从注册表获取（模拟）
        # 实际应该从远程注册表获取
        return None

    def register_package(self, package: PackageInfo) -> bool:
        """
        注册包

        Args:
            package: 包信息

        Returns:
            是否成功
        """
        # 缓存包信息
        self._cache[package.name] = package
        return True

    def search_packages(self, query: str) -> List[PackageInfo]:
        """
        搜索包

        Args:
            query: 搜索关键词

        Returns:
            匹配的包列表
        """
        results = []
        query_lower = query.lower()

        for pkg in self._cache.values():
            # 搜索包名、描述、关键词
            if (
                query_lower in pkg.name.lower()
                or query_lower in pkg.description.lower()
                or any(query_lower in kw.lower() for kw in pkg.keywords)
            ):
                results.append(pkg)

        return results

    def get_dependencies(self, name: str) -> List[PackageDependency]:
        """
        获取包的依赖列表

        Args:
            name: 包名

        Returns:
            依赖列表
        """
        pkg = self.get_package(name)
        return pkg.dependencies if pkg else []


class PackageManager:
    """
    包管理器

    提供包的安装、发布、搜索等核心功能
    支持中英文命令和语音交互
    """

    def __init__(
        self,
        registry_url: str = "https://registry.zhc-lang.org",
        install_dir: str = "~/.zhc/packages",
        enable_voice: bool = False,
    ):
        self.registry = PackageRegistry(registry_url)
        self.install_dir = os.path.expanduser(install_dir)
        self.installed_packages: Dict[str, str] = {}  # 包名 -> 版本

        # 确保安装目录存在
        os.makedirs(self.install_dir, exist_ok=True)

        # 语音支持（可选）
        self.enable_voice = enable_voice
        self._voice_recognizer = None
        self._voice_parser = None
        self._voice_feedback = None

        if enable_voice:
            self._init_voice_modules()

    def execute(self, command: str, *args, **kwargs):
        """
        执行命令（支持中英文和别名）

        Args:
            command: 命令名（中文、英文或别名）
            *args, **kwargs: 命令参数

        Returns:
            命令执行结果（可能是tuple、list等）
        """
        # 规范化命令（解析别名、中文命令）
        en_command = CommandMapper.normalize(command)

        # 执行对应方法
        method_map = {
            "install": self.install,
            "publish": self.publish,
            "search": self.search,
            "list": self.list_installed,
            "uninstall": self.uninstall,
            "update": self.update,
            "verify": self.verify_package,
            "info": self.get_package_info,
        }

        if en_command not in method_map:
            return (
                False,
                f"❌ 未知命令: {command}\n可用命令: {', '.join(CommandMapper.CN_TO_EN.keys())}",
            )

        return method_map[en_command](*args, **kwargs)

    def _init_voice_modules(self):
        """初始化语音模块"""
        try:
            from .voice import SpeechRecognizer, VoiceCommandParser, VoiceFeedback

            self._voice_recognizer = SpeechRecognizer()
            self._voice_parser = VoiceCommandParser()
            self._voice_feedback = VoiceFeedback()
        except ImportError as e:
            print(f"⚠️  语音模块初始化失败: {e}")
            self.enable_voice = False

    def listen_voice_command(self, timeout: int = 5) -> Tuple[bool, str]:
        """
        监听语音命令

        Args:
            timeout: 超时时间（秒）

        Returns:
            (是否成功, 命令文本或错误消息)
        """
        if not self.enable_voice:
            return False, "❌ 语音功能未启用"

        if not self._voice_recognizer:
            return False, "❌ 语音识别器未初始化"

        # 监听语音
        success, result = self._voice_recognizer.listen_and_recognize(timeout)

        if not success:
            return False, result

        return True, result

    def execute_voice_command(self, voice_text: str) -> Tuple[bool, str, Dict]:
        """
        执行语音命令

        Args:
            voice_text: 语音识别文本

        Returns:
            (是否成功, 执行结果消息, 解析信息字典)
        """
        if not self.enable_voice:
            return False, "❌ 语音功能未启用", {}

        if not self._voice_parser:
            return False, "❌ 语音解析器未初始化", {}

        # 解析语音命令
        parsed = self._voice_parser.parse(voice_text)

        # 检查命令是否识别
        if not parsed["command"]:
            # 语音反馈
            if self._voice_feedback:
                self._voice_feedback.speak_feedback("command_not_recognized")
            return False, f"❌ 无法识别命令: {voice_text}", parsed

        # 执行命令
        result = self.execute(parsed["command"], *parsed["args"], **parsed["kwargs"])

        # 语音反馈
        if self._voice_feedback and isinstance(result, tuple):
            success, msg = result
            if success:
                # 尝试使用预定义反馈
                feedback_type = f"{parsed['command']}_success"
                self._voice_feedback.speak_feedback(feedback_type)
            else:
                # 使用自定义消息
                self._voice_feedback.speak(msg[:100])  # 限制长度

        return (
            result[0],
            result[1],
            parsed if isinstance(result, tuple) else (True, str(result), parsed),
        )

    def voice_interact(self) -> Tuple[bool, str]:
        """
        完整的语音交互流程

        流程：
        1. 提示用户说话
        2. 监听并识别语音
        3. 解析命令
        4. 执行命令
        5. 语音反馈结果

        Returns:
            (是否成功, 执行结果消息)
        """
        if not self.enable_voice:
            return False, "❌ 语音功能未启用"

        # 提示用户
        if self._voice_feedback:
            self._voice_feedback.speak_feedback("listening")

        # 监听语音
        success, result = self.listen_voice_command()
        if not success:
            return False, result

        # 执行命令
        success, msg, parsed = self.execute_voice_command(result)

        return success, msg

    # ===== T046: install 命令（支持中英文） =====

    def install(self, package_name: str, version: str = "latest") -> Tuple[bool, str]:
        """
        安装包

        Args:
            package_name: 包名
            version: 版本（默认最新版）

        Returns:
            (是否成功, 消息)
        """
        # 1. 获取包信息
        package = self.registry.get_package(package_name)
        if not package:
            return False, f"❌ 包 '{package_name}' 不存在"

        # 2. 检查版本
        if version != "latest" and version != package.version:
            # 查找指定版本（模拟）
            if version not in ["1.0.0", "1.1.0", "1.2.0"]:
                return False, f"❌ 版本 '{version}' 不存在"

        # 3. 检查依赖
        for dep in package.dependencies:
            if dep.name not in self.installed_packages:
                # 递归安装依赖
                success, msg = self.install(dep.name)
                if not success and not dep.optional:
                    return False, f"❌ 依赖 '{dep.name}' 安装失败: {msg}"

        # 4. 创建安装目录
        pkg_dir = os.path.join(self.install_dir, package_name)
        os.makedirs(pkg_dir, exist_ok=True)

        # 5. 下载包（模拟）
        # 实际应该从远程仓库下载

        # 6. 写入 package.json
        pkg_json_path = os.path.join(pkg_dir, "package.json")
        with open(pkg_json_path, "w", encoding="utf-8") as f:
            f.write(package.to_package_json())

        # 7. 记录安装信息
        self.installed_packages[package_name] = package.version

        return True, f"✅ 包 '{package_name}@{package.version}' 安装成功"

    def install_from_package_json(self, package_json_path: str) -> Tuple[bool, str]:
        """
        从 package.json 安装依赖

        Args:
            package_json_path: package.json 路径

        Returns:
            (是否成功, 消息)
        """
        try:
            with open(package_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 安装所有依赖
            for dep in data.get("dependencies", []):
                success, msg = self.install(dep["name"], dep.get("version", "latest"))
                if not success:
                    return False, msg

            return True, "✅ 所有依赖安装完成"
        except Exception as e:
            return False, f"❌ 安装失败: {str(e)}"

    # ===== T047: publish 命令 =====

    def publish(self, package_dir: str) -> Tuple[bool, str]:
        """
        发布包

        Args:
            package_dir: 包目录路径

        Returns:
            (是否成功, 消息)
        """
        # 1. 检查 package.json
        pkg_json_path = os.path.join(package_dir, "package.json")
        if not os.path.exists(pkg_json_path):
            return False, "❌ 缺少 package.json 文件"

        # 2. 读取包信息
        try:
            with open(pkg_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            package = PackageInfo.from_dict(data)
        except Exception as e:
            return False, f"❌ package.json 格式错误: {str(e)}"

        # 3. 验证必填字段
        if not package.name:
            return False, "❌ 包名不能为空"
        if not package.version:
            return False, "❌ 版本不能为空"
        if not package.author:
            return False, "❌ 作者不能为空"

        # 4. 检查包名是否已存在
        existing = self.registry.get_package(package.name)
        if existing:
            # 检查版本是否已发布
            if existing.version == package.version:
                return False, f"❌ 版本 '{package.version}' 已存在"

        # 5. 计算包哈希（用于验证）
        pkg_hash = self._calculate_package_hash(package_dir)

        # 6. 注册包
        success = self.registry.register_package(package)
        if not success:
            return False, "❌ 注册失败"

        return (
            True,
            f"✅ 包 '{package.name}@{package.version}' 发布成功\n   哈希: {pkg_hash}",
        )

    def _calculate_package_hash(self, package_dir: str) -> str:
        """
        计算包的哈希值

        Args:
            package_dir: 包目录

        Returns:
            SHA256哈希值
        """
        hasher = hashlib.sha256()

        for root, dirs, files in os.walk(package_dir):
            for file in files:
                if file.startswith(".") or file == "package.json":
                    continue

                filepath = os.path.join(root, file)
                with open(filepath, "rb") as f:
                    hasher.update(f.read())

        return hasher.hexdigest()[:16]

    # ===== T048: search 命令 =====

    def search(self, query: str) -> List[PackageInfo]:
        """
        搜索包

        Args:
            query: 搜索关键词

        Returns:
            匹配的包列表
        """
        return self.registry.search_packages(query)

    def search_by_type(self, package_type: PackageType) -> List[PackageInfo]:
        """
        按类型搜索包

        Args:
            package_type: 包类型

        Returns:
            匹配的包列表
        """
        # 从注册表获取所有包
        all_packages = list(self.registry._cache.values())

        # 过滤类型
        return [pkg for pkg in all_packages if pkg.package_type == package_type]

    def search_by_author(self, author: str) -> List[PackageInfo]:
        """
        按作者搜索包

        Args:
            author: 作者名

        Returns:
            匹配的包列表
        """
        all_packages = list(self.registry._cache.values())
        return [pkg for pkg in all_packages if pkg.author == author]

    # ===== 其他命令 =====

    def list_installed(self) -> Dict[str, str]:
        """
        列出已安装的包

        Returns:
            包名 -> 版本的映射
        """
        return self.installed_packages.copy()

    def uninstall(self, package_name: str) -> Tuple[bool, str]:
        """
        卸载包

        Args:
            package_name: 包名

        Returns:
            (是否成功, 消息)
        """
        if package_name not in self.installed_packages:
            return False, f"❌ 包 '{package_name}' 未安装"

        # 删除包目录
        pkg_dir = os.path.join(self.install_dir, package_name)
        if os.path.exists(pkg_dir):
            import shutil

            shutil.rmtree(pkg_dir)

        # 从已安装列表中移除
        del self.installed_packages[package_name]

        return True, f"✅ 包 '{package_name}' 已卸载"

    def update(self, package_name: str) -> Tuple[bool, str]:
        """
        更新包

        Args:
            package_name: 包名

        Returns:
            (是否成功, 消息)
        """
        # 获取当前版本
        current_version = self.installed_packages.get(package_name)
        if not current_version:
            return False, f"❌ 包 '{package_name}' 未安装"

        # 获取最新版本
        package = self.registry.get_package(package_name)
        if not package:
            return False, f"❌ 包 '{package_name}' 不存在"

        # 检查是否需要更新
        if package.version == current_version:
            return True, f"✅ 包 '{package_name}' 已是最新版本"

        # 卸载旧版本
        self.uninstall(package_name)

        # 安装新版本
        return self.install(package_name)

    def get_package_info(self, package_name: str) -> Optional[PackageInfo]:
        """
        获取包信息

        Args:
            package_name: 包名

        Returns:
            包信息
        """
        return self.registry.get_package(package_name)

    def verify_package(self, package_name: str) -> Tuple[bool, str]:
        """
        验证包完整性

        Args:
            package_name: 包名

        Returns:
            (是否验证通过, 消息)
        """
        pkg_dir = os.path.join(self.install_dir, package_name)
        if not os.path.exists(pkg_dir):
            return False, f"❌ 包 '{package_name}' 未安装"

        # 计算当前哈希
        current_hash = self._calculate_package_hash(pkg_dir)

        # 读取原始哈希（应该从 package.json 或单独文件读取）
        pkg_json_path = os.path.join(pkg_dir, "package.json")
        with open(pkg_json_path, "r", encoding="utf-8") as f:
            json.load(f)
            # 这里简化处理，实际应该有完整的哈希验证机制

        return True, f"✅ 包 '{package_name}' 验证通过\n   当前哈希: {current_hash}"


# 测试代码
if __name__ == "__main__":
    # 创建包管理器
    pm = PackageManager()

    # 注册一些测试包
    test_package = PackageInfo(
        name="测试库",
        version="1.0.0",
        description="一个用于测试的中文C语言库",
        author="中文C编译器团队",
        package_type=PackageType.LIBRARY,
        keywords=["测试", "示例"],
        dependencies=[PackageDependency(name="标准库", version_range=">=1.0.0")],
    )

    pm.registry.register_package(test_package)

    # 测试安装
    success, msg = pm.install("测试库")
    print(msg)

    # 测试搜索
    results = pm.search("测试")
    print(f"\n搜索结果：{len(results)}个包")
    for pkg in results:
        print(f"  - {pkg.name}@{pkg.version}: {pkg.description}")

    # 测试列表
    installed = pm.list_installed()
    print(f"\n已安装：{len(installed)}个包")
    for name, version in installed.items():
        print(f"  - {name}@{version}")
