"""基础智能体类"""
from typing import Dict, List, Optional
from agents.llm_client import SimpleLLMClient, MultiLLMClient
from agents.prompts_config import BASE_AGENT_SYSTEM_PROMPT, BASE_AGENT_DEFAULT_REPLY


class DiagramAgentBase:
    """架构图绘制智能体基类"""
    
    def __init__(
        self,
        name: str = "diagram_agent",
        sys_prompt: str = BASE_AGENT_SYSTEM_PROMPT,
        model_config_name: str = "default",
        backend: Optional[str] = None,
        **kwargs
    ):
        self.name = name
        self.sys_prompt = sys_prompt
        # 支持传入backend参数
        if backend:
            self.llm_client = MultiLLMClient(backend=backend)
        else:
            self.llm_client = SimpleLLMClient()
    
    def model(self, prompt: str, stream: bool = False, **kwargs) -> str:
        """调用模型
        
        Args:
            prompt: 用户提示词
            stream: 是否流式返回
            **kwargs: 其他参数（如temperature, max_tokens等）
        """
        messages = [
            {"role": "system", "content": self.sys_prompt},
            {"role": "user", "content": prompt}
        ]
        return self.llm_client.chat(messages, stream=stream, **kwargs)
