"""需求澄清智能体"""
from typing import Dict, List
from agents.base_agent import DiagramAgentBase
from config import CLARIFICATION_CONFIG
from agents.prompts_config import (
    CLARIFICATION_SYSTEM_PROMPT,
    CLARIFICATION_GENERATE_TODO_PROMPT,
    CLARIFICATION_BUILD_PROMPT_TEMPLATE,
    CLARIFICATION_TODO_ITEM_PROMPT_TEMPLATE,
    CLARIFICATION_COLLECT_QUESTIONS_PROMPT_TEMPLATE,
)
from agents.utils.text_cleaner import TextCleaner
from agents.parsers.todo_parser import TodoParser
from agents.parsers.question_parser import QuestionParser


class ClarificationAgent(DiagramAgentBase):
    """需求澄清智能体 - 类似Traycer的交互式澄清"""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="clarification_agent",
            sys_prompt=self._get_sys_prompt(),
            **kwargs
        )
        self.clarification_rounds = 0
        self.max_rounds = CLARIFICATION_CONFIG["max_rounds"]
        self.clarified_points = []
    
    def clean_html_and_markdown(self, text: str) -> str:
        """清理HTML标签和Markdown符号（委托给工具类）"""
        return TextCleaner.clean_html_and_markdown(text)
    
    def _get_sys_prompt(self) -> str:
        return CLARIFICATION_SYSTEM_PROMPT
    
    def generate_todo_list(self, requirement: str) -> List[Dict]:
        """生成TODO列表（委托给解析器）"""
        prompt = CLARIFICATION_GENERATE_TODO_PROMPT.format(requirement=requirement)
        response = self.model(prompt, stream=False, temperature=0.1)
        return TodoParser.parse_todos(response, requirement)
    
    def add_clarified_point(self, question: str, answer: str):
        """记录已澄清的问题"""
        self.clarified_points.append({
            "round": self.clarification_rounds,
            "question": question,
            "answer": answer
        })
    
    def collect_all_clarification_questions(self, todo_list: List[Dict], requirement: str, context: Dict = None) -> Dict:
        """一次性收集所有TODO任务需要澄清的问题（委托给解析器）"""
        if context is None:
            context = {}
        
        # 构建针对所有TODO的澄清提示
        todos_text = ""
        for idx, todo in enumerate(todo_list, 1):
            todos_text += f"\n任务{idx}: {todo.get('title', '')}\n"
            if todo.get('description'):
                todos_text += f"  描述: {todo.get('description', '')}\n"
        
        previous_clarifications = context.get("previous_clarifications", [])
        
        # 构建已澄清问题部分
        previous_clarifications_section = ""
        if previous_clarifications:
            for i, qa in enumerate(previous_clarifications, 1):
                previous_clarifications_section += f"{i}. Q: {qa.get('question', '')}\n   A: {qa.get('answer', '')}\n\n"
        else:
            previous_clarifications_section = "暂无\n\n"
        
        prompt = CLARIFICATION_COLLECT_QUESTIONS_PROMPT_TEMPLATE.format(
            requirement=requirement,
            todos_text=todos_text,
            previous_clarifications_section=previous_clarifications_section
        )
        
        response = self.model(prompt, stream=False, temperature=0.1)
        
        # 使用解析器解析问题
        return QuestionParser.parse_questions(response)
