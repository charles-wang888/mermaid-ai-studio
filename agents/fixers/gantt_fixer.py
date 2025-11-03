"""甘特图语法修复器"""
import re
from datetime import datetime
from agents.fixers.base_fixer import SyntaxFixer


class GanttFixer(SyntaxFixer):
    """甘特图语法修复器"""
    
    def get_diagram_type(self) -> str:
        return "gantt"
    
    def fix(self, mermaid_code: str, **kwargs) -> str:
        """修复甘特图语法：移除taskId，修正任务格式"""
        if not mermaid_code or not mermaid_code.strip().startswith("gantt"):
            return mermaid_code
        
        lines = mermaid_code.split('\n')
        fixed_lines = []
        
        for line in lines:
            original_line = line
            line_stripped = line.strip()
            if not line_stripped:
                fixed_lines.append("")
                continue
            
            # 保留gantt、dateFormat、title、section行
            line_lower = line_stripped.lower()
            if line_lower.startswith('gantt') or line_lower.startswith('dateformat') or \
               line_lower.startswith('title') or line_lower.startswith('section'):
                fixed_lines.append(line_stripped)
                continue
            
            # 修复任务行：移除taskId
            task_match = re.match(r'^(.+?)\s*:\s*([^,]+?)\s*,\s*(\d+)\s*,\s*(\d{4}-\d{2}-\d{2})\s*,\s*(\d{4}-\d{2}-\d{2})$', line_stripped)
            if task_match:
                task_name = task_match.group(1).strip()
                status = task_match.group(2).strip()
                start_date = task_match.group(4).strip()
                end_date = task_match.group(5).strip()
                
                # 计算持续天数
                try:
                    start = datetime.strptime(start_date, '%Y-%m-%d')
                    end = datetime.strptime(end_date, '%Y-%m-%d')
                    duration = (end - start).days + 1
                    indent = len(original_line) - len(original_line.lstrip())
                    fixed_lines.append(" " * indent + f"{task_name} :{status}, {start_date}, {duration}d")
                except ValueError:
                    fixed_lines.append(original_line)
                continue
            
            # 检查是否是里程碑格式
            milestone_match = re.match(r'^(.+?)\s*:\s*milestone\s*,\s*(\d+)\s*,\s*(\d{4}-\d{2}-\d{2})$', line_stripped, re.IGNORECASE)
            if milestone_match:
                milestone_name = milestone_match.group(1).strip()
                milestone_date = milestone_match.group(3).strip()
                indent = len(original_line) - len(original_line.lstrip())
                fixed_lines.append(" " * indent + f"{milestone_name} :milestone, {milestone_date}, 0d")
                continue
            
            fixed_lines.append(original_line)
        
        return '\n'.join(fixed_lines)

