"""语法检查器基类"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple


class SyntaxChecker(ABC):
    """语法检查器抽象基类 - 策略模式"""
    
    @abstractmethod
    def check(self, lines: List[str], line_num: int, line: str, stripped: str, first_line: str) -> Optional[int]:
        """检查单行代码
        
        Args:
            lines: 所有代码行的列表
            line_num: 当前行号（从1开始）
            line: 原始行内容
            stripped: 去除首尾空白的行内容
            first_line: 第一行内容（用于判断图表类型）
            
        Returns:
            如果有错误，返回行号；如果没有错误，返回None
        """
        pass
    
    def get_error_message(self, line_num: int, line_content: str) -> str:
        """生成错误消息
        
        Args:
            line_num: 行号
            line_content: 行内容
            
        Returns:
            错误消息
        """
        return f"第{line_num}行: 语法错误 (完整行: {line_content[:50]})"

