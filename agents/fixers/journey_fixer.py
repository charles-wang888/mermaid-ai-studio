"""用户旅程图语法修复器"""
import re
from agents.fixers.base_fixer import SyntaxFixer


class JourneyFixer(SyntaxFixer):
    """用户旅程图语法修复器"""
    
    def get_diagram_type(self) -> str:
        return "journey"
    
    def fix(self, mermaid_code: str, **kwargs) -> str:
        """修复用户旅程图语法错误
        
        主要修复：
        1. 将格式从 "任务: 情感名称: 参与者, 分数" 改为 "任务: 分数: 参与者"
        2. 移除情感名称，只保留分数和参与者
        """
        if not mermaid_code or not mermaid_code.strip().startswith("journey"):
            return mermaid_code
        
        lines = mermaid_code.split('\n')
        fixed_lines = []
        
        # 情感名称到分数的映射（用于提取分数）
        emotion_keywords = ['excited', 'happy', 'sad', 'angry', 'neutral', 'disappointed', 'surprised', 'satisfied']
        
        for line in lines:
            line_stripped = line.strip()
            original_indent = len(line) - len(line.lstrip())
            
            if not line_stripped:
                fixed_lines.append("")
                continue
            
            # 保留 journey、title、section 行
            if (line_stripped.startswith('journey') or 
                line_stripped.startswith('title') or 
                line_stripped.startswith('section')):
                fixed_lines.append(line)
                continue
            
            # 修复任务行：格式应该是 "任务: 分数: 参与者"
            # 匹配错误的格式：任务: 情感名称: 参与者, 分数
            # 例如：通过朋友推荐: excited: 用户, 5
            wrong_pattern = r'^(.+?)\s*:\s*([^:]+?)\s*:\s*([^,]+?)\s*,\s*(\d+)$'
            wrong_match = re.match(wrong_pattern, line_stripped)
            if wrong_match:
                task = wrong_match.group(1).strip()
                emotion = wrong_match.group(2).strip()
                actor = wrong_match.group(3).strip()
                score = wrong_match.group(4).strip()
                
                # 确保分数在1-5范围内
                try:
                    score_int = int(score)
                    score_int = max(1, min(5, score_int))
                    score = str(score_int)
                except ValueError:
                    # 如果分数无效，使用默认值3
                    score = "3"
                
                # 正确的格式：任务: 分数: 参与者
                fixed_line = f"{' ' * original_indent}{task}: {score}: {actor}"
                fixed_lines.append(fixed_line)
                continue
            
            # 匹配正确的格式但可能有多余的空格：任务 : 分数 : 参与者
            correct_pattern = r'^(.+?)\s*:\s*(\d+)\s*:\s*(.+)$'
            correct_match = re.match(correct_pattern, line_stripped)
            if correct_match:
                task = correct_match.group(1).strip()
                score = correct_match.group(2).strip()
                actor = correct_match.group(3).strip()
                
                # 确保分数在1-5范围内
                try:
                    score_int = int(score)
                    score_int = max(1, min(5, score_int))
                    score = str(score_int)
                except ValueError:
                    score = "3"
                
                fixed_line = f"{' ' * original_indent}{task}: {score}: {actor}"
                fixed_lines.append(fixed_line)
                continue
            
            # 其他行直接保留
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)

