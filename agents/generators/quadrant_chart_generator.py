"""象限图生成器"""
from agents.generators.base_generator import DiagramGenerator
from agents.prompts_config import GENERATION_QUADRANT_CHART_PROMPT_TEMPLATE


class QuadrantChartGenerator(DiagramGenerator):
    """象限图生成器"""
    
    def get_prompt_template(self) -> str:
        return GENERATION_QUADRANT_CHART_PROMPT_TEMPLATE
    
    def get_diagram_type(self) -> str:
        return "quadrantChart"
    
    def generate(self, requirements: str) -> str:
        """生成象限图代码"""
        prompt = self.get_prompt_template().format(requirements=requirements)
        response = self.agent.model(prompt, stream=False, temperature=0.1, max_tokens=2000)
        
        # 提取并清理代码
        mermaid_code = self.extract_and_validate(response)
        
        # 验证代码格式
        if hasattr(self.agent, '_validate_and_fix_mermaid_code'):
            mermaid_code = self.agent._validate_and_fix_mermaid_code(mermaid_code, self.get_diagram_type())
        
        # 规范化代码：去除所有多余的空行
        if mermaid_code and mermaid_code.strip().startswith('quadrantChart'):
            lines = mermaid_code.split('\n')
            cleaned_lines = []
            prev_empty = False
            for line in lines:
                line_stripped = line.strip()
                if line_stripped == 'quadrantChart' or cleaned_lines:
                    if not line_stripped:
                        if not prev_empty and cleaned_lines:
                            cleaned_lines.append('')
                            prev_empty = True
                    else:
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

