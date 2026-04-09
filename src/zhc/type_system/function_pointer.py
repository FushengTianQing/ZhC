"""
函数指针类型系统

提供函数指针类型的定义、解析和 LLVM 类型映射。

创建日期: 2026-04-09
最后更新: 2026-04-09
维护者: ZHC开发团队
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, TYPE_CHECKING
import llvmlite.ir as ll

if TYPE_CHECKING:
    pass


@dataclass
class FunctionPointerTypeInfo:
    """
    函数指针类型信息

    存储函数指针的类型签名和 LLVM 类型。
    """

    return_type: str  # 返回类型名
    param_types: List[str]  # 参数类型名列表
    llvm_type: Optional[ll.Type] = None  # LLVM 函数类型
    is_vararg: bool = False  # 是否为可变参数

    def signature_str(self) -> str:
        """生成类型签名字符串"""
        params = ", ".join(self.param_types) if self.param_types else "void"
        return f"{self.return_type}({params})"

    def llvm_signature_str(self) -> str:
        """生成 LLVM 类型签名字符串"""
        if not self.llvm_type:
            return "unknown"

        if isinstance(self.llvm_type, ll.PointerType):
            func_type = self.llvm_type.pointee
            if hasattr(func_type, "return_type"):
                ret = str(func_type.return_type)
                args = (
                    ", ".join(str(a) for a in func_type.args)
                    if func_type.args
                    else "void"
                )
                return f"{ret} ({args})*"
        return str(self.llvm_type)

    def __str__(self) -> str:
        return f"函数指针<{self.signature_str()}>"


@dataclass
class FunctionPointerDecl:
    """
    函数指针声明

    存储函数指针变量的声明信息。
    """

    name: str  # 变量名
    func_ptr_type: FunctionPointerTypeInfo  # 函数指针类型
    target_func: Optional[str] = None  # 目标函数名（初始化表达式）
    source_location: Optional[str] = None  # 源代码位置

    def __str__(self) -> str:
        result = f"{self.name}: {self.func_ptr_type}"
        if self.target_func:
            result += f" = {self.target_func}"
        return result


class FunctionPointerTypeMapper:
    """
    函数指针类型映射器

    提供 ZhC 函数指针类型到 LLVM 类型的映射。
    """

    def __init__(self):
        """初始化映射器"""
        self._type_cache: Dict[str, ll.Type] = {}

    def map_function_pointer_type(
        self, return_type: str, param_types: List[str], target_platform: str = "linux"
    ) -> ll.PointerType:
        """
        映射函数指针类型到 LLVM

        Args:
            return_type: 返回类型名
            param_types: 参数类型名列表
            target_platform: 目标平台

        Returns:
            LLVM 函数指针类型
        """
        # 生成缓存键
        cache_key = f"{return_type}({','.join(param_types)})"

        if cache_key in self._type_cache:
            return self._type_cache[cache_key]

        # 获取返回类型的 LLVM 类型
        llvm_return = self._to_llvm_type(return_type)

        # 获取参数类型的 LLVM 类型列表
        llvm_params = [self._to_llvm_type(pt) for pt in param_types]

        # 创建 LLVM 函数类型
        func_type = ll.FunctionType(llvm_return, llvm_params)

        # 返回函数指针类型
        func_ptr_type = ll.PointerType(func_type)

        # 缓存
        self._type_cache[cache_key] = func_ptr_type

        return func_ptr_type

    def _to_llvm_type(self, type_name: str) -> ll.Type:
        """
        将 ZhC 类型转换为 LLVM 类型

        Args:
            type_name: ZhC 类型名

        Returns:
            LLVM 类型
        """
        # 基础类型映射
        TYPE_MAP = {
            # 整数类型
            "整数型": ll.IntType(32),
            "短整型": ll.IntType(16),
            "长整型": ll.IntType(64),
            "字符型": ll.IntType(8),
            "布尔型": ll.IntType(8),
            "无符号整数型": ll.IntType(32),
            "无符号短整型": ll.IntType(16),
            "无符号长整型": ll.IntType(64),
            "无符号字符型": ll.IntType(8),
            # 浮点类型
            "浮点型": ll.FloatType(),
            "双精度浮点型": ll.DoubleType(),
            # 特殊类型
            "空型": ll.VoidType(),
        }

        # 检查是否为指针类型
        if type_name.endswith("指针") or type_name.endswith("*"):
            base_type_name = type_name.rstrip("指针").rstrip("*").strip()
            if base_type_name == "字符":
                return ll.PointerType(ll.IntType(8))
            base_type = self._to_llvm_type(base_type_name)
            return ll.PointerType(base_type)

        return TYPE_MAP.get(type_name, ll.IntType(32))

    def get_function_pointer_info(
        self, return_type: str, param_types: List[str], target_platform: str = "linux"
    ) -> FunctionPointerTypeInfo:
        """
        获取函数指针类型信息

        Args:
            return_type: 返回类型名
            param_types: 参数类型名列表
            target_platform: 目标平台

        Returns:
            函数指针类型信息
        """
        llvm_type = self.map_function_pointer_type(
            return_type, param_types, target_platform
        )

        return FunctionPointerTypeInfo(
            return_type=return_type, param_types=param_types, llvm_type=llvm_type
        )

    def is_compatible(
        self, fp_type1: FunctionPointerTypeInfo, fp_type2: FunctionPointerTypeInfo
    ) -> bool:
        """
        检查两个函数指针类型是否兼容

        Args:
            fp_type1: 第一个函数指针类型
            fp_type2: 第二个函数指针类型

        Returns:
            是否兼容
        """
        # 返回类型必须匹配
        if fp_type1.return_type != fp_type2.return_type:
            return False

        # 参数数量必须匹配
        if len(fp_type1.param_types) != len(fp_type2.param_types):
            return False

        # 参数类型必须匹配
        for t1, t2 in zip(fp_type1.param_types, fp_type2.param_types):
            if not self._types_compatible(t1, t2):
                return False

        return True

    def _types_compatible(self, type1: str, type2: str) -> bool:
        """检查两个类型是否兼容"""
        # 完全匹配
        if type1 == type2:
            return True

        # 指针类型兼容
        if (type1.endswith("指针") or type1.endswith("*")) and (
            type2.endswith("指针") or type2.endswith("*")
        ):
            return True

        return False


class FunctionPointerRegistry:
    """
    函数指针注册表

    管理程序中所有函数指针的声明。
    """

    def __init__(self):
        """初始化注册表"""
        self._declarations: Dict[str, FunctionPointerDecl] = {}
        self._target_functions: Dict[str, str] = {}  # 函数指针名 -> 目标函数名

    def register(self, decl: FunctionPointerDecl):
        """
        注册函数指针

        Args:
            decl: 函数指针声明
        """
        self._declarations[decl.name] = decl

        if decl.target_func:
            self._target_functions[decl.name] = decl.target_func

    def get(self, name: str) -> Optional[FunctionPointerDecl]:
        """
        获取函数指针声明

        Args:
            name: 函数指针名

        Returns:
            函数指针声明，如果不存在则返回 None
        """
        return self._declarations.get(name)

    def is_function_pointer(self, name: str) -> bool:
        """
        检查是否为函数指针

        Args:
            name: 变量名

        Returns:
            是否为函数指针
        """
        return name in self._declarations

    def get_target_function(self, func_ptr_name: str) -> Optional[str]:
        """
        获取函数指针的目标函数

        Args:
            func_ptr_name: 函数指针名

        Returns:
            目标函数名
        """
        return self._target_functions.get(func_ptr_name)

    def get_all_declarations(self) -> List[FunctionPointerDecl]:
        """
        获取所有函数指针声明

        Returns:
            函数指针声明列表
        """
        return list(self._declarations.values())

    def clear(self):
        """清空注册表"""
        self._declarations.clear()
        self._target_functions.clear()


# 全局类型映射器实例
_global_type_mapper: Optional[FunctionPointerTypeMapper] = None
_global_registry: Optional[FunctionPointerRegistry] = None


def get_type_mapper() -> FunctionPointerTypeMapper:
    """获取全局类型映射器"""
    global _global_type_mapper
    if _global_type_mapper is None:
        _global_type_mapper = FunctionPointerTypeMapper()
    return _global_type_mapper


def get_registry() -> FunctionPointerRegistry:
    """获取全局注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = FunctionPointerRegistry()
    return _global_registry


def create_function_pointer_type(
    return_type: str, param_types: List[str]
) -> FunctionPointerTypeInfo:
    """
    创建函数指针类型信息

    Args:
        return_type: 返回类型名
        param_types: 参数类型名列表

    Returns:
        函数指针类型信息
    """
    mapper = get_type_mapper()
    return mapper.get_function_pointer_info(return_type, param_types)


def is_function_pointer_compatible(
    fp1: FunctionPointerTypeInfo, fp2: FunctionPointerTypeInfo
) -> bool:
    """
    检查两个函数指针类型是否兼容

    Args:
        fp1: 第一个函数指针类型
        fp2: 第二个函数指针类型

    Returns:
        是否兼容
    """
    mapper = get_type_mapper()
    return mapper.is_compatible(fp1, fp2)


# 导出公共 API
__all__ = [
    "FunctionPointerTypeInfo",
    "FunctionPointerDecl",
    "FunctionPointerTypeMapper",
    "FunctionPointerRegistry",
    "get_type_mapper",
    "get_registry",
    "create_function_pointer_type",
    "is_function_pointer_compatible",
]
