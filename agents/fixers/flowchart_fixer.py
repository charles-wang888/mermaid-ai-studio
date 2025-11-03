"""流程图语法修复器"""
import re
import logging
from agents.fixers.base_fixer import SyntaxFixer

logger = logging.getLogger(__name__)


class FlowchartFixer(SyntaxFixer):
    """流程图语法修复器"""
    
    def get_diagram_type(self) -> str:
        return "flowchart"
    
    def fix(self, mermaid_code: str, **kwargs) -> str:
        """修复流程图语法（包括布局优化）"""
        if not mermaid_code or not mermaid_code.strip().startswith("flowchart"):
            return mermaid_code
        
        # 修复一个箭头指向多个节点的问题（如 A --> B, C）
        mermaid_code = self._fix_multiple_targets(mermaid_code)
        
        # 修复未定义的节点引用（检测连接中使用的节点，如果未定义则添加定义）
        mermaid_code = self._fix_undefined_nodes(mermaid_code)
        
        # 先优化布局
        mermaid_code = self._optimize_layout(mermaid_code)
        
        # 修复subgraph连接问题
        mermaid_code = self._fix_subgraph_connections(mermaid_code)
        
        return mermaid_code
    
    def _fix_undefined_nodes(self, mermaid_code: str) -> str:
        """修复未定义的节点引用
        
        检测连接语句中引用的节点，如果节点未定义，尝试从连接语句中提取节点信息并添加定义
        例如：V((首页)) 在连接中使用，但没有节点定义，需要添加 V((首页))
        """
        lines = mermaid_code.split('\n')
        
        # 收集所有已定义的节点ID
        defined_nodes = set()
        # 收集连接中使用的节点（包括可能的定义信息）
        referenced_nodes = {}  # node_id -> (line, possible_definition)
        
        # 第一遍：收集已定义的节点和引用的节点
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            if not line_stripped or line_stripped.startswith('//') or line_stripped.startswith('subgraph') or line_stripped == 'end':
                continue
            
            # 检查是否是节点定义行（如 A["标签"] 或 A(标签) 或 A{"标签"} 或 A((标签))）
            node_def_patterns = [
                r'^(\w+)\[',  # A["标签"]
                r'^(\w+)\(',  # A(标签) 或 A((标签)) 或 A{"标签"}
                r'^(\w+)\{',  # A{"标签"}
            ]
            for pattern in node_def_patterns:
                match = re.match(pattern, line_stripped)
                if match:
                    node_id = match.group(1)
                    defined_nodes.add(node_id)
                    break
            
            # 检查是否是连接语句，提取节点ID
            if '-->' in line_stripped:
                # 提取源节点和目标节点
                arrow_patterns = [
                    r'(.+?)\s*-->\s*\|([^|]+)\|\s*(.+)',  # A -->|label| B
                    r'(.+?)\s*-->\s*(.+)',  # A --> B
                ]
                
                for pattern in arrow_patterns:
                    match = re.match(pattern, line_stripped)
                    if match:
                        if len(match.groups()) == 3:
                            source = match.group(1).strip()
                            target = match.group(3).strip()
                        else:
                            source = match.group(1).strip()
                            target = match.group(2).strip()
                        
                        # 检查源节点和目标节点
                        for node_str in [source, target]:
                            node_str_clean = node_str.strip()
                            # 提取节点ID（可能包含格式如 V((首页))）
                            # 匹配格式：V((首页)) 或 W{"标签"} 或 A["标签"] 或 简单的 A
                            node_id_match = re.match(r'^(\w+)', node_str_clean)
                            if node_id_match:
                                node_id = node_id_match.group(1)
                                if node_id not in defined_nodes:
                                    # 检查节点字符串是否包含格式信息（括号、方括号等）
                                    if re.search(r'[\(\[\{].*[\)\]\}]', node_str_clean):
                                        # 包含格式信息（如 V((首页))），保存完整字符串用于创建定义
                                        if node_id not in referenced_nodes:
                                            referenced_nodes[node_id] = (i, node_str_clean)
                                    else:
                                        # 只是节点ID，保存基本信息，稍后创建简单定义
                                        if node_id not in referenced_nodes:
                                            referenced_nodes[node_id] = (i, None)
                        break
        
        # 如果没有未定义的节点，直接返回
        if not referenced_nodes:
            return mermaid_code
        
        # 第二遍：添加缺失的节点定义
        # 在第一个连接语句之前插入节点定义
        fixed_lines = []
        first_connection_found = False
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # 在第一个连接语句之前插入缺失的节点定义
            if not first_connection_found and '-->' in line_stripped:
                first_connection_found = True
                
                # 插入缺失的节点定义
                for node_id, (ref_line, node_str) in referenced_nodes.items():
                    if node_id not in defined_nodes:
                        if node_str and any(char in node_str for char in ['(', '[', '{']):
                            # 使用原始格式创建节点定义
                            fixed_lines.append(f"    {node_str}")
                        else:
                            # 创建简单的节点定义
                            fixed_lines.append(f"    {node_id}[\"{node_id}\"]")
                        defined_nodes.add(node_id)
                
                fixed_lines.append("")  # 添加空行分隔
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _fix_multiple_targets(self, mermaid_code: str) -> str:
        """修复一个箭头指向多个节点的问题
        
        将格式：A -->|label| B, C 或 A --> B, C
        修复为：A -->|label| B
              A -->|label| C
        或：
              A --> B
              A --> C
        """
        lines = mermaid_code.split('\n')
        fixed_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            original_indent = len(line) - len(line.lstrip())
            
            if not line_stripped:
                fixed_lines.append(line)
                continue
            
            # 先检查是否是带标签的箭头（包含 |...|）
            if '|' in line_stripped and '-->' in line_stripped:
                # 匹配带标签的箭头：A -->|label| B, C
                pattern = r'(.+?)\s*-->\s*\|([^|]+)\|\s*(.+?)$'
                match = re.match(pattern, line_stripped)
                if match:
                    source = match.group(1).strip()
                    label = match.group(2).strip()
                    targets = match.group(3).strip()
                    
                    # 检查目标是否包含逗号
                    if ',' in targets:
                        target_list = [t.strip() for t in targets.split(',')]
                        # 为每个目标创建单独的连接
                        for target in target_list:
                            if target:
                                fixed_lines.append(f"{' ' * original_indent}{source} -->|{label}| {target}")
                        continue
            
            # 检查不带标签的箭头，但要排除其他包含 --> 的情况
            if '-->' in line_stripped and '|' not in line_stripped:
                # 匹配不带标签的箭头：A --> B, C
                # 注意：要确保目标部分包含逗号
                parts = line_stripped.split('-->', 1)
                if len(parts) == 2:
                    source = parts[0].strip()
                    targets = parts[1].strip()
                    
                    # 检查目标是否包含逗号（且不是节点定义中的逗号）
                    if ',' in targets:
                        # 确保是连接语句，不是节点定义
                        if not any(char in source for char in ['[', '(', '{']):
                            target_list = [t.strip() for t in targets.split(',')]
                            # 为每个目标创建单独的连接
                            for target in target_list:
                                if target:
                                    fixed_lines.append(f"{' ' * original_indent}{source} --> {target}")
                            continue
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _optimize_layout(self, mermaid_code: str) -> str:
        """优化流程图布局：对于步骤很多的流程，自动转换为TD布局"""
        lines = mermaid_code.split('\n')
        first_line = lines[0].strip()
        
        # 只处理LR布局（左右布局）
        if "LR" not in first_line.upper():
            return mermaid_code
        
        # 统计节点数量
        node_ids = set()
        
        for line in lines[1:]:
            line = line.strip()
            if not line or line.startswith('//') or line.startswith('subgraph') or line == 'end':
                continue
            
            # 提取连接关系中的节点ID
            arrow_patterns = ['-->', '-.->', '---']
            for pattern in arrow_patterns:
                if pattern in line:
                    parts = re.split(r'[|:\s]+', line.split(pattern)[0].strip())
                    if parts:
                        node_id = parts[0].strip()
                        if node_id and not node_id.startswith('//'):
                            node_ids.add(node_id)
                    parts = re.split(r'[|:\s]+', line.split(pattern)[-1].strip())
                    if parts:
                        node_id = parts[0].strip()
                        if node_id and not node_id.startswith('//'):
                            node_ids.add(node_id)
            
            # 检查节点定义行
            node_def_patterns = [
                r'(\w+)\[', r'(\w+)\(', r'(\w+)\(\(', r'(\w+)\{', r'(\w+)\{\{'
            ]
            for pattern in node_def_patterns:
                match = re.search(pattern, line)
                if match:
                    node_ids.add(match.group(1))
        
        node_count = len(node_ids)
        
        # 如果节点超过8个，转换为TD布局
        if node_count > 8:
            lines[0] = lines[0].replace("LR", "TD").replace("lr", "TD")
            logger.info("检测到 %d 个节点，自动将流程图布局从LR（左右）转换为TD（上下）以获得更好的显示效果", node_count)
            return '\n'.join(lines)
        
        return mermaid_code
    
    def _fix_subgraph_connections(self, mermaid_code: str) -> str:
        """修复流程图中subgraph的节点定义和连接问题"""
        if not mermaid_code or not mermaid_code.strip().startswith("flowchart"):
            return mermaid_code
        
        lines = mermaid_code.split('\n')
        if not any('subgraph' in line.lower() for line in lines):
            return mermaid_code
        
        # 修复空的subgraph
        try:
            mermaid_code = self._fix_empty_subgraphs(mermaid_code)
        except Exception as e:
            logger.exception("Failed to fix empty subgraphs for mermaid_code: %s", mermaid_code, exc_info=e)
        
        return mermaid_code
    
    def _fix_empty_subgraphs(self, mermaid_code: str) -> str:
        """修复空的subgraph"""
        lines = mermaid_code.split('\n')
        fixed_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            line_stripped = line.strip()
            
            # 检测subgraph开始
            if line_stripped.lower().startswith('subgraph'):
                fixed_lines.append(line)
                i += 1
                
                # 检查subgraph内容
                subgraph_lines = []
                found_content = False
                
                # 跳过空行和注释
                while i < len(lines):
                    current_line = lines[i]
                    current_stripped = current_line.strip()
                    
                    # 检查是否是end
                    if current_stripped.lower() == 'end':
                        if not found_content:
                            # 空的subgraph，尝试从前一行提取节点定义
                            subgraph_line = line_stripped
                            # 尝试从subgraph行提取节点ID
                            # 格式：subgraph ID["Label"] 或 subgraph "Label"
                            node_match = re.search(r'subgraph\s+(\w+)(\[|\(|$)', subgraph_line, re.IGNORECASE)
                            if node_match:
                                node_id = node_match.group(1)
                                # 创建一个简单的节点定义
                                fixed_lines.append(f"    {node_id}[\"{node_id}\"]")
                        fixed_lines.append(current_line)
                        i += 1
                        break
                    
                    if current_stripped and not current_stripped.startswith('//'):
                        found_content = True
                    subgraph_lines.append(current_line)
                    i += 1
                else:
                    # 没有找到end，添加内容
                    fixed_lines.extend(subgraph_lines)
            else:
                fixed_lines.append(line)
                i += 1
        
        return '\n'.join(fixed_lines)

