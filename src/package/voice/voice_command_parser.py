"""
语音命令解析器
Voice Command Parser

解析语音输入为包管理器命令
"""

import re
from typing import Optional, Dict, Tuple, List
from enum import Enum


class CommandIntent(Enum):
    """命令意图类型"""
    INSTALL = "install"
    PUBLISH = "publish"
    SEARCH = "search"
    LIST = "list"
    UNINSTALL = "uninstall"
    UPDATE = "update"
    VERIFY = "verify"
    INFO = "info"
    HELP = "help"
    UNKNOWN = "unknown"


class VoiceCommandParser:
    """
    语音命令解析器
    
    支持自然语言命令解析，提取命令和参数
    """
    
    # 命令关键词映射
    COMMAND_KEYWORDS = {
        # 安装命令
        'install': ['安装', '下载', '获取', 'install', 'add'],
        # 发布命令
        'publish': ['发布', 'publish', '发布包', '发布到'],
        # 搜索命令
        'search': ['搜索', '查找', '找', 'search', 'find'],
        # 列表命令（注意：列出要放在前面，避免被"安装"匹配）
        'list': ['列出', '显示', '查看', 'list', 'show'],
        # 卸载命令
        'uninstall': ['卸载', '删除', '移除', 'uninstall', 'remove', 'delete'],
        # 更新命令
        'update': ['更新', '升级', 'update', 'upgrade'],
        # 验证命令
        'verify': ['验证', '检查', 'verify', 'check'],
        # 信息命令
        'info': ['信息', '详情', 'info', 'detail'],
        # 帮助命令
        'help': ['帮助', '怎么用', 'help', 'usage'],
    }
    
    # 参数提取模式
    PARAM_PATTERNS = {
        # 包名模式（提取命令后的第一个词）
        'package_name': r'(?:安装|下载|获取|搜索|查找|找|卸载|删除|移除|更新|升级|验证|检查)\s*(.+?)(?:\s+版本|\s*$)',
        
        # 版本模式
        'version': r'(?:版本|version)?[:\s]*(\d+\.\d+\.\d+)',
        
        # 作者模式
        'author': r'(?:作者|author)[:\s]*([^\s]+)',
    }
    
    def __init__(self):
        """初始化语音命令解析器"""
        self.command_history = []
    
    def parse(self, text: str) -> Dict:
        """
        解析语音文本为命令
        
        Args:
            text: 语音识别文本
            
        Returns:
            解析结果字典，包含：
            - intent: 命令意图
            - command: 标准命令
            - args: 命令参数列表
            - kwargs: 命令关键字参数
            - confidence: 置信度
            - original_text: 原始文本
        """
        # 保存历史
        self.command_history.append({
            'text': text,
            'timestamp': self._get_timestamp()
        })
        
        # 清理文本
        text = text.strip()
        
        # 识别命令意图
        intent, command, confidence = self._recognize_intent(text)
        
        # 提取参数
        args, kwargs = self._extract_parameters(text, intent)
        
        return {
            'intent': intent.value,
            'command': command,
            'args': args,
            'kwargs': kwargs,
            'confidence': confidence,
            'original_text': text,
        }
    
    def _recognize_intent(self, text: str) -> Tuple[CommandIntent, str, float]:
        """
        识别命令意图
        
        Args:
            text: 输入文本
            
        Returns:
            (意图类型, 标准命令, 置信度)
        """
        text_lower = text.lower()
        
        # 收集所有匹配的关键词
        matched_commands = []
        for command, keywords in self.COMMAND_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # 记录匹配位置
                    pos = text_lower.find(keyword)
                    matched_commands.append((command, keyword, len(keyword), pos))
        
        # 如果没有匹配，返回未知
        if not matched_commands:
            return CommandIntent.UNKNOWN, '', 0.0
        
        # 优先级排序：
        # 1. 关键词长度（越长优先级越高）
        # 2. 出现位置（越靠前优先级越高）
        matched_commands.sort(key=lambda x: (-x[2], x[3]))
        
        # 返回最佳匹配
        command, keyword, _, _ = matched_commands[0]
        confidence = self._calculate_confidence(text, keyword)
        return CommandIntent(command), command, confidence
    
    def _calculate_confidence(self, text: str, keyword: str) -> float:
        """
        计算匹配置信度
        
        Args:
            text: 输入文本
            keyword: 匹配的关键词
            
        Returns:
            置信度 (0.0 - 1.0)
        """
        # 基础置信度
        base_confidence = 0.5
        
        # 关键词长度加权
        keyword_weight = len(keyword) / 10.0
        
        # 文本长度加权（越短置信度越高）
        text_weight = 1.0 - (len(text) / 100.0)
        
        # 计算最终置信度
        confidence = base_confidence + keyword_weight + text_weight
        
        # 限制在0.5-1.0之间
        return min(max(confidence, 0.5), 1.0)
    
    def _extract_parameters(self, text: str, intent: CommandIntent) -> Tuple[List, Dict]:
        """
        提取命令参数
        
        Args:
            text: 输入文本
            intent: 命令意图
            
        Returns:
            (位置参数列表, 关键字参数字典)
        """
        args = []
        kwargs = {}
        
        # 根据意图提取参数
        if intent == CommandIntent.INSTALL:
            # 提取包名（命令后的内容）
            package_match = re.search(self.PARAM_PATTERNS['package_name'], text)
            if package_match:
                args.append(package_match.group(1).strip())
            
            # 提取版本
            version_match = re.search(self.PARAM_PATTERNS['version'], text)
            if version_match:
                kwargs['version'] = version_match.group(1)
        
        elif intent == CommandIntent.SEARCH:
            # 提取搜索关键词
            package_match = re.search(self.PARAM_PATTERNS['package_name'], text)
            if package_match:
                args.append(package_match.group(1).strip())
        
        elif intent == CommandIntent.PUBLISH:
            # 提取包目录
            # 简化处理，取第一个参数作为目录
            words = text.split()
            for word in words[1:]:  # 跳过命令词
                if not any(kw in word for kw in ['发布', 'publish']):
                    args.append(word)
                    break
        
        elif intent == CommandIntent.UNINSTALL or intent == CommandIntent.UPDATE:
            # 提取包名
            package_match = re.search(self.PARAM_PATTERNS['package_name'], text)
            if package_match:
                args.append(package_match.group(1).strip())
        
        return args, kwargs
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def get_command_suggestions(self, text: str) -> List[Dict]:
        """
        获取命令建议（用于模糊匹配）
        
        Args:
            text: 输入文本
            
        Returns:
            建议列表，每个建议包含命令和置信度
        """
        suggestions = []
        
        for command, keywords in self.COMMAND_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text.lower():
                    confidence = self._calculate_confidence(text, keyword)
                    suggestions.append({
                        'command': command,
                        'keyword': keyword,
                        'confidence': confidence,
                    })
        
        # 按置信度排序
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        
        return suggestions[:5]  # 返回前5个建议
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """
        获取命令历史
        
        Args:
            limit: 返回数量限制
            
        Returns:
            历史记录列表
        """
        return self.command_history[-limit:]
    
    def clear_history(self):
        """清空命令历史"""
        self.command_history = []


# 测试代码
if __name__ == '__main__':
    # 创建解析器
    parser = VoiceCommandParser()
    
    # 测试解析
    test_texts = [
        "安装标准库",
        "搜索网络包",
        "列出已安装的包",
        "卸载测试库",
        "更新标准库到最新版本",
        "帮助",
    ]
    
    for text in test_texts:
        result = parser.parse(text)
        print(f"\n输入: {text}")
        print(f"命令: {result['command']}")
        print(f"参数: {result['args']}")
        print(f"置信度: {result['confidence']:.2f}")