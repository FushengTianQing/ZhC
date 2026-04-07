"""
中文C语言包管理器测试套件
Package Manager Test Suite for ZHC Language

测试包的安装、发布、搜索等功能
"""

import unittest
import sys
import os
import tempfile
import shutil

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'zhpp'))

from package import (
    PackageManager,
    PackageInfo,
    PackageRegistry,
    PackageDependency,
    PackageType,
    PackageStatus,
    CommandMapper,
    AliasManager
)


class TestPackageDependency(unittest.TestCase):
    """测试包依赖"""
    
    def test_dependency_creation(self):
        """测试依赖创建"""
        dep = PackageDependency(
            name="标准库",
            version_range=">=1.0.0 <2.0.0"
        )
        self.assertEqual(dep.name, "标准库")
        self.assertEqual(dep.version_range, ">=1.0.0 <2.0.0")
        self.assertFalse(dep.optional)
    
    def test_optional_dependency(self):
        """测试可选依赖"""
        dep = PackageDependency(
            name="图形库",
            version_range=">=1.0.0",
            optional=True
        )
        self.assertTrue(dep.optional)
    
    def test_version_satisfied(self):
        """测试版本满足检查"""
        dep = PackageDependency(
            name="测试库",
            version_range=">=1.0.0 <2.0.0"
        )
        self.assertTrue(dep.version_satisfied("1.0.0"))
        self.assertTrue(dep.version_satisfied("1.5.0"))
        self.assertFalse(dep.version_satisfied("2.0.0"))
    
    def test_dependency_serialization(self):
        """测试依赖序列化"""
        dep = PackageDependency(
            name="网络库",
            version_range=">=1.0.0"
        )
        data = dep.to_dict()
        restored = PackageDependency.from_dict(data)
        self.assertEqual(restored.name, dep.name)
        self.assertEqual(restored.version_range, dep.version_range)


class TestPackageInfo(unittest.TestCase):
    """测试包信息"""
    
    def test_package_creation(self):
        """测试包创建"""
        pkg = PackageInfo(
            name="测试包",
            version="1.0.0",
            description="测试用包",
            author="测试作者",
            package_type=PackageType.LIBRARY
        )
        self.assertEqual(pkg.name, "测试包")
        self.assertEqual(pkg.version, "1.0.0")
        self.assertEqual(pkg.package_type, PackageType.LIBRARY)
    
    def test_package_with_dependencies(self):
        """测试带依赖的包"""
        pkg = PackageInfo(
            name="应用库",
            version="2.0.0",
            description="应用开发库",
            author="开发团队",
            package_type=PackageType.LIBRARY,
            dependencies=[
                PackageDependency(name="标准库", version_range=">=1.0.0"),
                PackageDependency(name="网络库", version_range=">=1.5.0", optional=True)
            ]
        )
        self.assertEqual(len(pkg.dependencies), 2)
        self.assertEqual(pkg.dependencies[0].name, "标准库")
        self.assertTrue(pkg.dependencies[1].optional)
    
    def test_package_serialization(self):
        """测试包序列化"""
        pkg = PackageInfo(
            name="序列化测试",
            version="1.0.0",
            description="测试序列化功能",
            author="测试者",
            package_type=PackageType.TOOL
        )
        
        # 转换为字典
        data = pkg.to_dict()
        self.assertEqual(data['name'], "序列化测试")
        self.assertEqual(data['package_type'], "工具")
        
        # 从字典恢复
        restored = PackageInfo.from_dict(data)
        self.assertEqual(restored.name, pkg.name)
        self.assertEqual(restored.package_type, PackageType.TOOL)
    
    def test_package_json_generation(self):
        """测试 package.json 生成"""
        pkg = PackageInfo(
            name="JSON包",
            version="1.0.0",
            description="测试JSON生成",
            author="作者",
            package_type=PackageType.LIBRARY
        )
        
        json_str = pkg.to_package_json()
        self.assertIn('"name": "JSON包"', json_str)
        self.assertIn('"version": "1.0.0"', json_str)


