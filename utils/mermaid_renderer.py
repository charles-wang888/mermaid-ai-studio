"""Mermaid代码渲染器 - 将Mermaid代码渲染为PNG（重构版）"""
import os
from typing import Optional, Tuple, Dict, List
from utils.browser_manager import BrowserManager
from utils.checkers.checker_chain import SyntaxCheckerChain
from utils.error_factory import ErrorInfoFactory
from utils.mermaid_js_validator import MermaidJSValidator
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError


class MermaidRenderer:
    """Mermaid渲染器 - 使用Playwright渲染Mermaid为PNG（外观模式）"""
    
    def __init__(self, generation_agent=None):
        """初始化Mermaid渲染器
        
        Args:
            generation_agent: 已废弃，保留仅为向后兼容
        """
        self.browser_manager = BrowserManager()
        self.syntax_checker_chain = SyntaxCheckerChain()
        self.mermaid_js_validator = MermaidJSValidator()
        self.error_factory = ErrorInfoFactory()
        # generation_agent 已废弃，不再使用
        self.generation_agent = generation_agent
    
    def render_to_png(self, mermaid_code: str, output_path: str, width: int = 1920, height: int = 1080, validate: bool = True) -> str:
        """将Mermaid代码渲染为PNG文件
        
        Args:
            mermaid_code: Mermaid代码字符串
            output_path: 输出PNG文件路径
            width: 图片宽度（像素）
            height: 图片高度（像素）
            validate: 是否在渲染前验证语法（默认True）
        
        Returns:
            输出文件路径
            
        Raises:
            ValueError: 如果语法检查失败
        """
        # 规范化Mermaid代码
        normalized_code = self._normalize_code(mermaid_code)
        
        # 语法检查（如果启用）
        if validate:
            is_valid, error_message = self.validate_syntax(normalized_code)
            if not is_valid:
                raise ValueError(f"Mermaid语法错误: {error_message}")
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        
        # 创建HTML页面
        html_content = self._create_html_page(normalized_code)
        
        # 渲染为PNG
        try:
            browser = self.browser_manager.get_browser()
            try:
                page = browser.new_page(viewport={"width": width, "height": height})
                page.set_content(html_content)
                page.wait_for_timeout(3000)
                
                # 检查是否有错误信息
                error_div = page.query_selector('#mermaid-error')
                if error_div:
                    error_text = error_div.inner_text()
                    if error_text and error_text.strip():
                        raise ValueError(f"Mermaid渲染错误: {error_text.strip()}")
                
                # 等待Mermaid图表元素出现
                try:
                    page.wait_for_selector('.mermaid svg', timeout=5000)
                except PlaywrightTimeoutError as e:
                    error_div = page.query_selector('#mermaid-error')
                    if error_div:
                        error_text = error_div.inner_text()
                        if error_text and error_text.strip():
                            try:
                                console_errors = page.evaluate("() => window.consoleErrors || []")
                                error_details = error_text.strip()
                                if console_errors:
                                    error_details += f"\n控制台错误: {', '.join(console_errors)}"
                                raise ValueError(f"Mermaid渲染错误: {error_details}") from e
                            except PlaywrightError:
                                raise ValueError(f"Mermaid渲染错误: {error_text.strip()}")
                    try:
                        console_errors = page.evaluate("() => window.consoleErrors || []")
                        if console_errors:
                            raise ValueError(f"Mermaid渲染错误: {', '.join(console_errors)}") from e
                    except PlaywrightError as pe:
                        raise ValueError("Mermaid渲染超时且无法获取错误详情") from e
                
                # 截图保存为PNG
                page.screenshot(path=output_path, full_page=True)
                page.close()
            finally:
                browser.close()
            
            return output_path
        except ImportError:
            raise ImportError(
                "Playwright未安装。请运行以下命令安装：\n"
                "pip install playwright\n"
                "playwright install chromium"
            )
        except (PlaywrightError, PlaywrightTimeoutError) as e:
            raise RuntimeError("渲染PNG失败") from e
        except OSError as e:
            raise RuntimeError("输出文件写入失败") from e
        except Exception as e:
            raise RuntimeError("渲染过程中发生意外错误") from e
    
    def validate_syntax(self, mermaid_code: str) -> Tuple[bool, Optional[str]]:
        """验证Mermaid代码语法
        
        Args:
            mermaid_code: Mermaid代码字符串
            
        Returns:
            (is_valid, error_message): 语法是否有效，如果有错误则返回错误消息
        """
        is_valid, error_info = self.validate_syntax_with_details(mermaid_code)
        if is_valid:
            return True, None
        else:
            return False, error_info.get('message', '未知错误')
    
    def validate_syntax_with_details(self, mermaid_code: str) -> Tuple[bool, Dict]:
        """验证Mermaid代码语法，返回详细错误信息
        
        Args:
            mermaid_code: Mermaid代码字符串
            
        Returns:
            (is_valid, error_info): 
                - is_valid: 语法是否有效
                - error_info: 错误信息字典，包含：
                    - message: 错误消息
                    - line_number: 错误行号（如果可识别）
                    - error_lines: 可能有错误的行号列表
                    - code_snippet: 错误代码片段
        """
        if not mermaid_code or not mermaid_code.strip():
            error_info = self.error_factory.create_error_info(
                message="Mermaid代码为空",
                source="基础语法检查"
            )
            return False, error_info
        
        # 规范化代码格式
        normalized_code = mermaid_code.strip()
        
        # 第一步：基础语法检查（使用责任链模式）
        basic_error = self.syntax_checker_chain.check_all(normalized_code)
        
        # 第二步：使用 mermaid.js 进行语法验证
        mermaid_js_result = self.mermaid_js_validator.validate(normalized_code)
        
        # 收集所有错误
        all_errors = []
        if basic_error:
            error_info = self.error_factory.create_error_info(
                message=basic_error.get('message', '发现语法错误'),
                line_number=basic_error.get('error_lines', [None])[0] if basic_error.get('error_lines') else None,
                error_lines=basic_error.get('error_lines', []),
                code_snippet=self._extract_error_snippet(normalized_code, basic_error.get('error_lines', [])),
                source="基础语法检查"
            )
            all_errors.append(error_info)
        
        if mermaid_js_result and isinstance(mermaid_js_result, dict) and not mermaid_js_result.get('isValid', True):
            all_errors.append(mermaid_js_result)
        
        # 合并所有错误或返回成功
        if all_errors:
            merged_error = self.error_factory.merge_errors(all_errors)
            return False, merged_error
        
        # 所有验证都通过，返回成功
        diagram_type = None
        if mermaid_js_result and isinstance(mermaid_js_result, dict) and mermaid_js_result.get('diagramType'):
            diagram_type = mermaid_js_result.get('diagramType')
        
        success_info = self.error_factory.create_success_info(diagram_type=diagram_type)
        return True, success_info
    
    def _normalize_code(self, mermaid_code: str) -> str:
        """规范化Mermaid代码"""
        normalized_code = mermaid_code.strip()
        
        # 对于象限图，进一步清理格式
        if normalized_code.startswith('quadrantChart'):
            lines = normalized_code.split('\n')
            cleaned_lines = [lines[0]]  # quadrantChart
            for line in lines[1:]:
                if line.strip():  # 只保留非空行
                    cleaned_lines.append(line.strip())
            normalized_code = '\n'.join(cleaned_lines)
        
        return normalized_code
    
    def _extract_error_snippet(self, mermaid_code: str, error_lines: List[int], context_lines: int = 2) -> str:
        """提取错误代码片段"""
        if not error_lines:
            return ""
        
        lines = mermaid_code.split('\n')
        snippets = []
        
        for line_num in error_lines[:3]:  # 最多显示3个错误行的片段
            start = max(0, line_num - context_lines - 1)
            end = min(len(lines), line_num + context_lines)
            
            snippet_lines = []
            for i in range(start, end):
                line_marker = ">>> " if i == line_num - 1 else "    "
                snippet_lines.append(f"{line_marker}{i+1:4d} | {lines[i]}")
            
            snippets.append('\n'.join(snippet_lines))
        
        return '\n\n'.join(snippets)
    
    def _create_html_page(self, mermaid_code: str) -> str:
        """创建包含Mermaid的HTML页面"""
        # 获取本地 mermaid.js 文件路径并读取内容
        script_dir = os.path.dirname(os.path.abspath(__file__))
        mermaid_js_path = os.path.join(script_dir, 'mermaid.min.js')
        
        if not os.path.exists(mermaid_js_path):
            raise FileNotFoundError(
                f"本地 mermaid.min.js 文件不存在: {mermaid_js_path}\n"
                "请确保 utils/mermaid.min.js 文件存在"
            )
        
        with open(mermaid_js_path, 'r', encoding='utf-8') as f:
            mermaid_js_content = f.read()
        
        # 转义HTML特殊字符
        safe_code = mermaid_code.replace('</pre>', '&lt;/pre&gt;').replace('</script>', '&lt;/script&gt;')
        escaped_js = mermaid_js_content.replace('</script>', '<\\/script>')
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script>
        {escaped_js}
    </script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background: white;
            font-family: Arial, sans-serif;
        }}
        .mermaid {{
            background: white;
        }}
        #mermaid-error {{
            color: red;
            display: none;
            white-space: pre-wrap;
            padding: 10px;
            background: #ffebee;
            border: 1px solid #d32f2f;
            border-radius: 4px;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <pre class="mermaid" id="mermaid-diagram">{safe_code}</pre>
    <div id="mermaid-error"></div>
    <script>
        // 错误处理函数
        function handleMermaidError(error) {{
            const errorDiv = document.getElementById('mermaid-error');
            if (errorDiv) {{
                let errorMessage = '';
                if (error && error.message) {{
                    errorMessage = error.message;
                }} else if (typeof error === 'string') {{
                    errorMessage = error;
                }} else {{
                    errorMessage = 'Unknown error occurred while parsing Mermaid diagram';
                }}
                errorDiv.textContent = errorMessage;
                errorDiv.style.display = 'block';
                // 抛出错误以便外部捕获
                throw new Error(errorMessage);
            }}
        }}
        
        // 捕获全局JavaScript错误
        window.addEventListener('error', function(event) {{
            if (event.message && event.message.includes('mermaid')) {{
                handleMermaidError(event.message);
            }}
        }});
        
        // 捕获未处理的Promise拒绝
        window.addEventListener('unhandledrejection', function(event) {{
            if (event.reason && (event.reason.message || event.reason.toString()).includes('mermaid')) {{
                handleMermaidError(event.reason);
            }}
        }});
        
        // 存储控制台错误
        window.consoleErrors = [];
        window.originalConsoleError = console.error;
        console.error = function(...args) {{
            window.consoleErrors.push(args.join(' '));
            window.originalConsoleError.apply(console, args);
        }};
        
        try {{
            mermaid.initialize({{
                startOnLoad: true,
                theme: 'default',
                securityLevel: 'loose',
                // 设置错误回调
                errorCallback: function(error, hash) {{
                    const errorMsg = error?.message || error?.toString() || String(error);
                    window.consoleErrors.push(errorMsg);
                    handleMermaidError(error);
                }}
            }});
        }} catch (e) {{
            const errorMsg = e.message || e.toString();
            window.consoleErrors.push(errorMsg);
            handleMermaidError(errorMsg);
        }}
    </script>
</body>
</html>"""
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'browser_manager'):
            self.browser_manager.cleanup()

