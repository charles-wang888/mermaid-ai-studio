# Mermaid AI Studio - 智能架构设计图生成工具

基于大语言模型的智能架构设计图生成系统，支持多种 Mermaid 图表类型的自动生成、编辑和优化。

## 项目概述

Mermaid AI Studio 是一个集成了 AI 能力的企业级架构设计图生成工具，通过智能需求澄清、自动代码生成、语法校验和修复等功能，为架构师和开发者提供高效的图表设计解决方案。系统支持流程图、时序图、类图、状态图、甘特图、饼图、象限图、用户旅程图等多种 Mermaid 图表类型。

## 核心亮点

### 1. 智能需求澄清机制 - 谋定而后动

与传统的图形生成工具直接基于用户文本进行绘制不同，本系统引入了智能需求澄清机制。在生成图表前，系统首先对用户需求进行深度分析和结构化分解，通过 AI 驱动的交互式问答，自动识别需求中的模糊点、缺失信息和潜在矛盾，确保在绘制前充分理解用户意图。这种"先澄清、后绘制"的设计理念，显著提升了生成图表的准确性和完整性，避免了因需求理解偏差导致的重复修改。

### 2. Mermaid 源码可编辑性与重新渲染

系统生成的 Mermaid 图表不仅支持 PNG 格式导出，更提供了完整的源码编辑能力。用户可以直接在 Web 界面中对生成的 Mermaid 代码进行二次编辑和优化，系统支持实时语法校验和即时预览。编辑完成后，通过重新渲染功能即可生成更新后的图表，打破了传统图表生成工具"一次生成、无法修改"的局限性，为用户提供了灵活的定制化方案。

### 3. AI 驱动的自动语法检查与智能修复

针对 Mermaid 语法复杂、容易出错的特点，系统集成了基于 AI 的语法检查与修复引擎。当用户编辑 Mermaid 代码后，系统会自动检测语法错误，精确定位错误位置（具体到行号），并提供详细的错误分析。更重要的是，系统能够利用大语言模型分析错误原因，生成修复建议和修复后的完整代码。用户可以通过"一键采纳"功能自动应用修复方案，大幅降低了手动调试的时间成本，提升了代码质量。

## 技术架构

- **前端界面**：Streamlit Web 应用
- **图表生成引擎**：Mermaid.js 标准语法
- **渲染引擎**：Playwright + Mermaid.js（浏览器渲染）
- **AI 能力**：多模型后端支持（Ollama、OpenAI、Claude、vLLM、HuggingFace、硅基流动）

## 功能特性

1. **多种图表类型支持**：流程图、时序图、类图、状态图、甘特图、饼图、象限图、用户旅程图
2. **智能需求分解**：自动将复杂需求拆分为结构化任务列表
3. **交互式需求澄清**：AI 驱动的多轮问答澄清机制
4. **智能代码生成**：基于澄清后的需求自动生成标准 Mermaid 代码
5. **语法检查链**：多层级语法检查器，覆盖关键字、箭头、类型定义等
6. **错误定位与高亮**：精确定位语法错误行，可视化错误位置
7. **AI 错误解释**：智能分析错误原因，提供修复建议
8. **一键修复采纳**：自动应用 AI 生成的修复代码
9. **图表缩放控制**：支持放大、缩小、重置视图
10. **多格式导出**：支持 PNG 图片和 Mermaid 源码文件导出

## 安装

### 前置要求

- Python 3.8+
- Node.js 和 npm（用于 Mermaid.js 验证）
- Playwright 浏览器环境

### 安装步骤

```bash
# 1. 安装 Python 依赖
pip install -r requirements.txt

# 2. 安装 Playwright 浏览器
playwright install chromium

# 3. 安装 Node.js 依赖（可选，用于语法验证）
npm install
```

### 配置模型后端

系统默认使用 Ollama 本地模型，也支持其他模型后端。详细配置请参考 `config.py` 文件。

