"""时序图语法修复器"""
import re
from agents.fixers.base_fixer import SyntaxFixer


class SequenceDiagramFixer(SyntaxFixer):
    """时序图语法修复器"""
    
    def get_diagram_type(self) -> str:
        return "sequenceDiagram"
    
    def fix(self, mermaid_code: str, **kwargs) -> str:
        """修复时序图语法错误"""
        if not mermaid_code or not mermaid_code.strip().startswith("sequenceDiagram"):
            return mermaid_code
        
        lines = mermaid_code.split('\n')
        fixed_lines = []
        
        for line in lines:
            original_line = line
            line_stripped = line.strip()
            
            if not line_stripped:
                fixed_lines.append("")
                continue
            
            # 修复 participant 定义错误：participant "名称" as 别名
            if line_stripped.startswith('participant '):
                # 匹配：participant "名称" as 别名 或 participant 别名 as "名称"
                if 'as' in line_stripped:
                    parts = line_stripped.split('as', 1)
                    if len(parts) == 2:
                        left_part = parts[0].strip()
                        right_part = parts[1].strip()
                        
                        # 提取别名和名称
                        participant_match = re.match(r'participant\s+(.+)', left_part)
                        if participant_match:
                            participant_name = participant_match.group(1).strip().strip('"\'')
                            alias = right_part.strip().strip('"\'')
                            
                            # 构建正确的 participant 行
                            fixed_line = f"participant {participant_name} as {alias}"
                            fixed_lines.append(fixed_line)
                            continue
            
            fixed_lines.append(original_line)
        
        return '\n'.join(fixed_lines)