class TestPackageRegistry(unittest.TestCase):
    """测试包注册表"""
    
    def setUp(self):
        """设置测试环境"""
        self.registry = PackageRegistry()
    
    def test_register_package(self):
        """测试注册包"""
        pkg = PackageInfo(
            name="注册测试包",
            version="1.0.0",
            description="测试注册功能",
            author="测试者",
            package_type=PackageType.LIBRARY
        )
        
        success = self.registry.register_package(pkg)
        self.assertTrue(success)
        
        # 验证注册成功
        retrieved = self.registry.get_package("注册测试包")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "注册测试包")
    
    def test_get_nonexistent_package(self):
        """测试获取不存在的包"""
        pkg = self.registry.get_package("不存在的包")
        self.assertIsNone(pkg)
    
    def test_search_packages(self):
        """测试搜索包"""
        # 注册测试包
        pkg1 = PackageInfo(
            name="网络通信库",
            version="1.0.0",
            description="提供网络通信功能",
            author="网络团队",
            package_type=PackageType.LIBRARY,
            keywords=["网络", "通信"]
        )
        
        pkg2 = PackageInfo(
            name="文件处理库",
            version="1.0.0",
            description="提供文件操作功能",
            author="文件团队",
            package_type=PackageType.LIBRARY,
            keywords=["文件", "IO"]
        )
        
        self.registry.register_package(pkg1)
        self.registry.register_package(pkg2)
        
        # 搜索关键词
        results = self.registry.search_packages("网络")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "网络通信库")


