"""状态图语法修复器"""
import re
from agents.fixers.base_fixer import SyntaxFixer


class StateDiagramFixer(SyntaxFixer):
    """状态图语法修复器"""
    
    def get_diagram_type(self) -> str:
        return "stateDiagram-v2"
    
    def fix(self, mermaid_code: str, **kwargs) -> str:
        """修复状态图语法错误"""
        if not mermaid_code or not mermaid_code.strip().startswith("stateDiagram-v2"):
            return mermaid_code
        
        lines = mermaid_code.split('\n')
        fixed_lines = []
        seen_relationships = set()  # 用于去重
        
        def has_chinese(text: str) -> bool:
            return any('\u4e00' <= char <= '\u9fff' for char in text)
        
        def quote_if_needed(text: str) -> str:
            text = text.strip()
            if not text:
                return text
            if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
                return text
            if has_chinese(text) or ' ' in text or any(char in text for char in ['(', ')', '（', '）']):
                return f'"{text}"'
            return text
        
        for line in lines:
            line_stripped = line.strip()
            original_indent = len(line) - len(line.lstrip())
            
            if not line_stripped or line_stripped.startswith('//'):
                fixed_lines.append(line)
                continue
            
            if line_stripped.startswith('stateDiagram-v2'):
                fixed_lines.append(line)
                continue
            
            # 0. 首先修复嵌套状态中的 * 应该改为 [*]（在所有其他匹配之前）
            # 修复单独的 * 行
            if line_stripped.strip() == '*':
                fixed_lines.append(f"{' ' * original_indent}[*]")
                continue
            
            # 修复 * --> 开头的转换（没有方括号的情况）
            if re.match(r'^\*\s*-->\s*', line_stripped):
                line_stripped = line_stripped.replace('* -->', '[*] -->', 1)
            
            # 1. 修复使用花括号的转换条件
            brace_pattern = r'(\[[*]\]|"[^"]+"|[A-Za-z_][A-Za-z0-9_\s]*)\s*-->\s*(\[[*]\]|"[^"]+"|[A-Za-z_][A-Za-z0-9_\s]*)\s*\{\s*([^}]+)\s*\}' 
            brace_match = re.search(brace_pattern, line_stripped)
            if brace_match:
                source_state = brace_match.group(1).strip().strip('"\'')
                target_state = brace_match.group(2).strip().strip('"\'')
                condition = brace_match.group(3).strip()
                
                source_state = quote_if_needed(source_state)
                target_state = quote_if_needed(target_state)
                condition = quote_if_needed(condition)
                
                fixed_line = f"{' ' * original_indent}{source_state} --> {target_state} : {condition}"
                relationship_key = f"{source_state} --> {target_state} : {condition}"
                if relationship_key not in seen_relationships:
                    seen_relationships.add(relationship_key)
                    fixed_lines.append(fixed_line)
                continue
            
            # 2. 修复已有冒号但可能缺少引号的转换条件
            colon_pattern = r'(\[[*]\]|"[^"]+"|[A-Za-z_][A-Za-z0-9_\s]*)\s*-->\s*(\[[*]\]|"[^"]+"|[A-Za-z_][A-Za-z0-9_\s]*)\s*:\s*(.+)$'
            colon_match = re.match(colon_pattern, line_stripped)
            if colon_match:
                source_state = colon_match.group(1).strip().strip('"\'')
                target_state = colon_match.group(2).strip().strip('"\'')
                condition = colon_match.group(3).strip().strip('"\'')
                
                source_state = quote_if_needed(source_state)
                target_state = quote_if_needed(target_state)
                condition = quote_if_needed(condition)
                
                fixed_line = f"{' ' * original_indent}{source_state} --> {target_state} : {condition}"
                relationship_key = f"{source_state} --> {target_state} : {condition}"
                if relationship_key not in seen_relationships:
                    seen_relationships.add(relationship_key)
                    fixed_lines.append(fixed_line)
                continue
            
            # 3. 修复没有条件的转换
            simple_pattern = r'(\[[*]\]|"[^"]+"|[A-Za-z_][A-Za-z0-9_\s]*)\s*-->\s*(\[[*]\]|"[^"]+"|[A-Za-z_][A-Za-z0-9_\s]*)\s*$'
            simple_match = re.match(simple_pattern, line_stripped)
            if simple_match:
                source_state = simple_match.group(1).strip().strip('"\'')
                target_state = simple_match.group(2).strip().strip('"\'')
                
                source_state = quote_if_needed(source_state)
                target_state = quote_if_needed(target_state)
                
                fixed_line = f"{' ' * original_indent}{source_state} --> {target_state}"
                relationship_key = f"{source_state} --> {target_state}"
                if relationship_key not in seen_relationships:
                    seen_relationships.add(relationship_key)
                    fixed_lines.append(fixed_line)
                continue
            
            # 4. 处理状态定义行：修复状态名中的空格和中文
            state_def_pattern = r'state\s+(.+?)\s*\{'
            state_def_match = re.match(state_def_pattern, line_stripped)
            if state_def_match:
                state_name = state_def_match.group(1).strip().strip('"\'')
                quoted_state_name = quote_if_needed(state_name)
                fixed_line = f"{' ' * original_indent}state {quoted_state_name} {{"
                fixed_lines.append(fixed_line)
                continue
            
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)

