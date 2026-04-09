"""
外部函数解析器

解析和链接外部 C 函数。

创建日期: 2026-04-09
最后更新: 2026-04-09
维护者: ZHC开发团队
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Set
from enum import Enum
import llvmlite.ir as ll

from .c_types import get_c_type_mapper


class LinkageType(Enum):
    """链接类型"""

    EXTERN = "extern"  # 外部链接
    EXTERN_WEAK = "extern_weak"  # 弱外部链接
    PRIVATE = "private"  # 私有链接


@dataclass
class ExternalFunction:
    """外部函数信息"""

    name: str  # 函数名
    return_type: str  # 返回类型
    param_types: List[str]  # 参数类型列表
    linkage: LinkageType = LinkageType.EXTERN
    symbol: Optional[str] = None  # 实际符号名
    library: Optional[str] = None  # 所属库
    is_vararg: bool = False  # 是否可变参数


@dataclass
class ExternalBlock:
    """外部函数块"""

    language: str  # 语言（如 "C"）
    functions: List[ExternalFunction]  # 函数列表
    source_location: Optional[str] = None


class ExternalFunctionRegistry:
    """
    外部函数注册表

    管理程序中声明的外部函数。
    """

    def __init__(self):
        """初始化注册表"""
        self._functions: Dict[str, ExternalFunction] = {}
        self._libraries: Set[str] = set()

    def register(self, func: ExternalFunction):
        """
        注册外部函数

        Args:
            func: 外部函数信息
        """
        self._functions[func.name] = func
        if func.library:
            self._libraries.add(func.library)

    def get(self, name: str) -> Optional[ExternalFunction]:
        """
        获取外部函数

        Args:
            name: 函数名

        Returns:
            外部函数信息
        """
        return self._functions.get(name)

    def is_registered(self, name: str) -> bool:
        """
        检查函数是否已注册

        Args:
            name: 函数名

        Returns:
            是否已注册
        """
        return name in self._functions

    def get_all_functions(self) -> List[ExternalFunction]:
        """
        获取所有外部函数

        Returns:
            外部函数列表
        """
        return list(self._functions.values())

    def get_functions_by_library(self, library: str) -> List[ExternalFunction]:
        """
        获取指定库的函数

        Args:
            library: 库名

        Returns:
            函数列表
        """
        return [f for f in self._functions.values() if f.library == library]

    def get_libraries(self) -> List[str]:
        """
        获取所有库

        Returns:
            库列表
        """
        return sorted(self._libraries)

    def clear(self):
        """清空注册表"""
        self._functions.clear()
        self._libraries.clear()


class ExternalFunctionResolver:
    """
    外部函数解析器

    解析外部函数声明并生成 LLVM IR。
    """

    # 标准库函数预设
    STANDARD_FUNCTIONS: Dict[str, ExternalFunction] = {
        # 标准输入输出
        "printf": ExternalFunction(
            name="printf",
            return_type="整数型",
            param_types=["字符型指针"],
            library="libc",
            is_vararg=True,
        ),
        "scanf": ExternalFunction(
            name="scanf",
            return_type="整数型",
            param_types=["字符型指针"],
            library="libc",
            is_vararg=True,
        ),
        "sprintf": ExternalFunction(
            name="sprintf",
            return_type="整数型",
            param_types=["字符型指针", "字符型指针"],
            library="libc",
            is_vararg=True,
        ),
        "snprintf": ExternalFunction(
            name="snprintf",
            return_type="整数型",
            param_types=["字符型指针", "整数型", "字符型指针"],
            library="libc",
            is_vararg=True,
        ),
        "fprintf": ExternalFunction(
            name="fprintf",
            return_type="整数型",
            param_types=["文件型指针", "字符型指针"],
            library="libc",
            is_vararg=True,
        ),
        "fscanf": ExternalFunction(
            name="fscanf",
            return_type="整数型",
            param_types=["文件型指针", "字符型指针"],
            library="libc",
            is_vararg=True,
        ),
        # 文件操作
        "fopen": ExternalFunction(
            name="fopen",
            return_type="文件型指针",
            param_types=["字符型指针", "字符型指针"],
            library="libc",
        ),
        "fclose": ExternalFunction(
            name="fclose",
            return_type="整数型",
            param_types=["文件型指针"],
            library="libc",
        ),
        "fread": ExternalFunction(
            name="fread",
            return_type="整数型",
            param_types=["空型指针", "整数型", "整数型", "文件型指针"],
            library="libc",
        ),
        "fwrite": ExternalFunction(
            name="fwrite",
            return_type="整数型",
            param_types=["空型指针", "整数型", "整数型", "文件型指针"],
            library="libc",
        ),
        "fseek": ExternalFunction(
            name="fseek",
            return_type="整数型",
            param_types=["文件型指针", "长整型", "整数型"],
            library="libc",
        ),
        "ftell": ExternalFunction(
            name="ftell",
            return_type="长整型",
            param_types=["文件型指针"],
            library="libc",
        ),
        "rewind": ExternalFunction(
            name="rewind",
            return_type="空型",
            param_types=["文件型指针"],
            library="libc",
        ),
        "feof": ExternalFunction(
            name="feof",
            return_type="整数型",
            param_types=["文件型指针"],
            library="libc",
        ),
        "ferror": ExternalFunction(
            name="ferror",
            return_type="整数型",
            param_types=["文件型指针"],
            library="libc",
        ),
        # 内存操作
        "malloc": ExternalFunction(
            name="malloc",
            return_type="空型指针",
            param_types=["整数型"],
            library="libc",
        ),
        "calloc": ExternalFunction(
            name="calloc",
            return_type="空型指针",
            param_types=["整数型", "整数型"],
            library="libc",
        ),
        "free": ExternalFunction(
            name="free", return_type="空型", param_types=["空型指针"], library="libc"
        ),
        "realloc": ExternalFunction(
            name="realloc",
            return_type="空型指针",
            param_types=["空型指针", "整数型"],
            library="libc",
        ),
        "memcpy": ExternalFunction(
            name="memcpy",
            return_type="空型指针",
            param_types=["空型指针", "空型指针", "整数型"],
            library="libc",
        ),
        "memmove": ExternalFunction(
            name="memmove",
            return_type="空型指针",
            param_types=["空型指针", "空型指针", "整数型"],
            library="libc",
        ),
        "memset": ExternalFunction(
            name="memset",
            return_type="空型指针",
            param_types=["空型指针", "整数型", "整数型"],
            library="libc",
        ),
        "memcmp": ExternalFunction(
            name="memcmp",
            return_type="整数型",
            param_types=["空型指针", "空型指针", "整数型"],
            library="libc",
        ),
        # 字符串操作
        "strlen": ExternalFunction(
            name="strlen",
            return_type="整数型",
            param_types=["字符型指针"],
            library="libc",
        ),
        "strcpy": ExternalFunction(
            name="strcpy",
            return_type="字符型指针",
            param_types=["字符型指针", "字符型指针"],
            library="libc",
        ),
        "strncpy": ExternalFunction(
            name="strncpy",
            return_type="字符型指针",
            param_types=["字符型指针", "字符型指针", "整数型"],
            library="libc",
        ),
        "strcat": ExternalFunction(
            name="strcat",
            return_type="字符型指针",
            param_types=["字符型指针", "字符型指针"],
            library="libc",
        ),
        "strncat": ExternalFunction(
            name="strncat",
            return_type="字符型指针",
            param_types=["字符型指针", "字符型指针", "整数型"],
            library="libc",
        ),
        "strcmp": ExternalFunction(
            name="strcmp",
            return_type="整数型",
            param_types=["字符型指针", "字符型指针"],
            library="libc",
        ),
        "strncmp": ExternalFunction(
            name="strncmp",
            return_type="整数型",
            param_types=["字符型指针", "字符型指针", "整数型"],
            library="libc",
        ),
        "strchr": ExternalFunction(
            name="strchr",
            return_type="字符型指针",
            param_types=["字符型指针", "整数型"],
            library="libc",
        ),
        "strstr": ExternalFunction(
            name="strstr",
            return_type="字符型指针",
            param_types=["字符型指针", "字符型指针"],
            library="libc",
        ),
        # 数学函数
        "abs": ExternalFunction(
            name="abs", return_type="整数型", param_types=["整数型"], library="libm"
        ),
        "labs": ExternalFunction(
            name="labs", return_type="长整型", param_types=["长整型"], library="libm"
        ),
        "fabs": ExternalFunction(
            name="fabs",
            return_type="双精度浮点型",
            param_types=["双精度浮点型"],
            library="libm",
        ),
        "fabsf": ExternalFunction(
            name="fabsf", return_type="浮点型", param_types=["浮点型"], library="libm"
        ),
        "sqrt": ExternalFunction(
            name="sqrt",
            return_type="双精度浮点型",
            param_types=["双精度浮点型"],
            library="libm",
        ),
        "sqrtf": ExternalFunction(
            name="sqrtf", return_type="浮点型", param_types=["浮点型"], library="libm"
        ),
        "pow": ExternalFunction(
            name="pow",
            return_type="双精度浮点型",
            param_types=["双精度浮点型", "双精度浮点型"],
            library="libm",
        ),
        "sin": ExternalFunction(
            name="sin",
            return_type="双精度浮点型",
            param_types=["双精度浮点型"],
            library="libm",
        ),
        "cos": ExternalFunction(
            name="cos",
            return_type="双精度浮点型",
            param_types=["双精度浮点型"],
            library="libm",
        ),
        "tan": ExternalFunction(
            name="tan",
            return_type="双精度浮点型",
            param_types=["双精度浮点型"],
            library="libm",
        ),
        "asin": ExternalFunction(
            name="asin",
            return_type="双精度浮点型",
            param_types=["双精度浮点型"],
            library="libm",
        ),
        "acos": ExternalFunction(
            name="acos",
            return_type="双精度浮点型",
            param_types=["双精度浮点型"],
            library="libm",
        ),
        "atan": ExternalFunction(
            name="atan",
            return_type="双精度浮点型",
            param_types=["双精度浮点型"],
            library="libm",
        ),
        "atan2": ExternalFunction(
            name="atan2",
            return_type="双精度浮点型",
            param_types=["双精度浮点型", "双精度浮点型"],
            library="libm",
        ),
        "exp": ExternalFunction(
            name="exp",
            return_type="双精度浮点型",
            param_types=["双精度浮点型"],
            library="libm",
        ),
        "log": ExternalFunction(
            name="log",
            return_type="双精度浮点型",
            param_types=["双精度浮点型"],
            library="libm",
        ),
        "log10": ExternalFunction(
            name="log10",
            return_type="双精度浮点型",
            param_types=["双精度浮点型"],
            library="libm",
        ),
        "floor": ExternalFunction(
            name="floor",
            return_type="双精度浮点型",
            param_types=["双精度浮点型"],
            library="libm",
        ),
        "ceil": ExternalFunction(
            name="ceil",
            return_type="双精度浮点型",
            param_types=["双精度浮点型"],
            library="libm",
        ),
        "fmod": ExternalFunction(
            name="fmod",
            return_type="双精度浮点型",
            param_types=["双精度浮点型", "双精度浮点型"],
            library="libm",
        ),
        # 动态链接
        "dlopen": ExternalFunction(
            name="dlopen",
            return_type="空型指针",
            param_types=["字符型指针", "整数型"],
            library="libdl",
        ),
        "dlsym": ExternalFunction(
            name="dlsym",
            return_type="空型指针",
            param_types=["空型指针", "字符型指针"],
            library="libdl",
        ),
        "dlclose": ExternalFunction(
            name="dlclose",
            return_type="整数型",
            param_types=["空型指针"],
            library="libdl",
        ),
        "dlerror": ExternalFunction(
            name="dlerror", return_type="字符型指针", param_types=[], library="libdl"
        ),
    }

    def __init__(self, target_platform: str = "linux"):
        """
        初始化解析器

        Args:
            target_platform: 目标平台
        """
        self.target_platform = target_platform
        self._registry = ExternalFunctionRegistry()
        self._type_mapper = get_c_type_mapper(target_platform)
        self._module: Optional[ll.Module] = None

        # 注册标准函数
        for func in self.STANDARD_FUNCTIONS.values():
            self._registry.register(func)

    def set_module(self, module: ll.Module):
        """
        设置 LLVM 模块

        Args:
            module: LLVM 模块
        """
        self._module = module

    def declare_external_function(
        self,
        name: str,
        return_type: str,
        param_types: List[str],
        linkage: LinkageType = LinkageType.EXTERN,
        is_vararg: bool = False,
    ) -> Optional[ll.Function]:
        """
        声明外部函数

        Args:
            name: 函数名
            return_type: 返回类型
            param_types: 参数类型列表
            linkage: 链接类型
            is_vararg: 是否可变参数

        Returns:
            LLVM 函数
        """
        if self._module is None:
            return None

        # 检查是否已声明
        existing = self._module.get_global(name)
        if existing is not None:
            return existing

        # 创建函数类型
        func_type = self._type_mapper.create_function_type(return_type, param_types)

        # 创建函数
        func = ll.Function(self._module, func_type, name)

        # 设置链接类型
        if linkage == LinkageType.EXTERN_WEAK:
            func.linkage = "weak"
        elif linkage == LinkageType.PRIVATE:
            func.linkage = "private"
        else:
            func.linkage = "external"

        return func

    def resolve_function(self, name: str) -> Optional[ll.Function]:
        """
        解析函数

        Args:
            name: 函数名

        Returns:
            LLVM 函数
        """
        # 先检查注册表
        ext_func = self._registry.get(name)
        if ext_func is not None:
            return self.declare_external_function(
                ext_func.name,
                ext_func.return_type,
                ext_func.param_types,
                ext_func.linkage,
                ext_func.is_vararg,
            )

        # 尝试从标准函数中查找
        if name in self.STANDARD_FUNCTIONS:
            std_func = self.STANDARD_FUNCTIONS[name]
            return self.declare_external_function(
                std_func.name,
                std_func.return_type,
                std_func.param_types,
                std_func.linkage,
                std_func.is_vararg,
            )

        return None

    def parse_external_block(self, block: ExternalBlock) -> List[ll.Function]:
        """
        解析外部函数块

        Args:
            block: 外部函数块

        Returns:
            LLVM 函数列表
        """
        result = []
        for ext_func in block.functions:
            func = self.declare_external_function(
                ext_func.name,
                ext_func.return_type,
                ext_func.param_types,
                ext_func.linkage,
                ext_func.is_vararg,
            )
            if func is not None:
                result.append(func)
        return result

    def register_custom_function(self, func: ExternalFunction):
        """
        注册自定义外部函数

        Args:
            func: 外部函数信息
        """
        self._registry.register(func)


# 全局实例
_external_resolver: Optional[ExternalFunctionResolver] = None


def get_external_resolver(target_platform: str = "linux") -> ExternalFunctionResolver:
    """
    获取全局外部函数解析器

    Args:
        target_platform: 目标平台

    Returns:
        外部函数解析器
    """
    global _external_resolver
    if _external_resolver is None:
        _external_resolver = ExternalFunctionResolver(target_platform)
    return _external_resolver


# 导出公共 API
__all__ = [
    "LinkageType",
    "ExternalFunction",
    "ExternalBlock",
    "ExternalFunctionRegistry",
    "ExternalFunctionResolver",
    "get_external_resolver",
]