class TestPackageManager(unittest.TestCase):
    """测试包管理器"""
    
    def setUp(self):
        """设置测试环境"""
        # 使用临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.pm = PackageManager(install_dir=self.temp_dir)
        
        # 注册测试包
        self.test_pkg = PackageInfo(
            name="测试包",
            version="1.0.0",
            description="用于测试的包",
            author="测试团队",
            package_type=PackageType.LIBRARY,
            dependencies=[
                PackageDependency(name="依赖包", version_range=">=1.0.0")
            ]
        )
        
        self.dep_pkg = PackageInfo(
            name="依赖包",
            version="1.0.0",
            description="依赖测试包",
            author="依赖团队",
            package_type=PackageType.LIBRARY
        )
        
        self.pm.registry.register_package(self.test_pkg)
        self.pm.registry.register_package(self.dep_pkg)
    
    def tearDown(self):
        """清理测试环境"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    # ===== T046: install 命令测试 =====
    
    def test_install_package(self):
        """测试安装包"""
        success, msg = self.pm.install("测试包")
        self.assertTrue(success)
        self.assertIn("安装成功", msg)
        self.assertIn("测试包", self.pm.installed_packages)
    
    def test_install_nonexistent_package(self):
        """测试安装不存在的包"""
        success, msg = self.pm.install("不存在的包")
        self.assertFalse(success)
        self.assertIn("不存在", msg)
    
    def test_install_with_dependencies(self):
        """测试安装带依赖的包"""
        success, msg = self.pm.install("测试包")
        self.assertTrue(success)
        
        # 检查依赖是否也被安装
        self.assertIn("依赖包", self.pm.installed_packages)
    
    def test_install_from_package_json(self):
        """测试从 package.json 安装"""
        # 创建测试 package.json
        pkg_json_path = os.path.join(self.temp_dir, "package.json")
        pkg_json_content = {
            "名称": "测试项目",
            "版本": "1.0.0",
            "依赖": [
                {"名称": "依赖包", "版本": "latest"}
            ]
        }
        
        import json
        with open(pkg_json_path, 'w', encoding='utf-8') as f:
            json.dump(pkg_json_content, f, ensure_ascii=False, indent=2)
        
        success, msg = self.pm.install_from_package_json(pkg_json_path)
        self.assertTrue(success)
    
    # ===== T047: publish 命令测试 =====
    
    def test_publish_package(self):
        """测试发布包"""
        # 创建测试包目录
        pkg_dir = os.path.join(self.temp_dir, "发布测试")
        os.makedirs(pkg_dir)
        
        # 创建 package.json（使用正确的字段名）
        pkg_json = {
            "name": "发布测试包",
            "version": "1.0.0",
            "description": "测试发布功能",
            "author": "测试团队",
            "package_type": "库"
        }
        
        import json
        with open(os.path.join(pkg_dir, "package.json"), 'w', encoding='utf-8') as f:
            json.dump(pkg_json, f, ensure_ascii=False, indent=2)
        
        # 发布包
        success, msg = self.pm.publish(pkg_dir)
        self.assertTrue(success)
        self.assertIn("发布成功", msg)
    
    def test_publish_without_package_json(self):
        """测试缺少 package.json 的发布"""
        pkg_dir = os.path.join(self.temp_dir, "无效包")
        os.makedirs(pkg_dir)
        
        success, msg = self.pm.publish(pkg_dir)
        self.assertFalse(success)
        self.assertIn("缺少 package.json", msg)
    
    def test_publish_missing_required_fields(self):
        """测试缺少必填字段的发布"""
        pkg_dir = os.path.join(self.temp_dir, "不完整包")
        os.makedirs(pkg_dir)
        
        # 缺少作者字段和package_type字段（使用正确的字段名）
        pkg_json = {
            "name": "不完整包",
            "version": "1.0.0",
            "description": "测试不完整包"
        }
        
        import json
        with open(os.path.join(pkg_dir, "package.json"), 'w', encoding='utf-8') as f:
            json.dump(pkg_json, f, ensure_ascii=False, indent=2)
        
        success, msg = self.pm.publish(pkg_dir)
        # 发布应该失败，因为缺少必要字段
        self.assertFalse(success)
    
    # ===== T048: search 命令测试 =====
    
    def test_search_packages(self):
        """测试搜索包"""
        # 安装测试包使其可被搜索
        self.pm.install("测试包")
        
        results = self.pm.search("测试")
        self.assertGreater(len(results), 0)
        self.assertTrue(any(pkg.name == "测试包" for pkg in results))
    
    def test_search_by_type(self):
        """测试按类型搜索"""
        # 安装库类型包
        self.pm.install("测试包")
        
        results = self.pm.search_by_type(PackageType.LIBRARY)
        self.assertGreater(len(results), 0)
        self.assertTrue(all(pkg.package_type == PackageType.LIBRARY for pkg in results))
    
    def test_search_by_author(self):
        """测试按作者搜索"""
        self.pm.install("测试包")
        
        results = self.pm.search_by_author("测试团队")
        self.assertGreater(len(results), 0)
        self.assertTrue(all(pkg.author == "测试团队" for pkg in results))
    
    # ===== 其他功能测试 =====
    
    def test_list_installed(self):
        """测试列出已安装包"""
        self.pm.install("测试包")
        
        installed = self.pm.list_installed()
        self.assertIn("测试包", installed)
    
    def test_uninstall_package(self):
        """测试卸载包"""
        self.pm.install("测试包")
        self.assertIn("测试包", self.pm.installed_packages)
        
        success, msg = self.pm.uninstall("测试包")
        self.assertTrue(success)
        self.assertNotIn("测试包", self.pm.installed_packages)
    
    def test_uninstall_nonexistent_package(self):
        """测试卸载不存在的包"""
        success, msg = self.pm.uninstall("未安装的包")
        self.assertFalse(success)
        self.assertIn("未安装", msg)
    
    def test_update_package(self):
        """测试更新包"""
        # 先安装
        self.pm.install("测试包")
        
        # 模拟新版本
        new_pkg = PackageInfo(
            name="测试包",
            version="2.0.0",
            description="更新后的包",
            author="测试团队",
            package_type=PackageType.LIBRARY
        )
        self.pm.registry.register_package(new_pkg)
        
        # 更新
        success, msg = self.pm.update("测试包")
        self.assertTrue(success)
    
    def test_get_package_info(self):
        """测试获取包信息"""
        info = self.pm.get_package_info("测试包")
        self.assertIsNotNone(info)
        self.assertEqual(info.name, "测试包")
    
    def test_verify_package(self):
        """测试验证包"""
        self.pm.install("测试包")
        
        success, msg = self.pm.verify_package("测试包")
        self.assertTrue(success)
        self.assertIn("验证通过", msg)


class TestPackageTypeAndStatus(unittest.TestCase):
    """测试包类型和状态枚举"""
    
    def test_package_types(self):
        """测试包类型"""
        self.assertEqual(PackageType.LIBRARY.value, "库")
        self.assertEqual(PackageType.TOOL.value, "工具")
        self.assertEqual(PackageType.EXAMPLE.value, "示例")
        self.assertEqual(PackageType.TEMPLATE.value, "模板")
    
    def test_package_status(self):
        """测试包状态"""
        self.assertEqual(PackageStatus.STABLE.value, "稳定版")
        self.assertEqual(PackageStatus.BETA.value, "测试版")
        self.assertEqual(PackageStatus.DEPRECATED.value, "已废弃")


class TestPackageManagerIntegration(unittest.TestCase):
    """测试包管理器集成"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.pm = PackageManager(install_dir=self.temp_dir)
    
    def tearDown(self):
        """清理测试环境"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_complete_workflow(self):
        """测试完整工作流"""
        # 1. 注册包
        pkg = PackageInfo(
            name="完整工作流测试",
            version="1.0.0",
            description="测试完整工作流",
            author="集成测试团队",
            package_type=PackageType.LIBRARY
        )
        self.pm.registry.register_package(pkg)
        
        # 2. 搜索包
        results = self.pm.search("完整工作流")
        self.assertEqual(len(results), 1)
        
        # 3. 安装包
        success, msg = self.pm.install("完整工作流测试")
        self.assertTrue(success)
        
        # 4. 列出已安装
        installed = self.pm.list_installed()
        self.assertIn("完整工作流测试", installed)
        
        # 5. 验证包
        success, msg = self.pm.verify_package("完整工作流测试")
        self.assertTrue(success)
        
        # 6. 卸载包
        success, msg = self.pm.uninstall("完整工作流测试")
        self.assertTrue(success)


class TestChineseCommands(unittest.TestCase):
    """测试中文命令支持"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.pm = PackageManager(install_dir=self.temp_dir)
    
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_command_mapper_to_english(self):
        """测试中文转英文命令"""
        self.assertEqual(CommandMapper.to_english("安装"), "install")
        self.assertEqual(CommandMapper.to_english("发布"), "publish")
        self.assertEqual(CommandMapper.to_english("搜索"), "search")
        self.assertEqual(CommandMapper.to_english("列表"), "list")
        self.assertEqual(CommandMapper.to_english("卸载"), "uninstall")
        self.assertEqual(CommandMapper.to_english("更新"), "update")
        self.assertEqual(CommandMapper.to_english("验证"), "verify")
    
    def test_command_mapper_to_chinese(self):
        """测试英文转中文命令"""
        self.assertEqual(CommandMapper.to_chinese("install"), "安装")
        self.assertEqual(CommandMapper.to_chinese("publish"), "发布")
        self.assertEqual(CommandMapper.to_chinese("search"), "搜索")
        self.assertEqual(CommandMapper.to_chinese("list"), "列表")
    
    def test_command_mapper_is_chinese(self):
        """测试中文命令判断"""
        self.assertTrue(CommandMapper.is_chinese_command("安装"))
        self.assertTrue(CommandMapper.is_chinese_command("发布"))
        self.assertFalse(CommandMapper.is_chinese_command("install"))
        self.assertFalse(CommandMapper.is_chinese_command("publish"))
    
    def test_execute_chinese_command_install(self):
        """测试执行中文安装命令"""
        success, msg = self.pm.execute("安装", "测试包")
        self.assertFalse(success)  # 包不存在
        self.assertIn("不存在", msg)
    
    def test_execute_english_command_install(self):
        """测试执行英文安装命令"""
        success, msg = self.pm.execute("install", "测试包")
        self.assertFalse(success)  # 包不存在
        self.assertIn("不存在", msg)
    
    def test_execute_unknown_command(self):
        """测试执行未知命令"""
        success, msg = self.pm.execute("未知命令")
        self.assertFalse(success)
        self.assertIn("未知命令", msg)
    
    def test_command_mapper_roundtrip(self):
        """测试命令双向转换"""
        commands = ["安装", "发布", "搜索", "列表", "卸载", "更新", "验证"]
        for cn_cmd in commands:
            en_cmd = CommandMapper.to_english(cn_cmd)
            cn_cmd_back = CommandMapper.to_chinese(en_cmd)
            self.assertEqual(cn_cmd, cn_cmd_back)


