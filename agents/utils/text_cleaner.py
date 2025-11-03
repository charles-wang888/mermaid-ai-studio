"""文本清理工具类"""
import re
from typing import Optional


class TextCleaner:
    """HTML和Markdown清理工具类"""
    
    @staticmethod
    def clean_html_and_markdown(text: str) -> str:
        """清理HTML标签和Markdown符号
        
        清理内容：
        1. HTML标签：<div>、</div>、<span>、</span> 等所有HTML标签
        2. Markdown符号：**、*、__、_ 等（但保留文本中的单个*符号，只清理用于格式化的*）
        3. HTML实体：&nbsp;、&amp; 等
        
        Args:
            text: 要清理的文本
            
        Returns:
            清理后的文本
        """
        if not text:
            return text
        
        # 1. 清理HTML标签（包括<div>、</div>、<span>等）
        # 先提取div标签内的文本内容（如果有嵌套）
        while '<div' in text or '</div>' in text:
            # 移除所有div标签
            text = re.sub(r'<div[^>]*>', '', text, flags=re.IGNORECASE)
            text = re.sub(r'</div>', '', text, flags=re.IGNORECASE)
        # 清理所有其他HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 2. 清理HTML实体
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&#124;', '|')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        
        # 3. 清理Markdown格式化符号
        # 清理 **文本** 格式（粗体）
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        # 清理 *文本* 格式（斜体），但要小心不要误删数学表达式或代码中的*
        text = re.sub(r'(?<![*\w])\*([^*\n]+?)\*(?![*\w])', r'\1', text)
        # 清理 __文本__ 格式（粗体）
        text = re.sub(r'__([^_]+)__', r'\1', text)
        # 清理 _文本_ 格式（斜体）
        text = re.sub(r'(?<![_\w])_([^_\n]+?)_(?![_\w])', r'\1', text)
        # 清理行首或行尾的单独*符号
        text = re.sub(r'^\*+\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'\s*\*+$', '', text, flags=re.MULTILINE)
        
        # 4. 清理多余的空白字符
        text = re.sub(r'[ \t]+', ' ', text)  # 多个空格或制表符合并为一个空格
        text = text.strip()
        
        return text
    
    @staticmethod
    def clean_mermaid_code(mermaid_code: str) -> str:
        """清理Mermaid代码中的HTML标签和Markdown符号
        
        逐行处理，保留Mermaid语法结构，只清理文本内容部分
        
        Args:
            mermaid_code: Mermaid代码字符串
            
        Returns:
            清理后的Mermaid代码
        """
        if not mermaid_code:
            return mermaid_code
        
        lines = mermaid_code.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # 如果是空行或注释行，直接保留
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith('//'):
                cleaned_lines.append(line)
                continue
            
            # 保留原始缩进
            original_indent = len(line) - len(line.lstrip())
            indent = ' ' * original_indent
            
            # 保存Mermaid关键字和语法结构，只清理文本内容
            cleaned_line = line
            
            # 处理不同的Mermaid语法模式
            # 匹配引号内的内容进行清理的函数
            def clean_quoted_content(match):
                quote_char = match.group(1)  # 获取引号类型（"或'）
                content = match.group(2)  # 获取引号内的内容
                cleaned_content = TextCleaner.clean_html_and_markdown(content)
                # 处理转义的换行符
                cleaned_content = cleaned_content.replace('\\n', '\n')
                # 清理后再转义换行符
                cleaned_content = cleaned_content.replace('\n', '\\n')
                return f'{quote_char}{cleaned_content}{quote_char}'
            
            # 1. 流程图节点：NodeID["文本内容"] 或 NodeID("文本内容")
            # 清理双引号内的内容
            cleaned_line = re.sub(r'(")([^"]*)(")', clean_quoted_content, cleaned_line)
            # 清理单引号内的内容
            cleaned_line = re.sub(r"(')([^']*)(')", clean_quoted_content, cleaned_line)
            
            # 2. 时序图：participant A as "参与者名称" 或 A->>B: 消息内容
            # 先处理participant定义
            if 'participant' in cleaned_line.lower() or 'actor' in cleaned_line.lower():
                # participant A as "名称<div>xxx</div>" 或 participant "名称<div>xxx</div>" as A
                # 清理participant名称中的HTML标签和Markdown符号
                if 'as' in cleaned_line.lower():
                    parts = cleaned_line.split('as', 1)
                    if len(parts) == 2:
                        syntax_part = parts[0].strip()  # participant A
                        name_part = parts[1].strip()  # "名称" 或 A "名称"
                        # 提取引号内的名称并清理
                        name_match = re.search(r'"([^"]*)"', name_part)
                        if name_match:
                            cleaned_name = TextCleaner.clean_html_and_markdown(name_match.group(1))
                            name_part = f'"{cleaned_name}"'
                        cleaned_line = f'{syntax_part} as {name_part}'
            
            # 3. 时序图消息：A->>B: 消息内容（引号内的内容）
            # 清理冒号后的内容（优先匹配时序图语法）
            if ':' in cleaned_line and ('->>' in cleaned_line or '-->>' in cleaned_line or 
                                       '-.->' in cleaned_line or '--->' in cleaned_line or
                                       '->' in cleaned_line):
                parts = cleaned_line.split(':', 1)
                if len(parts) == 2:
                    syntax_part = parts[0].strip()  # 保留语法部分（如 A->>B）
                    content_part = parts[1]  # 清理内容部分
                    cleaned_content = TextCleaner.clean_html_and_markdown(content_part)
                    cleaned_line = f'{syntax_part}: {cleaned_content}'
            
            # 4. 甘特图任务：任务名称 :状态, 日期 或 任务名称<div>xxx</div> :状态, 日期
            # 清理任务名称中的HTML标签
            if ':' in cleaned_line and (line_stripped.startswith('section') or 
                                       not any(x in line_stripped for x in ['->', '--', 'activate', 'deactivate', 'Note'])):
                # 检查是否是任务定义行（包含日期格式 YYYY-MM-DD）
                if re.search(r'\d{4}-\d{2}-\d{2}', cleaned_line):
                    parts = cleaned_line.split(':', 1)
                    if len(parts) == 2:
                        task_name = parts[0]  # 任务名称部分
                        rest = parts[1]  # 状态和日期部分
                        cleaned_task_name = TextCleaner.clean_html_and_markdown(task_name)
                        cleaned_line = f'{cleaned_task_name}:{rest}'
            
            # 5. 类图：class 类名 { 或 +方法名() 返回类型
            # 类名和方法名中可能包含HTML标签
            if 'class' in cleaned_line.lower() or re.search(r'[+\-#~]\s*\w+', cleaned_line):
                # 清理类名和方法名中的HTML标签
                cleaned_line = re.sub(r'<[^>]+>', '', cleaned_line)
            
            cleaned_lines.append(cleaned_line)
        
        return '\n'.join(cleaned_lines)

