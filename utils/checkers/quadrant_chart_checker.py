"""象限图语法检查器"""
import re
from enum import Enum, auto
from typing import List, Optional, Tuple
from utils.checkers.base_checker import SyntaxChecker


class ErrorType(Enum):
    """错误类型枚举"""
    NONE = auto()
    AXIS = auto()
    QUADRANT = auto()


class QuadrantChartChecker(SyntaxChecker):
    """检查象限图相关的语法错误（中文标签引号）"""
    
    def __init__(self):
        super().__init__()
        self._last_error_type = ErrorType.NONE
    
    def _check_text_quotes(self, text: str) -> Tuple[bool, bool]:
        """检查文本是否包含中文且是否被引号包裹
        
        Args:
            text: 要检查的文本
            
        Returns:
            (has_chinese, is_quoted)元组
        """
        stripped_text = text.strip()
        clean_text = stripped_text.strip('"\'')
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in clean_text)
        is_quoted = (stripped_text.startswith('"') and stripped_text.endswith('"')) or \
                   (stripped_text.startswith("'") and stripped_text.endswith("'"))
        return has_chinese, is_quoted

    def _check_axis_labels(self, stripped: str) -> bool:
        """检查轴标签格式
        
        Returns:
            如果有错误返回True
        """
        if '-->' in stripped:
            axis_content = stripped.split(None, 1)[1] if ' ' in stripped else ''
            if axis_content and '-->' in axis_content:
                parts = axis_content.split('-->')
                if len(parts) == 2:
                    left_has_chinese, left_quoted = self._check_text_quotes(parts[0])
                    right_has_chinese, right_quoted = self._check_text_quotes(parts[1])
                    return (left_has_chinese and not left_quoted) or (right_has_chinese and not right_quoted)
        return False

    def check(self, lines: List[str], line_num: int, line: str, stripped: str, first_line: str) -> Optional[int]:
        """检查象限图语法错误"""
        self._last_error_type = ErrorType.NONE
        
        # 检查 x-axis、y-axis 行中的中文标签
        if (stripped.startswith('x-axis') or stripped.startswith('y-axis')) and self._check_axis_labels(stripped):
            self._last_error_type = ErrorType.AXIS
            return line_num
        
        # 检查 quadrant-* 行中的中文标签
        if re.match(r'^quadrant-\d+', stripped):
            parts = stripped.split(None, 1)
            if len(parts) == 2:
                has_chinese, is_quoted = self._check_text_quotes(parts[1])
                if has_chinese and not is_quoted:
                    self._last_error_type = ErrorType.QUADRANT
                    return line_num
        
        return None
    
    def get_error_message(self, line_num: int, line_content: str) -> str:
        """生成象限图相关的错误消息"""
        if self._last_error_type == ErrorType.AXIS:
            return f"第{line_num}行: 中文标签必须使用引号包裹 (完整行: {line_content[:80]})"
        elif self._last_error_type == ErrorType.QUADRANT:
            return f"第{line_num}行: 象限标签中的中文必须使用引号包裹 (完整行: {line_content[:80]})"
        return super().get_error_message(line_num, line_content)

