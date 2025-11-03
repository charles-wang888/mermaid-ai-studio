"""甘特图语法修复器"""
import re
from datetime import datetime
from agents.fixers.base_fixer import SyntaxFixer


class GanttFixer(SyntaxFixer):
    """甘特图语法修复器"""
    
    def get_diagram_type(self) -> str:
        return "gantt"
    
    def _has_chinese(self, text: str) -> bool:
        """检查文本是否包含中文字符"""
        return any('\u4e00' <= char <= '\u9fff' for char in text)
    
    def _quote_if_needed(self, text: str) -> str:
        """如果文本包含中文或空格，则添加引号"""
        text = text.strip()
        if not text:
            return text
        # 如果已经有引号，直接返回
        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            return text
        # 如果包含空格，添加引号（不要为中文和冒号添加引号，因为这会导致甘特图解析错误）
        if ' ' in text:
            return f'"{text}"'
        return text
    
    def fix(self, mermaid_code: str, **kwargs) -> str:
        """修复甘特图语法：移除taskId，修正任务格式，为中文添加引号"""
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
            
            original_indent = len(original_line) - len(original_line.lstrip())
            indent = " " * original_indent
            
            # 保留gantt、dateFormat行
            line_lower = line_stripped.lower()
            if line_lower.startswith('gantt') or line_lower.startswith('dateformat'):
                fixed_lines.append(line_stripped)
                continue
            
            # 处理 title 行：为中文标题添加引号
            if line_lower.startswith('title'):
                title_match = re.match(r'^title\s+(.+)$', line_stripped, re.IGNORECASE)
                if title_match:
                    title_content = title_match.group(1).strip()
                    quoted_title = self._quote_if_needed(title_content)
                    fixed_lines.append(f"title {quoted_title}")
                else:
                    fixed_lines.append(line_stripped)
                continue
            
            # 处理 section 行：为中文 section 名称添加引号
            if line_lower.startswith('section'):
                section_match = re.match(r'^section\s+(.+)$', line_stripped, re.IGNORECASE)
                if section_match:
                    section_content = section_match.group(1).strip()
                    quoted_section = self._quote_if_needed(section_content)
                    fixed_lines.append(f"{indent}section {quoted_section}")
                else:
                    fixed_lines.append(line_stripped)
                continue
            
            # 修复任务行：移除taskId，并为中文任务名称添加引号
            # 匹配格式：任务名称 :状态, taskId, 开始日期, 结束日期
            task_match = re.match(r'^(.+?)\s*:\s*([^,]+?)\s*,\s*(\d+)\s*,\s*(\d{4}-\d{2}-\d{2})\s*,\s*(\d{4}-\d{2}-\d{2})$', line_stripped)
            if task_match:
                task_name = task_match.group(1).strip()
                status = task_match.group(2).strip()
                start_date = task_match.group(4).strip()
                end_date = task_match.group(5).strip()
                
                # 为任务名称添加引号（如果包含中文或空格）
                quoted_task_name = self._quote_if_needed(task_name)
                
                # 计算持续天数
                try:
                    start = datetime.strptime(start_date, '%Y-%m-%d')
                    end = datetime.strptime(end_date, '%Y-%m-%d')
                    duration = (end - start).days + 1
                    fixed_lines.append(f"{indent}{quoted_task_name} :{status}, {start_date}, {duration}d")
                except ValueError:
                    fixed_lines.append(original_line)
                continue
            
            # 修复任务行：格式 任务名称 :状态, 开始日期, 持续天数
            # 为中文任务名称添加引号
            task_match2 = re.match(r'^(.+?)\s*:\s*([^,]+?)\s*,\s*(\d{4}-\d{2}-\d{2})\s*,\s*(\d+d)$', line_stripped)
            if task_match2:
                task_name = task_match2.group(1).strip()
                status = task_match2.group(2).strip()
                start_date = task_match2.group(3).strip()
                duration = task_match2.group(4).strip()
                
                # 为任务名称添加引号（如果包含中文或空格）
                quoted_task_name = self._quote_if_needed(task_name)
                fixed_lines.append(f"{indent}{quoted_task_name} :{status}, {start_date}, {duration}")
                continue
            
            # 检查是否是里程碑格式：任务名称 :milestone, taskId, 日期
            milestone_match = re.match(r'^(.+?)\s*:\s*milestone\s*,\s*(\d+)\s*,\s*(\d{4}-\d{2}-\d{2})$', line_stripped, re.IGNORECASE)
            if milestone_match:
                milestone_name = milestone_match.group(1).strip()
                milestone_date = milestone_match.group(3).strip()
                
                # 为里程碑名称添加引号（如果包含中文或空格）
                quoted_milestone_name = self._quote_if_needed(milestone_name)
                fixed_lines.append(f"{indent}{quoted_milestone_name} :milestone, {milestone_date}, 0d")
                continue
            
            # 检查是否是里程碑格式：任务名称 :milestone, 日期, 0d
            milestone_match2 = re.match(r'^(.+?)\s*:\s*milestone\s*,\s*(\d{4}-\d{2}-\d{2})\s*,\s*0d$', line_stripped, re.IGNORECASE)
            if milestone_match2:
                milestone_name = milestone_match2.group(1).strip()
                milestone_date = milestone_match2.group(2).strip()
                
                # 为里程碑名称添加引号（如果包含中文或空格）
                quoted_milestone_name = self._quote_if_needed(milestone_name)
                fixed_lines.append(f"{indent}{quoted_milestone_name} :milestone, {milestone_date}, 0d")
                continue
            
            fixed_lines.append(original_line)
        
        return '\n'.join(fixed_lines)

