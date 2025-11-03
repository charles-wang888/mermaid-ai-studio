"""时序图语法修复器"""
import re
from agents.fixers.base_fixer import SyntaxFixer


class SequenceDiagramFixer(SyntaxFixer):
    """时序图语法修复器"""
    
    def get_diagram_type(self) -> str:
        return "sequenceDiagram"
    
    def _has_chinese(self, text: str) -> bool:
        """检查文本是否包含中文字符"""
        return any('\u4e00' <= char <= '\u9fff' for char in text)
    
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
            
            # 修复 participant 定义错误
            if line_stripped.startswith('participant '):
                # 处理多种格式：
                # 1. participant 别名 as "显示名称"
                # 2. participant "显示名称" as 别名
                # 3. participant 别名1 as 别名2 as "显示名称" (错误格式，需要修复)
                if 'as' in line_stripped:
                    # 计算 'as' 的数量
                    as_count = line_stripped.count(' as ')
                    
                    if as_count > 1:
                        # 有多个 'as'，说明格式错误
                        # 例如：participant LogSt as h as 数据采集组件
                        # 应该是：participant LogStash as "数据采集组件"
                        # 找到最后一个 'as'，之前的全部作为别名，之后作为显示名称
                        last_as_index = line_stripped.rfind(' as ')
                        left_part = line_stripped[:last_as_index].strip()
                        right_part = line_stripped[last_as_index + 4:].strip()  # +4 是 ' as ' 的长度
                        
                        # 提取别名（第一个 participant 后面的内容，去除中间的 as）
                        participant_match = re.match(r'participant\s+(.+)', left_part)
                        if participant_match:
                            alias_part = participant_match.group(1).strip()
                            # 如果有多个词通过 as 连接，合并它们作为别名
                            # 例如：LogSt as h -> LogStash
                            alias_words = [w.strip() for w in alias_part.split(' as ')]
                            alias = ''.join(alias_words)  # 合并所有部分
                            
                            display_name = right_part.strip('"\'')
                            
                            # 如果显示名称包含中文或空格，添加引号
                            if self._has_chinese(display_name) or ' ' in display_name:
                                display_name = f'"{display_name}"'
                            
                            fixed_line = f"participant {alias} as {display_name}"
                            fixed_lines.append(fixed_line)
                            continue
                    else:
                        # 只有一个 'as'，正常处理
                        parts = line_stripped.split(' as ', 1)
                        if len(parts) == 2:
                            left_part = parts[0].strip()
                            right_part = parts[1].strip()
                            
                            # 提取别名和显示名称
                            participant_match = re.match(r'participant\s+(.+)', left_part)
                            if participant_match:
                                alias = participant_match.group(1).strip().strip('"\'')
                                display_name = right_part.strip().strip('"\'')
                                
                                # 如果显示名称包含中文或空格，添加引号
                                if self._has_chinese(display_name) or ' ' in display_name:
                                    display_name = f'"{display_name}"'
                                
                                # 构建正确的 participant 行：participant 别名 as "显示名称"
                                fixed_line = f"participant {alias} as {display_name}"
                                fixed_lines.append(fixed_line)
                                continue
                
                # 没有 'as' 的情况，直接保留（可能是 participant 名称）
                fixed_lines.append(original_line)
                continue
            
            # 处理 actor 定义（类似 participant）
            if line_stripped.startswith('actor '):
                if ' as ' in line_stripped:
                    as_count = line_stripped.count(' as ')
                    if as_count > 1:
                        last_as_index = line_stripped.rfind(' as ')
                        left_part = line_stripped[:last_as_index].strip()
                        right_part = line_stripped[last_as_index + 4:].strip()
                        actor_match = re.match(r'actor\s+(.+)', left_part)
                        if actor_match:
                            alias_part = actor_match.group(1).strip()
                            alias_words = [w.strip() for w in alias_part.split(' as ')]
                            alias = ''.join(alias_words)
                            display_name = right_part.strip('"\'')
                            if self._has_chinese(display_name) or ' ' in display_name:
                                display_name = f'"{display_name}"'
                            fixed_line = f"actor {alias} as {display_name}"
                            fixed_lines.append(fixed_line)
                            continue
                    else:
                        parts = line_stripped.split(' as ', 1)
                        if len(parts) == 2:
                            left_part = parts[0].strip()
                            right_part = parts[1].strip()
                            actor_match = re.match(r'actor\s+(.+)', left_part)
                            if actor_match:
                                alias = actor_match.group(1).strip().strip('"\'')
                                display_name = right_part.strip().strip('"\'')
                                if self._has_chinese(display_name) or ' ' in display_name:
                                    display_name = f'"{display_name}"'
                                fixed_line = f"actor {alias} as {display_name}"
                                fixed_lines.append(fixed_line)
                                continue
            
            fixed_lines.append(original_line)
        
        return '\n'.join(fixed_lines)

