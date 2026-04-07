"""
语音支持模块
Voice Support Module

提供语音识别、命令解析和语音反馈功能
"""

from .speech_recognizer import SpeechRecognizer, SpeechEngine
from .voice_command_parser import VoiceCommandParser, CommandIntent
from .voice_feedback import VoiceFeedback, TTSEngine

__all__ = [
    'SpeechRecognizer',
    'SpeechEngine',
    'VoiceCommandParser',
    'CommandIntent',
    'VoiceFeedback',
    'TTSEngine'
]