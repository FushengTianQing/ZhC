"""
中文C语言字符串模板测试套件
String Template Test Suite for ZHC Language

测试模板解析、编译和执行功能
"""

import unittest
import sys
import os

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'zhpp'))

from template import TemplateEngine, TemplateVariable, TemplateBlock, TemplateBlockType


class TestTemplateVariable(unittest.TestCase):
    """测试模板变量"""
    
    def test_simple_variable(self):
        """测试简单变量"""
        var = TemplateVariable(name='名字', path=['名字'])
        self.assertEqual(var.name, '名字')
        self.assertEqual(var.path, ['名字'])
    
    def test_nested_variable(self):
        """测试嵌套变量"""
        var = TemplateVariable(name='用户.年龄', path=['用户', '年龄'])
        self.assertEqual(len(var.path), 2)
        self.assertEqual(var.path[0], '用户')
        self.assertEqual(var.path[1], '年龄')
    
    def test_variable_with_default(self):
        """测试带默认值的变量"""
        var = TemplateVariable(
            name='名字',
            path=['名字'],
            default_value='未知'
        )
        self.assertEqual(var.default_value, '未知')
    
    def test_variable_to_c_code(self):
        """测试变量生成C代码"""
        var = TemplateVariable(name='计数', path=['计数'])
        c_code = var.to_c_code()
        self.assertEqual(c_code, '计数')


class TestTemplateBlock(unittest.TestCase):
    """测试模板块"""
    
    def test_text_block(self):
        """测试文本块"""
        block = TemplateBlock(TemplateBlockType.TEXT, '你好世界')
        self.assertEqual(block.block_type, TemplateBlockType.TEXT)
        self.assertEqual(block.content, '你好世界')
    
    def test_variable_block(self):
        """测试变量块"""
        block = TemplateBlock(TemplateBlockType.VARIABLE, '用户名')
        self.assertEqual(block.block_type, TemplateBlockType.VARIABLE)
    
    def test_conditional_block(self):
        """测试条件块"""
        block = TemplateBlock(
            TemplateBlockType.CONDITIONAL,
            '',
            condition='年龄 >= 18'
        )
        self.assertEqual(block.block_type, TemplateBlockType.CONDITIONAL)
        self.assertEqual(block.condition, '年龄 >= 18')
    
    def test_loop_block(self):
        """测试循环块"""
        block = TemplateBlock(
            TemplateBlockType.LOOP,
            '',
            variable='项目',
            collection='项目列表'
        )
        self.assertEqual(block.block_type, TemplateBlockType.LOOP)
        self.assertEqual(block.variable, '项目')
        self.assertEqual(block.collection, '项目列表')


class TestTemplateEngine(unittest.TestCase):
    """测试模板引擎"""
    
    def setUp(self):
        """设置测试环境"""
        self.engine = TemplateEngine()
    
    def test_parse_simple_template(self):
        """测试解析简单模板"""
        template = '你好，{名字}！'
        blocks = self.engine.parse(template)
        self.assertGreater(len(blocks), 0)
    
    def test_parse_variable(self):
        """测试解析变量"""
        template = '{用户.名字}'
        blocks = self.engine.parse(template)
        
        # 应该只有一个变量块
        var_blocks = [b for b in blocks if b.block_type == TemplateBlockType.VARIABLE]
        self.assertEqual(len(var_blocks), 1)
    
    def test_parse_text_and_variable(self):
        """测试解析文本和变量混合"""
        template = '你好，{名字}！欢迎来到{城市}。'
        blocks = self.engine.parse(template)
        
        # 应该有文本块和变量块
        text_blocks = [b for b in blocks if b.block_type == TemplateBlockType.TEXT]
        var_blocks = [b for b in blocks if b.block_type == TemplateBlockType.VARIABLE]
        
        self.assertGreater(len(text_blocks), 0)
        self.assertEqual(len(var_blocks), 2)
    
    def test_render_simple(self):
        """测试简单渲染"""
        template = '你好，{名字}！'
        context = {'名字': '张三'}
        result = self.engine.render(template, context)
        self.assertEqual(result, '你好，张三！')
    
    def test_render_nested(self):
        """测试嵌套变量渲染"""
        template = '年龄：{用户.年龄}'
        context = {
            '用户': {
                '年龄': 25
            }
        }
        result = self.engine.render(template, context)
        self.assertEqual(result, '年龄：25')
    
    def test_render_with_default(self):
        """测试带默认值渲染"""
        template = '名字：{名字|未知}'
        context = {}
        result = self.engine.render(template, context)
        self.assertEqual(result, '名字：未知')
    
    def test_compile_template(self):
        """测试编译模板"""
        template = '你好，{名字}！'
        c_code = self.engine.compile(template, 'render_hello')
        
        # 检查生成的代码包含函数定义
        self.assertIn('字符串型 render_hello', c_code)
        self.assertIn('return result', c_code)
    
    def test_get_statistics(self):
        """测试获取统计信息"""
        template = '你好，{名字}！年龄：{年龄}'
        stats = self.engine.get_statistics(template)
        
        self.assertIn('总块数', stats)
        self.assertIn('变量块', stats)
        self.assertGreater(stats['总块数'], 0)


