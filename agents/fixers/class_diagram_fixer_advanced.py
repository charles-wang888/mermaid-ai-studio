"""类图高级语法修复器"""
import re
from typing import Dict, Optional, Any
from agents.fixers.base_fixer import SyntaxFixer


class ClassDiagramFixerAdvanced(SyntaxFixer):
    """类图高级语法修复器 - 用于修复复杂错误"""
    
    def get_diagram_type(self) -> str:
        return "classDiagram"
    
    def fix(self, mermaid_code: str, error_info: Optional[Dict[str, Any]] = None, **kwargs) -> str:
        """高级修复类图语法错误（基于错误信息）"""
        if not mermaid_code or not mermaid_code.strip().startswith("classDiagram"):
            return mermaid_code
        
        lines = mermaid_code.split('\n')
        error_lines = []
        if error_info:
            error_lines = error_info.get('error_lines', [])
        
        fixed_lines = []
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            original_indent = len(line) - len(line.lstrip())
            
            # 如果是错误行或疑似错误行，进行修复
            if i in error_lines or (not line_stripped.startswith('class ') and re.match(r'^[A-Z]\w*\s*\{', line_stripped)):
                # 检测缺少 class 关键字的类定义
                if not line_stripped.startswith('class ') and re.match(r'^[A-Z]\w*\s*\{', line_stripped):
                    if not any(symbol in line_stripped for symbol in ['<|--', '<|..', '*--', 'o--', '-->', '..>']):
                        class_match = re.match(r'^([A-Z]\w*)\s*\{', line_stripped)
                        if class_match:
                            class_name = class_match.group(1)
                            fixed_line = f"{' ' * original_indent}class {class_name} {{"
                            fixed_lines.append(fixed_line)
                            continue
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)

