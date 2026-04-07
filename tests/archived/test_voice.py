"""
语音支持测试套件
Voice Support Test Suite

测试语音识别、命令解析和语音反馈功能
"""

import unittest
import sys
import os

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from package.voice import (
    SpeechRecognizer,
    VoiceCommandParser,
    VoiceFeedback,
    SpeechEngine,
    TTSEngine,
    CommandIntent
)


class TestSpeechRecognizer(unittest.TestCase):
    """测试语音识别器"""
    
    def test_recognizer_creation(self):
        """测试识别器创建"""
        recognizer = SpeechRecognizer(engine=SpeechEngine.PATTERN)
        self.assertEqual(recognizer.engine, SpeechEngine.PATTERN)
        self.assertFalse(recognizer.is_listening)
    
    def test_pattern_recognition(self):
        """测试规则匹配识别"""
        recognizer = SpeechRecognizer(engine=SpeechEngine.PATTERN)
        
        # 模拟识别（规则匹配模式）
        success, result = recognizer.recognize_from_file("test.wav")
        self.assertTrue(success)
        self.assertIn("规则匹配", result)
    
    def test_statistics(self):
        """测试统计信息"""
        recognizer = SpeechRecognizer(engine=SpeechEngine.PATTERN)
        
        # 获取初始统计
        stats = recognizer.get_stats()
        self.assertEqual(stats['total_requests'], 0)
        self.assertEqual(stats['successful_recognitions'], 0)
        
        # 模拟一次识别
        recognizer.recognize_from_file("test.wav")
        
        # 检查统计更新
        stats = recognizer.get_stats()
        self.assertEqual(stats['total_requests'], 1)
        self.assertEqual(stats['successful_recognitions'], 1)
    
    def test_stats_reset(self):
        """测试统计重置"""
        recognizer = SpeechRecognizer(engine=SpeechEngine.PATTERN)
        
        # 模拟识别
        recognizer.recognize_from_file("test.wav")
        
        # 重置统计
        recognizer.reset_stats()
        stats = recognizer.get_stats()
        
        self.assertEqual(stats['total_requests'], 0)


class TestVoiceCommandParser(unittest.TestCase):
    """测试语音命令解析器"""
    
    def test_parser_creation(self):
        """测试解析器创建"""
        parser = VoiceCommandParser()
        self.assertEqual(len(parser.command_history), 0)
    
    def test_install_command_parsing(self):
        """测试安装命令解析"""
        parser = VoiceCommandParser()
        
        result = parser.parse("安装标准库")
        
        self.assertEqual(result['intent'], 'install')
        self.assertEqual(result['command'], 'install')
        self.assertIn('标准库', result['args'])
        self.assertGreater(result['confidence'], 0.5)
    
    def test_search_command_parsing(self):
        """测试搜索命令解析"""
        parser = VoiceCommandParser()
        
        result = parser.parse("搜索网络包")
        
        self.assertEqual(result['intent'], 'search')
        self.assertEqual(result['command'], 'search')
        self.assertGreater(result['confidence'], 0.5)
    
    def test_list_command_parsing(self):
        """测试列表命令解析"""
        parser = VoiceCommandParser()
        
        result = parser.parse("列出已安装的包")
        
        self.assertEqual(result['intent'], 'list')
        self.assertEqual(result['command'], 'list')
    
    def test_uninstall_command_parsing(self):
        """测试卸载命令解析"""
        parser = VoiceCommandParser()
        
        result = parser.parse("卸载测试库")
        
        self.assertEqual(result['intent'], 'uninstall')
        self.assertEqual(result['command'], 'uninstall')
    
    def test_help_command_parsing(self):
        """测试帮助命令解析"""
        parser = VoiceCommandParser()
        
        result = parser.parse("帮助")
        
        self.assertEqual(result['intent'], 'help')
        self.assertEqual(result['command'], 'help')
    
    def test_unknown_command_parsing(self):
        """测试未知命令解析"""
        parser = VoiceCommandParser()
        
        result = parser.parse("这是未知命令")
        
        self.assertEqual(result['intent'], 'unknown')
        self.assertEqual(result['command'], '')
        self.assertEqual(result['confidence'], 0.0)
    
    def test_version_extraction(self):
        """测试版本提取"""
        parser = VoiceCommandParser()
        
        result = parser.parse("安装标准库 版本 1.2.3")
        
        self.assertEqual(result['command'], 'install')
        self.assertIn('version', result['kwargs'])
        self.assertEqual(result['kwargs']['version'], '1.2.3')
    
    def test_command_suggestions(self):
        """测试命令建议"""
        parser = VoiceCommandParser()
        
        suggestions = parser.get_command_suggestions("安装")
        
        self.assertGreater(len(suggestions), 0)
        self.assertEqual(suggestions[0]['command'], 'install')
    
    def test_command_history(self):
        """测试命令历史"""
        parser = VoiceCommandParser()
        
        # 执行多个命令
        parser.parse("安装包1")
        parser.parse("搜索包2")
        parser.parse("列出包")
        
        # 获取历史
        history = parser.get_history(limit=3)
        
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0]['text'], "安装包1")
        
        # 清空历史
        parser.clear_history()
        self.assertEqual(len(parser.command_history), 0)


