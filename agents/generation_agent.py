"""图生成智能体"""
import re
import os
from datetime import datetime
from typing import Dict, List
from agents.base_agent import DiagramAgentBase
from utils.mermaid_renderer import MermaidRenderer
from agents.prompts_config import (
    GENERATION_SYSTEM_PROMPT,
    GENERATION_FLOWCHART_PROMPT_TEMPLATE,
    GENERATION_SEQUENCE_DIAGRAM_PROMPT_TEMPLATE,
    GENERATION_GANTT_PROMPT_TEMPLATE,
    GENERATION_CLASS_DIAGRAM_PROMPT_TEMPLATE,
    GENERATION_STATE_DIAGRAM_PROMPT_TEMPLATE,
    GENERATION_PIE_CHART_PROMPT_TEMPLATE,
    GENERATION_QUADRANT_CHART_PROMPT_TEMPLATE,
    GENERATION_JOURNEY_PROMPT_TEMPLATE,
    GENERATION_ERROR_EXPLANATION_PROMPT_TEMPLATE,
    TYPE_SPECIFIC_NOTES_CLASS_DIAGRAM,
    TYPE_SPECIFIC_NOTES_QUADRANT_CHART,
    TYPE_SPECIFIC_NOTES_DEFAULT,
    TYPE_SPECIFIC_REQUIREMENTS_CLASS_DIAGRAM,
    TYPE_SPECIFIC_REQUIREMENTS_QUADRANT_CHART,
    TYPE_SPECIFIC_REQUIREMENTS_DEFAULT,
)
from agents.utils.text_cleaner import TextCleaner
from agents.utils.code_extractor import CodeExtractor
from agents.generators.generator_factory import DiagramGeneratorFactory
from agents.fixers.fixer_factory import SyntaxFixerFactory


