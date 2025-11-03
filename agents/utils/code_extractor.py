"""代码提取工具类"""
from typing import Optional


class CodeExtractor:
    """从LLM响应中提取代码的工具类"""
    
    @staticmethod
    def extract_mermaid_code(response: str) -> str:
        """从LLM响应中提取Mermaid代码
        
        Args:
            response: LLM的响应文本
            
        Returns:
            提取出的Mermaid代码
        """
        response = response.strip()
        
        # 如果包含markdown代码块，提取其中的内容
        if "```" in response:
            lines = response.split('\n')
            code_lines = []
            in_code = False
            code_lang = None
            
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('```'):
                    # 检查是否是mermaid代码块
                    if 'mermaid' in stripped.lower():
                        code_lang = 'mermaid'
                    in_code = not in_code
                    if not in_code:
                        break
                    continue
                if in_code:
                    code_lines.append(line)
            
            if code_lines:
                return '\n'.join(code_lines)
        
        # 如果没有代码块，直接返回响应（可能已经是纯代码）
        return response