class TestAliasManager(unittest.TestCase):
    """测试别名管理器"""
    
    def setUp(self):
        """测试前准备"""
        # 使用临时配置文件
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_config.close()
        self.alias_manager = AliasManager(config_path=self.temp_config.name)
    
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.temp_config.name):
            os.unlink(self.temp_config.name)
    
    def test_short_aliases(self):
        """测试官方短别名"""
        self.assertEqual(self.alias_manager.resolve("i"), "install")
        self.assertEqual(self.alias_manager.resolve("pub"), "publish")
        self.assertEqual(self.alias_manager.resolve("s"), "search")
        self.assertEqual(self.alias_manager.resolve("ls"), "list")
        self.assertEqual(self.alias_manager.resolve("rm"), "uninstall")
        self.assertEqual(self.alias_manager.resolve("up"), "update")
    
    def test_resolve_non_alias(self):
        """测试解析非别名"""
        # 标准命令应该原样返回
        self.assertEqual(self.alias_manager.resolve("install"), "install")
        self.assertEqual(self.alias_manager.resolve("搜索"), "搜索")
        # 未知命令原样返回
        self.assertEqual(self.alias_manager.resolve("未知命令"), "未知命令")
    
    def test_register_custom_alias(self):
        """测试注册自定义别名"""
        # 注册自定义别名
        success, msg = self.alias_manager.register_alias("ins", "install")
        self.assertTrue(success)
        self.assertIn("注册成功", msg)
        
        # 验证别名生效
        self.assertEqual(self.alias_manager.resolve("ins"), "install")
    
    def test_register_invalid_alias(self):
        """测试注册无效别名"""
        # 空别名
        success, msg = self.alias_manager.register_alias("", "install")
        self.assertFalse(success)
        self.assertIn("不能为空", msg)
        
        # 与标准命令冲突
        success, msg = self.alias_manager.register_alias("安装", "install")
        self.assertFalse(success)
        self.assertIn("冲突", msg)
        
        # 无效命令
        success, msg = self.alias_manager.register_alias("test", "invalid_command")
        self.assertFalse(success)
        self.assertIn("不是有效命令", msg)
    
    def test_unregister_alias(self):
        """测试注销别名"""
        # 注册别名
        self.alias_manager.register_alias("temp", "install")
        
        # 注销别名
        success, msg = self.alias_manager.unregister_alias("temp")
        self.assertTrue(success)
        self.assertIn("已删除", msg)
        
        # 验证别名已失效
        self.assertEqual(self.alias_manager.resolve("temp"), "temp")
    
    def test_unregister_official_alias(self):
        """测试注销官方别名（应失败）"""
        success, msg = self.alias_manager.unregister_alias("i")
        self.assertFalse(success)
        self.assertIn("不能删除", msg)
    
    def test_list_aliases(self):
        """测试列出所有别名"""
        # 注册一些自定义别名
        self.alias_manager.register_alias("test1", "install")
        self.alias_manager.register_alias("test2", "search")
        
        # 列出所有别名
        all_aliases = self.alias_manager.list_aliases()
        
        # 检查官方别名存在
        self.assertIn("i", all_aliases)
        self.assertIn("pub", all_aliases)
        
        # 检查自定义别名存在
        self.assertIn("test1", all_aliases)
        self.assertIn("test2", all_aliases)
    
    def test_get_alias_info(self):
        """测试获取别名信息"""
        # 官方别名
        info = self.alias_manager.get_alias_info("i")
        self.assertIsNotNone(info)
        self.assertEqual(info['alias'], "i")
        self.assertEqual(info['command'], "install")
        self.assertEqual(info['type'], "官方别名")
        
        # 自定义别名
        self.alias_manager.register_alias("myalias", "install")
        info = self.alias_manager.get_alias_info("myalias")
        self.assertIsNotNone(info)
        self.assertEqual(info['type'], "自定义别名")
        
        # 不存在的别名
        info = self.alias_manager.get_alias_info("nonexistent")
        self.assertIsNone(info)


