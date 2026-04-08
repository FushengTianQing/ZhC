"""
Phase 8 集成测试：验证 GenericManager 和 TypeInferenceEngine 集成

测试内容：
1. GenericManager 延迟初始化
2. TypeInferenceEngine 延迟初始化
3. 泛型函数注册
4. 泛型类型注册
5. 类型推导后备机制
"""

import pytest
import sys
from pathlib import Path

# 确保可以导入 zhc 包
SRC_ROOT = Path(__file__).resolve().parent.parent / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


class TestPhase8Integration:
    """Phase 8 集成测试"""

    def test_generic_manager_lazy_init(self):
        """测试 GenericManager 延迟初始化"""
        from zhc.semantic.semantic_analyzer import SemanticAnalyzer
        
        analyzer = SemanticAnalyzer()
        
        # 初始状态应该是 None
        assert analyzer._generic_manager is None
        
        # 访问属性触发初始化
        gm = analyzer.generic_manager
        assert gm is not None
        assert analyzer._generic_manager is not None
        
        # 再次访问应该返回同一个实例
        gm2 = analyzer.generic_manager
        assert gm is gm2

    def test_type_inference_engine_lazy_init(self):
        """测试 TypeInferenceEngine 延迟初始化"""
        from zhc.semantic.semantic_analyzer import SemanticAnalyzer
        
        analyzer = SemanticAnalyzer()
        
        # 初始状态应该是 None
        assert analyzer._type_inference_engine is None
        
        # 访问属性触发初始化
        tie = analyzer.type_inference_engine
        assert tie is not None
        assert analyzer._type_inference_engine is not None
        
        # 再次访问应该返回同一个实例
        tie2 = analyzer.type_inference_engine
        assert tie is tie2

    def test_generic_manager_functionality(self):
        """测试 GenericManager 功能"""
        from zhc.semantic.semantic_analyzer import SemanticAnalyzer
        from zhc.semantic.generics import GenericType, GenericFunction, TypeParameter
        
        analyzer = SemanticAnalyzer()
        gm = analyzer.generic_manager
        
        # 注册泛型类型
        generic_type = GenericType(
            name="列表",
            type_params=[TypeParameter(name="T")],
            members=[]
        )
        gm.register_generic_type(generic_type)
        
        # 验证注册成功
        assert gm.is_generic_type("列表")
        retrieved = gm.get_generic_type("列表")
        assert retrieved.name == "列表"
        
        # 注册泛型函数
        generic_func = GenericFunction(
            name="最大值",
            type_params=[TypeParameter(name="T")],
            return_type="T",
            params=[]
        )
        gm.register_generic_function(generic_func)
        
        # 验证注册成功
        assert gm.is_generic_function("最大值")

    def test_type_inference_engine_functionality(self):
        """测试 TypeInferenceEngine 功能"""
        from zhc.semantic.semantic_analyzer import SemanticAnalyzer
        from zhc.typeinfer.engine import TypeEnv, BaseType
        
        analyzer = SemanticAnalyzer()
        tie = analyzer.type_inference_engine
        
        # 创建类型环境
        env = TypeEnv()
        env.bindings["x"] = BaseType.INT
        
        # 测试类型推导（需要 AST 节点，这里只验证引擎可用）
        stats = tie.get_statistics()
        assert isinstance(stats, dict)
        assert "type_vars_created" in stats

    def test_infer_with_engine_fallback(self):
        """测试类型推导后备机制"""
        from zhc.semantic.semantic_analyzer import SemanticAnalyzer
        
        analyzer = SemanticAnalyzer()
        
        # _infer_with_engine 方法应该存在
        assert hasattr(analyzer, '_infer_with_engine')
        
        # 对于 None 节点应该返回 None
        result = analyzer._infer_with_engine(None)
        assert result is None

    def test_symbol_to_infer_type_conversion(self):
        """测试类型转换方法"""
        from zhc.semantic.semantic_analyzer import SemanticAnalyzer
        from zhc.typeinfer.engine import BaseType
        
        analyzer = SemanticAnalyzer()
        
        # 测试类型转换
        assert analyzer._symbol_to_infer_type("整数型") == BaseType.INT
        assert analyzer._symbol_to_infer_type("浮点型") == BaseType.FLOAT
        assert analyzer._symbol_to_infer_type("字符串型") == BaseType.STRING
        assert analyzer._symbol_to_infer_type("逻辑型") == BaseType.BOOL
        assert analyzer._symbol_to_infer_type("未知类型") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
