"""
ZHC包管理器自动补全测试套件
Auto-completion Test Suite for ZHC Package Manager

测试Tab补全功能
"""

import unittest
import sys
import os
import tempfile

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from package.completion import ZHCCompleter, print_installation_guide


class TestZHCCompleter(unittest.TestCase):
    """测试ZHC补全器"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.completer = ZHCCompleter(install_dir=self.temp_dir)
    
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
    
    # ===== 测试命令补全 =====
    
    def test_get_all_commands(self):
        """测试获取所有命令"""
        commands = self.completer.get_all_commands()
        
        # 应该包含中文命令
        self.assertIn("安装", commands)
        self.assertIn("发布", commands)
        self.assertIn("搜索", commands)
        
        # 应该包含英文命令
        self.assertIn("install", commands)
        self.assertIn("publish", commands)
        self.assertIn("search", commands)
    
    def test_complete_command_chinese(self):
        """测试中文命令补全"""
        # 测试 "安"
        matches = self.completer.complete_command("安")
        self.assertIn("安装", matches)
        
        # 测试 "发"
        matches = self.completer.complete_command("发")
        self.assertIn("发布", matches)
        
        # 测试 "搜"
        matches = self.completer.complete_command("搜")
        self.assertIn("搜索", matches)
    
    def test_complete_command_english(self):
        """测试英文命令补全"""
        # 测试 "in"
        matches = self.completer.complete_command("in")
        self.assertIn("install", matches)
        self.assertIn("info", matches)
        self.assertIn("init", matches)
        
        # 测试 "pub"
        matches = self.completer.complete_command("pub")
        self.assertIn("publish", matches)
        
        # 测试 "se"
        matches = self.completer.complete_command("se")
        self.assertIn("search", matches)
    
    def test_complete_command_case_insensitive(self):
        """测试不区分大小写的命令补全"""
        # 大写
        matches = self.completer.complete_command("IN")
        self.assertIn("install", matches)
        
        # 混合
        matches = self.completer.complete_command("Install")
        self.assertIn("install", matches)
    
    def test_complete_command_empty(self):
        """测试空前缀补全"""
        matches = self.completer.complete_command("")
        # 应该返回所有命令
        self.assertGreater(len(matches), 0)
    
    # ===== 测试包名补全 =====
    
    def test_complete_package_empty(self):
        """测试空包名补全"""
        # 创建测试包目录
        os.makedirs(os.path.join(self.temp_dir, "标准库"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, "网络库"), exist_ok=True)
        
        matches = self.completer.complete_package("")
        self.assertIn("标准库", matches)
        self.assertIn("网络库", matches)
    
    def test_complete_package_prefix(self):
        """测试包名前缀补全"""
        # 创建测试包
        os.makedirs(os.path.join(self.temp_dir, "标准库"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, "网络库"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, "数学库"), exist_ok=True)
        
        # 测试 "标"
        matches = self.completer.complete_package("标")
        self.assertIn("标准库", matches)
        self.assertNotIn("网络库", matches)
        
        # 测试 "网"
        matches = self.completer.complete_package("网")
        self.assertIn("网络库", matches)
        self.assertNotIn("标准库", matches)
    
    def test_complete_package_no_match(self):
        """测试无匹配的包名补全"""
        matches = self.completer.complete_package("不存在的包名前缀")
        self.assertEqual(len(matches), 0)
    
    def test_complete_package_nonexistent_dir(self):
        """测试目录不存在时的包名补全"""
        completer = ZHCCompleter(install_dir="/不存在的目录")
        matches = completer.complete_package("")
        self.assertEqual(len(matches), 0)
    
    # ===== 测试关键词补全 =====
    
    def test_complete_keyword_basic(self):
        """测试基础关键词补全"""
        # 测试 "网"
        matches = self.completer.complete_keyword("网")
        self.assertIn("网络", matches)
        
        # 测试 "数"
        matches = self.completer.complete_keyword("数")
        self.assertIn("数学", matches)
        self.assertIn("数据库", matches)
    
    def test_complete_keyword_case_insensitive(self):
        """测试不区分大小写的关键词补全"""
        matches = self.completer.complete_keyword("HTTP")
        self.assertIn("HTTP", matches)
        
        matches = self.completer.complete_keyword("http")
        self.assertIn("HTTP", matches)
    
    def test_complete_keyword_english(self):
        """测试英文关键词补全"""
        matches = self.completer.complete_keyword("SQL")
        self.assertIn("SQL", matches)
        
        matches = self.completer.complete_keyword("UI")
        self.assertIn("UI", matches)
    
    # ===== 测试智能补全 =====
    
    def test_complete_install_command(self):
        """测试安装命令的智能补全"""
        # 创建测试包
        os.makedirs(os.path.join(self.temp_dir, "标准库"), exist_ok=True)
        
        # 模拟：zhc 安装 标
        matches = self.completer.complete("", "标", "安装")
        self.assertIn("标准库", matches)
    
    def test_complete_search_command(self):
        """测试搜索命令的智能补全"""
        # 模拟：zhc 搜索 网
        matches = self.completer.complete("", "网", "搜索")
        self.assertIn("网络", matches)
    
    def test_complete_first_word(self):
        """测试第一个词（命令本身）的补全"""
        # prev_word为None表示是第一个词
        matches = self.completer.complete("", "安", None)
        self.assertIn("安装", matches)
    
    # ===== 测试命令帮助 =====
    
    def test_get_command_help_chinese(self):
        """测试中文命令帮助"""
        help_text = self.completer.get_command_help("安装")
        self.assertIn("安装包及依赖", help_text)
        
        help_text = self.completer.get_command_help("发布")
        self.assertIn("发布", help_text)
    
    def test_get_command_help_english(self):
        """测试英文命令帮助"""
        help_text = self.completer.get_command_help("install")
        self.assertIn("安装", help_text)
    
    def test_get_command_help_unknown(self):
        """测试未知命令帮助"""
        help_text = self.completer.get_command_help("未知命令")
        self.assertIn("未知命令", help_text)
    
    # ===== 测试补全脚本生成 =====
    
    def test_install_bash_completion(self):
        """测试Bash补全脚本生成"""
        from package.completion import install_bash_completion
        script = install_bash_completion()
        
        self.assertIn("_zhc_complete", script)
        self.assertIn("complete -F", script)
        self.assertIn("zhc", script)
    
    def test_install_zsh_completion(self):
        """测试Zsh补全脚本生成"""
        from package.completion import install_zsh_completion
        script = install_zsh_completion()
        
        self.assertIn("_zhc()", script)
        self.assertIn("#compdef zhc", script)
        self.assertIn("_describe", script)
    
    def test_print_installation_guide(self):
        """测试安装指南打印"""
        # 只测试函数能否正常调用，不检查输出
        from package.completion import print_installation_guide
        import io
        import sys
        
        # 捕获标准输出
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        try:
            print_installation_guide()
            output = sys.stdout.getvalue()
            self.assertIn("安装指南", output)
            self.assertIn("Bash", output)
            self.assertIn("Zsh", output)
        finally:
            sys.stdout = old_stdout


class TestCompleterIntegration(unittest.TestCase):
    """测试补全器集成"""
    
    def test_completer_with_real_package_manager(self):
        """测试补全器与真实包管理器集成"""
        from package import PackageManager
        import tempfile
        import shutil
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 创建包管理器和补全器
            pm = PackageManager(install_dir=temp_dir)
            completer = ZHCCompleter(install_dir=temp_dir)
            
            # 模拟安装包（创建目录）
            os.makedirs(os.path.join(temp_dir, "测试包"), exist_ok=True)
            
            # 测试补全
            matches = completer.complete_package("测")
            self.assertIn("测试包", matches)
        finally:
            shutil.rmtree(temp_dir)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestZHCCompleter))
    suite.addTests(loader.loadTestsFromTestCase(TestCompleterIntegration))
    
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
    print("=" * 60)
    print("📊 ZHC包管理器自动补全测试套件")
    print("=" * 60)
    print()
    
    # 运行测试
    success = run_tests()
    sys.exit(0 if success else 1)