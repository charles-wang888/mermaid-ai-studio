"""象限图语法修复器"""
import re
from agents.fixers.base_fixer import SyntaxFixer


class QuadrantChartFixer(SyntaxFixer):
    """象限图语法修复器"""
    
    def get_diagram_type(self) -> str:
        return "quadrantChart"
    
    def fix(self, mermaid_code: str, **kwargs) -> str:
        """修复象限图语法错误（主要是中文标签引号）"""
        if not mermaid_code or not mermaid_code.strip().startswith("quadrantChart"):
            return mermaid_code
        
        lines = mermaid_code.split('\n')
        fixed_lines = []
        
        def has_chinese(text: str) -> bool:
            return any('\u4e00' <= char <= '\u9fff' for char in text)
        
        def quote_if_needed(text: str) -> str:
            text = text.strip()
            if not text:
                return text
            if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
                return text
            if has_chinese(text) or ' ' in text:
                return f'"{text}"'
            return text
        
        for line in lines:
            line_stripped = line.strip()
            
            if not line_stripped:
                fixed_lines.append(line)
                continue
            
            # 修复 x-axis 和 y-axis 行的中文标签
            if line_stripped.startswith('x-axis') or line_stripped.startswith('y-axis'):
                if '-->' in line_stripped:
                    axis_content = line_stripped.split(None, 1)[1] if ' ' in line_stripped else ''
                    if axis_content and '-->' in axis_content:
                        parts = axis_content.split('-->')
                        if len(parts) == 2:
                            left_label = parts[0].strip().strip('"\'')
                            right_label = parts[1].strip().strip('"\'')
                            left_quoted = quote_if_needed(left_label)
                            right_quoted = quote_if_needed(right_label)
                            axis_prefix = 'x-axis' if line_stripped.startswith('x-axis') else 'y-axis'
                            fixed_lines.append(f"{axis_prefix} {left_quoted} --> {right_quoted}")
                            continue
            
            # 修复 quadrant-* 行的中文标签
            if re.match(r'^quadrant-\d+', line_stripped):
                parts = line_stripped.split(None, 1)
                if len(parts) == 2:
                    quadrant_prefix = parts[0]
                    quadrant_text = parts[1].strip().strip('"\'')
                    quadrant_quoted = quote_if_needed(quadrant_text)
                    fixed_lines.append(f"{quadrant_prefix} {quadrant_quoted}")
                    continue
            
            # 修复数据点的坐标格式和计算
            # 匹配格式：名称: [x, y] 或 名称 : [x, y]
            point_pattern = r'^([^:]+?)\s*:\s*\[([^\]]+)\]'
            point_match = re.match(point_pattern, line_stripped)
            if point_match:
                point_name = point_match.group(1).strip()
                coords_str = point_match.group(2).strip()
                
                try:
                    # 解析坐标
                    coords = [float(x.strip()) for x in coords_str.split(',')]
                    if len(coords) == 2:
                        x, y = coords
                        
                        # 检查坐标是否已经归一化（在0-1范围内）
                        # 如果 x > 1 或 y > 1，可能是原始值，需要转换
                        
                        # X轴：市场增长率 0%-50% -> 0-1
                        # 如果 x > 1，可能是百分比值（0-50），需要除以50
                        if x > 1:
                            x = x / 50.0
                        
                        # Y轴：相对市场份额 0-2.0 -> 0-1
                        # 如果 y > 1，可能是原始值（0-2.0），需要除以2.0
                        if y > 1:
                            y = y / 2.0
                        
                        # 确保坐标在 0-1 范围内
                        x = max(0.0, min(1.0, x))
                        y = max(0.0, min(1.0, y))
                        
                        fixed_lines.append(f"{point_name}: [{x:.2f}, {y:.2f}]")
                        continue
                except (ValueError, IndexError):
                    # 如果解析失败，保持原样
                    pass
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)

