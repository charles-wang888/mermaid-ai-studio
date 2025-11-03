"""错误信息工厂 - 工厂模式"""
from typing import Dict, List, Optional


class ErrorInfoFactory:
    """错误信息工厂 - 统一构建错误信息对象"""
    
    @staticmethod
    def create_error_info(
        message: str,
        line_number: Optional[int] = None,
        error_lines: Optional[List[int]] = None,
        code_snippet: str = "",
        diagram_type: Optional[str] = None,
        source: str = "验证"
    ) -> Dict:
        """创建错误信息字典
        
        Args:
            message: 错误消息
            line_number: 错误行号
            error_lines: 可能有错误的行号列表
            code_snippet: 错误代码片段
            diagram_type: 图表类型
            source: 错误来源
            
        Returns:
            错误信息字典
        """
        return {
            'message': f"[{source}] {message}",
            'line_number': line_number,
            'error_lines': error_lines or [],
            'code_snippet': code_snippet,
            'diagram_type': diagram_type,
            'source': source
        }
    
    @staticmethod
    def merge_errors(all_errors: List[Dict]) -> Optional[Dict]:
        """合并多个错误信息
        
        Args:
            all_errors: 所有错误信息列表
            
        Returns:
            合并后的错误信息字典
        """
        if not all_errors:
            return None
        
        error_messages = []
        all_error_lines = set()
        all_code_snippets = []
        diagram_type = None
        
        for error in all_errors:
            source = error.get('source', '验证')
            message = error.get('message', '')
            # 如果消息已经包含来源，不再重复添加
            if not message.startswith('['):
                error_messages.append(f"[{source}] {message}")
            else:
                error_messages.append(message)
            all_error_lines.update(error.get('error_lines', []))
            code_snippet = error.get('code_snippet', '')
            if code_snippet:
                all_code_snippets.append(code_snippet)
            if not diagram_type and error.get('diagram_type'):
                diagram_type = error.get('diagram_type')
        
        combined_message = "\n\n".join(error_messages)
        combined_error_lines = sorted(list(all_error_lines))
        combined_code_snippet = "\n\n".join(all_code_snippets) if all_code_snippets else ""
        
        return {
            'message': combined_message,
            'line_number': combined_error_lines[0] if combined_error_lines else None,
            'error_lines': combined_error_lines,
            'code_snippet': combined_code_snippet,
            'diagram_type': diagram_type
        }
    
    @staticmethod
    def create_success_info(diagram_type: Optional[str] = None) -> Dict:
        """创建成功信息字典
        
        Args:
            diagram_type: 图表类型
            
        Returns:
            成功信息字典
        """
        return {
            'message': None,
            'line_number': None,
            'error_lines': [],
            'code_snippet': '',
            'diagram_type': diagram_type
        }

