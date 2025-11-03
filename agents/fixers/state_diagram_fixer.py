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
        
        i = 0
        while i < len(lines):
            line = lines[i]
            line_stripped = line.strip()
            original_indent = len(line) - len(line.lstrip())
            
            if not line_stripped or line_stripped.startswith('//'):
                fixed_lines.append(line)
                i += 1
                continue
            
            if line_stripped.startswith('stateDiagram-v2'):
                fixed_lines.append(line)
                i += 1
                continue
            
            # 修复连在一起的引号问题（如 "待支付""待支付" --> "已支付"）
            # 根据错误信息：[*] --> "待支付""待支付" --> "已支付"
            # 这可能是状态名称被重复，或者是两行被错误合并
            if '""' in line_stripped:
                # 模式1: [*] --> "待支付""待支付" --> "已支付" (状态名称重复)
                # 修复为: [*] --> "待支付" 和 "待支付" --> "已支付" (分成两行)
                pattern1 = r'(\[[*]\]|"[^"]+"|[A-Za-z_][A-Za-z0-9_\s]*)\s*-->\s*"([^"]+)""\2"\s*-->\s*(\[[*]\]|"[^"]+"|[A-Za-z_][A-Za-z0-9_\s]*)'
                match1 = re.search(pattern1, line_stripped)
                if match1:
                    source = match1.group(1).strip()
                    repeated_state = match1.group(2)
                    target = match1.group(3).strip()
                    source_quoted = quote_if_needed(source)
                    state_quoted = quote_if_needed(repeated_state)
                    target_quoted = quote_if_needed(target)
                    # 分成两行
                    fixed_lines.append(f"{' ' * original_indent}{source_quoted} --> {state_quoted}")
                    fixed_lines.append(f"{' ' * original_indent}{state_quoted} --> {target_quoted}")
                    i += 1
                    continue
                
                # 模式2: "待支付""待支付" (重复的状态名称，没有箭头)
                line_stripped = re.sub(r'"([^"]+)""\1"(?!\s*-->)', r'"\1"', line_stripped)
                # 模式3: "状态A""状态B" --> "状态C" (不同的状态连在一起，中间缺少箭头)
                line_stripped = re.sub(r'"([^"]+)""([^"]+)"\s*-->\s*', r'"\1" --> "\2"\n    "\2" --> ', line_stripped)
                # 模式4: "状态A""状态A" --> (重复状态且后面有箭头)
                line_stripped = re.sub(r'"([^"]+)""\1"\s*-->\s*', r'"\1" --> ', line_stripped)
            
            # 0. 首先修复嵌套状态中的 * 应该改为 [*]（在所有其他匹配之前）
            # 修复单独的 * 行
            if line_stripped.strip() == '*':
                fixed_lines.append(f"{' ' * original_indent}[*]")
                i += 1
                continue
            
            # 修复 * --> 开头的转换（没有方括号的情况）
            if re.match(r'^\*\s*-->\s*', line_stripped):
                line_stripped = line_stripped.replace('* -->', '[*] -->', 1)
                # 注意：这里修改了 line_stripped，但后面还需要继续处理，所以不 continue
            
            # 修复反向箭头 <-- 和 <-
            # 将 "目标 <-- 源" 转换为 "源 --> 目标"
            if '<--' in line_stripped or '<-' in line_stripped:
                # 匹配反向箭头模式：目标 <-- 源 或 目标 <- 源（可能包含引号、方括号等）
                # 更宽松的匹配模式，支持中文、引号等
                reverse_pattern = r'(\[[*]\]|"[^"]+"|[\u4e00-\u9fff\w\s]+)\s*<--?\s*(\[[*]\]|"[^"]+"|[\u4e00-\u9fff\w\s]+)\s*$'
                reverse_match = re.match(reverse_pattern, line_stripped)
                if reverse_match:
                    target_state = reverse_match.group(1).strip().strip('"\'')
                    source_state = reverse_match.group(2).strip().strip('"\'')
                    # 反转方向：源 --> 目标，确保状态名称被正确引用
                    source_quoted = quote_if_needed(source_state)
                    target_quoted = quote_if_needed(target_state)
                    line_stripped = f"{source_quoted} --> {target_quoted}"
            
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
                i += 1
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
                i += 1
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
                i += 1
                continue
            
            # 4. 移除状态定义中的 description: 语法（Mermaid不支持）
            if 'description:' in line_stripped.lower():
                # 跳过包含 description 的行
                i += 1
                continue
            
            # 5. 处理状态定义行：如果状态定义块只包含 description，移除整个块
            state_def_pattern = r'state\s+(.+?)\s*\{'
            state_def_match = re.match(state_def_pattern, line_stripped)
            if state_def_match:
                state_name = state_def_match.group(1).strip().strip('"\'')
                # 查看后续行，判断是否只有 description
                brace_count = 1
                has_content = False
                has_nested_state = False
                j = i + 1
                
                while j < len(lines) and brace_count > 0:
                    next_line = lines[j]
                    next_stripped = next_line.strip()
                    if not next_stripped or next_stripped.startswith('//'):
                        j += 1
                        continue
                    if 'description:' in next_stripped.lower():
                        # 找到 description，但不是有效内容
                        j += 1
                        continue
                    if next_stripped.startswith('state '):
                        has_nested_state = True
                        has_content = True
                        break
                    if next_stripped == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            # 找到块的结束，检查块中是否有有效内容
                            break
                    else:
                        brace_count += next_line.count('{') - next_line.count('}')
                        if brace_count == 0:
                            break
                        # 如果到达这里，说明块中有其他内容（不是 description）
                        has_content = True
                    j += 1
                
                # 如果状态块只有 description（没有嵌套状态，没有其他内容），跳过整个块
                if not has_content and not has_nested_state:
                    # 跳过从当前 state 行到对应 } 行的所有内容
                    i = j + 1  # j 指向 } 行，所以 +1 跳过
                    continue
                
                # 有嵌套状态或真实内容，保留状态定义
                quoted_state_name = quote_if_needed(state_name)
                fixed_lines.append(f"{' ' * original_indent}state {quoted_state_name} {{")
                i += 1
                continue
            
            fixed_lines.append(line)
            i += 1
        
        return '\n'.join(fixed_lines)

