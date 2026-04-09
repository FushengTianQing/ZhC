#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证管理

管理仓库认证信息
"""

from typing import Dict, List, Optional
from pathlib import Path
import json
import base64
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta


class AuthType(Enum):
    """认证类型"""

    NONE = "none"
    TOKEN = "token"
    BASIC = "basic"
    API_KEY = "api_key"


@dataclass
class AuthConfig:
    """认证配置"""

    auth_type: AuthType
    credentials: Dict[str, str]
    expires_at: Optional[datetime] = None

    def is_valid(self) -> bool:
        """检查认证是否有效"""
        if self.auth_type == AuthType.NONE:
            return True

        if self.expires_at and datetime.now() > self.expires_at:
            return False

        return bool(self.credentials)

    def get_auth_header(self) -> Optional[Dict[str, str]]:
        """获取认证头

        Returns:
            HTTP 认证头字典
        """
        if not self.is_valid():
            return None

        if self.auth_type == AuthType.TOKEN:
            token = self.credentials.get("token", "")
            return {"Authorization": f"Bearer {token}"}

        elif self.auth_type == AuthType.BASIC:
            username = self.credentials.get("username", "")
            password = self.credentials.get("password", "")
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            return {"Authorization": f"Basic {credentials}"}

        elif self.auth_type == AuthType.API_KEY:
            key = self.credentials.get("api_key", "")
            key_name = self.credentials.get("key_name", "X-API-Key")
            return {key_name: key}

        return None


class AuthManager:
    """认证管理器

    管理多个仓库的认证信息
    """

    def __init__(self, config_path: Optional[Path] = None):
        """初始化认证管理器

        Args:
            config_path: 配置文件路径（可选）
        """
        self._auth_configs: Dict[str, AuthConfig] = {}
        self._config_path = config_path

        if config_path and config_path.exists():
            self._load_config()

    def set_auth(self, repository_name: str, auth_config: AuthConfig) -> None:
        """设置仓库认证

        Args:
            repository_name: 仓库名称
            auth_config: 认证配置
        """
        self._auth_configs[repository_name] = auth_config

    def set_token_auth(
        self, repository_name: str, token: str, expires_hours: Optional[int] = None
    ) -> None:
        """设置 Token 认证

        Args:
            repository_name: 仓库名称
            token: Token
            expires_hours: 过期时间（小时）
        """
        expires_at = None
        if expires_hours:
            expires_at = datetime.now() + timedelta(hours=expires_hours)

        self._auth_configs[repository_name] = AuthConfig(
            auth_type=AuthType.TOKEN,
            credentials={"token": token},
            expires_at=expires_at,
        )

    def set_basic_auth(
        self,
        repository_name: str,
        username: str,
        password: str,
    ) -> None:
        """设置 Basic 认证

        Args:
            repository_name: 仓库名称
            username: 用户名
            password: 密码
        """
        self._auth_configs[repository_name] = AuthConfig(
            auth_type=AuthType.BASIC,
            credentials={"username": username, "password": password},
        )

    def set_api_key_auth(
        self,
        repository_name: str,
        api_key: str,
        key_name: str = "X-API-Key",
    ) -> None:
        """设置 API Key 认证

        Args:
            repository_name: 仓库名称
            api_key: API Key
            key_name: Key 名称（HTTP 头名称）
        """
        self._auth_configs[repository_name] = AuthConfig(
            auth_type=AuthType.API_KEY,
            credentials={"api_key": api_key, "key_name": key_name},
        )

    def remove_auth(self, repository_name: str) -> bool:
        """移除仓库认证

        Args:
            repository_name: 仓库名称

        Returns:
            是否成功移除
        """
        if repository_name in self._auth_configs:
            del self._auth_configs[repository_name]
            return True
        return False

    def get_auth(self, repository_name: str) -> Optional[AuthConfig]:
        """获取仓库认证配置

        Args:
            repository_name: 仓库名称

        Returns:
            认证配置，不存在返回 None
        """
        return self._auth_configs.get(repository_name)

    def get_auth_header(self, repository_name: str) -> Optional[Dict[str, str]]:
        """获取仓库的 HTTP 认证头

        Args:
            repository_name: 仓库名称

        Returns:
            HTTP 认证头字典
        """
        auth_config = self._auth_configs.get(repository_name)
        if auth_config:
            return auth_config.get_auth_header()
        return None

    def has_auth(self, repository_name: str) -> bool:
        """检查是否有认证配置

        Args:
            repository_name: 仓库名称

        Returns:
            是否有认证配置
        """
        auth_config = self._auth_configs.get(repository_name)
        return auth_config is not None and auth_config.is_valid()

    def save_config(self) -> None:
        """保存配置到文件"""
        if not self._config_path:
            return

        config = {
            "auth": {
                name: {
                    "type": config.auth_type.value,
                    "credentials": config.credentials,
                    "expires_at": config.expires_at.isoformat()
                    if config.expires_at
                    else None,
                }
                for name, config in self._auth_configs.items()
            }
        }

        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def _load_config(self) -> None:
        """从文件加载配置"""
        if not self._config_path or not self._config_path.exists():
            return

        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            for name, auth_data in config.get("auth", {}).items():
                auth_type = AuthType(auth_data.get("type", "none"))
                credentials = auth_data.get("credentials", {})
                expires_at = auth_data.get("expires_at")

                if expires_at:
                    expires_at = datetime.fromisoformat(expires_at)

                self._auth_configs[name] = AuthConfig(
                    auth_type=auth_type,
                    credentials=credentials,
                    expires_at=expires_at,
                )
        except Exception:
            pass

    def list_repositories_with_auth(self) -> List[str]:
        """列出有认证配置的仓库

        Returns:
            仓库名称列表
        """
        return list(self._auth_configs.keys())

    def __len__(self) -> int:
        return len(self._auth_configs)

    def __contains__(self, repository_name: str) -> bool:
        return repository_name in self._auth_configs

    def __repr__(self) -> str:
        repos = ", ".join(self.list_repositories_with_auth())
        return f"AuthManager({repos})"
