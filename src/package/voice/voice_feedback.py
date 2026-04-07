"""
语音反馈模块
Voice Feedback Module

提供语音合成和反馈功能
"""

import os
import tempfile
from typing import Optional, Dict, Tuple
from enum import Enum
from datetime import datetime


class TTSEngine(Enum):
    """语音合成引擎类型"""
    ONLINE_API = "在线API"
    LOCAL_PYTTSX3 = "本地pyttsx3"
    LOCAL_ESPEAK = "本地eSpeak"
    SYSTEM = "系统TTS"


class VoiceFeedback:
    """
    语音反馈系统
    
    支持多种语音合成引擎
    """
    
    # 预定义的反馈消息
    FEEDBACK_MESSAGES = {
        # 成功消息
        'install_success': "包安装成功",
        'publish_success': "包发布成功",
        'search_success': "搜索完成，找到 {count} 个包",
        'uninstall_success': "包卸载成功",
        'update_success': "包更新成功",
        'verify_success': "包验证通过",
        
        # 错误消息
        'install_failed': "包安装失败，{reason}",
        'publish_failed': "包发布失败，{reason}",
        'search_failed': "搜索失败，{reason}",
        'uninstall_failed': "包卸载失败，{reason}",
        'update_failed': "包更新失败，{reason}",
        'verify_failed': "包验证失败，{reason}",
        
        # 提示消息
        'listening': "请说话",
        'processing': "正在处理",
        'command_not_recognized': "命令未识别，请重试",
        'waiting_input': "等待输入",
    }
    
    def __init__(self, 
                 engine: TTSEngine = TTSEngine.LOCAL_PYTTSX3,
                 voice_rate: int = 200,
                 voice_volume: float = 1.0,
                 language: str = "zh"):
        """
        初始化语音反馈系统
        
        Args:
            engine: 语音合成引擎
            voice_rate: 语速（默认200）
            voice_volume: 音量（0.0-1.0）
            language: 语言（zh/en）
        """
        self.engine = engine
        self.voice_rate = voice_rate
        self.voice_volume = voice_volume
        self.language = language
        
        # 统计信息
        self.stats = {
            'total_speeches': 0,
            'successful_speeches': 0,
            'failed_speeches': 0,
            'total_duration': 0.0,
        }
        
        # TTS引擎实例（懒加载）
        self._tts_engine = None
    
    def speak(self, text: str, blocking: bool = True) -> Tuple[bool, str]:
        """
        朗读文本
        
        Args:
            text: 要朗读的文本
            blocking: 是否阻塞等待朗读完成
            
        Returns:
            (是否成功, 消息)
        """
        start_time = datetime.now()
        self.stats['total_speeches'] += 1
        
        try:
            # 根据引擎选择合成方法
            if self.engine == TTSEngine.ONLINE_API:
                success, result = self._speak_online(text)
            elif self.engine == TTSEngine.LOCAL_PYTTSX3:
                success, result = self._speak_pyttsx3(text, blocking)
            elif self.engine == TTSEngine.LOCAL_ESPEAK:
                success, result = self._speak_espeak(text)
            else:
                success, result = self._speak_system(text)
            
            # 更新统计
            if success:
                self.stats['successful_speeches'] += 1
                duration = (datetime.now() - start_time).total_seconds()
                self.stats['total_duration'] += duration
            else:
                self.stats['failed_speeches'] += 1
            
            return success, result
            
        except Exception as e:
            self.stats['failed_speeches'] += 1
            return False, f"❌ 语音合成失败: {str(e)}"
    
    def _speak_online(self, text: str) -> Tuple[bool, str]:
        """在线API语音合成（百度/讯飞等）"""
        # 检查API配置
        # 这里可以集成百度语音API、讯飞语音API等
        
        # 模拟API调用
        return True, "✅ 在线API语音合成成功（模拟）"
    
    def _speak_pyttsx3(self, text: str, blocking: bool = True) -> Tuple[bool, str]:
        """本地pyttsx3语音合成"""
        try:
            import pyttsx3
            
            # 懒加载TTS引擎
            if self._tts_engine is None:
                self._tts_engine = pyttsx3.init()
                
                # 设置语音属性
                self._tts_engine.setProperty('rate', self.voice_rate)
                self._tts_engine.setProperty('volume', self.voice_volume)
                
                # 尝试设置中文语音
                voices = self._tts_engine.getProperty('voices')
                for voice in voices:
                    if 'zh' in voice.id.lower() or 'chinese' in voice.name.lower():
                        self._tts_engine.setProperty('voice', voice.id)
                        break
            
            # 朗读文本
            self._tts_engine.say(text)
            
            if blocking:
                self._tts_engine.runAndWait()
            
            return True, f"✅ 语音合成成功: {text[:50]}"
            
        except ImportError:
            return False, "❌ 未安装 pyttsx3 库\n安装命令: pip install pyttsx3"
        except Exception as e:
            return False, f"❌ pyttsx3合成失败: {str(e)}"
    
    def _speak_espeak(self, text: str) -> Tuple[bool, str]:
        """本地eSpeak语音合成"""
        try:
            import subprocess
            
            # 检查eSpeak是否可用
            result = subprocess.run(
                ['which', 'espeak'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return False, "❌ 未安装 espeak\n安装命令: brew install espeak (macOS)"
            
            # 合成语音
            subprocess.run(
                ['espeak', '-v', 'zh', '-s', str(self.voice_rate), text],
                capture_output=True,
                text=True
            )
            
            return True, f"✅ eSpeak语音合成成功: {text[:50]}"
            
        except Exception as e:
            return False, f"❌ eSpeak合成失败: {str(e)}"
    
    def _speak_system(self, text: str) -> Tuple[bool, str]:
        """系统TTS（macOS say命令）"""
        try:
            import subprocess
            import platform
            
            if platform.system() == 'Darwin':  # macOS
                # 使用say命令
                subprocess.run(
                    ['say', '-v', 'Ting-Ting', text],
                    capture_output=True,
                    text=True
                )
                return True, f"✅ 系统语音合成成功: {text[:50]}"
            
            elif platform.system() == 'Windows':
                # Windows使用PowerShell
                import win32com.client
                speaker = win32com.client.Dispatch("SAPI.SpVoice")
                speaker.Speak(text)
                return True, f"✅ 系统语音合成成功: {text[:50]}"
            
            else:
                return False, "❌ 当前系统不支持系统TTS"
                
        except Exception as e:
            return False, f"❌ 系统TTS失败: {str(e)}"
    
    def speak_feedback(self, feedback_type: str, **kwargs) -> Tuple[bool, str]:
        """
        朗读预定义的反馈消息
        
        Args:
            feedback_type: 反馈类型（如 'install_success'）
            **kwargs: 消息参数
            
        Returns:
            (是否成功, 消息)
        """
        # 获取消息模板
        template = self.FEEDBACK_MESSAGES.get(feedback_type)
        if not template:
            return False, f"❌ 未知的反馈类型: {feedback_type}"
        
        # 格式化消息
        try:
            message = template.format(**kwargs)
        except KeyError as e:
            return False, f"❌ 消息参数缺失: {str(e)}"
        
        # 朗读消息
        return self.speak(message)
    
    def save_to_file(self, text: str, output_path: str) -> Tuple[bool, str]:
        """
        将语音保存到文件
        
        Args:
            text: 文本内容
            output_path: 输出文件路径（.wav）
            
        Returns:
            (是否成功, 消息)
        """
        try:
            import pyttsx3
            
            # 创建TTS引擎
            engine = pyttsx3.init()
            engine.setProperty('rate', self.voice_rate)
            engine.setProperty('volume', self.voice_volume)
            
            # 保存到文件
            engine.save_to_file(text, output_path)
            engine.runAndWait()
            
            return True, f"✅ 语音已保存: {output_path}"
            
        except ImportError:
            return False, "❌ 未安装 pyttsx3 库"
        except Exception as e:
            return False, f"❌ 保存失败: {str(e)}"
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = self.stats.copy()
        if stats['successful_speeches'] > 0:
            stats['avg_duration'] = stats['total_duration'] / stats['successful_speeches']
        else:
            stats['avg_duration'] = 0.0
        return stats
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total_speeches': 0,
            'successful_speeches': 0,
            'failed_speeches': 0,
            'total_duration': 0.0,
        }


# 测试代码
if __name__ == '__main__':
    # 创建语音反馈系统
    feedback = VoiceFeedback(engine=TTSEngine.LOCAL_PYTTSX3)
    
    # 测试朗读
    print("测试语音合成...")
    success, result = feedback.speak("测试语音合成")
    
    if success:
        print(result)
    else:
        print(result)
    
    # 测试预定义消息
    success, result = feedback.speak_feedback('install_success')
    print(result)
    
    # 显示统计
    print(f"\n统计信息: {feedback.get_stats()}")