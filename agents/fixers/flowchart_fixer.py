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
        
        # 先优化布局
        mermaid_code = self._optimize_layout(mermaid_code)
        
        # 修复subgraph连接问题
        mermaid_code = self._fix_subgraph_connections(mermaid_code)
        
        return mermaid_code
    
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

