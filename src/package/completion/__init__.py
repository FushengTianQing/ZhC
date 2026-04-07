"""
ZHC包管理器自动补全模块
Auto-completion module for ZHC Package Manager
"""

from .completer import (
    ZHCCompleter,
    install_bash_completion,
    install_zsh_completion,
    print_installation_guide
)

__all__ = [
    'ZHCCompleter',
    'install_bash_completion',
    'install_zsh_completion',
    'print_installation_guide'
]