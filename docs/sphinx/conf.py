#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sphinx 配置文件

ZHC 中文C编译器 API 文档生成配置

使用方法:
    pip install sphinx sphinx-rtd-theme sphinx-autodoc2 sphinx-autoproto
    sphinx-build -b html docs/sphinx docs/_build/html
"""

import os
import sys
from pathlib import Path

# =============================================================================
# 项目信息
# =============================================================================

project = 'ZHC'
copyright = '2026, ZHC 开发团队'
author = 'ZHC 开发团队'
version = '6.0'
release = '6.0.0'

# =============================================================================
# 扩展配置
# =============================================================================

extensions = [
    # 文档生成
    'sphinx.ext.autodoc',      # 自动从 docstring 生成文档
    'sphinx.ext.viewcode',     # 在文档中显示源代码链接
    'sphinx.ext.napoleon',     # 支持 Google/NumPy docstring 风格
    'sphinx.ext.intersphinx',  # 跨文档引用
    'sphinx.ext.todo',         # TODO 标记支持
    
    # 输出格式
    'sphinx.ext.graphviz',     # Mermaid 图表支持（需安装 graphviz）
    'myst_parser',            # Markdown 支持
    
    # 其他
    'sphinx.ext.ifconfig',     # 条件内容
]

# =============================================================================
# 模板配置
# =============================================================================

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# =============================================================================
# HTML 输出配置
# =============================================================================

html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'style_nav_header_background': '#2980B9',
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False,
}

html_static_path = ['_static']

html_css_files = [
    'css/custom.css',
]

# =============================================================================
# autodoc 配置
# =============================================================================

autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': False,
    'show-inheritance': True,
}

autodoc_typehints = 'description'
autodoc_class_signature = 'separated'

# =============================================================================
# Napoleon 配置 (Google/NumPy docstring)
# =============================================================================

napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = True

# =============================================================================
# intersphinx 配置
# =============================================================================

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'pytest': ('https://docs.pytest.org/', None),
}

# =============================================================================
# todo 配置
# =============================================================================

todo_include_todos = True

# =============================================================================
# Mermaid 配置
# =============================================================================

graphviz_output_format = 'svg'

# =============================================================================
# 源文件路径配置
# =============================================================================

# 添加 src 目录到 Python 路径，以便 autodoc 能正确导入
sys.path.insert(0, os.path.abspath('../..'))

# autodoc 源目录
sphinx_autodoc2_modules = [
    ('../../src', 'src.*'),
]

# =============================================================================
# 构建警告处理
# =============================================================================

# 忽略特定警告
suppress_warnings = [
    'autodoc.import_cycle',
]

# =============================================================================
# 链接检查
# =============================================================================

linkcheck_timeout = 5
linkcheck_retries = 2
linkcheck_workers = 5