"""图表生成器工厂 - 工厂模式"""
from typing import Dict, ClassVar
from agents.base_agent import DiagramAgentBase
from agents.generators.base_generator import DiagramGenerator
from agents.generators.flowchart_generator import FlowchartGenerator
from agents.generators.sequence_generator import SequenceDiagramGenerator
from agents.generators.gantt_generator import GanttGenerator
from agents.generators.class_diagram_generator import ClassDiagramGenerator
from agents.generators.state_diagram_generator import StateDiagramGenerator
from agents.generators.pie_chart_generator import PieChartGenerator
from agents.generators.quadrant_chart_generator import QuadrantChartGenerator
from agents.generators.journey_generator import JourneyGenerator


class DiagramGeneratorFactory:
    """图表生成器工厂"""
    
    # 注册所有生成器
    _generators: ClassVar[Dict[str, type]] = {
        "flowchart": FlowchartGenerator,
        "sequenceDiagram": SequenceDiagramGenerator,
        "gantt": GanttGenerator,
        "classDiagram": ClassDiagramGenerator,
        "stateDiagram-v2": StateDiagramGenerator,
        "pie": PieChartGenerator,
        "quadrantChart": QuadrantChartGenerator,
        "journey": JourneyGenerator,
    }
    
    @classmethod
    def register(cls, diagram_type: str, generator_class: type):
        """注册生成器类
        
        Args:
            diagram_type: 图表类型
            generator_class: 生成器类
        """
        cls._generators[diagram_type] = generator_class
    
    @classmethod
    def create(cls, diagram_type: str, agent: DiagramAgentBase) -> DiagramGenerator:
        """创建生成器实例
        
        Args:
            diagram_type: 图表类型
            agent: 智能体实例
            
        Returns:
            生成器实例
        """
        generator_class = cls._generators.get(diagram_type)
        if not generator_class:
            # 默认使用流程图生成器
            generator_class = cls._generators.get("flowchart")
        if not generator_class:
            raise ValueError(f"未找到图表类型 {diagram_type} 的生成器")
        return generator_class(agent)

