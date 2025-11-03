"""配置文件"""
import os
from dotenv import load_dotenv

load_dotenv()

# LLM模型配置
# 支持的模型后端: ollama, huggingface, vllm, siliconflow, openai, anthropic

LLM_CONFIG = {
    # Ollama本地模型（默认）
    "ollama": {
        "model_name": "qwen2.5:7b",  # 可以改为qwen3:4b等其他模型
        "base_url": "http://localhost:11434/v1",
        "api_key": "NA",
        "timeout": 60,
    },
    
    # HuggingFace模型
    "huggingface": {
        "model_name": "Qwen/Qwen2.5-7B-Instruct",
        "base_url": "https://api-inference.huggingface.co/models",
        "api_key": os.getenv("HUGGINGFACE_API_KEY", ""),
        "timeout": 120,
    },
    
    # vLLM服务
    "vllm": {
        "model_name": "Qwen/Qwen2.5-7B-Instruct",
        "base_url": "http://localhost:8000/v1",
        "api_key": os.getenv("VLLM_API_KEY", ""),
        "timeout": 120,
    },
    
    # 硅基流动
    "siliconflow": {
        "model_name": "Qwen/Qwen2.5-7B-Instruct",
        "base_url": "https://api.siliconflow.cn/v1",
        "api_key": os.getenv("SILICONFLOW_API_KEY", ""),
        "timeout": 120,
    },
    
    # OpenAI API
    "openai": {
        "model_name": "gpt-4o-mini",
        "base_url": "https://api.openai.com/v1",
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "timeout": 60,
    },
    
    # Anthropic Claude
    "anthropic": {
        "model_name": "claude-3-5-sonnet-20241022",
        "base_url": "https://api.anthropic.com/v1",
        "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
        "timeout": 60,
    },
}

# 默认使用的后端
DEFAULT_LLM_BACKEND = "ollama"

# 绘图配置
DRAWING_CONFIG = {
    "canvas_size": {"width": 1200, "height": 800},
    "component_colors": {
        "input": "#E3F2FD",
        "process": "#E8F5E9",
        "storage": "#FFF9C4",
        "output": "#FFE0B2",
        "control": "#F3E5F5",
        "external": "#F5F5F5",
    },
    "connection_colors": {
        "data": "#1976D2",
        "control": "#388E3C",
        "feedback": "#F57C00",
        "critical": "#D32F2F",
    },
    "node_size": {"width": 120, "height": 80},
    "margin": 50,
}

# 导出配置
EXPORT_CONFIG = {
    "png": {"dpi": 300, "scale": 2.0},
    "jpg": {"dpi": 300, "quality": 95},
}

# 需求澄清配置
CLARIFICATION_CONFIG = {
    "max_rounds": 3,  # 最大澄清轮数（更贴近Traycer体验）
    "confidence_threshold": 0.8,  # 置信度阈值
    "clarification_template": """
    请针对以下架构需求进行澄清：
    
    需求描述：{requirement}
    
    当前理解：
    {current_understanding}
    
    请提出需要澄清的问题（如有）：
    1. 
    2. 
    3. 
    
    如果理解清晰，请回答："理解清晰，可以开始绘制"
    """
}