class TestTemplateComplex(unittest.TestCase):
    """测试复杂模板"""
    
    def setUp(self):
        """设置测试环境"""
        self.engine = TemplateEngine()
    
    def test_multiple_variables(self):
        """测试多变量模板"""
        template = '{名字}来自{城市}，今年{年龄}岁。'
        context = {
            '名字': '李四',
            '城市': '北京',
            '年龄': 30
        }
        result = self.engine.render(template, context)
        self.assertIn('李四', result)
        self.assertIn('北京', result)
        self.assertIn('30', result)
    
    def test_deep_nesting(self):
        """测试深层嵌套"""
        template = '{用户.资料.姓名.姓}'
        context = {
            '用户': {
                '资料': {
                    '姓名': {
                        '姓': '王'
                    }
                }
            }
        }
        result = self.engine.render(template, context)
        self.assertIn('王', result)
    
    def test_special_characters(self):
        """测试特殊字符"""
        template = '价格：{价格}元'
        context = {'价格': 99.99}
        result = self.engine.render(template, context)
        self.assertIn('99.99', result)


class TestTemplateErrorHandling(unittest.TestCase):
    """测试模板错误处理"""
    
    def setUp(self):
        """设置测试环境"""
        self.engine = TemplateEngine()
    
    def test_missing_variable(self):
        """测试缺失变量"""
        template = '名字：{名字}'
        context = {}
        result = self.engine.render(template, context)
        # 缺失变量应该替换为空字符串
        self.assertEqual(result, '名字：')
    
    def test_empty_template(self):
        """测试空模板"""
        template = ''
        blocks = self.engine.parse(template)
        self.assertEqual(len(blocks), 0)
    
    def test_no_variables(self):
        """测试无变量模板"""
        template = '这是一个纯文本模板'
        blocks = self.engine.parse(template)
        
        # 应该只有一个文本块
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].block_type, TemplateBlockType.TEXT)


class TestTemplatePerformance(unittest.TestCase):
    """测试模板性能"""
    
    def setUp(self):
        """设置测试环境"""
        self.engine = TemplateEngine()
    
    def test_large_template(self):
        """测试大型模板"""
        # 生成包含100个变量的模板
        variables = [f'{{变量{i}}}' for i in range(100)]
        template = ' '.join(variables)
        
        blocks = self.engine.parse(template)
        self.assertGreater(len(blocks), 0)
    
    def test_repeated_parsing(self):
        """测试重复解析"""
        template = '你好，{名字}！'
        
        # 多次解析同一模板
        for _ in range(10):
            blocks = self.engine.parse(template)
            self.assertGreater(len(blocks), 0)


class TestTemplateIntegration(unittest.TestCase):
    """测试模板集成"""
    
    def setUp(self):
        """设置测试环境"""
        self.engine = TemplateEngine()
    
    def test_complete_workflow(self):
        """测试完整工作流"""
        # 1. 定义模板
        template = '用户：{用户.名字}，年龄：{用户.年龄}'
        
        # 2. 解析模板
        blocks = self.engine.parse(template)
        self.assertGreater(len(blocks), 0)
        
        # 3. 获取统计
        stats = self.engine.get_statistics(template)
        self.assertIn('总块数', stats)
        
        # 4. 渲染模板
        context = {
            '用户': {
                '名字': '测试用户',
                '年龄': 25
            }
        }
        result = self.engine.render(template, context)
        self.assertIn('测试用户', result)
        self.assertIn('25', result)
        
        # 5. 编译模板
        c_code = self.engine.compile(template, 'render_user')
        self.assertIn('render_user', c_code)
    
    def test_template_with_chinese_identifiers(self):
        """测试中文标识符"""
        template = '{用户名}买了{商品名称}'
        context = {
            '用户名': '小明',
            '商品名称': '苹果'
        }
        result = self.engine.render(template, context)
        self.assertEqual(result, '小明买了苹果')


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestTemplateVariable))
    suite.addTests(loader.loadTestsFromTestCase(TestTemplateBlock))
    suite.addTests(loader.loadTestsFromTestCase(TestTemplateEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestTemplateComplex))
    suite.addTests(loader.loadTestsFromTestCase(TestTemplateErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestTemplatePerformance))
    suite.addTests(loader.loadTestsFromTestCase(TestTemplateIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 打印总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    print(f"✅ 通过: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ 失败: {len(result.failures)}")
    print(f"⚠️  错误: {len(result.errors)}")
    print(f"📋 总计: {result.testsRun}")
    print("=" * 60)
    
    if result.wasSuccessful():
        print("🎉 所有测试通过！")
    else:
        print("⚠️  部分测试失败")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)