"""象限图语法修复器"""
import re
from agents.fixers.base_fixer import SyntaxFixer


class QuadrantChartFixer(SyntaxFixer):
    """象限图语法修复器"""
    
    def get_diagram_type(self) -> str:
        return "quadrantChart"
    
    def fix(self, mermaid_code: str, **kwargs) -> str:
        """修复象限图语法错误（主要是中文标签引号）"""
        if not mermaid_code or not mermaid_code.strip().startswith("quadrantChart"):
            return mermaid_code
        
        lines = mermaid_code.split('\n')
        fixed_lines = []
        
        def has_chinese(text: str) -> bool:
            return any('\u4e00' <= char <= '\u9fff' for char in text)
        
        def quote_if_needed(text: str) -> str:
            text = text.strip()
            if not text:
                return text
            if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
                return text
            if has_chinese(text) or ' ' in text:
                return f'"{text}"'
            return text
        
        for line in lines:
            line_stripped = line.strip()
            
            if not line_stripped:
                fixed_lines.append(line)
                continue
            
            # 修复 x-axis 和 y-axis 行的中文标签
            if line_stripped.startswith('x-axis') or line_stripped.startswith('y-axis'):
                if '-->' in line_stripped:
                    axis_content = line_stripped.split(None, 1)[1] if ' ' in line_stripped else ''
                    if axis_content and '-->' in axis_content:
                        parts = axis_content.split('-->')
                        if len(parts) == 2:
                            left_label = parts[0].strip().strip('"\'')
                            right_label = parts[1].strip().strip('"\'')
                            left_quoted = quote_if_needed(left_label)
                            right_quoted = quote_if_needed(right_label)
                            axis_prefix = 'x-axis' if line_stripped.startswith('x-axis') else 'y-axis'
                            fixed_lines.append(f"{axis_prefix} {left_quoted} --> {right_quoted}")
                            continue
            
            # 修复 quadrant-* 行的中文标签
            if re.match(r'^quadrant-\d+', line_stripped):
                parts = line_stripped.split(None, 1)
                if len(parts) == 2:
                    quadrant_prefix = parts[0]
                    quadrant_text = parts[1].strip().strip('"\'')
                    quadrant_quoted = quote_if_needed(quadrant_text)
                    fixed_lines.append(f"{quadrant_prefix} {quadrant_quoted}")
                    continue
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)