class TestCommandMapperWithAlias(unittest.TestCase):
    """测试带别名支持的命令映射器"""
    
    def test_normalize_with_short_alias(self):
        """测试规范化短别名"""
        # 短别名应转换为标准命令
        self.assertEqual(CommandMapper.normalize("i"), "install")
        self.assertEqual(CommandMapper.normalize("pub"), "publish")
        self.assertEqual(CommandMapper.normalize("s"), "search")
    
    def test_normalize_with_chinese_command(self):
        """测试规范化中文命令"""
        self.assertEqual(CommandMapper.normalize("安装"), "install")
        self.assertEqual(CommandMapper.normalize("发布"), "publish")
    
    def test_normalize_with_english_command(self):
        """测试规范化英文命令"""
        self.assertEqual(CommandMapper.normalize("install"), "install")
        self.assertEqual(CommandMapper.normalize("search"), "search")
    
    def test_normalize_with_custom_alias(self):
        """测试规范化自定义别名"""
        # 获取别名管理器并注册自定义别名
        alias_manager = CommandMapper.get_alias_manager()
        
        # 注册临时别名（测试用）
        test_alias = f"test_alias_{id(self)}"
        alias_manager.register_alias(test_alias, "install")
        
        # 测试解析
        result = CommandMapper.normalize(test_alias)
        self.assertEqual(result, "install")
        
        # 清理测试别名
        alias_manager.unregister_alias(test_alias)
    
    def test_is_alias(self):
        """测试别名判断"""
        # 短别名
        self.assertTrue(CommandMapper.is_alias("i"))
        self.assertTrue(CommandMapper.is_alias("pub"))
        
        # 标准命令不是别名
        self.assertFalse(CommandMapper.is_alias("install"))
        self.assertFalse(CommandMapper.is_alias("安装"))


