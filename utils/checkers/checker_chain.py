"""语法检查器链 - 责任链模式"""
from typing import List, Dict, Optional
from utils.checkers.base_checker import SyntaxChecker
from utils.checkers.class_definition_checker import ClassDefinitionChecker
from utils.checkers.quadrant_chart_checker import QuadrantChartChecker
from utils.checkers.keyword_spelling_checker import KeywordSpellingChecker
from utils.checkers.arrow_syntax_checker import ArrowSyntaxChecker
from utils.checkers.generic_type_checker import GenericTypeChecker


class SyntaxCheckerChain:
    """语法检查器链 - 责任链模式，依次执行所有检查器"""
    
    def __init__(self):
        """初始化检查器链"""
        self.checkers: List[SyntaxChecker] = [
            ClassDefinitionChecker(),
            QuadrantChartChecker(),
            KeywordSpellingChecker(),
            ArrowSyntaxChecker(),
            GenericTypeChecker(),
        ]
    
    def check_all(self, mermaid_code: str) -> Dict:
        """检查所有代码行
        
        Args:
            mermaid_code: Mermaid代码
            
        Returns:
            如果有错误，返回 {'message': str, 'error_lines': List[int]}
            如果没有错误，返回 None
        """
        if not mermaid_code or not mermaid_code.strip():
            return None
        
        lines = mermaid_code.split('\n')
        first_line = mermaid_code.strip().split('\n')[0].strip() if mermaid_code.strip() else ""
        error_lines_map = {}  # {line_num: (checker, line_content)}
        
        # 单次遍历所有行，应用所有检查器
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('//'):
                continue
            
            # 依次应用所有检查器
            for checker in self.checkers:
                error_line = checker.check(lines, i, line, stripped, first_line)
                if error_line:
                    if error_line not in error_lines_map:
                        error_lines_map[error_line] = (checker, line)
                    break  # 找到一个错误就停止，避免重复
        
        if error_lines_map:
            # 构建错误消息
            error_messages = []
            error_lines = sorted(error_lines_map.keys())
            
            for line_num in error_lines[:3]:  # 只显示前3个错误的详细信息
                checker, line_content = error_lines_map[line_num]
                error_msg = checker.get_error_message(line_num, line_content)
                error_messages.append(error_msg)
            
            message = "发现语法错误:\n" + "\n".join(error_messages)
            if len(error_lines) > 3:
                message += f"\n... 还有 {len(error_lines) - 3} 处错误"
            
            # 提取错误代码片段
            code_snippet = self._extract_error_snippet(lines, error_lines)
            
            return {
                'message': message,
                'error_lines': error_lines,
                'code_snippet': code_snippet
            }
        
        return None
    
    def _extract_error_snippet(self, lines: List[str], error_lines: List[int], context_lines: int = 2) -> str:
        """提取错误代码片段"""
        if not error_lines:
            return ""
        
        snippets = []
        
        for line_num in error_lines[:3]:  # 最多显示3个错误行的片段
            start = max(0, line_num - context_lines - 1)
            end = min(len(lines), line_num + context_lines)
            
            snippet_lines = []
            for i in range(start, end):
                line_marker = ">>> " if i == line_num - 1 else "    "
                snippet_lines.append(f"{line_marker}{i+1:4d} | {lines[i]}")
            
            snippets.append('\n'.join(snippet_lines))
        
        return '\n\n'.join(snippets)