class TestVoiceFeedback(unittest.TestCase):
    """测试语音反馈系统"""
    
    def test_feedback_creation(self):
        """测试反馈系统创建"""
        feedback = VoiceFeedback(engine=TTSEngine.LOCAL_PYTTSX3)
        
        self.assertEqual(feedback.engine, TTSEngine.LOCAL_PYTTSX3)
        self.assertEqual(feedback.voice_rate, 200)
        self.assertEqual(feedback.voice_volume, 1.0)
    
    def test_predefined_messages(self):
        """测试预定义消息"""
        feedback = VoiceFeedback()
        
        # 检查预定义消息存在
        self.assertIn('install_success', feedback.FEEDBACK_MESSAGES)
        self.assertIn('install_failed', feedback.FEEDBACK_MESSAGES)
        self.assertIn('listening', feedback.FEEDBACK_MESSAGES)
    
    def test_feedback_stats(self):
        """测试反馈统计"""
        feedback = VoiceFeedback()
        
        # 获取初始统计
        stats = feedback.get_stats()
        self.assertEqual(stats['total_speeches'], 0)
        
        # 重置统计
        feedback.reset_stats()
        stats = feedback.get_stats()
        self.assertEqual(stats['total_speeches'], 0)


class TestPackageManagerWithVoice(unittest.TestCase):
    """测试包管理器的语音功能"""
    
    def test_voice_disabled(self):
        """测试语音功能禁用"""
        from package import PackageManager
        
        pm = PackageManager(enable_voice=False)
        
        # 尝试监听语音命令（应该失败）
        success, msg = pm.listen_voice_command()
        
        self.assertFalse(success)
        self.assertIn("未启用", msg)
    
    def test_voice_interact_disabled(self):
        """测试语音交互禁用"""
        from package import PackageManager
        
        pm = PackageManager(enable_voice=False)
        
        success, msg = pm.voice_interact()
        
        self.assertFalse(success)
        self.assertIn("未启用", msg)


class TestCommandIntegration(unittest.TestCase):
    """测试语音命令集成"""
    
    def test_full_command_flow(self):
        """测试完整命令流程"""
        parser = VoiceCommandParser()
        
        # 解析命令
        result = parser.parse("安装测试包")
        
        # 验证解析结果
        self.assertEqual(result['command'], 'install')
        self.assertIn('测试包', result['args'])
        
        # 模拟执行（实际项目中会调用PackageManager）
        command = result['command']
        args = result['args']
        
        self.assertEqual(command, 'install')
        self.assertEqual(args[0], '测试包')


def run_tests():
    """运行所有测试"""
    unittest.main(verbosity=2)


if __name__ == '__main__':
    run_tests()