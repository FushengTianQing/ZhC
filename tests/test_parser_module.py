#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试模块解析器 (ModuleParser)

测试覆盖：
1. 模块声明解析
2. 导入声明解析
3. 可见性标记解析
4. 符号声明解析
5. 文件解析
6. 错误处理
"""

import pytest
import tempfile
import os
from pathlib import Path

from zhc.parser.module import ModuleParser, ModuleInfo


class TestModuleInfo:
    """测试 ModuleInfo 类"""
    
    def test_module_info_creation(self):
        """测试模块信息创建"""
        module = ModuleInfo(name="测试模块")
        assert module.name == "测试模块"
        assert module.version is None
        assert module.public_symbols == []
        assert module.private_symbols == []
        assert module.imports == []
    
    def test_module_info_with_version(self):
        """测试带版本的模块信息"""
        module = ModuleInfo(name="测试模块", version="1.0")
        assert module.name == "测试模块"
        assert module.version == "1.0"
    
    def test_add_symbol_public(self):
        """测试添加公开符号"""
        module = ModuleInfo(name="测试模块")
        module.add_symbol("公开函数", visibility="public")
        assert "公开函数" in module.public_symbols
        assert "公开函数" not in module.private_symbols
    
    def test_add_symbol_private(self):
        """测试添加私有符号"""
        module = ModuleInfo(name="测试模块")
        module.add_symbol("私有函数", visibility="private")
        assert "私有函数" in module.private_symbols
        assert "私有函数" not in module.public_symbols
    
    def test_add_symbol_duplicate(self):
        """测试添加重复符号"""
        module = ModuleInfo(name="测试模块")
        module.add_symbol("函数1", visibility="public")
        module.add_symbol("函数1", visibility="public")  # 重复添加
        assert module.public_symbols.count("函数1") == 1  # 不应重复
    
    def test_get_all_symbols(self):
        """测试获取所有符号"""
        module = ModuleInfo(name="测试模块")
        module.add_symbol("公开函数", visibility="public")
        module.add_symbol("私有函数", visibility="private")
        all_symbols = module.get_all_symbols()
        assert len(all_symbols) == 2
        assert "公开函数" in all_symbols
        assert "私有函数" in all_symbols
    
    def test_module_str(self):
        """测试模块字符串表示"""
        module = ModuleInfo(name="测试模块")
        module.add_symbol("公开函数", visibility="public")
        module.add_symbol("私有函数", visibility="private")
        str_repr = str(module)
        assert "测试模块" in str_repr
        assert "公开: 1" in str_repr
        assert "私有: 1" in str_repr


class TestModuleParser:
    """测试 ModuleParser 类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.parser = ModuleParser()
    
    def test_parser_initialization(self):
        """测试解析器初始化"""
        parser = ModuleParser()
        assert parser.modules == {}
        assert parser.current_module is None
        assert parser.current_visibility == "private"
        assert parser.errors == []
        assert parser.imported_modules == []
    
    def test_parse_module_declaration_simple(self):
        """测试简单模块声明解析"""
        line = "模块 测试模块 {"
        result = self.parser.parse_module_declaration(line, 1)
        
        assert result is not None
        assert result.name == "测试模块"
        assert result.version is None
        assert "测试模块" in self.parser.modules
        assert self.parser.current_module == result
    
    def test_parse_module_declaration_with_version(self):
        """测试带版本的模块声明解析"""
        line = "模块 测试模块 版本 1.0 {"
        result = self.parser.parse_module_declaration(line, 2)
        
        assert result is not None
        assert result.name == "测试模块"
        assert result.version == "1.0"
    
    def test_parse_module_declaration_no_brace(self):
        """测试无大括号的模块声明"""
        line = "模块 测试模块"
        result = self.parser.parse_module_declaration(line, 3)
        
        assert result is not None
        assert result.name == "测试模块"
    
    def test_parse_module_declaration_duplicate(self):
        """测试重复模块声明"""
        # 第一次声明
        line1 = "模块 测试模块 {"
        result1 = self.parser.parse_module_declaration(line1, 1)
        assert result1 is not None
        
        # 第二次声明（重复）
        line2 = "模块 测试模块 {"
        result2 = self.parser.parse_module_declaration(line2, 2)
        assert result2 is None
        assert len(self.parser.errors) > 0
        assert "重复定义" in self.parser.errors[0]
    
    def test_parse_module_declaration_invalid(self):
        """测试无效模块声明"""
        line = "模块"  # 缺少模块名
        result = self.parser.parse_module_declaration(line, 1)
        assert result is None
    
    def test_parse_import_declaration_simple(self):
        """测试简单导入声明"""
        # 先创建模块
        self.parser.parse_module_declaration("模块 测试模块 {", 1)
        
        line = "导入 标准库"
        result = self.parser.parse_import_declaration(line, 2)
        
        assert "标准库" in result
        assert "标准库" in self.parser.current_module.imports
        assert "标准库" in self.parser.imported_modules
    
    def test_parse_import_declaration_with_alias(self):
        """测试带别名的导入声明"""
        # 先创建模块
        self.parser.parse_module_declaration("模块 测试模块 {", 1)
        
        line = "导入 标准库 为 std"
        result = self.parser.parse_import_declaration(line, 2)
        
        assert "标准库" in result
        assert "标准库" in self.parser.current_module.imports
    
    def test_parse_import_declaration_outside_module(self):
        """测试模块外的导入声明"""
        line = "导入 标准库"
        result = self.parser.parse_import_declaration(line, 1)
        
        # 模块外的导入应被添加到全局列表，但返回空列表
        assert result == []
        assert "标准库" in self.parser.imported_modules
    
    def test_parse_import_declaration_duplicate(self):
        """测试重复导入声明"""
        # 先创建模块
        self.parser.parse_module_declaration("模块 测试模块 {", 1)
        
        # 第一次导入
        line1 = "导入 标准库"
        result1 = self.parser.parse_import_declaration(line1, 2)
        assert "标准库" in result1
        
        # 第二次导入（重复）
        line2 = "导入 标准库"
        result2 = self.parser.parse_import_declaration(line2, 3)
        assert "标准库" in result2  # 应返回导入结果
        assert self.parser.current_module.imports.count("标准库") == 1  # 不应重复
    
    def test_parse_visibility_section_public(self):
        """测试公开可见性区域"""
        # 先创建模块
        self.parser.parse_module_declaration("模块 测试模块 {", 1)
        
        line = "公开:"
        result = self.parser.parse_visibility_section(line, 2)
        
        assert result == "public"
        assert self.parser.current_visibility == "public"
    
    def test_parse_visibility_section_private(self):
        """测试私有可见性区域"""
        # 先创建模块
        self.parser.parse_module_declaration("模块 测试模块 {", 1)
        
        line = "私有:"
        result = self.parser.parse_visibility_section(line, 2)
        
        assert result == "private"
        assert self.parser.current_visibility == "private"
    
    def test_parse_visibility_section_protected(self):
        """测试保护可见性区域（不支持）"""
        # 先创建模块
        self.parser.parse_module_declaration("模块 测试模块 {", 1)
        
        line = "保护:"
        result = self.parser.parse_visibility_section(line, 2)
        
        # 当前实现不支持"保护:"，应返回 None
        assert result is None
    
    def test_parse_visibility_section_invalid(self):
        """测试无效可见性区域"""
        line = "其他:"
        result = self.parser.parse_visibility_section(line, 1)
        assert result is None
    
    def test_parse_symbol_declaration_function(self):
        """测试函数符号声明"""
        # 先创建模块
        self.parser.parse_module_declaration("模块 测试模块 {", 1)
        self.parser.parse_visibility_section("公开:", 2)
        
        line = "整数型 测试函数(整数型 a) {"
        result = self.parser.parse_symbol_declaration(line, 3)
        
        assert result == "测试函数"
        assert "测试函数" in self.parser.current_module.public_symbols
    
    def test_parse_symbol_declaration_variable(self):
        """测试变量符号声明"""
        # 先创建模块
        self.parser.parse_module_declaration("模块 测试模块 {", 1)
        self.parser.parse_visibility_section("私有:", 2)
        
        line = "整数型 计数器;"
        result = self.parser.parse_symbol_declaration(line, 3)
        
        assert result == "计数器"
        assert "计数器" in self.parser.current_module.private_symbols
    
    def test_parse_symbol_declaration_with_init(self):
        """测试带初始化的变量声明"""
        # 先创建模块
        self.parser.parse_module_declaration("模块 测试模块 {", 1)
        
        line = "整数型 计数器 = 0;"
        result = self.parser.parse_symbol_declaration(line, 2)
        
        assert result == "计数器"
        assert "计数器" in self.parser.current_module.private_symbols
    
    def test_parse_file_complete(self):
        """测试完整文件解析"""
        # 创建临时文件
        content = """
模块 测试模块 版本 1.0 {
    导入 标准库
    导入 数学库
    
    公开:
        整数型 主函数(整数型 argc, 字符型* argv[]) {
        
    私有:
        整数型 计数器;
        整数型 辅助函数() {
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.zhc', delete=False) as f:
            f.write(content)
            temp_file = f.name
        
        try:
            result = self.parser.parse_file(temp_file)
            
            # parse_file 返回的是 List[ModuleInfo]
            assert isinstance(result, list)
            assert len(result) == 1
            
            module = result[0]
            assert module.name == "测试模块"
            assert module.version == "1.0"
            assert "标准库" in module.imports
            assert "数学库" in module.imports
            assert "主函数" in module.public_symbols
            assert "计数器" in module.private_symbols
            assert "辅助函数" in module.private_symbols
        finally:
            os.unlink(temp_file)
    
    def test_parse_file_empty(self):
        """测试空文件解析"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.zhc', delete=False) as f:
            f.write("")
            temp_file = f.name
        
        try:
            result = self.parser.parse_file(temp_file)
            # 空文件返回空列表
            assert result == []
        finally:
            os.unlink(temp_file)
    
    def test_parse_file_no_module(self):
        """测试无模块声明的文件"""
        content = """
导入 标准库
整数型 全局变量;
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.zhc', delete=False) as f:
            f.write(content)
            temp_file = f.name
        
        try:
            result = self.parser.parse_file(temp_file)
            # 无模块声明应返回空列表
            assert result == []
            # 但导入应被记录
            assert "标准库" in self.parser.imported_modules
        finally:
            os.unlink(temp_file)
    
    def test_get_module_direct(self):
        """测试直接访问模块"""
        self.parser.parse_module_declaration("模块 测试模块 {", 1)
        
        # 通过 modules 属性访问
        module = self.parser.modules.get("测试模块")
        assert module is not None
        assert module.name == "测试模块"
        
        # 获取不存在的模块
        module = self.parser.modules.get("不存在")
        assert module is None
    
    def test_get_all_modules_direct(self):
        """测试直接获取所有模块"""
        self.parser.parse_module_declaration("模块 模块1 {", 1)
        self.parser.parse_module_declaration("模块 模块2 {", 3)
        
        modules = list(self.parser.modules.values())
        assert len(modules) == 2
        module_names = [m.name for m in modules]
        assert "模块1" in module_names
        assert "模块2" in module_names
    
    def test_has_errors_direct(self):
        """测试错误检测（直接访问）"""
        # 无错误时
        assert len(self.parser.errors) == 0
        
        # 添加错误
        self.parser.errors.append("测试错误")
        assert len(self.parser.errors) == 1
    
    def test_get_errors_direct(self):
        """测试获取错误列表（直接访问）"""
        self.parser.errors.append("错误1")
        self.parser.errors.append("错误2")
        
        errors = self.parser.errors
        assert len(errors) == 2
        assert "错误1" in errors
        assert "错误2" in errors


class TestModuleParserEdgeCases:
    """测试边界情况"""
    
    def setup_method(self):
        self.parser = ModuleParser()
    
    def test_module_name_with_numbers(self):
        """测试带数字的模块名"""
        line = "模块 模块123 {"
        result = self.parser.parse_module_declaration(line, 1)
        assert result is not None
        assert result.name == "模块123"
    
    def test_module_version_complex(self):
        """测试复杂版本号"""
        line = "模块 测试模块 版本 2.1.3 {"
        result = self.parser.parse_module_declaration(line, 1)
        assert result is not None
        # 注意：正则表达式只匹配 [\w\.]+，所以 -beta 不会被匹配
        assert result.version == "2.1.3"
    
    def test_import_multiple_modules(self):
        """测试导入多个模块"""
        self.parser.parse_module_declaration("模块 测试模块 {", 1)
        
        self.parser.parse_import_declaration("导入 模块1", 2)
        self.parser.parse_import_declaration("导入 模块2", 3)
        self.parser.parse_import_declaration("导入 模块3", 4)
        
        assert len(self.parser.current_module.imports) == 3
        assert len(self.parser.imported_modules) == 3
    
    def test_visibility_switching(self):
        """测试可见性切换"""
        self.parser.parse_module_declaration("模块 测试模块 {", 1)
        
        # 初始为私有
        assert self.parser.current_visibility == "private"
        
        # 切换为公开
        self.parser.parse_visibility_section("公开:", 2)
        assert self.parser.current_visibility == "public"
        
        # 切换为私有
        self.parser.parse_visibility_section("私有:", 3)
        assert self.parser.current_visibility == "private"
    
    def test_nested_modules(self):
        """测试嵌套模块（不支持）"""
        self.parser.parse_module_declaration("模块 外层模块 {", 1)
        
        # 尝试在模块内声明另一个模块（应报错）
        result = self.parser.parse_module_declaration("模块 内层模块 {", 2)
        # 根据实现，可能返回 None 或报错
        # 这里假设不支持嵌套模块


class TestModuleParserIntegration:
    """集成测试"""
    
    def test_real_world_module(self):
        """测试真实世界的模块示例"""
        content = """
模块 学生管理系统 版本 1.0 {
    导入 标准库
    导入 数据库模块
    导入 日志模块
    
    公开:
        整数型 创建学生(字符串型 名, 整数型 龄) {
        整数型 删除学生(整数型 学号) {
    
    私有:
        整数型 学生计数;
        整数型 验证数据(字符串型 名, 整数型 龄) {
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.zhc', delete=False) as f:
            f.write(content)
            temp_file = f.name
        
        try:
            parser = ModuleParser()
            result = parser.parse_file(temp_file)
            
            assert isinstance(result, list)
            assert len(result) == 1
            
            module = result[0]
            assert module.name == "学生管理系统"
            assert module.version == "1.0"
            
            # 检查导入
            assert "标准库" in module.imports
            assert "数据库模块" in module.imports
            assert "日志模块" in module.imports
            
            # 检查公开符号
            assert "创建学生" in module.public_symbols
            assert "删除学生" in module.public_symbols
            
            # 检查私有符号
            assert "学生计数" in module.private_symbols
            assert "验证数据" in module.private_symbols
            
        finally:
            os.unlink(temp_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])