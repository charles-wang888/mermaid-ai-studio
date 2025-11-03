"""饼图语法修复器"""
import re
from agents.fixers.base_fixer import SyntaxFixer


class PieChartFixer(SyntaxFixer):
    """饼图语法修复器"""
    
    def get_diagram_type(self) -> str:
        return "pie"
    
    def fix(self, mermaid_code: str, **kwargs) -> str:
        """修复饼图语法错误"""
        if not mermaid_code or not mermaid_code.strip().startswith("pie"):
            return mermaid_code
        
        lines = mermaid_code.split('\n')
        fixed_lines = []
        has_title = False
        
        for line in lines:
            line_stripped = line.strip()
            original_indent = len(line) - len(line.lstrip())
            
            if not line_stripped:
                fixed_lines.append("")
                continue
            
            # 检查是否是 pie 开头行
            if line_stripped.startswith('pie'):
                # 检查是否已经有 title
                if 'title' in line_stripped.lower():
                    has_title = True
                    fixed_lines.append(line_stripped)
                else:
                    # 如果没有 title，添加默认 title
                    fixed_lines.append('pie title 数据分布')
                    has_title = True
                continue
            
            # 处理数据行：格式应该是 "标签" : 数值
            # 匹配引号内的标签和数值
            data_pattern = r'^(["\'])(.+?)\1\s*:\s*(\d+(?:\.\d+)?)$'
            data_match = re.match(data_pattern, line_stripped)
            if data_match:
                quote_char = data_match.group(1)
                label = data_match.group(2)
                value = data_match.group(3)
                
                # 确保标签用引号包裹
                fixed_line = f"{' ' * original_indent}\"{label}\" : {value}"
                fixed_lines.append(fixed_line)
                continue
            
            # 处理可能没有引号的数据行
            no_quote_pattern = r'^(.+?)\s*:\s*(\d+(?:\.\d+)?)$'
            no_quote_match = re.match(no_quote_pattern, line_stripped)
            if no_quote_match:
                label = no_quote_match.group(1).strip()
                value = no_quote_match.group(2)
                # 为标签添加引号
                fixed_line = f"{' ' * original_indent}\"{label}\" : {value}"
                fixed_lines.append(fixed_line)
                continue
            
            # 其他行直接保留
            fixed_lines.append(line)
        
        result = '\n'.join(fixed_lines)
        
        # 确保第一行是 pie title 格式
        if not has_title:
            result_lines = result.split('\n')
            if result_lines and result_lines[0].strip().startswith('pie'):
                result_lines[0] = 'pie title 数据分布'
                result = '\n'.join(result_lines)
        
        return result

