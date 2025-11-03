"""LLM客户端封装 - 支持多种模型后端"""
import re
import json
import requests
import logging
from typing import Dict, Optional, Literal, Iterator, Union
from config import LLM_CONFIG, DEFAULT_LLM_BACKEND


class MultiLLMClient:
    """多后端LLM客户端 - 支持Ollama, HuggingFace, vLLM, SiliconFlow, OpenAI, Anthropic"""
    
    def __init__(self, backend: str = None):
        """
        初始化LLM客户端
        
        Args:
            backend: 后端类型 ("ollama", "huggingface", "vllm", "siliconflow", "openai", "anthropic")
        """
        self.backend = backend or DEFAULT_LLM_BACKEND
        
        if self.backend not in LLM_CONFIG:
            raise ValueError(f"不支持的模型后端: {self.backend}")
        
        self.config = LLM_CONFIG[self.backend]
        self.base_url = self.config["base_url"]
        self.api_key = self.config.get("api_key", "")
        self.timeout = self.config.get("timeout", 60)
        
        # 根据后端类型设置模型名
        self.model_name = self.config.get("model_name") or self.config.get("model_id", "")
    
    def chat(self, messages: list, stream: bool = False, **kwargs) -> str:
        """
        发送聊天请求
        
        Args:
            messages: 消息列表
            stream: 是否流式返回
            **kwargs: 其他参数
        
        Returns:
            模型回复内容
        """
        try:
            if self.backend == "ollama":
                return self._chat_ollama(messages, stream, **kwargs)
            elif self.backend == "huggingface":
                return self._chat_huggingface(messages, **kwargs)
            elif self.backend == "vllm":
                return self._chat_openai_compatible(messages, stream, **kwargs)
            elif self.backend == "siliconflow":
                return self._chat_openai_compatible(messages, stream, **kwargs)
            elif self.backend == "openai":
                return self._chat_openai_compatible(messages, stream, **kwargs)
            elif self.backend == "anthropic":
                return self._chat_anthropic(messages, stream, **kwargs)
            else:
                raise ValueError(f"未实现的后端: {self.backend}")
        
        except requests.exceptions.RequestException as e:
            print(f"LLM调用失败 ({self.backend}): {e}")
            return self._mock_response(messages[-1].get("content", ""))
    
    def _chat_ollama(self, messages: list, stream: bool = False, **kwargs) -> str:
        """Ollama聊天"""
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": stream,
            **kwargs
        }
        
        response = requests.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        result = response.json()
        
        if stream:
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
        else:
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    def _chat_openai_compatible(self, messages: list, stream: bool = False, **kwargs) -> Union[str, Iterator[str]]:
        """OpenAI兼容的聊天接口（vLLM, SiliconFlow, OpenAI）"""
        url = f"{self.base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        
        if self.api_key:
            if self.backend == "openai":
                headers["Authorization"] = f"Bearer {self.api_key}"
            elif self.backend == "siliconflow":
                headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": stream,
            **kwargs
        }
        
        try:
            with requests.post(url, json=payload, headers=headers, timeout=self.timeout, stream=stream) as response:
                response.raise_for_status()
                
                if stream:
                    for chunk in response.iter_lines(decode_unicode=True):
                        if not chunk:  # Skip keep-alive lines
                            continue
                        
                        # Check for SSE data lines
                        if chunk.startswith('data:'):
                            try:
                                # Remove 'data: ' prefix and parse JSON
                                data = json.loads(chunk[6:].strip())
                                if 'choices' in data:
                                    content = data['choices'][0].get('delta', {}).get('content', '')
                                    if content:
                                        yield content
                            except json.JSONDecodeError as e:
                                logging.warning(f"Failed to parse SSE chunk: {str(e)}")
                                continue
                else:
                    result = response.json()
                    return result.get("choices", [{}])[0].get("message", {}).get("content", "")
        except (requests.RequestException, json.JSONDecodeError) as e:
            logging.error(f"Error in API call: {str(e)}", exc_info=True)
            raise
    
    def _chat_huggingface(self, messages: list, **kwargs) -> str:
        """HuggingFace聊天"""
        url = f"{self.base_url}/{self.model_name}"
        headers = {"Content-Type": "application/json"}
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        # HuggingFace格式转换
        prompt = self._messages_to_prompt(messages)
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "return_full_text": False,
                "max_new_tokens": kwargs.get("max_tokens", 512),
                "temperature": kwargs.get("temperature", 0.7),
            },
            **{k: v for k, v in kwargs.items() if k not in ["max_tokens", "temperature"]}
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        result = response.json()
        
        # HuggingFace返回格式
        if isinstance(result, list) and len(result) > 0:
            return result[0].get("generated_text", "")
        elif isinstance(result, dict):
            return result.get("generated_text", "")
        return ""
    
    def _chat_anthropic(self, messages: list, stream: bool = False, **kwargs) -> str:
        """Anthropic Claude聊天"""
        url = f"{self.base_url}/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        # Claude格式转换
        claude_messages = self._messages_to_claude(messages)
        
        payload = {
            "model": self.model_name,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "messages": claude_messages,
            **{k: v for k, v in kwargs.items() if k != "max_tokens"}
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        result = response.json()
        
        return result.get("content", [{}])[0].get("text", "")
    
    def _messages_to_prompt(self, messages: list) -> str:
        """将消息列表转换为提示字符串"""
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prompt += f"{role.capitalize()}: {content}\n"
        return prompt
    
    def _messages_to_claude(self, messages: list) -> list:
        """将消息列表转换为Claude格式"""
        claude_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            # Claude不支持system role，需要转换为user
            if role == "system":
                role = "user"
            claude_messages.append({
                "role": role,
                "content": msg.get("content", "")
            })
        return claude_messages
    
    def _mock_response(self, user_message: str) -> str:
        """模拟响应（用于演示）"""
        if "澄清" in user_message:
            return """---
状态：需要澄清
问题1：您希望绘制的系统是什么类型的？（例如：微服务、单体应用、数据管道等）
问题2：系统的主要用户是谁？预期的用户规模有多大？
"""
        else:
            return """组件1：名称=用户服务，类型=input，属性=用户认证、用户管理，形状=rectangle
组件2：名称=业务处理，类型=process，属性=逻辑处理、状态管理，形状=rounded_rect
组件3：名称=数据存储，类型=storage，属性=持久化、备份，形状=circle
关系1：源=用户服务，目标=业务处理，类型=data，内容=用户请求
关系2：源=业务处理，目标=数据存储，类型=data，内容=数据保存
"""


# 为了兼容性，保留旧类名
SimpleLLMClient = MultiLLMClient
