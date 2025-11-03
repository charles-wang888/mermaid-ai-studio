"""类定义语法检查器"""
import re
from typing import List, Optional
from utils.checkers.base_checker import SyntaxChecker


class ClassDefinitionChecker(SyntaxChecker):
    """检查类定义相关的语法错误"""
    
    def check(self, lines: List[str], line_num: int, line: str, stripped: str, first_line: str) -> Optional[int]:
        """检查类定义语法错误"""
        # 1. 类定义前面有非法字符（如 --, ##, **, {内容}-- 等）
        if 'class' in stripped and not stripped.startswith('class '):
            class_pos = stripped.find('class')
            if class_pos > 0:
                before_class = stripped[:class_pos].strip()
                if before_class and not before_class.startswith('//'):
                    after_class = stripped[class_pos + 5:].strip()
                    if after_class and (re.match(r'^[a-zA-Z_\u4e00-\u9fa5]', after_class) or re.match(r'^\w+', after_class)):
                        return line_num
        
        # 2. 关系符号在类定义行中（错误语法）
        if stripped.startswith('class ') and ('<|--' in stripped or '<|..' in stripped or 
                                              '*--' in stripped or 'o--' in stripped or
                                              '-->' in stripped or '..>' in stripped):
            return line_num
        
        return None
    
    def get_error_message(self, line_num: int, line_content: str) -> str:
        """生成类定义相关的错误消息"""
        stripped = line_content.strip()
        
        if 'class' in stripped and not stripped.startswith('class '):
            before_class = stripped[:stripped.find('class')].strip()
            if before_class:
                display_before = before_class[:30] + '...' if len(before_class) > 30 else before_class
                return f"第{line_num}行：类定义前有非法内容 '{display_before}' (完整行: {line_content[:50]})"
            illegal_match = re.match(r'^([^\w\s]+)', stripped)
            if illegal_match:
                illegal_chars = illegal_match.group(1)
                return f"第{line_num}行：类定义前有非法字符 '{illegal_chars}' (完整行: {line_content[:50]})"
        
        if 'class ' in stripped and ('<|--' in stripped or '-->' in stripped):
            return f"第{line_num}行：类定义与关系符号混写 (完整行: {line_content[:50]})"
        
        return super().get_error_message(line_num, line_content)