class GenerationAgent(DiagramAgentBase):
    """架构图生成智能体"""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="generation_agent",
            sys_prompt=self._get_sys_prompt(),
            **kwargs
        )
        # 将自身传入MermaidRenderer，使其可以使用AI进行语法检查
        self.mermaid_renderer = MermaidRenderer(generation_agent=self)
    
    def _get_sys_prompt(self) -> str:
        return GENERATION_SYSTEM_PROMPT
    
    def generate_diagram(self, clarified_requirements: str, diagram_type: str = "flowchart") -> Dict:
        """生成架构图 - 只生成Mermaid代码并渲染为PNG"""
        # 第一步：基于需求澄清，生成完整的Mermaid格式代码
        mermaid_code = self._generate_mermaid_code(clarified_requirements, diagram_type)
        
        # 保存Mermaid代码到mmd文件
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mmd_file = os.path.join(output_dir, f"diagram_{timestamp}.mmd")
        with open(mmd_file, 'w', encoding='utf-8') as f:
            f.write(mermaid_code)
        
        # 渲染Mermaid代码为PNG（渲染前会自动进行语法检查和修复）
        png_file = os.path.join(output_dir, f"diagram_{timestamp}.png")
        try:
            # 先进行语法检查（获取详细信息）
            is_valid, error_info = self.mermaid_renderer.validate_syntax_with_details(mermaid_code)
            is_valid_after_fix = is_valid
            
            if not is_valid:
                # 尝试自动修复语法错误
                print(f"检测到语法错误，尝试自动修复...")
                original_code = mermaid_code
                
                # 使用修复器工厂尝试修复
                fixer = SyntaxFixerFactory.create(diagram_type)
                if fixer:
                    mermaid_code = fixer.fix(mermaid_code)
                    is_valid_after_fix, error_info_after = self.mermaid_renderer.validate_syntax_with_details(mermaid_code)
                    
                    # 如果还有错误且是类图，尝试高级修复
                    if not is_valid_after_fix and diagram_type == "classDiagram":
                        advanced_fixer = SyntaxFixerFactory.create(diagram_type, advanced=True)
                        if advanced_fixer:
                            mermaid_code = advanced_fixer.fix(mermaid_code, error_info=error_info_after)
                            is_valid_after_fix, error_info_after = self.mermaid_renderer.validate_syntax_with_details(mermaid_code)
                else:
                    is_valid_after_fix = False
                    error_info_after = error_info
                
                if is_valid_after_fix:
                    print("✅ 语法错误已自动修复")
                    # 更新保存的mmd文件
                    with open(mmd_file, 'w', encoding='utf-8') as f:
                        f.write(mermaid_code)
                else:
                    # 修复失败，记录错误
                    error_info_after = error_info if diagram_type == "stateDiagram-v2" else error_info_after
                    error_log = os.path.join(output_dir, f"render_error_{timestamp}.txt")
                    with open(error_log, 'w', encoding='utf-8') as f:
                        f.write(f"Mermaid语法错误（已尝试自动修复但仍有错误）:\n{error_info_after.get('message', '未知错误')}\n\n")
                        f.write("原始生成的代码:\n")
                        f.write("-" * 50 + "\n")
                        f.write(original_code + "\n")
                        f.write("-" * 50 + "\n\n")
                        f.write("修复后的代码:\n")
                        f.write("-" * 50 + "\n")
                        f.write(mermaid_code + "\n")
                        f.write("-" * 50 + "\n\n")
                        f.write("请检查并修正上述代码中的语法错误。\n")
                    print(f"⚠️ 语法错误无法完全修复: {error_info_after.get('message', '未知错误')}")
                    png_file = None
                
                if not is_valid_after_fix:
                    # 其他图表类型，记录错误
                    error_log = os.path.join(output_dir, f"render_error_{timestamp}.txt")
                    with open(error_log, 'w', encoding='utf-8') as f:
                        f.write(f"Mermaid语法错误:\n{error_info.get('message', '未知错误')}\n\n")
                        f.write("生成的Mermaid代码:\n")
                        f.write("-" * 50 + "\n")
                        f.write(mermaid_code + "\n")
                        f.write("-" * 50 + "\n\n")
                        f.write("请检查并修正上述代码中的语法错误。\n")
                    print(f"警告: Mermaid语法错误: {error_info.get('message', '未知错误')}")
                    png_file = None
            
            # 如果语法正确（原始或修复后），进行渲染
            if is_valid_after_fix:
                try:
                    self.mermaid_renderer.render_to_png(mermaid_code, png_file, validate=False)
                except Exception as render_error:
                    print(f"渲染失败: {str(render_error)}")
                    png_file = None
        except ValueError as e:
            # 语法错误（从validate_syntax或render_to_png抛出）
            error_msg = str(e)
            error_log = os.path.join(output_dir, f"render_error_{timestamp}.txt")
            with open(error_log, 'w', encoding='utf-8') as f:
                f.write(f"Mermaid语法错误:\n{error_msg}\n\n")
                f.write("生成的Mermaid代码:\n")
                f.write("-" * 50 + "\n")
                f.write(mermaid_code + "\n")
                f.write("-" * 50 + "\n\n")
                f.write("请检查并修正上述代码中的语法错误。\n")
            print(f"警告: Mermaid语法错误: {error_msg}")
            png_file = None
        except Exception as e:
            # 其他渲染错误（如Playwright相关问题）
            error_msg = str(e)
            print(f"警告: 无法渲染PNG图片: {error_msg}")
            # 将错误信息写入日志文件
            error_log = os.path.join(output_dir, f"render_error_{timestamp}.txt")
            with open(error_log, 'w', encoding='utf-8') as f:
                f.write(f"渲染PNG失败:\n{error_msg}\n\n")
                f.write("可能的解决方案:\n")
                f.write("1. 确保已安装Playwright: pip install playwright\n")
                f.write("2. 安装浏览器: playwright install chromium\n")
                f.write("3. 如果仍有问题，可以使用Mermaid代码文件配合在线工具查看\n")
            png_file = None
        
        # 返回修复后的代码
        return {
            "mermaid_code": mermaid_code,  # 可能已经被修复
            "mermaid_file": mmd_file,
            "png_file": png_file,
        }

    def _generate_mermaid_code(self, requirements: str, diagram_type: str = "flowchart") -> str:
        """第一步：基于需求澄清，生成完整的Mermaid格式代码（使用工厂模式）"""
        # 使用工厂模式创建对应的生成器
        generator = DiagramGeneratorFactory.create(diagram_type, self)
        return generator.generate(requirements)
    
    def _generate_flowchart_code(self, requirements: str) -> str:
        """生成流程图代码"""
        prompt = GENERATION_FLOWCHART_PROMPT_TEMPLATE.format(requirements=requirements)
        # 使用较低的温度以提高输出的确定性和一致性
        max_tokens = 2000
        response = self.model(prompt, stream=False, temperature=0.1, max_tokens=max_tokens)
        
        # 提取代码块（如果被markdown包裹）
        mermaid_code = self._extract_mermaid_code(response)
        
        # 验证并修复代码
        mermaid_code = self._validate_and_fix_mermaid_code(mermaid_code, "flowchart")
        
        # 智能布局优化：如果步骤很多且使用LR布局，自动转换为TD布局
        mermaid_code = self._optimize_flowchart_layout(mermaid_code)
        
        # 检查并修复孤立的subgraph连接问题
        mermaid_code = self._fix_subgraph_connections(mermaid_code)
        
        return mermaid_code
    
    def _generate_sequence_diagram_code(self, requirements: str) -> str:
        """生成时序图代码"""
        prompt = GENERATION_SEQUENCE_DIAGRAM_PROMPT_TEMPLATE.format(requirements=requirements)
        response = self.model(prompt, stream=False, temperature=0.1, max_tokens=3000)
        mermaid_code = self._extract_mermaid_code(response)
        mermaid_code = self._validate_and_fix_mermaid_code(mermaid_code, "sequenceDiagram")
        return mermaid_code
    
    def _generate_gantt_code(self, requirements: str) -> str:
        """生成甘特图代码"""
        prompt = GENERATION_GANTT_PROMPT_TEMPLATE.format(requirements=requirements)
        response = self.model(prompt, stream=False, temperature=0.1, max_tokens=3000)
        mermaid_code = self._extract_mermaid_code(response)
        mermaid_code = self._validate_and_fix_mermaid_code(mermaid_code, "gantt")
        # 修复甘特图语法：移除taskId，修正任务格式
        mermaid_code = self._fix_gantt_syntax(mermaid_code)
        return mermaid_code
    
    def _generate_class_diagram_code(self, requirements: str) -> str:
        """生成类图代码"""
        prompt = GENERATION_CLASS_DIAGRAM_PROMPT_TEMPLATE.format(requirements=requirements)
        response = self.model(prompt, stream=False, temperature=0.1, max_tokens=3000)
        mermaid_code = self._extract_mermaid_code(response)
        mermaid_code = self._validate_and_fix_mermaid_code(mermaid_code, "classDiagram")
        # 修复常见的类图语法错误（方法定义冒号、关系符号等）
        mermaid_code = self._fix_class_diagram_syntax(mermaid_code)
        
        # 再次进行语法验证，如果还有错误，尝试自动修复
        if self.mermaid_renderer:
            is_valid, error_info = self.mermaid_renderer.validate_syntax_with_details(mermaid_code)
            if not is_valid:
                # 如果还有错误，尝试进一步的自动修复
                mermaid_code = self._fix_class_diagram_syntax_advanced(mermaid_code, error_info)
        
        return mermaid_code
    
    def _generate_state_diagram_code(self, requirements: str) -> str:
        """生成状态图代码"""
        prompt = GENERATION_STATE_DIAGRAM_PROMPT_TEMPLATE.format(requirements=requirements)
        response = self.model(prompt, stream=False, temperature=0.1, max_tokens=3000)
        mermaid_code = self._extract_mermaid_code(response)
        mermaid_code = self._validate_and_fix_mermaid_code(mermaid_code, "stateDiagram-v2")
        return mermaid_code
    
    def _generate_pie_chart_code(self, requirements: str) -> str:
        """生成饼图代码"""
        prompt = GENERATION_PIE_CHART_PROMPT_TEMPLATE.format(requirements=requirements)
        response = self.model(prompt, stream=False, temperature=0.1, max_tokens=1000)
        mermaid_code = self._extract_mermaid_code(response)
        mermaid_code = self._validate_and_fix_mermaid_code(mermaid_code, "pie")
        return mermaid_code
    
    def _generate_quadrant_chart_code(self, requirements: str) -> str:
        """生成象限图代码"""
        prompt = GENERATION_QUADRANT_CHART_PROMPT_TEMPLATE.format(requirements=requirements)
        response = self.model(prompt, stream=False, temperature=0.1, max_tokens=2000)
        mermaid_code = self._extract_mermaid_code(response)
        mermaid_code = self._fix_quadrant_chart_syntax(mermaid_code)
        mermaid_code = self._validate_and_fix_mermaid_code(mermaid_code, "quadrantChart")
        # 规范化代码：去除所有多余的空行，确保格式正确
        if mermaid_code and mermaid_code.strip().startswith('quadrantChart'):
            lines = mermaid_code.split('\n')
            cleaned_lines = []
            prev_empty = False
            for line in lines:
                line_stripped = line.strip()
                # 保留 quadrantChart 行（即使后面有空格）
                if line_stripped == 'quadrantChart' or cleaned_lines:
                    # 如果是空行
                    if not line_stripped:
                        # 只在前面不是空行时添加一个空行（允许一个空行作为分隔）
                        if not prev_empty and cleaned_lines:
                            cleaned_lines.append('')
                            prev_empty = True
                    else:
                        # 非空行，直接添加
                        cleaned_lines.append(line_stripped)
                        prev_empty = False
            
            # 去除开头和结尾的空行
            while cleaned_lines and not cleaned_lines[0]:
                cleaned_lines.pop(0)
            while cleaned_lines and not cleaned_lines[-1]:
                cleaned_lines.pop()
            
            mermaid_code = '\n'.join(cleaned_lines)
        else:
            mermaid_code = mermaid_code.strip()
        return mermaid_code
    
    def _fix_quadrant_chart_syntax(self, mermaid_code: str) -> str:
        """修复象限图语法错误"""
        if not mermaid_code or not mermaid_code.strip().startswith("quadrantChart"):
            return mermaid_code
        
        lines = mermaid_code.split('\n')
        fixed_lines = []
        
        def needs_quotes(text):
            """检查文本是否需要引号（包含中文、空格或特殊字符）"""
            if not text:
                return False
            # 如果包含中文字符、空格或特殊字符，需要引号
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)
            has_space = ' ' in text
            has_special = any(char in text for char in ['-', '+', '*', '/', '(', ')', '[', ']'])
            return has_chinese or has_space or has_special
        
        def quote_if_needed(text):
            """如果需要，给文本添加引号"""
            if needs_quotes(text):
                return f'"{text}"'
            return text
        
        for line in lines:
            line_stripped = line.strip()
            original_indent = len(line) - len(line.lstrip())
            
            # 跳过空行（将在最后统一处理）
            if not line_stripped:
                continue
            
            # 1. 修复 x-axis 格式：x-axis 市场增长率 (0%-50%) -> x-axis "低增长率" --> "高增长率"
            if line_stripped.startswith('x-axis'):
                # 提取 x-axis 后面的内容
                x_axis_content = line_stripped[7:].strip()  # 跳过 "x-axis"
                # 如果包含括号，尝试提取标签
                if '(' in x_axis_content and ')' in x_axis_content:
                    # 提取括号前的内容作为轴名称
                    axis_name = x_axis_content.split('(')[0].strip()
                    # 尝试从括号中提取范围信息，用于生成左右标签
                    range_match = re.search(r'\(([^)]+)\)', x_axis_content)
                    if range_match:
                        range_text = range_match.group(1)
                        # 尝试提取范围值（如 0%-50%）
                        if '-' in range_text:
                            parts = range_text.split('-')
                            if len(parts) >= 2:
                                # 生成左右标签并添加引号
                                left_label = quote_if_needed(f"低{axis_name}" if axis_name else "低")
                                right_label = quote_if_needed(f"高{axis_name}" if axis_name else "高")
                                fixed_line = f"{' ' * original_indent}x-axis {left_label} --> {right_label}"
                                fixed_lines.append(fixed_line)
                                continue
                # 如果没有括号，检查是否已经是箭头格式
                if '-->' in x_axis_content:
                    # 提取箭头两边的标签
                    parts = x_axis_content.split('-->')
                    if len(parts) == 2:
                        left = parts[0].strip()
                        right = parts[1].strip()
                        # 移除已有的引号（如果有）
                        left = left.strip('"\'')
                        right = right.strip('"\'')
                        # 重新添加引号（如果需要）
                        left = quote_if_needed(left)
                        right = quote_if_needed(right)
                        fixed_line = f"{' ' * original_indent}x-axis {left} --> {right}"
                        fixed_lines.append(fixed_line)
                        continue
                    else:
                        fixed_lines.append(line)
                        continue
                # 如果只是简单标签，尝试添加默认格式
                if x_axis_content:
                    left_label = quote_if_needed(f"低{x_axis_content}")
                    right_label = quote_if_needed(f"高{x_axis_content}")
                    fixed_line = f"{' ' * original_indent}x-axis {left_label} --> {right_label}"
                    fixed_lines.append(fixed_line)
                    continue
            
            # 2. 修复 y-axis 格式：y-axis 相对市场份额 (0-2.0) -> y-axis "低市场份额" --> "高市场份额"
            if line_stripped.startswith('y-axis'):
                y_axis_content = line_stripped[7:].strip()  # 跳过 "y-axis"
                # 如果包含括号，尝试提取标签
                if '(' in y_axis_content and ')' in y_axis_content:
                    axis_name = y_axis_content.split('(')[0].strip()
                    range_match = re.search(r'\(([^)]+)\)', y_axis_content)
                    if range_match:
                        range_text = range_match.group(1)
                        if '-' in range_text:
                            parts = range_text.split('-')
                            if len(parts) >= 2:
                                left_label = quote_if_needed(f"低{axis_name}" if axis_name else "低")
                                right_label = quote_if_needed(f"高{axis_name}" if axis_name else "高")
                                fixed_line = f"{' ' * original_indent}y-axis {left_label} --> {right_label}"
                                fixed_lines.append(fixed_line)
                                continue
                # 如果没有括号，检查是否已经是箭头格式
                if '-->' in y_axis_content:
                    # 提取箭头两边的标签
                    parts = y_axis_content.split('-->')
                    if len(parts) == 2:
                        left = parts[0].strip().strip('"\'')
                        right = parts[1].strip().strip('"\'')
                        left = quote_if_needed(left)
                        right = quote_if_needed(right)
                        fixed_line = f"{' ' * original_indent}y-axis {left} --> {right}"
                        fixed_lines.append(fixed_line)
                        continue
                    else:
                        fixed_lines.append(line)
                        continue
                # 如果只是简单标签，尝试添加默认格式
                if y_axis_content:
                    left_label = quote_if_needed(f"低{y_axis_content}")
                    right_label = quote_if_needed(f"高{y_axis_content}")
                    fixed_line = f"{' ' * original_indent}y-axis {left_label} --> {right_label}"
                    fixed_lines.append(fixed_line)
                    continue
            
            # 3. 修复 quadrant-1 到 quadrant-4 标签，为中文添加引号
            if line_stripped.startswith('quadrant-'):
                parts = line_stripped.split(None, 1)  # 按空格分割，最多分割一次
                if len(parts) == 2:
                    quadrant_label = parts[0]  # quadrant-1
                    quadrant_text = parts[1].strip().strip('"\'')  # 移除已有引号
                    quadrant_text = quote_if_needed(quadrant_text)
                    fixed_line = f"{' ' * original_indent}{quadrant_label} {quadrant_text}"
                    fixed_lines.append(fixed_line)
                    continue
            
            # 4. 修复点名称：点A -> A, 点B -> B，并归一化坐标到0-1范围
            if ':' in line_stripped and '[' in line_stripped:
                # 匹配点名称: [x, y] 格式
                point_match = re.match(r'^(点)?([^:]+?)\s*:\s*\[([^\]]+)\]', line_stripped)
                if point_match:
                    point_prefix = point_match.group(1)  # "点"
                    point_name = point_match.group(2).strip()
                    coordinates_str = point_match.group(3).strip()
                    
                    # 尝试解析和归一化坐标
                    try:
                        coords = [float(x.strip()) for x in coordinates_str.split(',')]
                        if len(coords) == 2:
                            x, y = coords
                            # 归一化 x 坐标（假设范围是 0-0.5，对应 0%-50%）
                            # 如果 x > 1，可能是百分比（0-50），需要除以50
                            if x > 1:
                                x = x / 50.0
                            # 归一化 y 坐标（假设范围是 0-2.0）
                            # 如果 y > 1，可能是原始值（0-2.0），需要除以2.0
                            if y > 1:
                                y = y / 2.0
                            # 确保坐标在 0-1 范围内
                            x = max(0.0, min(1.0, x))
                            y = max(0.0, min(1.0, y))
                            coordinates_str = f"{x:.2f}, {y:.2f}"
                    except (ValueError, IndexError):
                        # 如果解析失败，保持原样
                        pass
                    
                    # 移除"点"前缀
                    if point_prefix:
                        fixed_line = f"{' ' * original_indent}{point_name}: [{coordinates_str}]"
                        fixed_lines.append(fixed_line)
                        continue
                    else:
                        # 即使没有"点"前缀，也要检查是否需要归一化坐标
                        try:
                            coords = [float(x.strip()) for x in coordinates_str.split(',')]
                            if len(coords) == 2:
                                x, y = coords
                                if x > 1:
                                    x = x / 50.0
                                if y > 1:
                                    y = y / 2.0
                                x = max(0.0, min(1.0, x))
                                y = max(0.0, min(1.0, y))
                                coordinates_str = f"{x:.2f}, {y:.2f}"
                                fixed_line = f"{' ' * original_indent}{point_name}: [{coordinates_str}]"
                                fixed_lines.append(fixed_line)
                                continue
                        except (ValueError, IndexError):
                            pass
            
            # 其他行保持原样（包括 quadrantChart、title 等）
            fixed_lines.append(line_stripped)
        
        # 确保第一行是 quadrantChart，没有多余空行
        result_lines = []
        for i, line in enumerate(fixed_lines):
            if i == 0:
                # 第一行必须是 quadrantChart
                if line.strip() == 'quadrantChart' or line.strip().startswith('quadrantChart'):
                    result_lines.append('quadrantChart')
                else:
                    result_lines.append(line)
            else:
                result_lines.append(line)
        
        return '\n'.join(result_lines)
    
    def _generate_journey_code(self, requirements: str) -> str:
        """生成用户旅程图代码"""
        prompt = GENERATION_JOURNEY_PROMPT_TEMPLATE.format(requirements=requirements)
        response = self.model(prompt, stream=False, temperature=0.1, max_tokens=3000)
        mermaid_code = self._extract_mermaid_code(response)
        mermaid_code = self._validate_and_fix_mermaid_code(mermaid_code, "journey")
        return mermaid_code
    
    def _clean_html_and_markdown(self, text: str) -> str:
        """清理HTML标签和Markdown符号（委托给工具类）"""
        return TextCleaner.clean_html_and_markdown(text)
    
    def _clean_mermaid_code(self, mermaid_code: str) -> str:
        """清理Mermaid代码中的HTML标签和Markdown符号
        
        逐行处理，保留Mermaid语法结构，只清理文本内容部分
        """
        if not mermaid_code:
            return mermaid_code
        
        lines = mermaid_code.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # 如果是空行或注释行，直接保留
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith('//'):
                cleaned_lines.append(line)
                continue
            
            # 保留原始缩进
            original_indent = len(line) - len(line.lstrip())
            indent = ' ' * original_indent
            
            # 保存Mermaid关键字和语法结构，只清理文本内容
            cleaned_line = line
            
            # 处理不同的Mermaid语法模式
            # 匹配引号内的内容进行清理的函数
            def clean_quoted_content(match):
                quote_char = match.group(1)  # 获取引号类型（"或'）
                content = match.group(2)  # 获取引号内的内容
                cleaned_content = TextCleaner.clean_html_and_markdown(content)
                # 处理转义的换行符
                cleaned_content = cleaned_content.replace('\\n', '\n')
                # 清理后再转义换行符
                cleaned_content = cleaned_content.replace('\n', '\\n')
                return f'{quote_char}{cleaned_content}{quote_char}'
            
            # 1. 流程图节点：NodeID["文本内容"] 或 NodeID("文本内容")
            # 清理双引号内的内容
            cleaned_line = re.sub(r'(")([^"]*)(")', clean_quoted_content, cleaned_line)
            # 清理单引号内的内容
            cleaned_line = re.sub(r"(')([^']*)(')", clean_quoted_content, cleaned_line)
            
            # 2. 时序图：participant A as "参与者名称" 或 A->>B: 消息内容
            # 先处理participant定义
            if 'participant' in cleaned_line.lower() or 'actor' in cleaned_line.lower():
                # participant A as "名称<div>xxx</div>" 或 participant "名称<div>xxx</div>" as A
                # 清理participant名称中的HTML标签和Markdown符号
                if 'as' in cleaned_line.lower():
                    parts = cleaned_line.split('as', 1)
                    if len(parts) == 2:
                        syntax_part = parts[0].strip()  # participant A
                        name_part = parts[1].strip()  # "名称" 或 A "名称"
                        # 提取引号内的名称并清理
                        name_match = re.search(r'"([^"]*)"', name_part)
                        if name_match:
                            cleaned_name = TextCleaner.clean_html_and_markdown(name_match.group(1))
                            name_part = f'"{cleaned_name}"'
                        cleaned_line = f'{syntax_part} as {name_part}'
            
            # 处理时序图消息：A->>B: 消息内容 或 A->>B: <div>消息</div>
            # 清理冒号后的内容（优先匹配时序图语法）
            if ':' in cleaned_line and ('->>' in cleaned_line or '-->>' in cleaned_line or 
                                       '-.->' in cleaned_line or '--->' in cleaned_line or
                                       '->' in cleaned_line):
                parts = cleaned_line.split(':', 1)
                if len(parts) == 2:
                    syntax_part = parts[0].strip()  # 保留语法部分（如 A->>B）
                    content_part = parts[1]  # 清理内容部分
                    cleaned_content = TextCleaner.clean_html_and_markdown(content_part)
                    cleaned_line = f'{syntax_part}: {cleaned_content}'
            
            # 3. 甘特图任务：任务名称 :状态, 日期 或 任务名称<div>xxx</div> :状态, 日期
            # 清理任务名称中的HTML标签
            if ':' in cleaned_line and (line_stripped.startswith('section') or 
                                       not any(x in line_stripped for x in ['->', '--', 'activate', 'deactivate', 'Note'])):
                # 检查是否是任务定义行（包含日期格式 YYYY-MM-DD）
                if re.search(r'\d{4}-\d{2}-\d{2}', cleaned_line):
                    parts = cleaned_line.split(':', 1)
                    if len(parts) == 2:
                        task_name = parts[0]  # 任务名称部分
                        rest = parts[1]  # 状态和日期部分
                        cleaned_task_name = TextCleaner.clean_html_and_markdown(task_name)
                        cleaned_line = f'{cleaned_task_name}:{rest}'
            
            # 4. 类图：class 类名 { 或 +方法名() 返回类型
            # 类名和方法名中可能包含HTML标签
            if 'class' in cleaned_line.lower() or re.search(r'[+\-#~]\s*\w+', cleaned_line):
                # 清理类名和方法名中的HTML标签
                cleaned_line = re.sub(r'<[^>]+>', '', cleaned_line)
                cleaned_line = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned_line)
            
            # 5. 状态图：state 状态名 : 转换条件
            if 'state' in cleaned_line.lower() and ':' in cleaned_line:
                parts = cleaned_line.split(':', 1)
                if len(parts) == 2:
                    state_part = parts[0]
                    condition_part = parts[1]
                    cleaned_condition = self._clean_html_and_markdown(condition_part)
                    cleaned_line = f'{state_part}: {cleaned_condition}'
            
            # 6. 象限图：点名称: [坐标] 或 quadrant-1 "标签"
            if ':' in cleaned_line and ('[' in cleaned_line or 'quadrant' in cleaned_line.lower()):
                parts = cleaned_line.split(':', 1)
                if len(parts) == 2:
                    label_part = parts[0]
                    value_part = parts[1]
                    # 清理标签中的HTML和Markdown
                    cleaned_label = self._clean_html_and_markdown(label_part)
                    # 值部分（坐标或象限标签）也需要清理引号内的内容
                    cleaned_value = value_part
                    cleaned_value = re.sub(r'(")([^"]*)(")', clean_quoted_content, cleaned_value)
                    cleaned_line = f'{cleaned_label}: {cleaned_value}'
            
            # 7. 用户旅程图：步骤名称: 情感状态: 参与者, 分数
            if ':' in cleaned_line and 'journey' not in cleaned_line.lower():
                # 处理可能包含HTML标签的步骤名称
                cleaned_line = re.sub(r'<[^>]+>', '', cleaned_line)
                # 清理Markdown符号
                cleaned_line = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned_line)
            
            # 8. Note注释：Note over A,B: 注释内容
            if cleaned_line.strip().startswith('Note'):
                if ':' in cleaned_line:
                    parts = cleaned_line.split(':', 1)
                    if len(parts) == 2:
                        note_syntax = parts[0]
                        note_content = parts[1]
                        cleaned_note = self._clean_html_and_markdown(note_content)
                        cleaned_line = f'{note_syntax}: {cleaned_note}'
            
            # 9. 通用清理：对于所有行，如果还包含HTML标签或Markdown符号，进行最终清理
            # 这主要是为了捕获前面步骤可能遗漏的情况
            # 但要注意不要破坏已经处理过的引号内容
            # 检查是否还有HTML标签（排除引号内的，因为已经处理过了）
            if '<' in cleaned_line and '>' in cleaned_line:
                # 如果引号已经处理过，可能引号内没有HTML标签了
                # 对于没有引号的行，直接清理
                if '"' not in cleaned_line and "'" not in cleaned_line:
                    cleaned_line = self._clean_html_and_markdown(cleaned_line)
                else:
                    # 对于有引号的行，只清理引号外的HTML标签
                    # 这个情况比较复杂，暂时只清理明显的标签
                    cleaned_line = re.sub(r'<[^>]+>', '', cleaned_line)
            
            # 检查是否还有Markdown符号（排除引号内的）
            if ('**' in cleaned_line or '__' in cleaned_line) and ('"' not in cleaned_line and "'" not in cleaned_line):
                # 只对没有引号的行进行Markdown清理
                cleaned_line = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned_line)
                cleaned_line = re.sub(r'__([^_]+)__', r'\1', cleaned_line)
            
            cleaned_lines.append(cleaned_line)
        
        return '\n'.join(cleaned_lines)
    
    def _validate_and_fix_mermaid_code(self, mermaid_code: str, diagram_type: str) -> str:
        """验证并修复Mermaid代码，确保以正确的图类型开头"""
        # 先清理HTML标签和Markdown符号
        mermaid_code = TextCleaner.clean_mermaid_code(mermaid_code)
        
        # 自动检测图表类型（如果第一行类型错误）
        first_line = mermaid_code.strip().split('\n')[0].strip().lower()
        
        # 检测实际图表类型（通过内容特征）
        actual_type = None
        lines = mermaid_code.split('\n')
        
        # 检查是否包含时序图特征
        if any('participant' in line.lower() or 'sequenceDiagram' in line.lower() for line in lines):
            actual_type = 'sequenceDiagram'
        # 检查是否包含流程图特征
        elif any('subgraph' in line.lower() or 'flowchart' in line.lower() or 'graph' in line.lower() for line in lines if not line.strip().startswith('flowchart') and not line.strip().startswith('graph')):
            if not first_line.startswith('sequence') and not first_line.startswith('class') and not first_line.startswith('gantt'):
                actual_type = 'flowchart'
        # 检查是否包含类图特征
        elif any('classDiagram' in line.lower() or (line.strip().startswith('class ') and 'as' not in line.lower()) for line in lines):
            actual_type = 'classDiagram'
        
        expected_starts = {
            "flowchart": "flowchart",
            "sequenceDiagram": "sequenceDiagram",
            "gantt": "gantt",
            "classDiagram": "classDiagram",
            "stateDiagram-v2": "stateDiagram-v2",
            "pie": "pie",
            "quadrantChart": "quadrantChart",
            "journey": "journey"
        }
        
        # 如果检测到实际类型且与第一行不匹配，使用实际类型
        if actual_type and actual_type != diagram_type:
            diagram_type = actual_type
        
        expected_start = expected_starts.get(diagram_type, None)
        
        # 如果diagram_type为空，使用检测到的类型
        if not expected_start:
            expected_start = expected_starts.get(actual_type, "flowchart")
        
        if not mermaid_code.strip().startswith(expected_start):
            lines = mermaid_code.split('\n')
            start_idx = -1
            for i, line in enumerate(lines):
                if expected_start.lower() in line.lower():
                    start_idx = i
                    break
            if start_idx >= 0:
                # 移除错误的类型声明行
                mermaid_code = '\n'.join(lines[start_idx:])
            else:
                # 如果还是没有找到，在开头添加
                mermaid_code = f'{expected_start}\n' + mermaid_code
        else:
            # 即使第一行正确，也要确保没有重复的图表类型声明
            lines = mermaid_code.split('\n')
            fixed_lines = []
            found_first_declaration = False
            for i, line in enumerate(lines):
                line_lower = line.strip().lower()
                # 如果是图表类型声明
                if any(line_lower.startswith(start.lower()) for start in expected_starts.values()):
                    if not found_first_declaration:
                        # 保留第一个声明，确保是正确的类型
                        if line_lower.startswith(expected_start.lower()):
                            fixed_lines.append(expected_start)
                        else:
                            fixed_lines.append(expected_start)
                        found_first_declaration = True
                    # 跳过后续的重复声明
                    continue
                fixed_lines.append(line)
            if found_first_declaration:
                mermaid_code = '\n'.join(fixed_lines)
        
        return mermaid_code
    
    def _fix_sequence_diagram_syntax(self, mermaid_code: str) -> str:
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
            
            # 修复 participant 定义中的双 as 错误
            # 例如：participant El as ticSearch as 索引存储集群
            # 应该是：participant ElasticSearch as 索引存储集群
            if line_stripped.lower().startswith('participant'):
                # 统计 as 的出现次数
                as_count = line_stripped.lower().count(' as ')
                if as_count > 1:
                    # 提取 participant 关键字和参与者别名（最后一个 as 后面的内容）
                    parts = line_stripped.split(' as ')
                    if len(parts) >= 3:
                        # 第一个部分是 "participant 名称"，最后一个部分是别名
                        participant_part = parts[0]  # "participant El"
                        alias = parts[-1]  # "索引存储集群"
                        
                        # 尝试从 participant_part 提取原始名称
                        participant_match = re.match(r'participant\s+(\S+)', participant_part, re.IGNORECASE)
                        if participant_match:
                            participant_name_start = participant_match.group(1)  # "El"
                            
                            # 合并所有中间部分作为完整名称（例如：El + ticSearch = ElasticSearch）
                            middle_parts = parts[1:-1]  # ["ticSearch"]
                            if middle_parts:
                                # 合并第一个名称和中间部分
                                participant_name = participant_name_start + ''.join(middle_parts)
                            else:
                                participant_name = participant_name_start
                            
                            # 确保 participant 名称是有效的（去除特殊字符，但保留字母、数字和下划线）
                            participant_name = re.sub(r'[^\w]', '', participant_name)
                            
                            # 如果合并后的名称仍然太短或不合理，尝试从别名或代码上下文中推断
                            if len(participant_name) < 3:
                                # 如果名称太短，尝试使用代码中其他地方出现的名称
                                # 查找代码中是否有使用这个参与者的地方
                                for other_line in lines:
                                    if alias in other_line and '->>' in other_line:
                                        # 尝试从箭头语句中提取名称
                                        arrow_match = re.search(r'(\w+)\s*-', other_line)
                                        if arrow_match:
                                            participant_name = arrow_match.group(1)
                                            break
                                
                                # 如果还是找不到，使用别名的第一个词（如果别名是英文）
                                if len(participant_name) < 3:
                                    alias_words = re.findall(r'[a-zA-Z]+', alias)
                                    if alias_words:
                                        participant_name = alias_words[0]
                            
                            # 构建正确的 participant 行
                            fixed_line = f"participant {participant_name} as {alias}"
                            fixed_lines.append(fixed_line)
                            continue
            
            fixed_lines.append(original_line)
        
        return '\n'.join(fixed_lines)
    
    def _fix_gantt_syntax(self, mermaid_code: str) -> str:
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
            
            # 保留gantt、dateFormat、title、section行（不区分大小写）
            line_lower = line_stripped.lower()
            if line_lower.startswith('gantt') or line_lower.startswith('dateformat') or \
               line_lower.startswith('title') or line_lower.startswith('section'):
                fixed_lines.append(line_stripped)
                continue
            
            # 修复任务行：格式应该是 任务名称 :状态, 开始日期, 持续天数 或 任务名称 :状态, 开始日期, 结束日期
            # 错误格式：任务名称 :状态, taskId, 开始日期, 结束日期
            # 正确格式：任务名称 :状态, 开始日期, 持续天数
            # 匹配：任务名称 :状态, 数字, YYYY-MM-DD, YYYY-MM-DD
            task_match = re.match(r'^(.+?)\s*:\s*([^,]+?)\s*,\s*(\d+)\s*,\s*(\d{4}-\d{2}-\d{2})\s*,\s*(\d{4}-\d{2}-\d{2})$', line_stripped)
            if task_match:
                # 有taskId的情况：任务名称 :状态, taskId, 开始日期, 结束日期
                task_name = task_match.group(1).strip()
                status = task_match.group(2).strip()
                task_id = task_match.group(3).strip()
                start_date = task_match.group(4).strip()
                end_date = task_match.group(5).strip()
                
                # 计算持续天数
                from datetime import datetime
                try:
                    start = datetime.strptime(start_date, '%Y-%m-%d')
                    end = datetime.strptime(end_date, '%Y-%m-%d')
                    duration = (end - start).days + 1  # 包含结束日
                    # 保持原始缩进
                    indent = len(original_line) - len(original_line.lstrip())
                    fixed_lines.append(" " * indent + f"{task_name} :{status}, {start_date}, {duration}d")
                except Exception as e:
                    # 如果日期解析失败，保持原样
                    fixed_lines.append(original_line)
                continue
            
            # 检查是否是里程碑格式：任务名称 :milestone, taskId, 日期
            milestone_match = re.match(r'^(.+?)\s*:\s*milestone\s*,\s*(\d+)\s*,\s*(\d{4}-\d{2}-\d{2})$', line_stripped, re.IGNORECASE)
            if milestone_match:
                milestone_name = milestone_match.group(1).strip()
                milestone_id = milestone_match.group(2).strip()
                milestone_date = milestone_match.group(3).strip()
                # 保持原始缩进
                indent = len(original_line) - len(original_line.lstrip())
                fixed_lines.append(" " * indent + f"{milestone_name} :milestone, {milestone_date}, 0d")
                continue
            
            # 其他行保持原样（保持原始格式）
            fixed_lines.append(original_line)
        
        return '\n'.join(fixed_lines)
    
    def _fix_class_diagram_syntax(self, mermaid_code: str) -> str:
        """修复类图语法：将类定义和关系分开，修复方法定义格式等"""
        if not mermaid_code or not mermaid_code.strip().startswith("classDiagram"):
            return mermaid_code
        
        lines = mermaid_code.split('\n')
        fixed_lines = []
        class_definitions = {}  # 存储类定义
        relationships = []  # 存储关系
        
        i = 0
        while i < len(lines):
            line = lines[i]
            line_stripped = line.strip()
            original_indent = len(line) - len(line.lstrip())
            
            if not line_stripped or line_stripped.startswith('//'):
                fixed_lines.append(line)
                i += 1
                continue
            
            # 1. 修复方法定义中的冒号错误：方法名(): 返回类型 -> 方法名() 返回类型
            # 匹配模式：+/-/#/~方法名(): 返回类型
            method_pattern = r'^([+\-#~])\s*(\w+)\s*\(\s*\)\s*:\s*(.+)$'
            method_match = re.match(method_pattern, line_stripped)
            if method_match:
                visibility = method_match.group(1)
                method_name = method_match.group(2)
                return_type = method_match.group(3).strip()
                # 修复：移除冒号，用空格分隔
                fixed_line = f"{' ' * original_indent}{visibility}{method_name}() {return_type}"
                fixed_lines.append(fixed_line)
                i += 1
                continue
            
            # 2. 修复关系符号错误
            # --|> 应该是 -->（关联）
            if '--|>' in line_stripped:
                line_stripped = line_stripped.replace('--|>', '-->')
                fixed_lines.append(' ' * original_indent + line_stripped)
                i += 1
                continue
            
            # -- 单独的关系符号（缺少箭头），默认改为 -->（关联）
            if re.match(r'^\w+\s+--\s+\w+$', line_stripped) and not any(s in line_stripped for s in ['<|--', '-->', '..>', '*--', 'o--', '<|..']):
                line_stripped = line_stripped.replace(' -- ', ' --> ')
                fixed_lines.append(' ' * original_indent + line_stripped)
                i += 1
                continue
            
            # 3. 检测缺少 class 关键字的类定义
            # 例如：LibraryService { 或 UserService {
            # 匹配：类名 { （但不是 class 开头，也不是关系行）
            if not line_stripped.startswith('class ') and re.match(r'^[A-Z]\w*\s*\{', line_stripped):
                # 检查不是关系行
                if not any(symbol in line_stripped for symbol in ['<|--', '<|..', '*--', 'o--', '-->', '..>', '--|>', ' -- ', ' .. ']):
                    # 提取类名
                    class_match = re.match(r'^([A-Z]\w*)\s*\{', line_stripped)
                    if class_match:
                        class_name = class_match.group(1)
                        # 添加 class 关键字
                        fixed_line = f"{' ' * original_indent}class {class_name} {{"
                        fixed_lines.append(fixed_line)
                        i += 1
                        # 收集类定义内容
                        brace_count = 1
                        while i < len(lines) and brace_count > 0:
                            current_line = lines[i]
                            current_stripped = current_line.strip()
                            # 修复方法定义中的冒号
                            method_match_inner = re.match(method_pattern, current_stripped)
                            if method_match_inner:
                                visibility = method_match_inner.group(1)
                                method_name = method_match_inner.group(2)
                                return_type = method_match_inner.group(3).strip()
                                inner_indent = len(current_line) - len(current_line.lstrip())
                                current_line = f"{' ' * inner_indent}{visibility}{method_name}() {return_type}"
                            fixed_lines.append(current_line)
                            brace_count += current_line.count('{') - current_line.count('}')
                            i += 1
                        continue
            
            # 4. 检查是否是类定义行，并且包含关系符号（错误语法）
            # 例如：class Admin <|-- User { 或 class Member <|-- User {
            if line_stripped.startswith('class ') and ('<|--' in line_stripped or '<|..' in line_stripped or 
                                                       '*--' in line_stripped or 'o--' in line_stripped or
                                                       '-->' in line_stripped or '..>' in line_stripped):
                # 提取类名和关系
                # 匹配：class ClassName <|-- OtherClass {
                match = re.match(r'class\s+(\w+)\s+(<\|--|<\|\.\.|\*--|o--|-->|\.\.>)\s+(\w+)\s*\{', line_stripped)
                if match:
                    class_name = match.group(1)
                    relation_symbol = match.group(2)
                    other_class = match.group(3)
                    
                    # 开始收集类定义内容
                    class_content = [line_stripped.split('{')[0] + '{']  # 只保留类定义部分
                    i += 1
                    brace_count = 1  # 已经有一个左大括号
                    
                    # 收集类定义内容直到大括号闭合
                    while i < len(lines) and brace_count > 0:
                        current_line = lines[i]
                        # 在收集过程中也修复方法定义
                        current_stripped = current_line.strip()
                        method_match_inner = re.match(method_pattern, current_stripped)
                        if method_match_inner:
                            visibility = method_match_inner.group(1)
                            method_name = method_match_inner.group(2)
                            return_type = method_match_inner.group(3).strip()
                            inner_indent = len(current_line) - len(current_line.lstrip())
                            current_line = f"{' ' * inner_indent}{visibility}{method_name}() {return_type}"
                        class_content.append(current_line)
                        brace_count += current_line.count('{') - current_line.count('}')
                        i += 1
                    
                    # 保存类定义
                    class_def_key = class_name
                    if class_def_key not in class_definitions:
                        class_definitions[class_def_key] = '\n'.join(class_content)
                    
                    # 保存关系（需要判断方向）
                    # 如果是 <|-- 或 <|..，左边是父类，右边是子类
                    # 但这里的关系是在类定义行上，所以需要根据语义判断
                    if relation_symbol in ['<|--', '<|..']:
                        # 通常继承关系是：父类 <|-- 子类
                        # 如果写的是 class 子类 <|-- 父类，需要反转
                        relationships.append(f"{other_class} {relation_symbol} {class_name}")
                    else:
                        relationships.append(f"{class_name} {relation_symbol} {other_class}")
                    
                    continue
            
            fixed_lines.append(line)
            i += 1
        
        # 第二步：修复fixed_lines中剩余的语法错误（方法定义冒号、关系符号、缺少class关键字等）
        final_fixed_lines = []
        for line in fixed_lines:
            line_stripped = line.strip()
            original_indent = len(line) - len(line.lstrip())
            
            if not line_stripped or line_stripped.startswith('//'):
                final_fixed_lines.append(line)
                continue
            
            # 再次检测缺少 class 关键字的类定义（以防第一步漏掉）
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
            
            # 修复关系符号错误
            # --|> 应该是 -->（关联）
            if '--|>' in line_stripped:
                line_stripped = line_stripped.replace('--|>', '-->')
                final_fixed_lines.append(' ' * original_indent + line_stripped)
                continue
            
            # -- 单独的关系符号（缺少箭头），默认改为 -->（关联）
            if re.match(r'^\w+\s+--\s+\w+$', line_stripped) and not any(s in line_stripped for s in ['<|--', '-->', '..>', '*--', 'o--', '<|..', '--|>']):
                line_stripped = line_stripped.replace(' -- ', ' --> ')
                final_fixed_lines.append(' ' * original_indent + line_stripped)
                continue
            
            final_fixed_lines.append(line)
        
        # 重新组织代码：先输出所有类定义，然后输出所有关系
        # 收集所有类定义和关系
        all_class_defs = []  # 存储所有完整的类定义（包括类名和内容）
        all_relationships = []  # 存储所有关系
        other_lines = []  # 存储其他行（如注释、空行等）
        
        in_class_def = False
        current_class_lines = []
        current_class_name = None
        
        for line in final_fixed_lines:
            line_stripped = line.strip()
            
            # 检测类定义开始
            if line_stripped.startswith('class ') and '{' in line_stripped:
                # 如果之前有未完成的类定义，保存它
                if in_class_def and current_class_lines:
                    all_class_defs.append(('\n'.join(current_class_lines), current_class_name))
                
                in_class_def = True
                current_class_lines = [line]
                # 提取类名
                class_match = re.match(r'class\s+(\w+)', line_stripped)
                if class_match:
                    current_class_name = class_match.group(1)
                else:
                    current_class_name = None
            elif in_class_def:
                # 类定义内容
                current_class_lines.append(line)
                if '}' in line:
                    # 类定义结束
                    if current_class_lines:
                        all_class_defs.append(('\n'.join(current_class_lines), current_class_name))
                    current_class_lines = []
                    current_class_name = None
                    in_class_def = False
            else:
                # 检查是否是关系行
                is_relationship = any(symbol in line_stripped for symbol in ['<|--', '<|..', '*--', 'o--', '-->', '..>', '--|>'])
                if is_relationship:
                    # 修复关系符号后添加到relationships
                    rel_line = line_stripped.replace('--|>', '-->')
                    if re.match(r'^\w+\s+--\s+\w+$', rel_line) and not any(s in rel_line for s in ['<|--', '-->', '..>', '*--', 'o--', '<|..']):
                        rel_line = rel_line.replace(' -- ', ' --> ')
                    all_relationships.append(rel_line)
                else:
                    # 其他行（如 classDiagram、注释、空行等）
                    if not line_stripped or line_stripped.startswith('//') or line_stripped.startswith('classDiagram'):
                        other_lines.append(line)
                    else:
                        # 可能是遗漏的类定义（缺少class关键字但已修复）
                        if re.match(r'^[A-Z]\w*\s*\{', line_stripped):
                            # 已经在前面修复过了，这里应该是正常的类定义
                            other_lines.append(line)
                        else:
                            other_lines.append(line)
        
        # 保存最后未完成的类定义
        if in_class_def and current_class_lines:
            all_class_defs.append(('\n'.join(current_class_lines), current_class_name))
        
        # 添加修复后的类定义（从class_definitions字典）
        for class_name, class_def in class_definitions.items():
            # 检查是否已经存在
            exists = any(name == class_name for _, name in all_class_defs)
            if not exists:
                all_class_defs.append((class_def, class_name))
        
        # 合并关系（避免重复）
        for rel in relationships:
            if rel not in all_relationships:
                all_relationships.append(rel)
        
        # 重新组织：classDiagram -> 所有类定义 -> 所有关系
        result_lines = []
        
        # 检查是否已经按正确顺序组织（类定义在前，关系在后）
        # 如果代码已经正确，并且没有检测到语法错误，可能不需要重新组织
        original_has_class_defs = any('class ' in line for line in lines)
        original_has_relationships = any(any(symbol in line for symbol in ['<|--', '<|..', '*--', 'o--', '-->', '..>']) for line in lines)
        
        # 1. 添加classDiagram声明
        class_diagram_line = None
        for line in other_lines:
            if line.strip().startswith('classDiagram'):
                class_diagram_line = line
                break
        if not class_diagram_line:
            # 从原始代码中查找
            for line in lines:
                if line.strip().startswith('classDiagram'):
                    class_diagram_line = line
                    break
        if class_diagram_line:
            result_lines.append(class_diagram_line)
        elif not result_lines:
            result_lines.append('classDiagram')
        
        # 2. 添加所有类定义（确保每个类定义都有完整的开始和结束）
        for class_def, class_name in all_class_defs:
            if class_def.strip():
                # 确保类定义格式正确
                if not class_def.strip().startswith('class '):
                    # 如果不是以class开头，尝试修复
                    class_def_lines = class_def.split('\n')
                    first_line = class_def_lines[0].strip()
                    if not first_line.startswith('class ') and re.match(r'^[A-Z]\w*\s*\{', first_line):
                        # 添加class关键字
                        class_match = re.match(r'^([A-Z]\w*)\s*\{', first_line)
                        if class_match:
                            indent = len(class_def_lines[0]) - len(class_def_lines[0].lstrip())
                            class_def_lines[0] = ' ' * indent + f"class {class_match.group(1)} {{"
                            class_def = '\n'.join(class_def_lines)
                result_lines.append(class_def)
        
        # 3. 添加所有关系（确保关系格式正确）
        for rel in all_relationships:
            if rel.strip():
                # 清理关系行中的多余空格
                rel = re.sub(r'\s+', ' ', rel.strip())
                result_lines.append(rel)
        
        # 如果重新组织后的代码与原始代码结构相似（类定义在前，关系在后），使用重新组织的结果
        # 否则，如果原始代码已经是正确的，尽量保持原样
        reorganized_code = '\n'.join(result_lines)
        
        # 如果重新组织后没有有效内容，返回修复后的原始代码
        if not reorganized_code.strip() or (not all_class_defs and not all_relationships):
            return '\n'.join(final_fixed_lines) if final_fixed_lines else mermaid_code
        
        return reorganized_code
    
    def _fix_class_diagram_syntax_advanced(self, mermaid_code: str, error_info: Dict) -> str:
        """高级类图语法修复，基于错误信息进行更精确的修复"""
        if not mermaid_code or not mermaid_code.strip().startswith("classDiagram"):
            return mermaid_code
        
        # 先尝试基本修复
        mermaid_code = self._fix_class_diagram_syntax(mermaid_code)
        
        # 再次检查，如果还有错误，进行针对性修复
        lines = mermaid_code.split('\n')
        fixed_lines = []
        error_lines = error_info.get('error_lines', [])
        
        for i, line in enumerate(lines, 1):
            original_indent = len(line) - len(line.lstrip())
            line_stripped = line.strip()
            
            if i in error_lines or not line_stripped.startswith('class ') and re.match(r'^[A-Z]\w*\s*\{', line_stripped):
                # 这是错误行，尝试修复
                # 1. 修复缺少class关键字
                if not line_stripped.startswith('class ') and re.match(r'^[A-Z]\w*\s*\{', line_stripped):
                    if not any(symbol in line_stripped for symbol in ['<|--', '<|..', '*--', 'o--', '-->', '..>', '--|>', ' -- ', ' .. ']):
                        class_match = re.match(r'^([A-Z]\w*)\s*\{', line_stripped)
                        if class_match:
                            class_name = class_match.group(1)
                            fixed_line = f"{' ' * original_indent}class {class_name} {{"
                            fixed_lines.append(fixed_line)
                            continue
                
                # 2. 修复方法定义冒号
                method_pattern = r'^([+\-#~])\s*(\w+)\s*\(\s*\)\s*:\s*(.+)$'
                method_match = re.match(method_pattern, line_stripped)
                if method_match:
                    visibility = method_match.group(1)
                    method_name = method_match.group(2)
                    return_type = method_match.group(3).strip()
                    fixed_line = f"{' ' * original_indent}{visibility}{method_name}() {return_type}"
                    fixed_lines.append(fixed_line)
                    continue
                
                # 3. 修复关系符号
                if '--|>' in line_stripped:
                    line_stripped = line_stripped.replace('--|>', '-->')
                    fixed_lines.append(' ' * original_indent + line_stripped)
                    continue
                
                # 4. 修复单独的双横线
                if re.match(r'^\w+\s+--\s+\w+$', line_stripped) and not any(s in line_stripped for s in ['<|--', '-->', '..>', '*--', 'o--', '<|..']):
                    line_stripped = line_stripped.replace(' -- ', ' --> ')
                    fixed_lines.append(' ' * original_indent + line_stripped)
                    continue
            
            fixed_lines.append(line)
        
        # 再次调用基本修复以确保类定义顺序正确
        result = '\n'.join(fixed_lines)
        return self._fix_class_diagram_syntax(result)
    
    def _fix_state_diagram_syntax(self, mermaid_code: str) -> str:
        """修复状态图语法错误
        
        主要修复内容：
        1. 将转换条件格式从 {条件} 改为 : "条件"
        2. 为包含中文的状态名称和转换条件添加引号
        3. 去除重复的状态转换关系
        """
        if not mermaid_code or not mermaid_code.strip().startswith("stateDiagram-v2"):
            return mermaid_code
        
        lines = mermaid_code.split('\n')
        fixed_lines = []
        seen_relationships = set()  # 用于去重（格式：source --> target : condition）
        
        # 检测是否包含中文字符的函数
        def has_chinese(text: str) -> bool:
            return any('\u4e00' <= char <= '\u9fff' for char in text)
        
        # 为文本添加引号的函数（如果包含中文或空格）
        def quote_if_needed(text: str) -> str:
            text = text.strip()
            if not text:
                return text
            # 如果已经用引号包裹，直接返回
            if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
                return text
            # 如果包含中文、空格或特殊字符，需要引号
            if has_chinese(text) or ' ' in text or any(char in text for char in ['(', ')', '（', '）']):
                return f'"{text}"'
            return text
        
        for line in lines:
            line_stripped = line.strip()
            original_indent = len(line) - len(line.lstrip())
            
            # 空行或注释行直接保留
            if not line_stripped or line_stripped.startswith('//'):
                fixed_lines.append(line)
                continue
            
            # 保留图表类型声明
            if line_stripped.startswith('stateDiagram-v2'):
                fixed_lines.append(line)
                continue
            
            # 修复连在一起的引号问题（如 "待支付""待支付" --> "已支付"）
            # 根据错误信息：[*] --> "待支付""待支付" --> "已支付"
            if '""' in line_stripped:
                # 模式1: [*] --> "待支付""待支付" --> "已支付" (状态名称重复)
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
                    continue
                
                # 模式2: "待支付""待支付" (重复的状态名称，没有箭头)
                line_stripped = re.sub(r'"([^"]+)""\1"(?!\s*-->)', r'"\1"', line_stripped)
                # 模式3: "状态A""状态B" --> "状态C" (不同的状态连在一起，中间缺少箭头)
                line_stripped = re.sub(r'"([^"]+)""([^"]+)"\s*-->\s*', r'"\1" --> "\2"\n    "\2" --> ', line_stripped)
                # 模式4: "状态A""状态A" --> (重复状态且后面有箭头)
                line_stripped = re.sub(r'"([^"]+)""\1"\s*-->\s*', r'"\1" --> ', line_stripped)
            
            # 修复状态转换行的格式
            # 匹配模式：State1 --> State2 { 条件 } 或 State1 --> State2: 条件
            # 匹配模式：[*] --> State { 条件 } 或 [*] --> State: 条件
            
            # 1. 修复使用花括号的转换条件：State1 --> State2 { 条件 } -> State1 --> State2 : "条件"
            # 状态名可能是 [*], 引号包裹的字符串，或未引号的标识符（可能包含空格）
            brace_pattern = r'(\[[*]\]|"[^"]+"|[A-Za-z_][A-Za-z0-9_\s]*)\s*-->\s*(\[[*]\]|"[^"]+"|[A-Za-z_][A-Za-z0-9_\s]*)\s*\{\s*([^}]+)\s*\}'
            brace_match = re.search(brace_pattern, line_stripped)
            if brace_match:
                source_state = brace_match.group(1).strip().strip('"\'')
                target_state = brace_match.group(2).strip().strip('"\'')
                condition = brace_match.group(3).strip()
                
                # 为状态名称添加引号（如果包含中文或空格）
                source_state = quote_if_needed(source_state)
                target_state = quote_if_needed(target_state)
                condition = quote_if_needed(condition)
                
                # 构建修复后的行
                fixed_line = f"{' ' * original_indent}{source_state} --> {target_state} : {condition}"
                
                # 去重检查（包含条件，因为同一状态转换可以有多个不同的条件）
                relationship_key = f"{source_state} --> {target_state} : {condition}"
                if relationship_key not in seen_relationships:
                    seen_relationships.add(relationship_key)
                    fixed_lines.append(fixed_line)
                continue
            
            # 2. 修复已有冒号但可能缺少引号的转换条件：State1 --> State2: 条件 -> State1 --> State2: "条件"
            colon_pattern = r'(\[[*]\]|"[^"]+"|[A-Za-z_][A-Za-z0-9_\s]*)\s*-->\s*(\[[*]\]|"[^"]+"|[A-Za-z_][A-Za-z0-9_\s]*)\s*:\s*(.+)$'
            colon_match = re.match(colon_pattern, line_stripped)
            if colon_match:
                source_state = colon_match.group(1).strip().strip('"\'')
                target_state = colon_match.group(2).strip().strip('"\'')
                condition = colon_match.group(3).strip().strip('"\'')
                
                # 为状态名称和条件添加引号（如果包含中文或空格）
                source_state = quote_if_needed(source_state)
                target_state = quote_if_needed(target_state)
                condition = quote_if_needed(condition)
                
                # 构建修复后的行
                fixed_line = f"{' ' * original_indent}{source_state} --> {target_state} : {condition}"
                
                # 去重检查（包含条件，因为同一状态转换可以有多个不同的条件）
                relationship_key = f"{source_state} --> {target_state} : {condition}"
                if relationship_key not in seen_relationships:
                    seen_relationships.add(relationship_key)
                    fixed_lines.append(fixed_line)
                continue
            
            # 3. 修复没有条件的转换，但状态名称需要引号：State1 --> State2
            simple_pattern = r'(\[[*]\]|"[^"]+"|[A-Za-z_][A-Za-z0-9_\s]*)\s*-->\s*(\[[*]\]|"[^"]+"|[A-Za-z_][A-Za-z0-9_\s]*)\s*$'
            simple_match = re.match(simple_pattern, line_stripped)
            if simple_match:
                source_state = simple_match.group(1).strip().strip('"\'')
                target_state = simple_match.group(2).strip().strip('"\'')
                
                # 为状态名称添加引号（如果包含中文或空格）
                source_state = quote_if_needed(source_state)
                target_state = quote_if_needed(target_state)
                
                # 构建修复后的行
                fixed_line = f"{' ' * original_indent}{source_state} --> {target_state}"
                
                # 去重检查
                relationship_key = f"{source_state} --> {target_state}"
                if relationship_key not in seen_relationships:
                    seen_relationships.add(relationship_key)
                    fixed_lines.append(fixed_line)
                continue
            
            # 4. 处理状态定义行：state 状态名 {} 或 state 状态名 { ... }
            state_def_pattern = r'state\s+([A-Za-z_][A-Za-z0-9_\s]*)\s*\{'
            state_def_match = re.match(state_def_pattern, line_stripped)
            if state_def_match:
                # 状态定义行保持原样，但需要检查状态名是否需要引号
                # 这里先保留原行，因为状态定义可能跨多行
                fixed_lines.append(line)
                continue
            
            # 其他行直接保留
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _optimize_flowchart_layout(self, mermaid_code: str) -> str:
        """优化流程图布局：对于步骤很多的流程，自动转换为TD布局"""
        if not mermaid_code or not mermaid_code.strip().startswith("flowchart"):
            return mermaid_code
        
        lines = mermaid_code.split('\n')
        first_line = lines[0].strip()
        
        # 只处理LR布局（左右布局）
        if "LR" not in first_line.upper():
            return mermaid_code
        
        # 统计节点数量（通过连接关系统计）
        node_count = 0
        node_ids = set()
        
        for line in lines[1:]:
            line = line.strip()
            if not line or line.startswith('//') or line.startswith('subgraph') or line == 'end':
                continue
            
            # 提取连接关系中的节点ID
            # 格式：NodeA --> NodeB 或 NodeA -->|label| NodeB
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
            
            # 也检查节点定义行
            node_def_patterns = [
                r'(\w+)\[', r'(\w+)\(', r'(\w+)\(\(', r'(\w+)\{', r'(\w+)\{\{'
            ]
            for pattern in node_def_patterns:
                match = re.search(pattern, line)
                if match:
                    node_ids.add(match.group(1))
        
        node_count = len(node_ids)
        
        # 如果节点超过8个，转换为TD布局（从上到下）
        if node_count > 8:
            # 替换第一行的LR为TD
            lines[0] = lines[0].replace("LR", "TD").replace("lr", "TD")
            print(f"检测到 {node_count} 个节点，自动将流程图布局从LR（左右）转换为TD（上下）以获得更好的显示效果")
            return '\n'.join(lines)
        
        return mermaid_code
    
    def _fix_subgraph_connections(self, mermaid_code: str) -> str:
        """修复流程图中subgraph的节点定义和连接问题
        
        主要修复：
        1. 修复空的subgraph（在subgraph标题中定义节点但内部为空的情况）
        2. 将在subgraph内部定义但在外部使用的节点移到subgraph外部
        3. 确保节点在使用前已定义
        """
        if not mermaid_code or not mermaid_code.strip().startswith("flowchart"):
            return mermaid_code
        
        lines = mermaid_code.split('\n')
        if not any('subgraph' in line.lower() for line in lines):
            # 没有subgraph，直接返回
            return mermaid_code
        
        # 首先修复空的subgraph问题（仅在确实为空时才修复）
        # 注意：这个修复可能会影响正常的subgraph，所以只在必要时执行
        try:
            mermaid_code = self._fix_empty_subgraphs(mermaid_code)
            lines = mermaid_code.split('\n')
        except Exception as e:
            # 如果修复出错，使用原始代码继续处理
            print(f"修复空的subgraph时出错: {str(e)}，使用原始代码")
            lines = mermaid_code.split('\n')
        
        # 收集所有节点ID和它们的位置（是否在subgraph内）
        node_definitions = {}  # node_id -> (line_index, line_content, in_subgraph)
        connections = []  # (line_index, source_id, target_id)
        subgraph_ranges = []  # [(start_line, end_line), ...]
        
        current_subgraph_start = -1
        in_subgraph = False
        
        # 第一步：识别所有节点定义和subgraph范围
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith('//') or line_stripped.startswith('flowchart'):
                continue
            
            # 检测subgraph开始
            if line_stripped.lower().startswith('subgraph'):
                current_subgraph_start = i
                in_subgraph = True
                continue
            
            # 检测subgraph结束
            if line_stripped.lower() == 'end':
                if in_subgraph and current_subgraph_start >= 0:
                    subgraph_ranges.append((current_subgraph_start, i))
                in_subgraph = False
                current_subgraph_start = -1
                continue
            
            # 检测连接关系（可能在连接中定义节点）
            arrow_patterns = ['-->', '-.->', '---', '==>']
            connection_found = False
            for pattern in arrow_patterns:
                if pattern in line_stripped:
                    # 提取源节点和目标节点
                    parts = line_stripped.split(pattern)
                    if len(parts) >= 2:
                        # 提取源节点ID（可能在连接前单独定义，或在连接中）
                        source_part = parts[0].strip()
                        source_match = re.search(r'(\w+)(?:\s*$|\s*\|)', source_part)
                        if not source_match:
                            source_match = re.search(r'(\w+)$', source_part)
                        
                        # 提取目标节点（可能在连接中定义，格式如 F1[(热油)]）
                        target_part = parts[-1].strip()
                        # 匹配目标节点：可能是 NodeID 或 NodeID[...] 等
                        target_match = re.search(r'^(\w+)', target_part)
                        
                        if source_match:
                            source_id = source_match.group(1)
                            # 检查源节点是否在当前行定义（不在node_definitions中）
                            if source_id not in node_definitions:
                                # 尝试从源部分提取节点定义
                                source_node_match = re.search(r'(\w+)(\[|\(|\{|\]|\(\(|\[\()', source_part)
                                if source_node_match:
                                    source_id = source_node_match.group(1)
                            
                            if target_match:
                                target_id = target_match.group(1)
                                connections.append((i, source_id, target_id, in_subgraph))
                                
                                # 检查目标节点是否在连接语句中定义（如 F1[(热油)]）
                                target_node_def = re.search(r'(\w+)(\[|\(|\{|\]|\(\(|\[\()', target_part)
                                if target_node_def:
                                    target_id = target_node_def.group(1)
                                    if target_id not in node_definitions:
                                        # 节点在连接语句中定义
                                        node_definitions[target_id] = (i, line, in_subgraph)
                                
                                # 同样检查源节点
                                source_node_def = re.search(r'(\w+)(\[|\(|\{|\]|\(\(|\[\()', source_part)
                                if source_node_def:
                                    source_id_from_def = source_node_def.group(1)
                                    if source_id_from_def not in node_definitions:
                                        node_definitions[source_id_from_def] = (i, line, in_subgraph)
                    connection_found = True
                    break
            
            # 如果当前行不是连接，检查是否是单独的节点定义
            if not connection_found:
                # 匹配：NodeID[文本] 或 NodeID(文本) 或 NodeID{文本} 或 NodeID((文本)) 或 NodeID[(文本)]
                node_patterns = [
                    r'^(\w+)\[', r'^(\w+)\(', r'^(\w+)\{', r'^(\w+)\(\(', r'^(\w+)\[\('
                ]
                for pattern in node_patterns:
                    match = re.match(pattern, line_stripped)
                    if match:
                        node_id = match.group(1)
                        if node_id not in node_definitions:  # 避免重复
                            node_definitions[node_id] = (i, line, in_subgraph)
                        break
        
        # 第二步：找出在subgraph内定义但在外部使用的节点
        nodes_to_move = set()
        for conn_line_idx, source_id, target_id, conn_in_subgraph in connections:
            # 如果连接在subgraph外部，但节点在subgraph内部定义
            if not conn_in_subgraph:
                if source_id in node_definitions and node_definitions[source_id][2]:
                    nodes_to_move.add(source_id)
                if target_id in node_definitions and node_definitions[target_id][2]:
                    nodes_to_move.add(target_id)
        
        if not nodes_to_move:
            # 没有需要移动的节点
            return mermaid_code
        
        # 第三步：重构代码，将需要移动的节点定义移到subgraph外部
        fixed_lines = []
        nodes_to_move_defs = {}  # 保存需要移动的节点定义
        
        in_subgraph = False
        skip_subgraph = False
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # 处理subgraph开始
            if line_stripped.lower().startswith('subgraph'):
                in_subgraph = True
                fixed_lines.append(line)
                continue
            
            # 处理subgraph结束
            if line_stripped.lower() == 'end':
                in_subgraph = False
                fixed_lines.append(line)
                continue
            
            # 如果在subgraph内，检查是否是需要移动的节点定义
            if in_subgraph:
                # 检查当前行是否定义了需要移动的节点
                node_found = False
                for node_id in nodes_to_move:
                    if node_id in node_definitions:
                        def_line_idx, def_line, _ = node_definitions[node_id]
                        if def_line_idx == i:
                            # 这是需要移动的节点定义
                            nodes_to_move_defs[node_id] = line
                            node_found = True
                            # 不添加到fixed_lines，因为要移到外部
                            break
                
                if not node_found:
                    fixed_lines.append(line)
            else:
                # 不在subgraph内
                fixed_lines.append(line)
        
        # 第四步：在所有subgraph之前插入需要移动的节点定义
        # 找到第一个subgraph的位置
        first_subgraph_idx = -1
        for i, line in enumerate(fixed_lines):
            if line.strip().lower().startswith('subgraph'):
                first_subgraph_idx = i
                break
        
        if first_subgraph_idx >= 0:
            # 在第一个subgraph之前插入节点定义
            inserted_lines = []
            for node_id in nodes_to_move:
                if node_id in nodes_to_move_defs:
                    inserted_lines.append(nodes_to_move_defs[node_id])
            
            if inserted_lines:
                # 插入节点定义
                fixed_lines = fixed_lines[:first_subgraph_idx] + inserted_lines + fixed_lines[first_subgraph_idx:]
        
        return '\n'.join(fixed_lines)
    
    def _fix_empty_subgraphs(self, mermaid_code: str) -> str:
        """修复空的subgraph问题
        
        如果subgraph是空的（只有标题，内部没有节点定义），但标题中包含节点信息，
        需要在subgraph内部添加节点定义，或者将节点移到外部。
        """
        lines = mermaid_code.split('\n')
        fixed_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            line_stripped = line.strip()
            
            # 检测subgraph开始
            if line_stripped.lower().startswith('subgraph'):
                # 提取subgraph ID和标签
                # 格式：subgraph ID["Label"] 或 subgraph ID 或 subgraph "Label"
                # 使用更灵活的匹配，处理标签中的换行符等特殊字符
                subgraph_match = re.match(r'subgraph\s+([^\s\["]+?)(?:\["([^"]+)"\])?', line_stripped, re.IGNORECASE | re.DOTALL)
                if not subgraph_match:
                    # 尝试其他格式
                    subgraph_match = re.match(r'subgraph\s+([^\s\["]+?)(?:\[([^\]]+)\])?', line_stripped, re.IGNORECASE | re.DOTALL)
                
                if subgraph_match:
                    subgraph_id = subgraph_match.group(1)
                    # 提取标签（如果存在），注意标签可能在引号中
                    if subgraph_match.group(2):
                        # 从匹配组中获取标签内容（不包含引号）
                        raw_label = subgraph_match.group(2)
                        # 移除可能的引号包装（如果正则匹配到了引号）
                        subgraph_label = raw_label.strip('"').strip("'")
                    else:
                        subgraph_label = subgraph_id
                    
                    fixed_lines.append(line)
                    i += 1
                    
                    # 检查subgraph内容是否为空（直到遇到end）
                    subgraph_start_idx = i
                    subgraph_content = []
                    empty_subgraph = True
                    
                    while i < len(lines):
                        current_line = lines[i]
                        current_stripped = current_line.strip()
                        
                        # 跳过空行
                        if not current_stripped:
                            i += 1
                            continue
                        
                        # 遇到end，结束subgraph
                        if current_stripped.lower() == 'end':
                            break
                        
                        # 如果有非空内容（不是注释），说明subgraph不为空
                        if not current_stripped.startswith('//'):
                            empty_subgraph = False
                            subgraph_content.append(current_line)
                        
                        i += 1
                    
                    # 如果subgraph为空，需要在内部添加节点定义
                    # 但要注意：只有在外部确实有引用这个节点时才添加
                    if empty_subgraph and subgraph_id:
                        # 检查外部是否有对这个节点的引用
                        # 简单检查：如果 subgraph_id 在后续的代码中被引用
                        has_external_reference = False
                        for j in range(i + 1, len(lines)):
                            future_line = lines[j].strip()
                            # 检查是否在连接中使用了这个节点ID
                            if future_line and (f'{subgraph_id} -->' in future_line or f'--> {subgraph_id}' in future_line or f'--> {subgraph_id}[' in future_line):
                                has_external_reference = True
                                break
                        
                        # 只有在有外部引用时才添加节点定义
                        if has_external_reference:
                            # 在subgraph内部添加节点定义
                            # 使用subgraph的ID作为节点ID，标签作为节点内容
                            indent = '    '  # 标准缩进
                            
                            # 处理标签：确保中文和特殊字符用引号包裹
                            # subgraph_label 应该已经是纯文本（不包含引号）
                            # 如果标签包含中文、空格或特殊字符（如 \n），需要用引号包裹
                            # 转义标签内的引号和反斜杠
                            escaped_label = subgraph_label.replace('\\', '\\\\').replace('"', '\\"')
                            # 始终使用引号包裹标签（Mermaid 要求中文标签必须用引号）
                            label_content = f'"{escaped_label}"'
                            
                            node_def_line = f'{indent}{subgraph_id}[{label_content}]'
                            fixed_lines.append(node_def_line)
                    
                    # 添加subgraph内容
                    fixed_lines.extend(subgraph_content)
                    
                    # 添加end
                    if i < len(lines) and lines[i].strip().lower() == 'end':
                        fixed_lines.append(lines[i])
                        i += 1
                    
                    continue
            
            fixed_lines.append(line)
            i += 1
        
        return '\n'.join(fixed_lines)
    
    def _extract_mermaid_code(self, response: str) -> str:
        """从LLM响应中提取Mermaid代码（委托给工具类）"""
        return CodeExtractor.extract_mermaid_code(response)
    
    def explain_mermaid_error(self, mermaid_code: str, error_info: Dict) -> str:
        """使用AI解释Mermaid语法错误并提供修复建议
        
        Args:
            mermaid_code: 完整的Mermaid代码
            error_info: 错误信息字典，包含message, line_number, error_lines, code_snippet
            
        Returns:
            AI生成的错误解释和修复建议
        """
        error_message = error_info.get('message', '未知错误')
        error_lines = error_info.get('error_lines', [])
        code_snippet = error_info.get('code_snippet', '')
        
        # 检测图表类型
        diagram_type = self._detect_diagram_type(mermaid_code)
        
        # 根据图表类型生成特定的提示词
        type_specific_notes = self._get_type_specific_notes(diagram_type)
        
        type_specific_requirements = self._get_type_specific_requirements(diagram_type)
        prompt = GENERATION_ERROR_EXPLANATION_PROMPT_TEMPLATE.format(
            error_message=error_message,
            code_snippet=code_snippet if code_snippet else '（未提供代码片段）',
            mermaid_code=mermaid_code,
            diagram_type=diagram_type,
            type_specific_notes=type_specific_notes,
            type_specific_requirements=type_specific_requirements
        )
        
        try:
            # 增加 max_tokens 以确保能生成完整的代码
            # 估算需要的 token 数：原代码长度 + 解释文本（通常2-3倍）
            estimated_tokens = len(mermaid_code) // 3 + 1500
            max_tokens = max(3000, estimated_tokens)  # 至少3000，根据代码长度动态调整
            explanation = self.model(prompt, stream=False, temperature=0.3, max_tokens=min(max_tokens, 8000))
            return explanation.strip()
        except Exception as e:
            return f"无法生成AI解释：{str(e)}\n\n错误信息：{error_message}"
    
    def _detect_diagram_type(self, mermaid_code: str) -> str:
        """检测Mermaid代码的图表类型"""
        if not mermaid_code:
            return "未知"
        
        first_line = mermaid_code.strip().split('\n')[0].strip()
        
        type_map = {
            'classDiagram': '类图',
            'flowchart': '流程图',
            'sequenceDiagram': '时序图',
            'gantt': '甘特图',
            'stateDiagram-v2': '状态图',
            'stateDiagram': '状态图',
            'pie': '饼图',
            'quadrantChart': '象限图',
            'journey': '用户旅程图'
        }
        
        for key, name in type_map.items():
            if first_line.startswith(key):
                return name
        
        return "未知"
    
    def _get_type_specific_notes(self, diagram_type: str) -> str:
        """根据图表类型获取特定的修复提示"""
        if diagram_type == '类图':
            return TYPE_SPECIFIC_NOTES_CLASS_DIAGRAM
        elif diagram_type == '象限图':
            return TYPE_SPECIFIC_NOTES_QUADRANT_CHART
        else:
            return TYPE_SPECIFIC_NOTES_DEFAULT
    
    def _get_type_specific_requirements(self, diagram_type: str) -> str:
        """根据图表类型获取特定的修复要求"""
        if diagram_type == '类图':
            return TYPE_SPECIFIC_REQUIREMENTS_CLASS_DIAGRAM
        elif diagram_type == '象限图':
            return TYPE_SPECIFIC_REQUIREMENTS_QUADRANT_CHART
        else:
            return TYPE_SPECIFIC_REQUIREMENTS_DEFAULT
    
    def extract_fixed_code_from_explanation(self, explanation: str, original_code: str) -> str:
        """从AI解释中提取修复后的代码，并自动修复可能遗漏的语法错误
        
        Args:
            explanation: AI生成的解释文本
            original_code: 原始代码
            
        Returns:
            修复后的代码，如果提取失败则返回原始代码
        """
        import re
        
        extracted_codes = []  # 收集所有提取的代码 [(type, code), ...]
        
        # 1. 优先查找"修复后的完整代码"部分（通常是最完整、最准确的）
        fixed_section_pattern = r'##\s*修复后的完整代码.*?\n```(?:mermaid)?\s*\n(.*?)```'
        matches = re.findall(fixed_section_pattern, explanation, re.DOTALL)
        if matches:
            extracted_codes.append(('fixed_section', matches[0].strip()))
        
        # 2. 其次查找 ```mermaid 代码块
        mermaid_pattern = r'```mermaid\s*\n(.*?)```'
        matches = re.findall(mermaid_pattern, explanation, re.DOTALL)
        if matches:
            extracted_codes.append(('mermaid_block', matches[-1].strip()))
        
        # 3. 如果没有找到，尝试查找任何代码块
        if not extracted_codes:
            code_pattern = r'```(?:mermaid)?\s*\n(.*?)```'
            matches = re.findall(code_pattern, explanation, re.DOTALL)
            if matches:
                extracted_codes.append(('code_block', matches[-1].strip()))
        
        # 从提取的代码中选择最合适的（优先选择"修复后的完整代码"部分）
        for code_type, fixed_code in extracted_codes:
            if not fixed_code:
                continue
            
            # 检查代码完整性：必须至少是原代码长度的70%才认为是完整的
            if len(fixed_code) < len(original_code) * 0.7:
                continue
            
            # 进一步验证：确保代码包含完整的图表声明
            if not (fixed_code.startswith('classDiagram') or fixed_code.startswith('flowchart') or \
                   any(fixed_code.startswith(d) for d in ['sequenceDiagram', 'gantt', 'stateDiagram', 'pie', 'journey'])):
                continue
            
            # 如果是类图，应用自动修复确保没有遗漏的错误（如缺少class关键字）
            if fixed_code.strip().startswith('classDiagram'):
                fixed_code = self._fix_class_diagram_syntax(fixed_code)
                # 再次验证修复后的代码长度（修复后长度可能会变化，但应该不会减少太多）
                if len(fixed_code) < len(original_code) * 0.6:
                    continue
            
            # 找到合适的代码，返回修复后的版本
            return fixed_code
        
        # 如果都找不到或代码不完整，返回原始代码（避免丢失内容）
        # 注意：返回原始代码后，会在调用处再次应用自动修复
        return original_code
