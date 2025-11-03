"""箭头和前缀语法检查器"""
import re
from typing import List, Optional
from utils.checkers.base_checker import SyntaxChecker


class ArrowSyntaxChecker(SyntaxChecker):
    """检查箭头和行首前缀相关的语法错误"""
    
    def check(self, lines: List[str], line_num: int, line: str, stripped: str, first_line: str) -> Optional[int]:
        """检查箭头和前缀语法错误"""
        # 4. 行首有非法前缀（如 --, ##, -x4fa31 等，但不是注释）
        if re.match(r'^[\-\#\*]{2,}', stripped) and not stripped.startswith('//'):
            valid_starts = ['flowchart', 'classDiagram', 'sequenceDiagram', 'gantt', 
                          'stateDiagram', 'pie', 'quadrantChart', 'journey', 'class ']
            if not any(stripped.startswith(start) for start in valid_starts):
                return line_num
        
        # 检测行首的单个 - 后跟非空字符（如 -x4fa31, -xxx 等，但排除合法的连接语法和类图属性）
        if stripped.startswith('-') and not stripped.startswith('//'):
            valid_arrow_patterns = ['-->', '-.->', '---', '==>', '--', '-.-']
            if not any(stripped.startswith(pattern) for pattern in valid_arrow_patterns):
                # 检查是否是类图中的私有属性或方法
                is_class_diagram = first_line.startswith('classDiagram')
                if is_class_diagram:
                    class_member_pattern = r'^[-+#~]\s*\w+\s*(\(\)\s*[\w<>\[\]~]+|:\s*[\w<>\[\]~]+)'
                    if re.match(class_member_pattern, stripped):
                        return None  # 合法的类图成员定义
                
                if len(stripped) > 1 and stripped[1] != ' ':
                    if not any(arrow in stripped for arrow in ['-->', '-.->', '---', '==>']):
                        return line_num
        
        return None
    
    def get_error_message(self, line_num: int, line_content: str) -> str:
        """生成箭头和前缀相关的错误消息"""
        stripped = line_content.strip()
        
        if re.match(r'^[\-\#\*]{2,}', stripped) and not stripped.startswith('//'):
            prefix_match = re.match(r'^([\-\#\*]{2,})', stripped)
            if prefix_match:
                prefix = prefix_match.group(1)
                return f"第{line_num}行：行首有非法前缀 '{prefix}' (完整行: {line_content[:50]})"
        
        if stripped.startswith('-') and not stripped.startswith('//') and not any(stripped.startswith(p) for p in ['-->', '-.->', '---', '==>', '--', '-.-']):
            if len(stripped) > 1 and stripped[1] != ' ' and not any(arrow in stripped for arrow in ['-->', '-.->', '---', '==>']):
                illegal_part = stripped.split()[0] if stripped.split() else ''
                return f"第{line_num}行：行首有非法字符 '{illegal_part}'，这可能是语法错误 (完整行: {line_content[:50]})"
        
        return super().get_error_message(line_num, line_content)

