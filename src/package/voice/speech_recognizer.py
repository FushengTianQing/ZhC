"""
语音识别器
Speech Recognizer

支持多种语音识别引擎（在线/离线）
"""

import os
import json
import tempfile
from typing import Optional, Dict, Tuple
from enum import Enum
from datetime import datetime


class SpeechEngine(Enum):
    """语音识别引擎类型"""
    ONLINE_API = "在线API"
    LOCAL_WHISPER = "本地Whisper"
    LOCAL_VOSK = "本地Vosk"
    PATTERN = "规则匹配"


class SpeechRecognizer:
    """
    语音识别器
    
    支持多级降级策略：
    1. 在线API（百度/讯飞/腾讯云等）
    2. 本地Whisper模型（OpenAI）
    3. 本地Vosk模型（离线）
    4. 规则匹配（兜底）
    """
    
    # 预定义的语音命令模式（规则匹配用）
    VOICE_PATTERNS = {
        # 安装命令
        r"安装.*包": "install",
        r"安装(.+)": "install",
        r"下载.*": "install",
        r"获取.*": "install",
        
        # 搜索命令
        r"搜索.*": "search",
        r"查找.*": "search",
        r"找.*": "search",
        
        # 列表命令
        r"列出.*": "list",
        r"显示.*": "list",
        r"查看.*": "list",
        
        # 卸载命令
        r"卸载.*": "uninstall",
        r"删除.*": "uninstall",
        r"移除.*": "uninstall",
        
        # 更新命令
        r"更新.*": "update",
        r"升级.*": "update",
        
        # 发布命令
        r"发布.*": "publish",
        
        # 验证命令
        r"验证.*": "verify",
        r"检查.*": "verify",
        
        # 帮助命令
        r"帮助": "help",
        r"帮助.*": "help",
        r"怎么用": "help",
        r"使用.*帮助": "help",
    }
    
    def __init__(self, 
                 engine: SpeechEngine = SpeechEngine.PATTERN,
                 api_key: Optional[str] = None,
                 model_path: Optional[str] = None):
        """
        初始化语音识别器
        
        Args:
            engine: 识别引擎类型
            api_key: 在线API密钥（可选）
            model_path: 本地模型路径（可选）
        """
        self.engine = engine
        self.api_key = api_key
        self.model_path = model_path
        self.is_listening = False
        
        # 统计信息
        self.stats = {
            'total_requests': 0,
            'successful_recognitions': 0,
            'failed_recognitions': 0,
            'avg_latency': 0.0,
        }
    
    def listen(self, timeout: int = 5) -> Tuple[bool, str]:
        """
        监听麦克风输入
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            (是否成功, 音频数据或错误消息)
        """
        try:
            # 尝试导入音频库
            try:
                import speech_recognition as sr
            except ImportError:
                return False, "❌ 未安装 speech_recognition 库\n安装命令: pip install SpeechRecognition"
            
            # 初始化识别器
            recognizer = sr.Recognizer()
            
            with sr.Microphone() as source:
                print("🎤 请说话...")
                self.is_listening = True
                
                # 调整环境噪音
                recognizer.adjust_for_ambient_noise(source, duration=1)
                
                # 监听音频
                audio = recognizer.listen(source, timeout=timeout)
                self.is_listening = False
                
                # 保存音频到临时文件
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                    f.write(audio.get_wav_data())
                    temp_path = f.name
                
                return True, temp_path
                
        except Exception as e:
            self.is_listening = False
            return False, f"❌ 音频录制失败: {str(e)}"
    
    def recognize_from_file(self, audio_path: str) -> Tuple[bool, str]:
        """
        从音频文件识别文本
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            (是否成功, 识别文本或错误消息)
        """
        start_time = datetime.now()
        self.stats['total_requests'] += 1
        
        try:
            # 根据引擎类型选择识别方法
            if self.engine == SpeechEngine.ONLINE_API:
                success, result = self._recognize_online(audio_path)
            elif self.engine == SpeechEngine.LOCAL_WHISPER:
                success, result = self._recognize_whisper(audio_path)
            elif self.engine == SpeechEngine.LOCAL_VOSK:
                success, result = self._recognize_vosk(audio_path)
            else:
                success, result = self._recognize_pattern(audio_path)
            
            # 更新统计
            if success:
                self.stats['successful_recognitions'] += 1
            else:
                self.stats['failed_recognitions'] += 1
            
            # 计算延迟
            latency = (datetime.now() - start_time).total_seconds()
            self.stats['avg_latency'] = (
                (self.stats['avg_latency'] * (self.stats['total_requests'] - 1) + latency) 
                / self.stats['total_requests']
            )
            
            return success, result
            
        except Exception as e:
            self.stats['failed_recognitions'] += 1
            return False, f"❌ 识别失败: {str(e)}"
    
    def _recognize_online(self, audio_path: str) -> Tuple[bool, str]:
        """在线API识别（百度/讯飞等）"""
        # 检查API密钥
        if not self.api_key:
            # 降级到规则匹配
            return self._recognize_pattern(audio_path)
        
        try:
            # 这里可以集成百度语音API、讯飞语音API等
            # 示例：使用百度语音识别
            # from aip import AipSpeech
            # client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)
            # result = client.asr(audio_path, 'wav', 16000, {'dev_pid': 1537})
            
            # 模拟API调用
            return False, "⚠️  在线API未配置，使用规则匹配降级"
            
        except Exception as e:
            # 降级到规则匹配
            return self._recognize_pattern(audio_path)
    
    def _recognize_whisper(self, audio_path: str) -> Tuple[bool, str]:
        """本地Whisper模型识别"""
        try:
            import whisper
            
            # 加载模型（如果未加载）
            model = whisper.load_model("base")
            
            # 识别
            result = model.transcribe(audio_path, language="zh")
            text = result['text'].strip()
            
            return True, text
            
        except ImportError:
            return False, "❌ 未安装 whisper 库\n安装命令: pip install openai-whisper"
        except Exception as e:
            return False, f"❌ Whisper识别失败: {str(e)}"
    
    def _recognize_vosk(self, audio_path: str) -> Tuple[bool, str]:
        """本地Vosk模型识别"""
        try:
            from vosk import Model, KaldiRecognizer
            import wave
            
            # 检查模型路径
            if not self.model_path:
                self.model_path = os.path.expanduser("~/.zhc/models/vosk-model-cn")
            
            if not os.path.exists(self.model_path):
                return False, f"❌ Vosk模型不存在: {self.model_path}"
            
            # 加载模型
            model = Model(self.model_path)
            recognizer = KaldiRecognizer(model, 16000)
            
            # 读取音频文件
            wf = wave.open(audio_path, "rb")
            
            # 转换为16kHz单声道
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
                return False, "❌ 音频格式不支持（需要16kHz单声道PCM）"
            
            # 识别
            text_parts = []
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text_parts.append(result.get('text', ''))
            
            # 获取最后结果
            result = json.loads(recognizer.FinalResult())
            text_parts.append(result.get('text', ''))
            
            text = ''.join(text_parts).strip()
            
            return True, text if text else "（无语音内容）"
            
        except ImportError:
            return False, "❌ 未安装 vosk 库\n安装命令: pip install vosk"
        except Exception as e:
            return False, f"❌ Vosk识别失败: {str(e)}"
    
    def _recognize_pattern(self, audio_path: str) -> Tuple[bool, str]:
        """规则匹配（兜底方案）"""
        # 实际应用中可以结合简单的语音特征检测
        # 这里返回提示信息
        return True, "（规则匹配模式：请使用文本命令）"
    
    def listen_and_recognize(self, timeout: int = 5) -> Tuple[bool, str]:
        """
        监听麦克风并识别（一步完成）
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            (是否成功, 识别文本或错误消息)
        """
        # 监听
        success, result = self.listen(timeout)
        if not success:
            return False, result
        
        # 识别
        return self.recognize_from_file(result)
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total_requests': 0,
            'successful_recognitions': 0,
            'failed_recognitions': 0,
            'avg_latency': 0.0,
        }


# 测试代码
if __name__ == '__main__':
    # 创建语音识别器
    recognizer = SpeechRecognizer(engine=SpeechEngine.PATTERN)
    
    # 测试监听
    print("测试语音识别...")
    success, result = recognizer.listen_and_recognize()
    
    if success:
        print(f"✅ 识别结果: {result}")
    else:
        print(result)
    
    # 显示统计
    print(f"\n统计信息: {recognizer.get_stats()}")