"""关键字拼写检查器"""
import re
from typing import List, Optional
from utils.checkers.base_checker import SyntaxChecker


class KeywordSpellingChecker(SyntaxChecker):
    """检查关键字拼写错误"""
    
    def check(self, lines: List[str], line_num: int, line: str, stripped: str, first_line: str) -> Optional[int]:
        """检查关键字拼写错误"""
        stripped_lower = stripped.lower()
        
        # 检查用户旅程图：section 拼写错误
        if first_line.startswith('journey'):
            if re.match(r'^\s*sections\s+', stripped, re.IGNORECASE):
                return line_num
            if re.match(r'^\s*section[^a-z\s]', stripped, re.IGNORECASE):
                return line_num
        
        # 检查 subgraph 拼写错误
        if stripped_lower.startswith('subgraph'):
            if len(stripped) > 8:
                char_after_subgraph = stripped[8]
                if char_after_subgraph not in [' ', '"', "'", '[', '(', '\t']:
                    return line_num
        elif 'ubgraph' in stripped_lower or 'subgrap' in stripped_lower or 'subgr' in stripped_lower:
            if re.match(r'^\s*s{2,}ubgraph', stripped_lower):
                return line_num
            if re.match(r'^\s*subgrap[^h\s]', stripped_lower):
                return line_num
            if re.match(r'^\s*subgr[^a\s]', stripped_lower):
                return line_num
        
        # 检查 flowchart 拼写错误
        if 'owchart' in stripped_lower or 'flowch' in stripped_lower:
            if not stripped_lower.startswith('flowchart'):
                if re.match(r'^\s*fl{2,}owchart', stripped_lower):
                    return line_num
                if re.match(r'^\s*flowch[^a\s]', stripped_lower):
                    return line_num
        
        # 检查 participant 拼写错误
        if 'articipan' in stripped_lower:
            if not stripped_lower.startswith('participant'):
                if re.match(r'^\s*participan[^t\s]', stripped_lower):
                    return line_num
        
        # 检查 sequenceDiagram 拼写错误
        if 'equence' in stripped_lower or 'equenc' in stripped_lower:
            if not stripped_lower.startswith('sequencediagram'):
                if re.match(r'^\s*sequenc[^e]diagram', stripped_lower):
                    return line_num
        
        return None
    
    def get_error_message(self, line_num: int, line_content: str) -> str:
        """生成关键字拼写错误消息"""
        stripped = line_content.strip()
        stripped_lower = stripped.lower()
        
        if stripped_lower.startswith('sections'):
            return f"第{line_num}行：用户旅程图语法错误，应该是 'section' 而不是 'sections' (完整行: {line_content[:50]})"
        
        if stripped_lower.startswith('subgraph'):
            if len(line_content) > 8 and not (line_content[8:9].isspace() or line_content[8:9] in ['"', "'", '[', '(']):
                wrong_part = line_content[8:].split()[0] if len(line_content) > 8 else ''
                return f"第{line_num}行：subgraph语法错误，'subgraph' 后面应该是空格、ID或标签，而不是 '{wrong_part}' (完整行: {line_content[:50]})"
        
        if ('ubgraph' in stripped_lower or 'subgrap' in stripped_lower) and not stripped_lower.startswith('subgraph'):
            wrong_word = stripped.split()[0] if stripped.split() else ''
            return f"第{line_num}行：拼写错误，应该是 'subgraph' 而不是 '{wrong_word}' (完整行: {line_content[:50]})"
        
        if ('owchart' in stripped_lower or 'flowch' in stripped_lower) and not stripped_lower.startswith('flowchart'):
            wrong_word = stripped.split()[0] if stripped.split() else ''
            return f"第{line_num}行：拼写错误，应该是 'flowchart' 而不是 '{wrong_word}' (完整行: {line_content[:50]})"
        
        if 'articipan' in stripped_lower and not stripped_lower.startswith('participant'):
            wrong_word = stripped.split()[0] if stripped.split() else ''
            return f"第{line_num}行：拼写错误，应该是 'participant' 而不是 '{wrong_word}' (完整行: {line_content[:50]})"
        
        if ('equence' in stripped_lower or 'equenc' in stripped_lower) and not stripped_lower.startswith('sequencediagram'):
            wrong_word = stripped.split()[0] if stripped.split() else ''
            return f"第{line_num}行：拼写错误，应该是 'sequenceDiagram' 而不是 '{wrong_word}' (完整行: {line_content[:50]})"
        
        return super().get_error_message(line_num, line_content)

