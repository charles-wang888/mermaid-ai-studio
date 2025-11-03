"""时序图生成器"""
from agents.generators.base_generator import DiagramGenerator
from agents.prompts_config import GENERATION_SEQUENCE_DIAGRAM_PROMPT_TEMPLATE


class SequenceDiagramGenerator(DiagramGenerator):
    """时序图生成器"""
    
    def get_prompt_template(self) -> str:
        return GENERATION_SEQUENCE_DIAGRAM_PROMPT_TEMPLATE
    
    def get_diagram_type(self) -> str:
        return "sequenceDiagram"
    
    def generate(self, requirements: str) -> str:
        """生成时序图代码"""
        prompt = self.get_prompt_template().format(requirements=requirements)
        response = self.agent.model(prompt, stream=False, temperature=0.1, max_tokens=3000)
        
        # 提取并清理代码
        mermaid_code = self.extract_and_validate(response)
        
        # 验证并修复代码
        if hasattr(self.agent, '_validate_and_fix_mermaid_code'):
            mermaid_code = self.agent._validate_and_fix_mermaid_code(mermaid_code, self.get_diagram_type())
        
        return mermaid_code

