"""TODO列表解析器"""
import json
import re
import logging
from typing import List, Dict, ClassVar
from agents.utils.text_cleaner import TextCleaner

logger = logging.getLogger(__name__)


class TodoParser:
    """TODO列表解析器"""
    
    # 需要过滤的不相关任务关键词
    EXCLUDED_KEYWORDS: ClassVar[List[str]] = [
        '审阅', '评审', 'review', '审查',
        '调整', '修改设计', '优化设计', '调整方案',
        '实施', '部署', '上线', 'implement', 'deploy',
        '测试', '验证', 'test', 'validate', 'verify',
        '反馈', '优化', '改进'
    ]
    
    @staticmethod
    def is_excluded_task(title: str) -> bool:
        """判断任务是否应该被排除"""
        title_lower = title.lower()
        return any(keyword in title_lower for keyword in TodoParser.EXCLUDED_KEYWORDS)
    
    @staticmethod
    def parse_todos(response: str, requirement: str = "") -> List[Dict]:
        """解析TODO列表
        
        Args:
            response: LLM响应文本
            requirement: 原始需求（用于创建默认TODO）
            
        Returns:
            TODO列表
        """
        # 尝试从文本中找到并解析JSON对象
        decoder = json.JSONDecoder()
        start_idx = 0
        while start_idx < len(response):
            try:
                # 跳过前导空白字符
                match = response.find('{', start_idx)
                if match == -1:
                    break
                
                try:
                    result, _ = decoder.raw_decode(response[match:])
                    if isinstance(result, dict) and "todos" in result:
                        todos_raw = result.get("todos", [])
                        # 过滤掉不相关的任务
                        todos = []
                        for todo in todos_raw:
                            title = todo.get("title", "")
                            if title:
                                # 使用统一的清理函数清理HTML标签和Markdown符号
                                title = TextCleaner.clean_html_and_markdown(title)
                                if title and not TodoParser.is_excluded_task(title):
                                    todo["title"] = title
                                    # 处理description字段
                                    description = todo.get("description", "")
                                    if description:
                                        description = TextCleaner.clean_html_and_markdown(description)
                                        todo["description"] = description
                                    if "status" not in todo:
                                        todo["status"] = "pending"
                                    todos.append(todo)
                        if todos:
                            return todos
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parse error at position {start_idx}: {str(e)}")
                    logger.warning(f"Failed JSON slice: {response[match:match+50]}...")
                
                start_idx = match + 1
            except Exception as e:
                logger.error(f"Unexpected error while parsing todos: {str(e)}", exc_info=True)
                break
        
        # 如果JSON解析失败，尝试从文本中提取TODO
        todos = []
        lines = response.split('\n')
        current_id = 1
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('*') or re.match(r'^\d+[\.\)]', line)):
                title = re.sub(r'^[-*\d\.\)\s]+', '', line).strip()
                # 使用统一的清理函数清理HTML标签和Markdown符号
                title = TextCleaner.clean_html_and_markdown(title)
                if title and not TodoParser.is_excluded_task(title):
                    todos.append({
                        "id": current_id,
                        "title": title,
                        "description": "",
                        "status": "pending"
                    })
                    current_id += 1
        
        # 如果没有提取到任何TODO，创建一个默认的
        if not todos:
            todos = [{
                "id": 1,
                "title": "理解核心需求",
                "description": requirement,
                "status": "pending"
            }]
        
        return todos

