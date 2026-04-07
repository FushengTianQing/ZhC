# -*- coding: utf-8 -*-
"""
错误处理工具函数

提供统一的错误处理和日志记录功能。

作者：远
日期：2026-04-07
"""

import sys
import traceback
from typing import Optional, Callable, Any, Dict
from functools import wraps


def safe_execute(
    func: Callable,
    *args,
    default_return: Any = None,
    log_errors: bool = True,
    **kwargs
) -> Any:
    """
    安全执行函数，捕获异常并返回默认值
    
    Args:
        func: 要执行的函数
        *args: 函数参数
        default_return: 异常时的默认返回值
        log_errors: 是否记录错误日志
        **kwargs: 函数关键字参数
        
    Returns:
        函数执行结果或默认返回值
        
    Example:
        >>> result = safe_execute(read_file, 'config.json', default_return='')
        >>> data = safe_execute(json.loads, content, default_return={})
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            log_error(e, context=f"执行 {func.__name__}")
        return default_return


def format_error_message(
    error: Exception,
    context: Optional[str] = None,
    include_traceback: bool = False
) -> str:
    """
    格式化错误消息
    
    Args:
        error: 异常对象
        context: 错误上下文信息
        include_traceback: 是否包含堆栈跟踪
        
    Returns:
        格式化后的错误消息
        
    Example:
        >>> try:
        >>>     ...
        >>> except Exception as e:
        >>>     msg = format_error_message(e, context="读取配置文件")
        >>>     print(msg)
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    parts = [f"[{error_type}] {error_msg}"]
    
    if context:
        parts.append(f"上下文: {context}")
    
    if include_traceback:
        tb = traceback.format_exc()
        parts.append(f"堆栈跟踪:\n{tb}")
    
    return '\n'.join(parts)


def log_error(error: Exception, context: Optional[str] = None) -> None:
    """
    记录错误日志
    
    Args:
        error: 异常对象
        context: 错误上下文信息
        
    Example:
        >>> try:
        >>>     ...
        >>> except Exception as e:
        >>>     log_error(e, context="处理用户请求")
    """
    error_msg = format_error_message(error, context)
    
    # 输出到 stderr
    print(f"❌ {error_msg}", file=sys.stderr)


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    重试装饰器工厂，在异常时自动重试
    
    Args:
        max_retries: 最大重试次数
        delay: 重试间隔（秒）
        exceptions: 要捕获的异常类型
        
    Returns:
        装饰器函数
        
    Example:
        >>> @retry_on_error(max_retries=3, delay=0.5)
        >>> def fetch_data():
        >>>     ...
    """
    import time
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        if delay > 0:
                            time.sleep(delay)
                        log_error(e, context=f"{func.__name__} 第 {attempt + 1} 次尝试失败")
            
            # 所有重试都失败，抛出最后一次异常
            raise last_exception
        
        return wrapper
    
    return decorator


def validate_type(value: Any, expected_type: type, name: str = "参数") -> Any:
    """
    验证参数类型
    
    Args:
        value: 要验证的值
        expected_type: 期望的类型
        name: 参数名称
        
    Returns:
        验证通过的值
        
    Raises:
        TypeError: 类型不匹配
        
    Example:
        >>> def process(data: str):
        >>>     data = validate_type(data, str, "data")
        >>>     ...
    """
    if not isinstance(value, expected_type):
        raise TypeError(
            f"{name} 类型错误: 期望 {expected_type.__name__}, "
            f"实际 {type(value).__name__}"
        )
    return value


def validate_range(
    value: int,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
    name: str = "参数"
) -> int:
    """
    验证数值范围
    
    Args:
        value: 要验证的值
        min_value: 最小值（可选）
        max_value: 最大值（可选）
        name: 参数名称
        
    Returns:
        验证通过的值
        
    Raises:
        ValueError: 值超出范围
        
    Example:
        >>> def set_timeout(seconds: int):
        >>>     seconds = validate_range(seconds, 1, 60, "seconds")
        >>>     ...
    """
    if min_value is not None and value < min_value:
        raise ValueError(f"{name} 值过小: 最小值为 {min_value}, 实际为 {value}")
    
    if max_value is not None and value > max_value:
        raise ValueError(f"{name} 值过大: 最大值为 {max_value}, 实际为 {value}")
    
    return value


def validate_not_empty(value: str, name: str = "参数") -> str:
    """
    验证字符串非空
    
    Args:
        value: 要验证的字符串
        name: 参数名称
        
    Returns:
        验证通过的字符串
        
    Raises:
        ValueError: 字符串为空
        
    Example:
        >>> def load_file(filepath: str):
        >>>     filepath = validate_not_empty(filepath, "filepath")
        >>>     ...
    """
    if not value or not value.strip():
        raise ValueError(f"{name} 不能为空")
    
    return value.strip()


class ErrorContext:
    """
    错误上下文管理器
    
    用于在代码块中捕获异常并添加上下文信息
    
    Example:
        >>> with ErrorContext("处理配置文件"):
        >>>     config = read_json_file('config.json')
        >>>     process_config(config)
    """
    
    def __init__(self, context: str, log_errors: bool = True):
        self.context = context
        self.log_errors = log_errors
        self.error: Optional[Exception] = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:
            self.error = exc_val
            if self.log_errors:
                log_error(exc_val, context=self.context)
            # 返回 True 表示异常已处理，不再传播
            return True
        return False
    
    def get_error(self) -> Optional[Exception]:
        """获取捕获的异常"""
        return self.error
    
    def has_error(self) -> bool:
        """检查是否有异常"""
        return self.error is not None