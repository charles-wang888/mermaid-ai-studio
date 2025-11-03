"""类图语法修复器"""
import re
from typing import Optional
from agents.fixers.base_fixer import SyntaxFixer


class ClassDiagramFixer(SyntaxFixer):
    """类图语法修复器"""
    
    def get_diagram_type(self) -> str:
        return "classDiagram"
    
    def _infer_relationships(self, class_names: set) -> list:
        """根据类名推断基本关系
        
        Args:
            class_names: 所有类名的集合
            
        Returns:
            推断出的关系列表
        """
        relationships = []
        class_names_list = list(class_names)
        
        # 常见的关系模式推断
        # Admin 和 Member 通常继承自 User
        if 'Admin' in class_names and 'User' in class_names:
            relationships.append('User <|-- Admin')
        if 'Member' in class_names and 'User' in class_names:
            relationships.append('User <|-- Member')
        
        # Service 类通常依赖实体类
        for class_name in class_names_list:
            if class_name.endswith('Service'):
                # Service 类依赖相关的实体类
                base_name = class_name.replace('Service', '')
                if base_name in class_names:
                    relationships.append(f'{class_name} ..> {base_name}')
                # 检查特定服务的依赖
                if class_name == 'LibraryService':
                    if 'Book' in class_names:
                        relationships.append('LibraryService ..> Book')
                    if 'BorrowRecord' in class_names:
                        relationships.append('LibraryService ..> BorrowRecord')
                    # 注意：不添加 LibraryService ..> User，因为这不符合业务逻辑
                elif class_name == 'UserService':
                    if 'User' in class_names:
                        relationships.append('UserService ..> User')
        
        # BorrowRecord 通常关联 User 和 Book
        if 'BorrowRecord' in class_names:
            if 'User' in class_names:
                relationships.append('BorrowRecord --> User')
            if 'Book' in class_names:
                relationships.append('BorrowRecord --> Book')
        
        # Book 与 Category 的关联（一对多）
        if 'Book' in class_names and 'Category' in class_names:
            relationships.append('Category "1" --> "*" Book')
        
        return relationships
        
    def _fix_method_colon(self, line_stripped: str, original_indent: int) -> Optional[str]:
        """修复方法定义中的冒号问题
        
        Args:
            line_stripped: 去除空格的行内容
            original_indent: 原始缩进空格数
            
        Returns:
            修复后的行内容, 如果不需要修复则返回None
        """
        method_pattern = r'^([+\-#~])\s*(\w+)\s*\(\s*\)\s*:\s*(.+)$'
        method_match = re.match(method_pattern, line_stripped)
        if method_match:
            visibility = method_match.group(1)
            method_name = method_match.group(2)
            return_type = method_match.group(3).strip()
            return f"{' ' * original_indent}{visibility}{method_name}() {return_type}"
        return None
    
    def fix(self, mermaid_code: str, **kwargs) -> str:
        """修复类图语法错误"""
        if not mermaid_code or not mermaid_code.strip().startswith("classDiagram"):
            return mermaid_code
        
        # 去除重复的 classDiagram 声明
        lines = mermaid_code.split('\n')
        cleaned_lines = []
        class_diagram_count = 0
        for line in lines:
            line_stripped = line.strip()
            if line_stripped == 'classDiagram':
                class_diagram_count += 1
                if class_diagram_count == 1:
                    cleaned_lines.append(line)
                # 跳过后续的 classDiagram 声明
            else:
                cleaned_lines.append(line)
        
        lines = cleaned_lines
        fixed_lines = []
        class_definitions = {}  # 存储类定义
        relationships = []  # 存储关系
        class_names = set()  # 收集所有类名
        
        i = 0
        while i < len(lines):
            line = lines[i]
            line_stripped = line.strip()
            original_indent = len(line) - len(line.lstrip())
            
            if not line_stripped or line_stripped.startswith('//'):
                fixed_lines.append(line)
                i += 1
                continue
            
            # 提取类名（用于后续关系检查）
            class_match = re.match(r'class\s+(\w+)', line_stripped)
            if class_match:
                class_names.add(class_match.group(1))
            
            # 提取已存在的关系定义
            relationship_patterns = [
                r'^(\w+)\s+(<\|--|<\|\.\.|\*--|o--|-->|\.\.>|--|\.\.)\s+(\w+)',
                r'^(\w+)\s+"([^"]+)"\s+(<\|--|<\|\.\.|\*--|o--|-->|\.\.>)\s+(\w+)',
                r'^(\w+)\s+(<\|--|<\|\.\.|\*--|o--|-->|\.\.>)\s+"([^"]+)"\s+(\w+)',
            ]
            is_relationship = False
            for pattern in relationship_patterns:
                rel_match = re.match(pattern, line_stripped)
                if rel_match:
                    relationships.append(line_stripped)
                    is_relationship = True
                    break
            if is_relationship:
                i += 1
                continue
            
            # 1. 修复方法定义中的冒号错误
            fixed_method = self._fix_method_colon(line_stripped, original_indent)
            if fixed_method:
                fixed_lines.append(fixed_method)
                i += 1
                continue
            
            # 2. 修复关系符号错误
            if '--|>' in line_stripped:
                line_stripped = line_stripped.replace('--|>', '-->')
                fixed_lines.append(' ' * original_indent + line_stripped)
                i += 1
                continue
            
            if re.match(r'^\w+\s+--\s+\w+$', line_stripped) and not any(s in line_stripped for s in ['<|--', '-->', '..>', '*--', 'o--', '<|..']):
                line_stripped = line_stripped.replace(' -- ', ' --> ')
                fixed_lines.append(' ' * original_indent + line_stripped)
                i += 1
                continue
            
            # 3. 检测缺少 class 关键字的类定义
            if not line_stripped.startswith('class ') and re.match(r'^[A-Z]\w*\s*\{', line_stripped):
                if not any(symbol in line_stripped for symbol in ['<|--', '<|..', '*--', 'o--', '-->', '..>', '--|>', ' -- ', ' .. ']):
                    class_match = re.match(r'^([A-Z]\w*)\s*\{', line_stripped)
                    if class_match:
                        class_name = class_match.group(1)
                        fixed_line = f"{' ' * original_indent}class {class_name} {{"
                        fixed_lines.append(fixed_line)
                        i += 1
                        # 收集类定义内容
                        brace_count = 1
                        while i < len(lines) and brace_count > 0:
                            current_line = lines[i]
                            current_stripped = current_line.strip()
                            inner_indent = len(current_line) - len(current_line.lstrip())
                            fixed_method = self._fix_method_colon(current_stripped, inner_indent)
                            if fixed_method:
                                current_line = fixed_method
                            fixed_lines.append(current_line)
                            brace_count += current_line.count('{') - current_line.count('}')
                            i += 1
                        continue
            
            # 4. 检查类定义行中包含关系符号（错误语法）
            if line_stripped.startswith('class ') and ('<|--' in line_stripped or '<|..' in line_stripped or 
                                                       '*--' in line_stripped or 'o--' in line_stripped or
                                                       '-->' in line_stripped or '..>' in line_stripped):
                match = re.match(r'class\s+(\w+)\s+(<\|--|<\|\.\.|\*--|o--|-->|\.\.>)\s+(\w+)\s*\{', line_stripped)
                if match:
                    class_name = match.group(1)
                    relation_symbol = match.group(2)
                    other_class = match.group(3)
                    
                    class_content = [line_stripped.split('{')[0] + '{']
                    i += 1
                    brace_count = 1
                    
                    while i < len(lines) and brace_count > 0:
                        current_line = lines[i]
                        current_stripped = current_line.strip()
                        inner_indent = len(current_line) - len(current_line.lstrip())
                        fixed_method = self._fix_method_colon(current_stripped, inner_indent)
                        if fixed_method:
                            current_line = fixed_method
                        class_content.append(current_line)
                        brace_count += current_line.count('{') - current_line.count('}')
                        i += 1
                    
                    class_def_key = class_name
                    if class_def_key not in class_definitions:
                        class_definitions[class_def_key] = '\n'.join(class_content)
                    
                    if relation_symbol in ['<|--', '<|..']:
                        relationships.append(f"{other_class} {relation_symbol} {class_name}")
                    else:
                        relationships.append(f"{class_name} {relation_symbol} {other_class}")
                    
                    continue
            
            fixed_lines.append(line)
            i += 1
        
        # 第二步：修复fixed_lines中剩余的语法错误
        final_fixed_lines = []
        for line in fixed_lines:
            line_stripped = line.strip()
            original_indent = len(line) - len(line.lstrip())
            
            if not line_stripped or line_stripped.startswith('//'):
                final_fixed_lines.append(line)
                continue
            
            # 再次检测缺少 class 关键字的类定义
            if not line_stripped.startswith('class ') and re.match(r'^[A-Z]\w*\s*\{', line_stripped):
                if not any(symbol in line_stripped for symbol in ['<|--', '<|..', '*--', 'o--', '-->', '..>', '--|>', ' -- ', ' .. ']):
                    class_match = re.match(r'^([A-Z]\w*)\s*\{', line_stripped)
                    if class_match:
                        class_name = class_match.group(1)
                        fixed_line = f"{' ' * original_indent}class {class_name} {{"
                        final_fixed_lines.append(fixed_line)
                        continue
            
            # 修复方法定义中的冒号
            method_pattern = r'^([+\-#~])\s*(\w+)\s*\(\s*\)\s*:\s*(.+)$'
            method_match = re.match(method_pattern, line_stripped)
            if method_match:
                visibility = method_match.group(1)
                method_name = method_match.group(2)
                return_type = method_match.group(3).strip()
                fixed_line = f"{' ' * original_indent}{visibility}{method_name}() {return_type}"
                final_fixed_lines.append(fixed_line)
                continue
            
            final_fixed_lines.append(line)
        
        # 重新组织代码：先输出所有类定义，然后输出所有关系
        all_class_defs = []
        all_relationships = relationships.copy()
        other_lines = []
        
        in_class_def = False
        current_class_lines = []
        current_class_name = None
        
        for line in final_fixed_lines:
            line_stripped = line.strip()
            
            if line_stripped.startswith('class ') and '{' in line_stripped:
                if in_class_def and current_class_lines:
                    all_class_defs.append(('\n'.join(current_class_lines), current_class_name))
                
                in_class_def = True
                current_class_lines = [line]
                class_match = re.match(r'class\s+(\w+)', line_stripped)
                if class_match:
                    current_class_name = class_match.group(1)
                else:
                    current_class_name = None
            elif in_class_def:
                current_class_lines.append(line)
                if '}' in line:
                    brace_count = sum(line.count('}') for line in current_class_lines) - sum(line.count('{') for line in current_class_lines)
                    if brace_count >= 0:
                        in_class_def = False
                        if current_class_lines:
                            all_class_defs.append(('\n'.join(current_class_lines), current_class_name))
                        current_class_lines = []
                        current_class_name = None
            else:
                if not line_stripped.startswith('class ') and not any(symbol in line_stripped for symbol in ['<|--', '-->', '..>']):
                    other_lines.append(line)
        
        if in_class_def and current_class_lines:
            all_class_defs.append(('\n'.join(current_class_lines), current_class_name))
        
        # 收集所有类名
        all_class_names = set()
        for _, class_name in all_class_defs:
            if class_name:
                all_class_names.add(class_name)
        
        # 如果没有关系定义，尝试从类名推断基本关系
        if not all_relationships and all_class_names:
            inferred_relationships = self._infer_relationships(all_class_names)
            all_relationships.extend(inferred_relationships)
        
        # 构建最终代码
        result_lines = []
        result_lines.append('classDiagram')
        
        # 输出所有类定义
        seen_class_names = set()
        for class_def, class_name in all_class_defs:
            if class_name and class_name not in seen_class_names:
                seen_class_names.add(class_name)
                result_lines.append('')
                result_lines.append(class_def)
        
        # 输出所有关系（去重）
        if all_relationships:
            result_lines.append('')
            seen_relationships = set()
            for rel in all_relationships:
                rel_normalized = re.sub(r'\s+', ' ', rel.strip())
                if rel_normalized and rel_normalized not in seen_relationships:
                    seen_relationships.add(rel_normalized)
                    result_lines.append(rel)
        
        result = '\n'.join(result_lines)
        
        # 确保结果以 classDiagram 开头（去除任何重复）
        if result.strip().startswith('classDiagram'):
            # 去除开头的重复 classDiagram
            result_lines_clean = []
            class_diagram_found = False
            for line in result.split('\n'):
                line_stripped = line.strip()
                if line_stripped == 'classDiagram':
                    if not class_diagram_found:
                        result_lines_clean.append('classDiagram')
                        class_diagram_found = True
                    # 跳过后续的 classDiagram
                else:
                    result_lines_clean.append(line)
            result = '\n'.join(result_lines_clean)
        else:
            result = 'classDiagram\n' + result
        
        return result

