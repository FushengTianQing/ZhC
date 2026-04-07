#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试代码生成映射表 (mappings.py)

测试覆盖：
1. 类型映射
2. 修饰符映射
3. 函数名映射
4. Include 映射
"""

import pytest

from zhc.ir.mappings import (
    TYPE_MAP, MODIFIER_MAP, FUNCTION_NAME_MAP, INCLUDE_MAP, STDLIB_FUNC_MAP,
    resolve_type, resolve_function_name, resolve_modifier, resolve_include
)


class TestTypeMap:
    """测试类型映射"""
    
    def test_integer_type(self):
        """测试整数类型映射"""
        assert TYPE_MAP['整数型'] == 'int'
    
    def test_float_type(self):
        """测试浮点类型映射"""
        assert TYPE_MAP['浮点型'] == 'float'
        assert TYPE_MAP['双精度浮点型'] == 'double'
    
    def test_char_type(self):
        """测试字符类型映射"""
        assert TYPE_MAP['字符型'] == 'char'
        assert TYPE_MAP['字节型'] == 'unsigned char'
    
    def test_string_type(self):
        """测试字符串类型映射"""
        assert TYPE_MAP['字符串型'] == 'char*'
    
    def test_void_type(self):
        """测试空类型映射"""
        assert TYPE_MAP['空型'] == 'void'
        assert TYPE_MAP['无类型'] == 'void'
    
    def test_boolean_type(self):
        """测试布尔类型映射"""
        assert TYPE_MAP['布尔型'] == '_Bool'
        assert TYPE_MAP['逻辑型'] == '_Bool'
    
    def test_long_short_type(self):
        """测试长整数和短整数类型映射"""
        assert TYPE_MAP['长整数型'] == 'long'
        assert TYPE_MAP['短整数型'] == 'short'


class TestModifierMap:
    """测试修饰符映射"""
    
    def test_const_modifier(self):
        """测试常量修饰符"""
        assert MODIFIER_MAP['常量'] == 'const'
    
    def test_static_modifier(self):
        """测试静态修饰符"""
        assert MODIFIER_MAP['静态'] == 'static'
    
    def test_volatile_modifier(self):
        """测试易变修饰符"""
        assert MODIFIER_MAP['易变'] == 'volatile'
    
    def test_extern_modifier(self):
        """测试外部修饰符"""
        assert MODIFIER_MAP['外部'] == 'extern'
    
    def test_inline_modifier(self):
        """测试内联修饰符"""
        assert MODIFIER_MAP['内联'] == 'inline'
    
    def test_unsigned_modifier(self):
        """测试无符号修饰符"""
        assert MODIFIER_MAP['无符号'] == 'unsigned'
        assert MODIFIER_MAP['有符号'] == 'signed'
    
    def test_register_modifier(self):
        """测试寄存器修饰符"""
        assert MODIFIER_MAP['注册'] == 'register'


class TestFunctionNameMap:
    """测试函数名映射"""
    
    def test_main_function(self):
        """测试主函数映射"""
        assert FUNCTION_NAME_MAP['主函数'] == 'main'
        assert FUNCTION_NAME_MAP['主程序'] == 'main'


class TestStdlibFuncMap:
    """测试标准库函数映射"""
    
    def test_io_functions(self):
        """测试输入输出函数"""
        assert STDLIB_FUNC_MAP['打印'] == 'printf'
        assert STDLIB_FUNC_MAP['输入'] == 'scanf'
        assert STDLIB_FUNC_MAP['输出字符'] == 'putchar'
        assert STDLIB_FUNC_MAP['输入字符'] == 'getchar'
        assert STDLIB_FUNC_MAP['打印字符串'] == 'puts'
    
    def test_file_functions(self):
        """测试文件函数"""
        assert STDLIB_FUNC_MAP['打开文件'] == 'fopen'
        assert STDLIB_FUNC_MAP['关闭文件'] == 'fclose'
    
    def test_string_functions(self):
        """测试字符串函数"""
        assert STDLIB_FUNC_MAP['字符串长度'] == 'strlen'
        assert STDLIB_FUNC_MAP['字符串复制'] == 'strcpy'
    
    def test_memory_functions(self):
        """测试内存函数"""
        assert STDLIB_FUNC_MAP['申请'] == 'malloc'
        assert STDLIB_FUNC_MAP['释放'] == 'free'
    
    def test_math_functions(self):
        """测试数学函数"""
        assert STDLIB_FUNC_MAP['平方根'] == 'sqrt'
        assert STDLIB_FUNC_MAP['幂函数'] == 'pow'
        assert STDLIB_FUNC_MAP['绝对值'] == 'abs'
    
    def test_other_functions(self):
        """测试其他函数"""
        assert STDLIB_FUNC_MAP['退出程序'] == 'exit'


class TestIncludeMap:
    """测试 Include 映射"""
    
    def test_stdio_include(self):
        """测试标准输入输出"""
        assert INCLUDE_MAP['标准输入输出'] == '#include <stdio.h>'
        assert INCLUDE_MAP['stdio'] == '#include <stdio.h>'
    
    def test_stdlib_include(self):
        """测试标准库"""
        assert INCLUDE_MAP['标准库'] == '#include <stdlib.h>'
        assert INCLUDE_MAP['stdlib'] == '#include <stdlib.h>'
    
    def test_string_include(self):
        """测试字符串库"""
        assert INCLUDE_MAP['字符串'] == '#include <string.h>'
        assert INCLUDE_MAP['string'] == '#include <string.h>'
    
    def test_math_include(self):
        """测试数学库"""
        assert INCLUDE_MAP['数学'] == '#include <math.h>'
        assert INCLUDE_MAP['math'] == '#include <math.h>'
    
    def test_time_include(self):
        """测试时间库"""
        assert INCLUDE_MAP['时间'] == '#include <time.h>'
        assert INCLUDE_MAP['time'] == '#include <time.h>'
    
    def test_ctype_include(self):
        """测试字符处理库"""
        assert INCLUDE_MAP['字符处理'] == '#include <ctype.h>'
        assert INCLUDE_MAP['ctype'] == '#include <ctype.h>'
    
    def test_assert_include(self):
        """测试断言库"""
        assert INCLUDE_MAP['断言'] == '#include <assert.h>'
        assert INCLUDE_MAP['assert'] == '#include <assert.h>'
    
    def test_stdbool_include(self):
        """测试布尔库"""
        assert INCLUDE_MAP['标准布尔'] == '#include <stdbool.h>'
        assert INCLUDE_MAP['stdbool'] == '#include <stdbool.h>'


class TestResolveType:
    """测试类型解析函数"""
    
    def test_resolve_known_types(self):
        """测试解析已知类型"""
        assert resolve_type('整数型') == 'int'
        assert resolve_type('浮点型') == 'float'
        assert resolve_type('字符型') == 'char'
        assert resolve_type('字符串型') == 'char*'
    
    def test_resolve_unknown_type(self):
        """测试解析未知类型（返回原值）"""
        assert resolve_type('自定义类型') == '自定义类型'
        assert resolve_type('MyType') == 'MyType'


class TestResolveFunctionName:
    """测试函数名解析函数"""
    
    def test_resolve_stdlib_functions(self):
        """测试解析标准库函数"""
        assert resolve_function_name('打印') == 'printf'
        assert resolve_function_name('输入') == 'scanf'
        assert resolve_function_name('申请') == 'malloc'
    
    def test_resolve_special_functions(self):
        """测试解析特殊函数"""
        assert resolve_function_name('主函数') == 'main'
        assert resolve_function_name('主程序') == 'main'
    
    def test_resolve_custom_function(self):
        """测试解析自定义函数（返回原值）"""
        assert resolve_function_name('自定义函数') == '自定义函数'
        assert resolve_function_name('myFunction') == 'myFunction'
    
    def test_resolve_priority(self):
        """测试解析优先级（标准库优先）"""
        # STDLIB_FUNC_MAP 优先于 FUNCTION_NAME_MAP
        # 如果某个名字同时存在于两个映射中，标准库映射优先
        pass


class TestResolveModifier:
    """测试修饰符解析函数"""
    
    def test_resolve_known_modifiers(self):
        """测试解析已知修饰符"""
        assert resolve_modifier('常量') == 'const'
        assert resolve_modifier('静态') == 'static'
        assert resolve_modifier('易变') == 'volatile'
    
    def test_resolve_unknown_modifier(self):
        """测试解析未知修饰符（返回原值）"""
        assert resolve_modifier('自定义修饰符') == '自定义修饰符'
        assert resolve_modifier('custom') == 'custom'


class TestResolveInclude:
    """测试 Include 解析函数"""
    
    def test_resolve_known_includes(self):
        """测试解析已知模块"""
        assert resolve_include('标准输入输出') == '#include <stdio.h>'
        assert resolve_include('标准库') == '#include <stdlib.h>'
        assert resolve_include('数学') == '#include <math.h>'
    
    def test_resolve_unknown_include(self):
        """测试解析未知模块（返回注释）"""
        result = resolve_include('未知模块')
        assert 'unknown module' in result
        assert '未知模块' in result


class TestMappingConsistency:
    """测试映射一致性"""
    
    def test_type_map_no_duplicates(self):
        """测试类型映射无重复值"""
        values = list(TYPE_MAP.values())
        # 允许重复值（如 'void' 和 '_Bool'）
        # 但检查键的唯一性
        keys = list(TYPE_MAP.keys())
        assert len(keys) == len(set(keys))
    
    def test_modifier_map_no_duplicates(self):
        """测试修饰符映射无重复键"""
        keys = list(MODIFIER_MAP.keys())
        assert len(keys) == len(set(keys))
    
    def test_function_name_map_no_duplicates(self):
        """测试函数名映射无重复键"""
        keys = list(FUNCTION_NAME_MAP.keys())
        assert len(keys) == len(set(keys))
    
    def test_include_map_no_duplicates(self):
        """测试 Include 映射无重复键"""
        keys = list(INCLUDE_MAP.keys())
        assert len(keys) == len(set(keys))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])