"""问题解析器"""
import re
from typing import List, Dict
from agents.utils.text_cleaner import TextCleaner


class QuestionParser:
    """问题解析器 - 从LLM响应中解析澄清问题"""
    
    # 格式相关的问题关键词（需要过滤）
    FORMAT_KEYWORDS = [
        '格式', 'format', 'visio', 'pdf', '导出格式', '导出方式', '图片格式', 
        '文件格式', '输出格式', '输出方式', '图的格式', '图格式', '什么格式', 
        '哪种格式', 'ppt', 'powerpoint', 'word', 'excel', 'jpg', 'jpeg'
    ]
    
    @staticmethod
    def is_format_question(question: str) -> bool:
        """判断是否是格式相关的问题"""
        q_lower = question.lower()
        return any(keyword in q_lower for keyword in QuestionParser.FORMAT_KEYWORDS)
    
    @staticmethod
    def parse_questions(response: str) -> Dict:
        """解析澄清问题
        
        Args:
            response: LLM响应文本
            
        Returns:
            包含问题信息的字典
        """
        if "理解清晰" in response or "所有任务" in response:
            return {
                "type": "complete",
                "message": "所有任务已澄清清楚",
                "needs_input": False,
                "questions_by_todo": []
            }
        
        # 按任务解析问题
        all_questions = []
        current_todo_index = -1
        current_todo_title = ""
        current_questions = []
        
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('任务') and ':' in line:
                # 保存上一个任务的问题
                if current_todo_index >= 0 and current_questions:
                    all_questions.append({
                        "todo_index": current_todo_index,
                        "todo_title": current_todo_title,
                        "questions": current_questions
                    })
                # 开始新任务
                match = re.match(r'任务(\d+):\s*(.+)', line)
                if match:
                    current_todo_index = int(match.group(1)) - 1
                    current_todo_title = match.group(2).strip()
                    current_todo_title = TextCleaner.clean_html_and_markdown(current_todo_title)
                    current_questions = []
            elif line.startswith('问题') and ':' in line:
                q = re.sub(r'^问题\d+[：:]\s*', '', line).strip()
                if q and q != "无需澄清":
                    q = TextCleaner.clean_html_and_markdown(q)
                    current_questions.append(q)
            elif line and not line.startswith('---') and current_todo_index >= 0:
                # 可能是问题内容的延续
                if current_questions:
                    cleaned_line = TextCleaner.clean_html_and_markdown(line)
                    current_questions[-1] += " " + cleaned_line
        
        # 保存最后一个任务的问题
        if current_todo_index >= 0 and current_questions:
            all_questions.append({
                "todo_index": current_todo_index,
                "todo_title": current_todo_title,
                "questions": current_questions
            })
        
        # 如果没有解析到结构化的问题，尝试提取所有问题
        if not all_questions:
            questions = []
            for line in lines:
                line = line.strip()
                if line.startswith('问题') and ':' in line:
                    q = re.sub(r'^问题\d+[：:]\s*', '', line).strip()
                    if q:
                        q = TextCleaner.clean_html_and_markdown(q)
                        questions.append(q)
            if questions:
                all_questions.append({
                    "todo_index": 0,
                    "todo_title": "整体需求",
                    "questions": questions
                })
        
        # 收集所有问题并过滤格式相关的问题，限制最多8个
        flat_questions = []
        for item in all_questions:
            for q in item.get("questions", []):
                if not QuestionParser.is_format_question(q):
                    flat_questions.append({
                        "todo_index": item.get("todo_index", 0),
                        "todo_title": item.get("todo_title", ""),
                        "question": q
                    })
        
        # 限制最多8个问题
        if len(flat_questions) > 8:
            flat_questions = flat_questions[:8]
        
        # 如果没有有效问题
        if not flat_questions:
            return {
                "type": "complete",
                "message": "没有需要澄清的问题",
                "needs_input": False,
                "questions_by_todo": []
            }
        
        # 重新组织为按TODO分组的问题列表
        questions_by_todo = {}
        for q_item in flat_questions:
            todo_idx = q_item["todo_index"]
            if todo_idx not in questions_by_todo:
                todo_title = q_item.get("todo_title", "")
                todo_title = TextCleaner.clean_html_and_markdown(todo_title)
                questions_by_todo[todo_idx] = {
                    "todo_index": todo_idx,
                    "todo_title": todo_title,
                    "questions": []
                }
            questions_by_todo[todo_idx]["questions"].append(q_item["question"])
        
        final_questions_by_todo = list(questions_by_todo.values())
        
        return {
            "type": "clarification",
            "message": response,
            "questions_by_todo": final_questions_by_todo,
            "needs_input": True
        }

