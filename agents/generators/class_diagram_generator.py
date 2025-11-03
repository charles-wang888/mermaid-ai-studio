"""类图生成器"""
from agents.generators.base_generator import DiagramGenerator
from agents.prompts_config import GENERATION_CLASS_DIAGRAM_PROMPT_TEMPLATE


class ClassDiagramGenerator(DiagramGenerator):
    """类图生成器"""
    
    def get_prompt_template(self) -> str:
        return GENERATION_CLASS_DIAGRAM_PROMPT_TEMPLATE
    
    def get_diagram_type(self) -> str:
        return "classDiagram"
    
    def generate(self, requirements: str) -> str:
        """生成类图代码"""
        prompt = self.get_prompt_template().format(requirements=requirements)
        response = self.agent.model(prompt, stream=False, temperature=0.1, max_tokens=3000)
        
        # 提取并清理代码
        mermaid_code = self.extract_and_validate(response)
        
        # 验证代码格式
        if hasattr(self.agent, '_validate_and_fix_mermaid_code'):
            mermaid_code = self.agent._validate_and_fix_mermaid_code(mermaid_code, self.get_diagram_type())
        
        # 使用修复器修复语法错误
        from agents.fixers.fixer_factory import SyntaxFixerFactory
        fixer = SyntaxFixerFactory.create(self.get_diagram_type())
        if fixer:
            mermaid_code = fixer.fix(mermaid_code)
        
        # 再次进行语法验证，如果还有错误，尝试高级修复
        if hasattr(self.agent, 'mermaid_renderer') and self.agent.mermaid_renderer:
            is_valid, error_info = self.agent.mermaid_renderer.validate_syntax_with_details(mermaid_code)
            if not is_valid:
                advanced_fixer = SyntaxFixerFactory.create(self.get_diagram_type(), advanced=True)
                if advanced_fixer:
                    mermaid_code = advanced_fixer.fix(mermaid_code, error_info=error_info)
        
        return mermaid_code