**使用 Ollama（推荐）**：

```bash
# 安装 Ollama（访问 https://ollama.ai/ 下载）
# 下载模型
ollama pull qwen2.5:7b

# 启动 Ollama 服务
ollama serve
```

## 使用

### 快速启动

```bash
python main.py
```

浏览器将自动打开 `http://localhost:8501`，进入应用界面。

### 使用流程

1. **选择图表类型**：从支持的图表类型中选择目标图表
2. **输入需求**：描述要生成的图表需求
3. **需求分解**：系统自动将需求拆分为结构化任务列表
4. **需求澄清**：回答 AI 提出的澄清问题，完善需求理解
5. **需求确认**：确认并编辑澄清后的需求
6. **图表生成**：系统自动生成 Mermaid 代码并渲染为 PNG
7. **编辑优化**：可编辑 Mermaid 源码，进行二次优化
8. **语法检查**：自动检查语法错误，获取修复建议
9. **导出保存**：下载 PNG 图片或 Mermaid 源码文件

## 项目结构

```
mermaid-ai-studio/
├── agents/                          # 智能体模块
│   ├── base_agent.py               # 基础智能体抽象类，定义通用接口和生命周期
│   ├── clarification_agent.py      # 需求澄清智能体，负责需求分解和交互式澄清
│   ├── generation_agent.py         # 图表生成智能体，负责 Mermaid 代码生成和修复
│   ├── llm_client.py               # 大语言模型客户端，统一封装多后端 API 调用
│   ├── prompts_config.py           # 提示词配置，集中管理所有 AI 提示模板
│   ├── generators/                 # 图表生成器模块
│   │   ├── base_generator.py       # 生成器基类，定义生成器接口
│   │   ├── generator_factory.py    # 生成器工厂，根据图表类型创建对应生成器
│   │   ├── flowchart_generator.py  # 流程图生成器
│   │   ├── sequence_generator.py   # 时序图生成器
│   │   ├── class_diagram_generator.py  # 类图生成器
│   │   ├── state_diagram_generator.py  # 状态图生成器
│   │   ├── gantt_generator.py      # 甘特图生成器
│   │   ├── pie_chart_generator.py  # 饼图生成器
│   │   ├── quadrant_chart_generator.py  # 象限图生成器
│   │   └── journey_generator.py    # 用户旅程图生成器
│   ├── fixers/                     # 语法修复器模块
│   │   ├── base_fixer.py           # 修复器基类，定义修复器接口
│   │   ├── fixer_factory.py        # 修复器工厂，根据图表类型创建对应修复器
│   │   ├── flowchart_fixer.py      # 流程图语法修复器
│   │   ├── sequence_fixer.py       # 时序图语法修复器
│   │   ├── class_diagram_fixer.py  # 类图基础语法修复器
│   │   ├── class_diagram_fixer_advanced.py  # 类图高级语法修复器
│   │   ├── state_diagram_fixer.py  # 状态图语法修复器
│   │   ├── gantt_fixer.py          # 甘特图语法修复器
│   │   └── quadrant_chart_fixer.py # 象限图语法修复器
│   ├── parsers/                    # 解析器模块
│   │   ├── todo_parser.py          # TODO 列表解析器，解析 AI 生成的任务列表
│   │   └── question_parser.py      # 问题解析器，解析 AI 生成的澄清问题
│   └── utils/                      # 智能体工具模块
│       ├── text_cleaner.py         # 文本清理工具，清理 HTML 和 Markdown 符号
│       └── code_extractor.py       # 代码提取工具，从 AI 响应中提取 Mermaid 代码
├── utils/                          # 工具模块
│   ├── mermaid_renderer.py         # Mermaid 渲染器，将代码渲染为 PNG 图片
│   ├── browser_manager.py          # 浏览器管理器，管理 Playwright 浏览器实例
│   ├── mermaid_js_validator.py     # Mermaid.js 验证器，使用浏览器执行语法验证
│   ├── mermaid_validator.js        # Node.js 语法验证脚本（备用方案）
│   ├── mermaid.min.js              # Mermaid.js 库文件
│   ├── error_factory.py            # 错误信息工厂，标准化错误信息格式
│   └── checkers/                   # 语法检查器模块
│       ├── base_checker.py         # 检查器基类
│       ├── checker_chain.py        # 检查器链，组合多个检查器
│       ├── keyword_spelling_checker.py  # 关键字拼写检查器
│       ├── arrow_syntax_checker.py      # 箭头语法检查器
│       ├── class_definition_checker.py  # 类定义检查器
│       ├── generic_type_checker.py      # 泛型类型检查器
│       └── quadrant_chart_checker.py    # 象限图专用检查器
├── app.py                          # Streamlit Web 应用主文件，包含完整的用户界面逻辑
├── main.py                         # 程序入口，启动 Streamlit 应用
├── config.py                       # 配置文件，包含模型后端配置、绘图配置、导出配置等
├── requirements.txt                # Python 依赖列表
├── package.json                    # Node.js 依赖配置（用于 Mermaid 验证）
├── LICENSE                         # 许可证文件
└── output/                         # 输出目录，存储生成的图表文件
```

