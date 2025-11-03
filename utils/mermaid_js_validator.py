"""Mermaid.js验证器"""
import os
import logging
from typing import Optional, Dict
from utils.browser_manager import BrowserManager
from utils.error_factory import ErrorInfoFactory

logger = logging.getLogger(__name__)


class MermaidJSValidator:
    """Mermaid.js验证器 - 使用浏览器执行mermaid.js进行验证"""
    
    def __init__(self):
        """初始化验证器"""
        self.browser_manager = BrowserManager()
        self._mermaid_js_path = None
        self._validation_js = None
    
    @property
    def mermaid_js_path(self) -> str:
        """获取mermaid.js文件路径"""
        if self._mermaid_js_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self._mermaid_js_path = os.path.join(script_dir, 'mermaid.min.js')
        return self._mermaid_js_path
    
    @property
    def validation_javascript(self) -> str:
        """获取验证JavaScript代码"""
        if self._validation_js is None:
            self._validation_js = self._get_mermaid_validation_javascript()
        return self._validation_js
    
    def validate(self, mermaid_code: str) -> Optional[Dict]:
        """验证Mermaid代码
        
        Args:
            mermaid_code: Mermaid代码
            
        Returns:
            如果有错误，返回错误信息字典；如果成功，返回None
        """
        if not os.path.exists(self.mermaid_js_path):
            return None  # mermaid.js不存在，跳过验证
        
        browser = None
        page = None
        try:
            browser = self.browser_manager.get_browser()
            page = browser.new_page()
            
            # 执行验证
            result = self._execute_validation(page, mermaid_code)
            
            if result and not result.get('isValid', True):
                # 有错误
                error_msg = result.get('error', '未知错误')
                error_lines = self._extract_error_lines(mermaid_code, error_msg)
                code_snippet = self._extract_error_snippet(mermaid_code, error_lines)
                
                return ErrorInfoFactory.create_error_info(
                    message=f"语法错误: {error_msg}",
                    line_number=error_lines[0] if error_lines else None,
                    error_lines=error_lines,
                    code_snippet=code_snippet,
                    diagram_type=result.get('diagramType'),
                    source='mermaid.js 验证'
                )
            elif result and result.get('isValid', True):
                # 验证成功，返回图表类型信息（用于后续使用）
                return {
                    'isValid': True,
                    'diagramType': result.get('diagramType')
                }
        except Exception:
            # 验证过程出现异常，返回None表示验证失败但不影响其他验证
            return None
        finally:
            if page is not None:
                try:
                    page.close()
                except:
                    pass
            if browser is not None:
                try:
                    browser.close()
                except:
                    pass
        
        return None
    
    def _execute_validation(self, page, mermaid_code: str) -> Optional[Dict]:
        """在浏览器页面中执行验证"""
        try:
            # 读取 mermaid.js 文件内容
            with open(self.mermaid_js_path, 'r', encoding='utf-8') as f:
                mermaid_js_content = f.read()
            
            # 先添加 init script（在页面导航之前）
            page.add_init_script(mermaid_js_content)
            
            # 导航到空白页面，触发 init script 执行
            page.goto('about:blank')
            
            # 等待一小段时间，确保 mermaid.js 加载完成
            page.wait_for_timeout(500)
            
            # 执行验证逻辑
            result = page.evaluate(self.validation_javascript, mermaid_code)
            
            return result
        except Exception:
            return None
    
    def _extract_error_lines(self, mermaid_code: str, error_message: str) -> list:
        """从错误消息中提取可能有错误的行号"""
        error_lines = []
        lines = mermaid_code.split('\n')
        import re
        
        # 尝试从错误消息中提取行号
        line_patterns = [
            r'line\s+(\d+)',
            r'Line\s+(\d+)',
            r'第\s*(\d+)\s*行',
            r'at\s+line\s+(\d+)',
        ]
        
        for pattern in line_patterns:
            matches = re.findall(pattern, error_message, re.IGNORECASE)
            for match in matches:
                try:
                    line_num = int(match)
                    if 1 <= line_num <= len(lines):
                        error_lines.append(line_num)
                except ValueError:
                    pass
        
        return error_lines[:5]  # 最多返回5个行号
    
    def _extract_error_snippet(self, mermaid_code: str, error_lines: list, context_lines: int = 2) -> str:
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
    
    def _get_mermaid_validation_javascript(self) -> str:
        """获取用于mermaid.js语法验证的JavaScript代码"""
        return """
        function(code) {
            try {
                // 检查参数是否有效
                if (!code || typeof code !== 'string') {
                    return {
                        isValid: false,
                        error: 'Mermaid代码参数无效',
                        diagramType: null
                    };
                }
                
                // 初始化 mermaid
                if (typeof mermaid !== 'undefined' && mermaid.initialize) {
                    mermaid.initialize({ startOnLoad: false, securityLevel: 'loose' });
                }
                
                // 检测图表类型
                const codeTrimmed = code.trim();
                if (!codeTrimmed) {
                    return {
                        isValid: false,
                        error: 'Mermaid代码为空',
                        diagramType: null
                    };
                }
                
                const firstLine = codeTrimmed.split('\\n')[0].trim();
                let diagramType = null;
                
                // 定义有效的图表类型关键字（精确匹配，不区分大小写）
                const validDiagramTypes = [
                    'flowchart', 'graph', 'sequenceDiagram', 'classDiagram',
                    'stateDiagram-v2', 'stateDiagram', 'erDiagram', 'journey',
                    'gantt', 'pie', 'gitgraph', 'quadrantChart'
                ];
                
                // 先提取第一个单词（去除可能的空格和方向指示符）
                const firstWord = firstLine.split(/\\s+/)[0].toLowerCase();
                
                // 检查是否是有效的图表类型（精确匹配，防止 flowcharts, subgraphs 等错误）
                let matchedType = null;
                for (const validType of validDiagramTypes) {
                    if (firstWord === validType.toLowerCase()) {
                        matchedType = validType;
                        break;
                    }
                }
                
                // 如果没有精确匹配，检查是否是常见的拼写错误
                if (!matchedType) {
                    // 检查常见的拼写错误
                    if (firstWord.startsWith('flowchart') && firstWord !== 'flowchart') {
                        return {
                            isValid: false,
                            error: `图表类型拼写错误：'${firstLine.split(/\\s+/)[0]}' 应该是 'flowchart' 或 'graph'`,
                            diagramType: null
                        };
                    }
                    if (firstWord.includes('subgraph') && !firstWord.startsWith('subgraph') || firstWord === 'subgraphs') {
                        return {
                            isValid: false,
                            error: `语法错误：'subgraph' 拼写错误，请检查代码中的 'subgraphs' 是否为 'subgraph'`,
                            diagramType: null
                        };
                    }
                    // 如果第一个单词完全不匹配任何有效类型，报告错误
                    return {
                        isValid: false,
                        error: `无效的图表类型：'${firstLine.split(/\\s+/)[0]}'，有效的类型包括：flowchart, graph, sequenceDiagram, classDiagram, stateDiagram, erDiagram, journey, gantt, pie, gitgraph, quadrantChart`,
                        diagramType: null
                    };
                }
                
                // 设置图表类型
                const diagramTypeMap = {
                    'flowchart': 'flowchart',
                    'graph': 'flowchart',
                    'sequencediagram': 'sequenceDiagram',
                    'classdiagram': 'classDiagram',
                    'statediagram-v2': 'stateDiagram-v2',
                    'statediagram': 'stateDiagram',
                    'erdiagram': 'erDiagram',
                    'journey': 'journey',
                    'gantt': 'gantt',
                    'pie': 'pie',
                    'gitgraph': 'gitgraph',
                    'quadrantchart': 'quadrantChart'
                };
                diagramType = diagramTypeMap[firstWord] || matchedType;
                
                // 定义所有Mermaid关键字及其常见的错误拼写（精确匹配检查）
                const keywordPatterns = [
                    // 图表类型关键字（复数形式错误）
                    { wrong: /\\bflowcharts\\b/i, correct: 'flowchart', description: '图表类型关键字' },
                    { wrong: /\\bgraphs\\b/i, correct: 'graph', description: '图表类型关键字' },
                    { wrong: /\\bsequenceDiagrams\\b/i, correct: 'sequenceDiagram', description: '图表类型关键字' },
                    { wrong: /\\bclassDiagrams\\b/i, correct: 'classDiagram', description: '图表类型关键字' },
                    { wrong: /\\bstateDiagrams\\b/i, correct: 'stateDiagram', description: '图表类型关键字' },
                    { wrong: /\\berDiagrams\\b/i, correct: 'erDiagram', description: '图表类型关键字' },
                    { wrong: /\\bjourneys\\b/i, correct: 'journey', description: '图表类型关键字' },
                    { wrong: /\\bgantts\\b/i, correct: 'gantt', description: '图表类型关键字' },
                    { wrong: /\\bquadrantCharts\\b/i, correct: 'quadrantChart', description: '图表类型关键字' },
                    { wrong: /\\bgitgraphs\\b/i, correct: 'gitgraph', description: '图表类型关键字' },
                    
                    // 流程图关键字
                    { wrong: /\\bsubgraphs\\b/i, correct: 'subgraph', description: '流程图关键字' },
                    
                    // 时序图关键字
                    { wrong: /\\bparticipants\\b/i, correct: 'participant', description: '时序图关键字' },
                    { wrong: /\\bactivates\\b/i, correct: 'activate', description: '时序图关键字' },
                    { wrong: /\\bdeactivates\\b/i, correct: 'deactivate', description: '时序图关键字' },
                    
                    // 用户旅程图关键字
                    { wrong: /\\bsections\\b/i, correct: 'section', description: '用户旅程图关键字' },
                    
                    // 类图关键字
                    { wrong: /\\bclasses\\b/i, correct: 'class', description: '类图关键字（如果出现在类定义行）' },
                ];
                
                // 检查代码中是否有任何关键字拼写错误（对所有行进行全局检查）
                const lines = codeTrimmed.split('\\n');
                for (let i = 0; i < lines.length; i++) {
                    const line = lines[i].trim();
                    
                    // 跳过注释行
                    if (line.startsWith('//') || line.startsWith('%%')) {
                        continue;
                    }
                    
                    // 检查每个关键字模式
                    for (const pattern of keywordPatterns) {
                        if (pattern.wrong.test(line)) {
                            // 提取匹配的错误关键字
                            const match = line.match(pattern.wrong);
                            const wrongKeyword = match ? match[0] : '';
                            
                            return {
                                isValid: false,
                                error: `第${i + 1}行语法错误：'${wrongKeyword}' 应该是 '${pattern.correct}'（${pattern.description}）`,
                                diagramType: diagramType
                            };
                        }
                    }
                }
                
                // 使用 mermaid.parse 进行语法验证（这是最关键的验证逻辑）
                if (mermaid && mermaid.mermaidAPI && typeof mermaid.mermaidAPI.parse === 'function') {
                    try {
                        mermaid.mermaidAPI.parse(codeTrimmed);
                        return {
                            isValid: true,
                            error: null,
                            diagramType: diagramType
                        };
                    } catch (parseError) {
                        return {
                            isValid: false,
                            error: parseError.message || String(parseError),
                            diagramType: diagramType
                        };
                    }
                } else {
                    return {
                        isValid: false,
                        error: 'Mermaid API不可用',
                        diagramType: null
                    };
                }
            } catch (error) {
                return {
                    isValid: false,
                    error: error.message || String(error),
                    diagramType: null
                };
            }
        }
        """