class TestPackageManagerWithAlias(unittest.TestCase):
    """测试包管理器别名功能"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.pm = PackageManager(install_dir=self.temp_dir)
        
        # 注册测试包
        self.test_pkg = PackageInfo(
            name="别名测试包",
            version="1.0.0",
            description="测试别名功能",
            author="别名测试团队",
            package_type=PackageType.LIBRARY
        )
        self.pm.registry.register_package(self.test_pkg)
    
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_execute_with_short_alias(self):
        """测试使用短别名执行命令"""
        # 使用 "i" 别名执行安装
        success, msg = self.pm.execute("i", "别名测试包")
        self.assertTrue(success)
        self.assertIn("安装成功", msg)
    
    def test_execute_with_chinese_alias(self):
        """测试使用中文命令执行"""
        success, msg = self.pm.execute("安装", "别名测试包")
        self.assertTrue(success)
        self.assertIn("安装成功", msg)
    
    def test_mixed_commands(self):
        """测试混合使用别名"""
        # 使用不同形式的命令
        commands = ["安装", "install", "i"]
        
        for cmd in commands:
            # 每次都重新安装（测试各种形式）
            if "别名测试包" in self.pm.installed_packages:
                self.pm.uninstall("别名测试包")
            
            success, msg = self.pm.execute(cmd, "别名测试包")
            self.assertTrue(success, f"命令 {cmd} 执行失败")
            self.assertIn("别名测试包", self.pm.installed_packages)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestPackageDependency))
    suite.addTests(loader.loadTestsFromTestCase(TestPackageInfo))
    suite.addTests(loader.loadTestsFromTestCase(TestPackageRegistry))
    suite.addTests(loader.loadTestsFromTestCase(TestPackageManager))
    suite.addTests(loader.loadTestsFromTestCase(TestPackageTypeAndStatus))
    suite.addTests(loader.loadTestsFromTestCase(TestPackageManagerIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestChineseCommands))
    suite.addTests(loader.loadTestsFromTestCase(TestAliasManager))
    suite.addTests(loader.loadTestsFromTestCase(TestCommandMapperWithAlias))
    suite.addTests(loader.loadTestsFromTestCase(TestPackageManagerWithAlias))
    
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

