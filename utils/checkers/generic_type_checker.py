"""泛型类型和方法定义检查器"""
import re
from typing import List, Optional
from utils.checkers.base_checker import SyntaxChecker


class GenericTypeChecker(SyntaxChecker):
    """检查泛型类型和方法定义相关的语法错误"""
    
    def check(self, lines: List[str], line_num: int, line: str, stripped: str, first_line: str) -> Optional[int]:
        """检查泛型类型和方法定义语法错误"""
        # 方法定义使用了错误的冒号格式
        if re.search(r'[+\-#~]\s*\w+\s*\(\s*\)\s*:', stripped):
            return line_num
        
        # 使用了尖括号的泛型（应该用波浪号）
        if re.search(r'List\s*<|Map\s*<|Set\s*<', stripped):
            return line_num
        
        return None
    
    def get_error_message(self, line_num: int, line_content: str) -> str:
        """生成泛型类型和方法定义相关的错误消息"""
        # 这里可以使用通用的错误消息，因为格式错误通常很明显
        return f"第{line_num}行：方法定义或泛型类型格式错误 (完整行: {line_content[:50]})"

