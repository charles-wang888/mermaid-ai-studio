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
        
        # 第一步：扫描所有消息行，收集实际使用的 participant 名称
        used_participants = set()
        participant_definitions = {}  # alias -> (line_index, display_name)
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # 提取 participant 定义
            if line_stripped.startswith('participant ') or line_stripped.startswith('actor '):
                participant_definitions[i] = line_stripped
            
            # 提取消息中使用的 participant（箭头前或后）
            # 格式如：A->>B, A-->>B, A-.->B, Note over A,B, activate A, deactivate A
            arrow_patterns = [
                r'(\w+)\s*[-=]>>',  # A->>, A-->>, A=>>>
                r'[-=]>>\s*(\w+)',  # ->>A, -->>A
                r'(\w+)\s*[-.]->',  # A->, A-.->, A-->
                r'[-.]->>\s*(\w+)',  # ->A, -.->A
                r'Note\s+over\s+([\w,]+)',  # Note over A,B
                r'Note\s+(?:left|right)\s+of\s+(\w+)',  # Note right of A
                r'activate\s+(\w+)',  # activate A
                r'deactivate\s+(\w+)',  # deactivate A
            ]
            
            for pattern in arrow_patterns:
                matches = re.findall(pattern, line_stripped)
                for match in matches:
                    if isinstance(match, str):
                        # 处理逗号分隔的多个 participant
                        for p in match.split(','):
                            p = p.strip()
                            if p:
                                used_participants.add(p)
                    elif isinstance(match, tuple):
                        for p in match:
                            if p:
                                used_participants.add(p)
        
        # 第二步：修复 participant 定义并建立别名映射
        alias_mapping = {}  # old_alias -> correct_alias
        fixed_lines = []
        participant_index_map = {}  # line_index -> (correct_alias, display_name)
        
        for i, line in enumerate(lines):
            original_line = line
            line_stripped = line.strip()
            
            if not line_stripped:
                fixed_lines.append("")
                continue
            
            # 修复 participant 定义错误
            if line_stripped.startswith('participant ') or line_stripped.startswith('actor '):
                is_actor = line_stripped.startswith('actor ')
                prefix = 'actor ' if is_actor else 'participant '
                
                if ' as ' in line_stripped:
                    # 计算 'as' 的数量
                    as_count = line_stripped.count(' as ')
                    
                    if as_count > 1:
                        # 有多个 'as'，说明格式错误
                        # 例如：participant LogSt as h as 数据采集组件
                        last_as_index = line_stripped.rfind(' as ')
                        left_part = line_stripped[:last_as_index].strip()
                        right_part = line_stripped[last_as_index + 4:].strip()
                        
                        # 提取别名部分
                        prefix_match = re.match(rf'{prefix}\s+(.+)', left_part)
                        if prefix_match:
                            alias_part = prefix_match.group(1).strip()
                            # 合并所有 as 分割的部分作为候选别名
                            alias_words = [w.strip() for w in alias_part.split(' as ')]
                            candidate_alias = ''.join(alias_words)
                            
                            display_name = right_part.strip('"\'')
                            
                            # 尝试从已使用的 participant 中找到匹配的完整名称
                            # 例如：candidate_alias 是 "LogSth"（由 "LogSt" + "h" 合并），但消息中使用的是 "LogStash"
                            # 又如：candidate_alias 是 "ElticSearch"（由 "El" + "ticSearch" 合并），但消息中使用的是 "ElasticSearch"
                            correct_alias = candidate_alias
                            best_match = None
                            best_score = 0
                            
                            # 检查合并后的别名是否已经是正确的（可能刚好匹配）
                            if candidate_alias in used_participants:
                                correct_alias = candidate_alias
                            else:
                                # 需要找到匹配的完整名称
                                candidate_lower = candidate_alias.lower()
                                
                                for used_p in used_participants:
                                    used_lower = used_p.lower()
                                    
                                    # 策略1：计算最长公共前缀（最优先）
                                    # 例如：LogSth -> LogStash（公共前缀是 LogSt，5个字符）
                                    common_prefix_len = 0
                                    min_len = min(len(candidate_lower), len(used_lower))
                                    for i in range(min_len):
                                        if candidate_lower[i] == used_lower[i]:
                                            common_prefix_len += 1
                                        else:
                                            break
                                    
                                    # 如果公共前缀足够长（至少3个字符），且候选别名看起来是已用 participant 的一部分
                                    if common_prefix_len >= 3:
                                        # 如果长度差异在合理范围内（≤5），且前缀匹配度高
                                        if abs(len(used_p) - len(candidate_alias)) <= 5:
                                            score = common_prefix_len / max(len(candidate_lower), len(used_lower))
                                            if score > best_score:
                                                best_score = score
                                                best_match = used_p
                                    
                                    # 策略2：如果已用 participant 的前几个字符与候选别名匹配
                                    # 例如：LogSth 的开头 "LogSt" 与 LogStash 的开头匹配
                                    elif len(candidate_lower) >= 4:
                                        # 检查候选别名是否是已用 participant 的前缀（允许一些差异）
                                        prefix_len = min(4, len(candidate_lower), len(used_lower))
                                        if candidate_lower[:prefix_len] == used_lower[:prefix_len]:
                                            # 检查后续字符是否相似
                                            if abs(len(used_p) - len(candidate_alias)) <= 3:
                                                score = prefix_len / max(len(candidate_lower), len(used_lower))
                                                if score > best_score:
                                                    best_score = score
                                                    best_match = used_p
                                    
                                    # 策略3：字符相似度匹配（针对拆分的情况）
                                    # 例如：ElticSearch 与 ElasticSearch
                                    if abs(len(used_p) - len(candidate_alias)) <= 5:
                                        # 计算字符级别的相似度
                                        common_prefix = 0
                                        min_len = min(len(candidate_lower), len(used_lower))
                                        for i in range(min_len):
                                            if candidate_lower[i] == used_lower[i]:
                                                common_prefix += 1
                                            else:
                                                break
                                        
                                        # 如果前缀匹配度足够高
                                        if common_prefix >= min(4, len(candidate_lower) * 0.6):
                                            score = common_prefix / max(len(candidate_lower), len(used_lower))
                                            if score > best_score:
                                                best_score = score
                                                best_match = used_p
                                
                                # 如果找到了良好的匹配（相似度 > 0.4），使用它
                                if best_match and best_score > 0.4:
                                    correct_alias = best_match
                                    alias_mapping[candidate_alias] = correct_alias
                            
                            # 如果显示名称包含中文或空格，添加引号
                            if self._has_chinese(display_name) or ' ' in display_name:
                                display_name = f'"{display_name}"'
                            
                            fixed_line = f"{prefix}{correct_alias} as {display_name}"
                            fixed_lines.append(fixed_line)
                            participant_index_map[i] = (correct_alias, display_name)
                            continue
                    else:
                        # 只有一个 'as'，正常处理
                        parts = line_stripped.split(' as ', 1)
                        if len(parts) == 2:
                            left_part = parts[0].strip()
                            right_part = parts[1].strip()
                            
                            prefix_match = re.match(rf'{prefix}\s+(.+)', left_part)
                            if prefix_match:
                                alias = prefix_match.group(1).strip().strip('"\'')
                                display_name = right_part.strip().strip('"\'')
                                
                                # 检查别名是否在已使用的 participant 中
                                # 如果不在，尝试找到匹配的
                                if alias not in used_participants:
                                    for used_p in used_participants:
                                        if alias.lower() in used_p.lower() or used_p.lower().startswith(alias.lower()):
                                            alias_mapping[alias] = used_p
                                            alias = used_p
                                            break
                                
                                # 如果显示名称包含中文或空格，添加引号
                                if self._has_chinese(display_name) or ' ' in display_name:
                                    display_name = f'"{display_name}"'
                                
                                fixed_line = f"{prefix}{alias} as {display_name}"
                                fixed_lines.append(fixed_line)
                                participant_index_map[i] = (alias, display_name)
                                continue
                
                # 没有 'as' 的情况，直接保留
                fixed_lines.append(original_line)
                continue
            
            # 移除不完整的箭头行（如 Kibana---> 没有目标）
            if re.match(r'^\s*\w+\s*[-=.]*>\s*$', line_stripped):
                # 不完整的箭头，跳过
                continue
            
            # 修复消息中使用的 participant 别名（根据映射更新）
            fixed_line = original_line
            for old_alias, correct_alias in alias_mapping.items():
                # 使用词边界匹配，避免部分匹配
                pattern = r'\b' + re.escape(old_alias) + r'\b'
                fixed_line = re.sub(pattern, correct_alias, fixed_line)
            
            fixed_lines.append(fixed_line)
        
        return '\n'.join(fixed_lines)

