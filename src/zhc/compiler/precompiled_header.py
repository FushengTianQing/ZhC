#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
预编译头文件系统（增强版）
Precompiled Header System Enhanced

高性能预编译头文件系统，支持：
1. 头文件预处理缓存
2. 符号索引加速
3. 宏定义缓存
4. 类型定义缓存
5. 增量更新机制
6. 多版本管理

作者：阿福
日期：2026-04-03
"""

import time
import json
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class HeaderType(Enum):
    """头文件类型"""

    SYSTEM = "系统头文件"
    PROJECT = "项目头文件"
    MODULE = "模块头文件"
    STANDARD = "标准库头文件"


@dataclass
class HeaderSymbol:
    """头文件符号"""

    name: str
    symbol_type: str  # function, class, variable, typedef, macro
    header_file: str
    line: int
    signature: Optional[str] = None
    namespace: Optional[str] = None
    is_exported: bool = True


@dataclass
class MacroDefinition:
    """宏定义"""

    name: str
    body: str
    params: Optional[List[str]] = None
    is_function_like: bool = False
    defined_in: str = ""
    line: int = 0


@dataclass
class TypeDefinition:
    """类型定义"""

    name: str
    kind: str  # struct, class, typedef, enum
    size: int = 0
    alignment: int = 0
    members: List[Dict[str, Any]] = field(default_factory=list)
    base_classes: List[str] = field(default_factory=list)
    defined_in: str = ""
    line: int = 0


@dataclass
class HeaderIndex:
    """头文件索引"""

    filepath: str
    header_type: HeaderType
    last_modified: float
    content_hash: str
    symbols: Dict[str, HeaderSymbol] = field(default_factory=dict)
    macros: Dict[str, MacroDefinition] = field(default_factory=dict)
    types: Dict[str, TypeDefinition] = field(default_factory=dict)
    includes: List[str] = field(default_factory=list)
    included_by: List[str] = field(default_factory=list)
    parse_time: float = 0.0
    size: int = 0


@dataclass
class PrecompiledHeader:
    """预编译头文件"""

    header_index: HeaderIndex
    compiled_time: float
    version: str
    dependencies: List[str] = field(default_factory=list)
    checksum: str = ""
    is_valid: bool = True
    cache_hits: int = 0


class SymbolIndex:
    """符号索引（加速符号查找）"""

    def __init__(self):
        self.symbols: Dict[str, List[HeaderSymbol]] = {}  # name -> symbols
        self.by_type: Dict[str, List[HeaderSymbol]] = {}  # type -> symbols
        self.by_header: Dict[str, List[HeaderSymbol]] = {}  # header -> symbols
        self.namespace_map: Dict[str, Set[str]] = {}  # namespace -> symbols

    def add_symbol(self, symbol: HeaderSymbol):
        """添加符号"""
        # 按名称索引
        if symbol.name not in self.symbols:
            self.symbols[symbol.name] = []
        self.symbols[symbol.name].append(symbol)

        # 按类型索引
        if symbol.symbol_type not in self.by_type:
            self.by_type[symbol.symbol_type] = []
        self.by_type[symbol.symbol_type].append(symbol)

        # 按头文件索引
        if symbol.header_file not in self.by_header:
            self.by_header[symbol.header_file] = []
        self.by_header[symbol.header_file].append(symbol)

        # 按命名空间索引
        if symbol.namespace:
            if symbol.namespace not in self.namespace_map:
                self.namespace_map[symbol.namespace] = set()
            self.namespace_map[symbol.namespace].add(symbol.name)

    def lookup(self, name: str, symbol_type: str = None) -> List[HeaderSymbol]:
        """查找符号"""
        results = self.symbols.get(name, [])

        if symbol_type:
            results = [s for s in results if s.symbol_type == symbol_type]

        return results

    def lookup_in_namespace(self, namespace: str) -> List[HeaderSymbol]:
        """在命名空间中查找"""
        symbols = []
        if namespace in self.namespace_map:
            for name in self.namespace_map[namespace]:
                symbols.extend(self.symbols.get(name, []))
        return symbols

    def remove_header_symbols(self, header_file: str):
        """移除头文件的所有符号"""
        if header_file in self.by_header:
            for symbol in self.by_header[header_file]:
                if symbol.name in self.symbols:
                    self.symbols[symbol.name] = [
                        s
                        for s in self.symbols[symbol.name]
                        if s.header_file != header_file
                    ]
                    if not self.symbols[symbol.name]:
                        del self.symbols[symbol.name]

            del self.by_header[header_file]


class PrecompiledHeaderManager:
    """预编译头文件管理器"""

    VERSION = "1.0.0"

    def __init__(self, cache_dir: str = ".zhc_pch", max_size_mb: int = 512):
        """
        初始化预编译头文件管理器

        Args:
            cache_dir: 缓存目录
            max_size_mb: 最大缓存大小（MB）
        """
        self.cache_dir = Path(cache_dir)
        self.max_size = max_size_mb * 1024 * 1024

        # 索引和缓存
        self.headers: Dict[str, PrecompiledHeader] = {}
        self.symbol_index = SymbolIndex()
        self.macro_cache: Dict[str, MacroDefinition] = {}
        self.type_cache: Dict[str, TypeDefinition] = {}

        # 统计
        self.stats = {
            "total_headers": 0,
            "total_symbols": 0,
            "total_macros": 0,
            "total_types": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_parse_time": 0.0,
            "space_used": 0,
        }

        # 初始化
        self._initialize()

    def _initialize(self):
        """初始化缓存目录"""
        self.cache_dir.mkdir(exist_ok=True)

        # 加载现有缓存
        index_file = self.cache_dir / "pch_index.json"
        if index_file.exists():
            try:
                with open(index_file, "r", encoding="utf-8") as f:
                    index_data = json.load(f)

                for filepath, data in index_data.items():
                    header_index = self._dict_to_header_index(data["header_index"])
                    pch = PrecompiledHeader(
                        header_index=header_index,
                        compiled_time=data["compiled_time"],
                        version=data["version"],
                        dependencies=data.get("dependencies", []),
                        checksum=data.get("checksum", ""),
                        is_valid=data.get("is_valid", True),
                        cache_hits=data.get("cache_hits", 0),
                    )
                    self.headers[filepath] = pch

                print(f"📦 加载预编译头文件索引: {len(self.headers)} 个")
            except Exception as e:
                print(f"⚠️ 加载索引失败: {e}")
                self.headers = {}

    def _save_index(self):
        """保存索引"""
        index_file = self.cache_dir / "pch_index.json"
        index_data = {}

        for filepath, pch in self.headers.items():
            index_data[filepath] = {
                "header_index": self._header_index_to_dict(pch.header_index),
                "compiled_time": pch.compiled_time,
                "version": pch.version,
                "dependencies": pch.dependencies,
                "checksum": pch.checksum,
                "is_valid": pch.is_valid,
                "cache_hits": pch.cache_hits,
            }

        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)

    def preprocess_header(
        self, filepath: str, content: str = None
    ) -> PrecompiledHeader:
        """
        预处理头文件

        Args:
            filepath: 头文件路径
            content: 文件内容（可选，如果未提供则从文件读取）

        Returns:
            预编译头文件对象
        """
        path = Path(filepath)

        # 检查缓存
        if filepath in self.headers:
            pch = self.headers[filepath]

            # 检查是否需要更新
            if self._is_cache_valid(pch, path):
                pch.cache_hits += 1
                self.stats["cache_hits"] += 1
                return pch

        self.stats["cache_misses"] += 1

        # 读取文件内容
        if content is None:
            if not path.exists():
                raise FileNotFoundError(f"头文件不存在: {filepath}")
            content = path.read_text(encoding="utf-8")

        # 计算哈希
        content_hash = hashlib.md5(content.encode()).hexdigest()

        # 解析头文件
        start_time = time.time()
        header_index = self._parse_header(filepath, content)
        parse_time = time.time() - start_time

        # 更新统计
        header_index.parse_time = parse_time
        header_index.content_hash = content_hash
        header_index.last_modified = (
            path.stat().st_mtime if path.exists() else time.time()
        )
        header_index.size = len(content)

        # 创建预编译头文件
        pch = PrecompiledHeader(
            header_index=header_index,
            compiled_time=time.time(),
            version=self.VERSION,
            dependencies=header_index.includes,
            checksum=content_hash,
            is_valid=True,
            cache_hits=1,
        )

        # 缓存
        self.headers[filepath] = pch

        # 更新符号索引
        for symbol in header_index.symbols.values():
            self.symbol_index.add_symbol(symbol)

        # 更新宏缓存
        for name, macro in header_index.macros.items():
            self.macro_cache[name] = macro

        # 更新类型缓存
        for name, typedef in header_index.types.items():
            self.type_cache[name] = typedef

        # 更新统计
        self.stats["total_headers"] += 1
        self.stats["total_symbols"] += len(header_index.symbols)
        self.stats["total_macros"] += len(header_index.macros)
        self.stats["total_types"] += len(header_index.types)
        self.stats["total_parse_time"] += parse_time
        self.stats["space_used"] += header_index.size

        # 保存索引
        self._save_index()

        return pch

    def _parse_header(self, filepath: str, content: str) -> HeaderIndex:
        """解析头文件"""
        header_type = self._determine_header_type(filepath)

        header_index = HeaderIndex(
            filepath=filepath,
            header_type=header_type,
            last_modified=0,
            content_hash="",
            symbols={},
            macros={},
            types={},
            includes=[],
        )

        # 简化的解析（实际实现需要完整的词法/语法分析）
        lines = content.split("\n")

        for i, line in enumerate(lines):
            line_stripped = line.strip()

            # 检测 #include
            if line_stripped.startswith("#include"):
                include = self._extract_include(line_stripped)
                if include:
                    header_index.includes.append(include)

            # 检测 #define
            elif line_stripped.startswith("#define"):
                macro = self._parse_macro(line_stripped, i + 1, filepath)
                if macro:
                    header_index.macros[macro.name] = macro

            # 检测函数声明
            elif self._is_function_decl(line_stripped):
                symbol = self._parse_function_decl(line_stripped, i + 1, filepath)
                if symbol:
                    header_index.symbols[symbol.name] = symbol

            # 检测类/结构体声明
            elif self._is_type_decl(line_stripped):
                typedef = self._parse_type_decl(line_stripped, i + 1, filepath)
                if typedef:
                    header_index.types[typedef.name] = typedef

        return header_index

    def _determine_header_type(self, filepath: str) -> HeaderType:
        """确定头文件类型"""
        if any(p in filepath for p in ["标准库", "stdlib", "标准"]):
            return HeaderType.STANDARD
        elif any(p in filepath for p in ["系统", "system", "sys"]):
            return HeaderType.SYSTEM
        elif any(p in filepath for p in ["模块", "module"]):
            return HeaderType.MODULE
        else:
            return HeaderType.PROJECT

    def _extract_include(self, line: str) -> Optional[str]:
        """提取include路径"""
        import re

        match = re.search(r'[<"]([^>"]+)[>"]', line)
        if match:
            return match.group(1)
        return None

    def _parse_macro(
        self, line: str, line_num: int, filepath: str
    ) -> Optional[MacroDefinition]:
        """解析宏定义"""
        import re

        # 函数宏: #define NAME(args) body
        func_match = re.match(r"#define\s+(\w+)\s*\(([^)]*)\)\s*(.*)", line)
        if func_match:
            name = func_match.group(1)
            params_str = func_match.group(2)
            body = func_match.group(3).strip()

            params = [p.strip() for p in params_str.split(",") if p.strip()]

            return MacroDefinition(
                name=name,
                params=params,
                body=body,
                is_function_like=True,
                defined_in=filepath,
                line=line_num,
            )

        # 简单宏: #define NAME value
        simple_match = re.match(r"#define\s+(\w+)\s*(.*)", line)
        if simple_match:
            name = simple_match.group(1)
            body = simple_match.group(2).strip()

            return MacroDefinition(
                name=name,
                params=None,
                body=body,
                is_function_like=False,
                defined_in=filepath,
                line=line_num,
            )

        return None

    def _is_function_decl(self, line: str) -> bool:
        """检查是否是函数声明"""
        # 简化检查
        return (
            "(" in line
            and ")" in line
            and ("函数" in line or "function" in line.lower())
        )

    def _parse_function_decl(
        self, line: str, line_num: int, filepath: str
    ) -> Optional[HeaderSymbol]:
        """解析函数声明"""
        import re

        # 简化解析
        match = re.match(r".*函数\s+(\w+)\s*\(([^)]*)\)", line)
        if not match:
            match = re.match(r".*function\s+(\w+)\s*\(([^)]*)\)", line, re.IGNORECASE)

        if match:
            name = match.group(1)
            return HeaderSymbol(
                name=name,
                symbol_type="function",
                header_file=filepath,
                line=line_num,
                signature=line,
            )

        return None

    def _is_type_decl(self, line: str) -> bool:
        """检查是否是类型声明"""
        keywords = ["结构体", "类", "类型", "struct", "class", "typedef"]
        return any(kw in line.lower() for kw in keywords)

    def _parse_type_decl(
        self, line: str, line_num: int, filepath: str
    ) -> Optional[TypeDefinition]:
        """解析类型声明"""
        import re

        # 结构体/类
        match = re.match(r".*(结构体|类|struct|class)\s+(\w+)", line, re.IGNORECASE)
        if match:
            kind = (
                "struct"
                if "struct" in match.group(1).lower() or "结构体" in match.group(1)
                else "class"
            )
            name = match.group(2)

            return TypeDefinition(
                name=name, kind=kind, defined_in=filepath, line=line_num
            )

        return None

    def _is_cache_valid(self, pch: PrecompiledHeader, path: Path) -> bool:
        """检查缓存是否有效"""
        if not path.exists():
            return False

        if pch.version != self.VERSION:
            return False

        # 检查修改时间
        if path.stat().st_mtime > pch.header_index.last_modified:
            return False

        # 检查依赖文件
        for dep in pch.dependencies:
            dep_path = Path(dep)
            if dep_path.exists() and dep_path.stat().st_mtime > pch.compiled_time:
                return False

        return pch.is_valid

    def lookup_symbol(self, name: str) -> List[HeaderSymbol]:
        """查找符号"""
        return self.symbol_index.lookup(name)

    def lookup_macro(self, name: str) -> Optional[MacroDefinition]:
        """查找宏定义"""
        return self.macro_cache.get(name)

    def lookup_type(self, name: str) -> Optional[TypeDefinition]:
        """查找类型定义"""
        return self.type_cache.get(name)

    def invalidate(self, filepath: str):
        """使缓存失效"""
        if filepath in self.headers:
            # 移除符号索引
            self.symbol_index.remove_header_symbols(filepath)

            # 移除宏缓存
            header_index = self.headers[filepath].header_index
            for name in header_index.macros:
                if name in self.macro_cache:
                    del self.macro_cache[name]

            # 移除类型缓存
            for name in header_index.types:
                if name in self.type_cache:
                    del self.type_cache[name]

            # 移除缓存
            del self.headers[filepath]

            self._save_index()

    def clear(self):
        """清空所有缓存"""
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(exist_ok=True)

        self.headers.clear()
        self.symbol_index = SymbolIndex()
        self.macro_cache.clear()
        self.type_cache.clear()

        self.stats = {
            "total_headers": 0,
            "total_symbols": 0,
            "total_macros": 0,
            "total_types": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_parse_time": 0.0,
            "space_used": 0,
        }

        print("🧹 已清空预编译头文件缓存")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        hit_rate = 0.0
        total_requests = self.stats["cache_hits"] + self.stats["cache_misses"]
        if total_requests > 0:
            hit_rate = self.stats["cache_hits"] / total_requests * 100

        return {
            **self.stats,
            "hit_rate_percent": hit_rate,
            "avg_parse_time": self.stats["total_parse_time"]
            / max(self.stats["total_headers"], 1),
            "space_used_mb": self.stats["space_used"] / 1024 / 1024,
        }

    def generate_report(self) -> str:
        """生成报告"""
        stats = self.get_stats()

        lines = [
            "=" * 70,
            "预编译头文件系统报告",
            "=" * 70,
            "",
            "📈 统计:",
            f"  头文件数: {stats['total_headers']}",
            f"  符号数: {stats['total_symbols']}",
            f"  宏定义数: {stats['total_macros']}",
            f"  类型定义数: {stats['total_types']}",
            "",
            f"  缓存命中: {stats['cache_hits']}",
            f"  缓存未中: {stats['cache_misses']}",
            f"  命中率: {stats['hit_rate_percent']:.1f}%",
            "",
            f"  总解析时间: {stats['total_parse_time']:.2f}s",
            f"  平均解析时间: {stats['avg_parse_time']:.4f}s",
            f"  空间使用: {stats['space_used_mb']:.2f} MB",
            "",
        ]

        if self.headers:
            lines.append("已缓存头文件:")
            lines.append("-" * 70)
            for filepath, pch in list(self.headers.items())[:10]:
                symbols_count = len(pch.header_index.symbols)
                lines.append(
                    f"  {Path(filepath).name}: {symbols_count} 符号 (命中{pch.cache_hits}次)"
                )

        lines.append("")
        lines.append("=" * 70)

        return "\n".join(lines)

    def _header_index_to_dict(self, index: HeaderIndex) -> dict:
        """将HeaderIndex转换为字典"""
        return {
            "filepath": index.filepath,
            "header_type": index.header_type.value,
            "last_modified": index.last_modified,
            "content_hash": index.content_hash,
            "symbols": {
                k: {
                    "name": v.name,
                    "symbol_type": v.symbol_type,
                    "header_file": v.header_file,
                    "line": v.line,
                    "signature": v.signature,
                    "namespace": v.namespace,
                    "is_exported": v.is_exported,
                }
                for k, v in index.symbols.items()
            },
            "macros": {
                k: {
                    "name": v.name,
                    "params": v.params,
                    "body": v.body,
                    "is_function_like": v.is_function_like,
                    "defined_in": v.defined_in,
                    "line": v.line,
                }
                for k, v in index.macros.items()
            },
            "types": {
                k: {
                    "name": v.name,
                    "kind": v.kind,
                    "defined_in": v.defined_in,
                    "line": v.line,
                }
                for k, v in index.types.items()
            },
            "includes": index.includes,
            "parse_time": index.parse_time,
            "size": index.size,
        }

    def _dict_to_header_index(self, data: dict) -> HeaderIndex:
        """将字典转换为HeaderIndex"""
        return HeaderIndex(
            filepath=data["filepath"],
            header_type=HeaderType(data["header_type"]),
            last_modified=data["last_modified"],
            content_hash=data["content_hash"],
            symbols={
                k: HeaderSymbol(
                    name=v["name"],
                    symbol_type=v["symbol_type"],
                    header_file=v["header_file"],
                    line=v["line"],
                    signature=v.get("signature"),
                    namespace=v.get("namespace"),
                    is_exported=v.get("is_exported", True),
                )
                for k, v in data.get("symbols", {}).items()
            },
            macros={
                k: MacroDefinition(
                    name=v["name"],
                    params=v.get("params"),
                    body=v["body"],
                    is_function_like=v.get("is_function_like", False),
                    defined_in=v.get("defined_in", ""),
                    line=v.get("line", 0),
                )
                for k, v in data.get("macros", {}).items()
            },
            types={
                k: TypeDefinition(
                    name=v["name"],
                    kind=v["kind"],
                    defined_in=v.get("defined_in", ""),
                    line=v.get("line", 0),
                )
                for k, v in data.get("types", {}).items()
            },
            includes=data.get("includes", []),
            parse_time=data.get("parse_time", 0.0),
            size=data.get("size", 0),
        )


# 便捷函数
def create_pch_manager(cache_dir: str = ".zhc_pch") -> PrecompiledHeaderManager:
    """创建预编译头文件管理器"""
    return PrecompiledHeaderManager(cache_dir)


# 测试
if __name__ == "__main__":
    print("=== 预编译头文件系统测试 ===\n")

    # 创建管理器
    manager = PrecompiledHeaderManager()

    # 测试头文件内容
    test_header = """
#include "标准库/stdio"
#include "标准库/stdlib"

#define MAX_SIZE 100
#define MIN(a, b) ((a) < (b) ? (a) : (b))

整数型 最大值(整数型 a, 整数型 b);
浮点型 平均值(整数型 数组[], 整数型 长度);

结构体 点 {
    整数型 x;
    整数型 y;
};
"""

    # 预处理头文件
    pch = manager.preprocess_header("test_header.zhh", test_header)

    print("预处理完成:")
    print(f"  符号数: {len(pch.header_index.symbols)}")
    print(f"  宏定义数: {len(pch.header_index.macros)}")
    print(f"  类型定义数: {len(pch.header_index.types)}")
    print(f"  包含文件数: {len(pch.header_index.includes)}")
    print()

    # 查找符号
    symbols = manager.lookup_symbol("最大值")
    if symbols:
        print(f"找到符号: {symbols[0].name} ({symbols[0].symbol_type})")

    # 查找宏
    macro = manager.lookup_macro("MAX_SIZE")
    if macro:
        print(f"找到宏: {macro.name} = {macro.body}")

    print()
    print(manager.generate_report())

    print("\n=== 测试完成 ===")
