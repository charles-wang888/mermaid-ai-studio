"""语法修复器基类"""
from abc import ABC, abstractmethod


class SyntaxFixer(ABC):
    """语法修复器抽象基类 - 策略模式"""
    
    @abstractmethod
    def fix(self, mermaid_code: str, **kwargs) -> str:
        """修复语法错误
        
        Args:
            mermaid_code: Mermaid代码字符串
            **kwargs: 其他参数（如error_info等）
            
        Returns:
            修复后的Mermaid代码
        """
        pass
    
    @abstractmethod
    def get_diagram_type(self) -> str:
        """获取支持的图表类型"""
        pass

