"""语法修复器工厂 - 工厂模式"""
from typing import Dict, Optional, ClassVar
from agents.fixers.base_fixer import SyntaxFixer
from agents.fixers.class_diagram_fixer import ClassDiagramFixer
from agents.fixers.class_diagram_fixer_advanced import ClassDiagramFixerAdvanced
from agents.fixers.state_diagram_fixer import StateDiagramFixer
from agents.fixers.gantt_fixer import GanttFixer
from agents.fixers.sequence_fixer import SequenceDiagramFixer
from agents.fixers.quadrant_chart_fixer import QuadrantChartFixer
from agents.fixers.flowchart_fixer import FlowchartFixer
from agents.fixers.pie_chart_fixer import PieChartFixer
from agents.fixers.journey_fixer import JourneyFixer


class SyntaxFixerFactory:
    """语法修复器工厂"""
    
    # 注册所有修复器
    _fixers: ClassVar[Dict[str, type]] = {
        "flowchart": FlowchartFixer,
        "classDiagram": ClassDiagramFixer,
        "stateDiagram-v2": StateDiagramFixer,
        "gantt": GanttFixer,
        "sequenceDiagram": SequenceDiagramFixer,
        "quadrantChart": QuadrantChartFixer,
        "pie": PieChartFixer,
        "journey": JourneyFixer,
    }
    
    _advanced_fixers: ClassVar[Dict[str, type]] = {
        "classDiagram": ClassDiagramFixerAdvanced,
    }
    
    @classmethod
    def create(cls, diagram_type: str, advanced: bool = False) -> Optional[SyntaxFixer]:
        """创建修复器实例
        
        Args:
            diagram_type: 图表类型
            advanced: 是否使用高级修复器
            
        Returns:
            修复器实例，如果不存在则返回None
        """
        if advanced:
            fixer_class = cls._advanced_fixers.get(diagram_type)
        else:
            fixer_class = cls._fixers.get(diagram_type)
        
        if fixer_class:
            return fixer_class()
        return None
    
    @classmethod
    def register(cls, diagram_type: str, fixer_class: type, advanced: bool = False):
        """注册修复器类
        
        Args:
            diagram_type: 图表类型
            fixer_class: 修复器类
            advanced: 是否是高级修复器
        """
        if advanced:
            cls._advanced_fixers[diagram_type] = fixer_class
        else:
            cls._fixers[diagram_type] = fixer_class