## 文件职责详解

### 核心应用文件

- **`main.py`**：程序入口点，负责启动 Streamlit 应用，处理启动参数和异常
- **`app.py`**：Streamlit Web 应用的主文件，包含完整的用户界面逻辑，包括：
  - 图表类型选择界面
  - 需求输入与澄清流程
  - 图表显示与编辑界面
  - 语法检查与修复界面
  - 文件导出功能
- **`config.py`**：集中管理所有配置信息，包括：
  - 大语言模型后端配置（Ollama、OpenAI、Claude 等）
  - 绘图样式配置（颜色、尺寸、边距等）
  - 导出配置（PNG、JPG 参数）
  - 需求澄清配置（最大轮数、置信度阈值等）

### 智能体模块 (`agents/`)

- **`base_agent.py`**：定义所有智能体的基础接口和行为，包括模型调用、提示词管理、响应处理等通用功能
- **`clarification_agent.py`**：需求澄清智能体，核心职责包括：
  - 将复杂需求分解为结构化 TODO 列表
  - 收集所有需要澄清的问题
  - 管理澄清历史和上下文
  - 清理和标准化用户输入文本
- **`generation_agent.py`**：图表生成智能体，核心职责包括：
  - 根据需求生成标准 Mermaid 代码
  - 调用对应的生成器生成特定类型图表
  - 执行语法检查和修复
  - 使用 AI 解释语法错误并生成修复代码
- **`llm_client.py`**：统一的大语言模型客户端，封装不同后端（Ollama、OpenAI、Claude 等）的 API 调用差异，提供统一的接口

### 生成器模块 (`agents/generators/`)

每种图表类型都有对应的生成器，负责将澄清后的需求转换为符合 Mermaid 语法的代码：

- **流程图生成器**：生成标准流程图代码，支持节点、连接线、子图等
- **时序图生成器**：生成时序图代码，处理参与者、消息、激活框等元素
- **类图生成器**：生成类图代码，处理类、接口、关系、属性、方法等
- **状态图生成器**：生成状态图代码，处理状态、转换、条件等
- **甘特图生成器**：生成甘特图代码，处理任务、日期、依赖关系等
- **饼图生成器**：生成饼图代码，处理数据和标签
- **象限图生成器**：生成象限图代码，处理数据点和象限划分
- **用户旅程图生成器**：生成用户旅程图代码，处理阶段、任务、体验等

### 修复器模块 (`agents/fixers/`)

每种图表类型都有对应的语法修复器，负责检测和修复特定类型的语法错误：

