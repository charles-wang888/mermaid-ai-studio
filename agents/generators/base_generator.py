"""图表生成器基类"""
from abc import ABC, abstractmethod
from typing import Dict
from agents.base_agent import DiagramAgentBase
from agents.utils.code_extractor import CodeExtractor


class DiagramGenerator(ABC):
    """图表生成器抽象基类 - 策略模式"""
    
    def __init__(self, agent: DiagramAgentBase):
        """初始化生成器
        
        Args:
            agent: 智能体实例，用于调用LLM
        """
        self.agent = agent
    
    @abstractmethod
    def generate(self, requirements: str) -> str:
        """生成图表代码
        
        Args:
            requirements: 需求描述
            
        Returns:
            Mermaid代码字符串
        """
        pass
    
    @abstractmethod
    def get_prompt_template(self) -> str:
        """获取提示词模板"""
        pass
    
    @abstractmethod
    def get_diagram_type(self) -> str:
        """获取图表类型"""
        pass
    
    def extract_and_validate(self, response: str) -> str:
        """提取并验证代码（通用方法）"""
        from agents.utils.code_extractor import CodeExtractor
        from agents.utils.text_cleaner import TextCleaner
        
        # 提取Mermaid代码
        mermaid_code = CodeExtractor.extract_mermaid_code(response)
        
        # 清理HTML标签和Markdown符号
        mermaid_code = TextCleaner.clean_mermaid_code(mermaid_code)
        
        return mermaid_code