- **基础修复器**：处理通用的语法问题，如空格、换行、注释清理等
- **高级修复器**：处理复杂的语法问题，如类图中的 `class` 关键字缺失、泛型类型错误等
- **修复器工厂**：根据图表类型自动选择合适的修复器

### 工具模块 (`utils/`)

- **`mermaid_renderer.py`**：核心渲染引擎，负责：
  - 将 Mermaid 代码渲染为 PNG 图片
  - 执行语法验证（通过检查器链和 Mermaid.js）
  - 规范化代码格式
  - 管理渲染过程和错误处理
- **`browser_manager.py`**：浏览器实例管理器，管理 Playwright 浏览器生命周期，提供浏览器上下文和页面对象
- **`mermaid_js_validator.py`**：Mermaid.js 验证器，在浏览器环境中执行 Mermaid.js 解析器进行语法验证
- **`error_factory.py`**：标准化错误信息格式，将不同来源的错误信息统一为结构化格式
- **检查器链**：组合多个专用检查器，依次检查不同类型的语法问题：
  - 关键字拼写检查
  - 箭头语法检查
  - 类定义检查
  - 泛型类型检查
  - 象限图专用检查

### 解析器模块 (`agents/parsers/`)

- **`todo_parser.py`**：解析 AI 生成的 TODO 列表，提取任务标题、描述、状态等信息
- **`question_parser.py`**：解析 AI 生成的澄清问题，提取问题内容和相关上下文

### 工具类模块 (`agents/utils/`)

- **`text_cleaner.py`**：清理和标准化文本内容，移除 HTML 标签、Markdown 符号等
- **`code_extractor.py`**：从 AI 响应文本中提取 Mermaid 代码块，处理代码块标记和格式化

## 支持的图表类型

| 图表类型 | 说明 | 应用场景 |
|---------|------|---------|
| 流程图 (Flowchart) | 表示流程或系统工作原理 | 业务流程、系统架构、算法流程 |
| 时序图 (Sequence Diagram) | 显示对象之间的交互顺序 | API 调用、系统交互、通信协议 |
| 类图 (Class Diagram) | 表示类、接口及其关系 | 面向对象设计、代码架构 |
| 状态图 (State Diagram) | 描述对象的状态变化 | 状态机设计、业务流程状态 |
| 甘特图 (Gantt) | 项目管理和调度 | 项目管理、任务安排 |
| 饼图 (Pie Chart) | 显示比例或百分比数据 | 数据分析、统计展示 |
| 象限图 (Quadrant Chart) | 数据点分布在4个象限 | 战略分析、优先级矩阵 |
| 用户旅程图 (Journey) | 用户与系统交互的体验步骤 | 用户体验设计、产品规划 |

## 快速测试

无需启动 LLM，测试基本功能：

```bash
python test_demo.py
```

这会生成一个演示 Mermaid 文件。

## 依赖说明

### Python 依赖

- `streamlit>=1.28.0`：Web 应用框架
- `requests>=2.31.0`：HTTP 请求库
- `pillow>=10.0.0`：图像处理库
- `playwright>=1.40.0`：浏览器自动化框架
- `python-dotenv>=1.0.0`：环境变量管理

### Node.js 依赖（可选）

- `mermaid`：Mermaid.js 库（用于语法验证）

## 文档

- [快速开始](QUICKSTART.md) - 5分钟上手指南
- [安装指南](INSTALL.md) - 详细安装说明
- [使用指南](USAGE.md) - 完整使用说明
- [模型配置](MODEL_CONFIG.md) - 多模型后端配置指南
- [模型示例](MODEL_USAGE_EXAMPLE.md) - 使用示例
- [更新日志](CHANGELOG.md) - 版本历史

## 贡献

欢迎提交 Issue 和 Pull Request！在提交代码前，请确保：

1. 代码符合项目的代码规范
2. 添加必要的测试用例
3. 更新相关文档

## 许可证

MIT License
