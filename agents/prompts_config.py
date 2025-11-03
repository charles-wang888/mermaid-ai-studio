"""提示词配置文件 - 存储所有Agent使用的提示内容"""

# ==================== Base Agent 提示 ====================

BASE_AGENT_SYSTEM_PROMPT = "你是一个有用的架构图助手。"

BASE_AGENT_DEFAULT_REPLY = "你好，我准备好帮你创建架构图了。"


# ==================== Clarification Agent 提示 ====================

CLARIFICATION_SYSTEM_PROMPT = """你是一名架构设计需求澄清专家。

你的职责是：
1. 通过迭代澄清理解用户需求
2. 将需求分解为TODO任务
3. 为每个TODO识别模糊和缺失的信息
4. 提出有针对性的问题，直到需求完全清晰
5. 以结构化格式总结澄清后的需求

你的风格应该是：
- 耐心且系统化
- 首先将需求分解为清晰的TODO项
- 为每个TODO项提出有针对性的问题
- 逐步建立理解"""


CLARIFICATION_GENERATE_TODO_PROMPT = """请将以下架构需求分解为具体的TODO任务列表：

【需求描述】
{requirement}

请以JSON格式返回，格式如下：
{{
    "todos": [
        {{
            "id": 1,
            "title": "任务标题",
            "description": "任务描述",
            "status": "pending"
        }}
    ]
}}

重要要求：
1. 将需求分解为3-8个具体的TODO任务
2. 每个任务应该清晰、可操作
3. 任务应该覆盖需求的所有关键方面
4. **严格限制**：只分解与生成图表直接相关的任务，即收集生成图表所需的信息：
   - 例如：明确系统组件、确定组件关系、了解数据流向、识别关键业务流程等
5. **禁止包含**以下类型的任务（这些是图表生成之后的操作，不属于工作分解范围）：
   - 审阅、评审相关的任务
   - 调整、修改相关的任务
   - 实施、部署相关的任务
   - 测试、验证相关的任务
6. 所有任务都应该聚焦在：为了生成准确的图表，需要收集哪些信息、澄清哪些细节"""


CLARIFICATION_BUILD_PROMPT_TEMPLATE = """请针对以下架构需求进行澄清：

【原始需求】
{requirement}

【当前理解】
{current_understanding}

{previous_clarifications_section}

【任务】
请评估当前理解是否清晰，如有歧义或不完整，请提出1-2个最关键的问题。

如果理解清晰，请回答：
---
状态：理解清晰，可以开始绘制
总结：[用结构化方式总结您的理解]
---

如果仍需澄清，请回答：
---
状态：需要澄清
问题1：[具体问题]
问题2：[具体问题]
"""


CLARIFICATION_TODO_ITEM_PROMPT_TEMPLATE = """针对以下TODO任务，请提出1-2个关键问题来澄清需求细节：

【原始需求】
{requirement}

【当前TODO任务】
标题：{todo_title}
描述：{todo_description}

【已澄清的问题】
{previous_clarifications_section}

请评估：如果这个TODO任务需要更多信息才能完成，请提出1-2个最关键的问题。
如果信息已足够，请回答"理解清晰，可以继续"。

如果理解清晰，请回答：
---
状态：理解清晰
总结：[简要总结对这项任务的理解]
---

如果仍需澄清，请回答：
---
状态：需要澄清
问题1：[具体问题]
问题2：[具体问题（如需要）]
---"""


CLARIFICATION_COLLECT_QUESTIONS_PROMPT_TEMPLATE = """针对以下所有TODO任务，请一次性提出所有需要澄清的关键问题：

【原始需求】
{requirement}

【所有TODO任务】
{todos_text}

【已澄清的问题】
{previous_clarifications_section}

请评估每个任务，一次性提出所有需要澄清的关键问题。

重要说明：
1. 最多提出8个问题（如果问题较多，请选择最关键的8个）
2. 严格禁止询问关于输出格式、图表格式、导出格式的问题：
   - 不要问"需要什么格式的图"、"输出格式是什么"、"要导出成什么格式"等问题
   - 系统输出格式已明确：生成Mermaid文件（.mmd）并自动渲染为PNG图片
   - 不要询问Visio、PDF、PPT等格式相关问题
3. 不要询问关于图表类型选择的问题，用户已经选择了图表类型
4. 重点关注需求内容、组件关系、数据流向、业务流程等架构设计相关的细节

请以以下格式返回：
---
任务1: [任务标题]
问题1: [具体问题]
问题2: [具体问题（如需要）]

任务2: [任务标题]
问题1: [具体问题]

任务3: [任务标题]
（如果此任务已清晰，可以写"无需澄清"或省略）
---

如果没有需要澄清的问题，请回答"所有任务理解清晰"。"""


# ==================== Generation Agent 提示 ====================

GENERATION_SYSTEM_PROMPT = """你是一位生成各种类型Mermaid图表的专家。

你的职责：
1. 清晰理解用户需求
2. 为请求的图表类型生成标准的Mermaid代码
3. 使用标准Mermaid语法，不使用自定义样式

你应该生成干净、标准的Mermaid图表，遵循标准Mermaid约定。
图表应该易于理解，并与标准Mermaid渲染器兼容。

支持的图表类型：
- flowchart：用于流程和系统工作流的流程图
- sequenceDiagram：用于对象交互的时序图
- gantt：用于项目调度的甘特图
- classDiagram：用于面向对象建模的类图
- stateDiagram-v2：用于状态转换的状态图
- pie：用于比例数据的饼图
- quadrantChart：用于战略分析的象限图
- journey：用于用户体验的用户旅程图"""


# 流程图提示
GENERATION_FLOWCHART_PROMPT_TEMPLATE = """请根据以下需求生成详细的Mermaid流程图代码。

需求：
{requirements}

要求：
1. 使用标准的Mermaid flowchart语法
2. 布局方向选择（重要）：
   - 如果流程步骤很多（超过8个步骤），使用 flowchart TD（从上到下）布局，这样可以在多行显示，避免图表过长过窄
   - 如果流程步骤较少（8个或更少），可以使用 flowchart LR（从左到右）布局
   - 如果步骤很多且需要更好的组织，可以使用 flowchart TD 并配合 subgraph 分组显示
3. 节点要包含详细内容，使用\\n分隔多个子项，例如：NodeID["节点标题\\n子项1\\n子项2"]
4. 使用标准节点形状：
   - 矩形：NodeID["节点标题\\n子项1\\n子项2"]
   - 圆角矩形：NodeID("节点标题\\n子项1")
   - 圆形：NodeID((节点标题))
   - 菱形：NodeID{{节点标题}}
   - 六边形：NodeID{{节点标题}}
5. 使用标准连接线并添加有意义的标签：
   - 实线箭头：NodeA -->|标签| NodeB 或 NodeA --> NodeB
   - 虚线箭头：NodeA -.->|标签| NodeB 或 NodeA -.-> NodeB
   - 粗线：NodeA --- NodeB
6. 对于长流程（如烹饪步骤、工艺流程等），使用 flowchart TD 布局，让节点纵向排列，这样：
   - 图表不会太长太窄
   - 文字会更大更清晰
   - 更适应屏幕显示
7. 可以使用 subgraph 对相关步骤进行分组，但**必须确保子图与外部节点有连接**，例如：
   A --> B
   subgraph 准备阶段["准备阶段"]
   B --> C
   C --> D
   end
   D --> E
   subgraph 执行阶段["执行阶段"]
   E --> F
   F --> G
   end
   G --> H
   **重要**：如果使用subgraph，必须确保：
   - 子图内的节点能够连接到子图外的节点
   - 子图外的节点能够连接到子图内的节点
   - 子图之间能够相互连接
   - 不要创建孤立的subgraph（没有与外部连接的子图）
8. 确保图表详细完整，包含所有相关组件和连接关系
9. 不要添加任何样式定义（classDef、style、linkStyle等）
10. 不要添加任何注释
11. 只输出Mermaid代码，不要markdown代码块标记

请生成详细的Mermaid代码（注意：对于步骤多的流程，优先使用 flowchart TD 布局）：
"""


# 时序图提示
GENERATION_SEQUENCE_DIAGRAM_PROMPT_TEMPLATE = """请根据以下需求生成详细的Mermaid时序图代码。

需求：
{requirements}

要求：
1. 使用标准的Mermaid sequenceDiagram语法
2. 第一行必须是：sequenceDiagram
3. 定义参与者（participants）：
   - 使用 participant 或 actor 关键字
   - 例如：participant A as 参与者A
4. 定义交互流程：
   - 使用箭头语法：A->>B: 消息内容
   - 实线箭头：->>
   - 虚线箭头：-->
   - 实线箭头（返回）：-->> 
   - 虚线箭头（返回）：--->
5. 可以添加激活框：activate A 和 deactivate A
6. 可以添加注释：Note over A,B: 注释内容
7. 确保图表完整清晰，包含所有交互步骤
8. 不要添加任何样式定义
9. 只输出Mermaid代码，不要markdown代码块标记

请生成详细的时序图代码：
"""


# 甘特图提示
GENERATION_GANTT_PROMPT_TEMPLATE = """请根据以下需求生成详细的Mermaid甘特图代码。

需求：
{requirements}

要求：
1. 使用标准的Mermaid gantt语法
2. 第一行必须是：gantt
3. 定义日期格式：dateFormat YYYY-MM-DD（必须在title之前）
4. 定义标题：title 项目名称
5. 定义任务：
   - section 阶段名称（每个阶段用section分隔）
   - 任务名称 :状态, 开始日期, 持续天数（如：任务A :active, 2023-10-01, 7d）
   - 或者任务名称 :状态, 开始日期, 结束日期（如：任务A :active, 2023-10-01, 2023-10-07）
   - 里程碑格式：任务名称 :milestone, 日期, 0d（如：里程碑1 :milestone, 2023-10-07, 0d）
6. 状态标识（可选）：
   - done: 已完成
   - active: 进行中
   - crit: 关键路径
   - milestone: 里程碑
7. 重要：任务定义格式必须正确：
   - 普通任务：任务名称 :状态, YYYY-MM-DD, Xd（Xd表示持续天数）
   - 里程碑：任务名称 :milestone, YYYY-MM-DD, 0d
   - 不要使用taskId，直接写任务名称和日期
8. 确保时间安排合理，任务顺序清晰
9. 日期必须使用YYYY-MM-DD格式
10. 只输出Mermaid代码，不要markdown代码块标记

请生成详细的甘特图代码：
"""


# 类图提示
GENERATION_CLASS_DIAGRAM_PROMPT_TEMPLATE = """请根据以下需求生成详细的Mermaid类图代码。

需求：
{requirements}

要求：
1. 使用标准的Mermaid classDiagram语法
2. 第一行必须是：classDiagram
3. 定义类（重要：类定义和关系必须分开）：
   - **必须使用 class 关键字**：class 类名 {{}} 或 class 类名 {{
   - **错误示例**：LibraryService {{ }}（缺少class关键字）
   - **正确示例**：class LibraryService {{ }}
   - 详细格式：class 类名 {{
        +属性名: 类型
        +方法名() 返回类型
      }}
   - **重要**：类定义必须完整，不要在类定义行上写关系符号（如 <|--）
   - **重要**：所有类定义必须在关系定义之前，不要将类定义放在关系之后
4. 类成员语法（**严格遵守**）：
   - + 表示public
   - - 表示private
   - # 表示protected
   - ~ 表示package/internal
   - **属性定义**：属性名: 类型（使用冒号，如：+id: String）
   - **方法定义**：方法名() 返回类型（**绝对不要使用冒号**，用空格分隔，如：+login() Boolean）
   - **错误示例**：+login(): Boolean（有冒号，错误！）
   - **正确示例**：+login() Boolean（无冒号，正确！）
   - 返回类型如果是泛型，使用 ~ 包裹，如：List~String~
5. 定义关系（必须单独成行，不能和类定义写在一起）：
   - **继承**：父类 <|-- 子类（父类在左边，子类在右边，箭头指向父类）
   - **实现**：接口 <|.. 实现类
   - **组合**：整体 *-- 部分
   - **聚合**：整体 o-- 部分
   - **关联**：类A --> 类B（使用 -->，不是 --|> 或 --）
   - **依赖**：类A ..> 类B
   - **重要**：不要使用 --|> 或单独的 --，使用标准的 --> 表示关联
6. **关键语法规则**：
   - 所有类必须先定义完成（用大括号闭合），然后再在单独的行定义关系
   - **错误的写法1**：LibraryService {{ }}（缺少class关键字）
   - **错误的写法2**：class Admin <|-- User {{ ... }}（关系不能和类定义写在一起）
   - **错误的写法3**：+login(): Boolean（方法定义不能用冒号）
   - **错误的写法4**：Book --|> Category（应该用 --> 或 <|--）
   - **错误的写法5**：LibraryService -- Book（应该用 --> 或其他标准关系符号）
   - **错误的写法6**：在关系定义之后定义类（所有类必须在所有关系之前）
   - **正确的写法**：
     classDiagram
     class User {{
         +id: String
         +login() Boolean
     }}
     class Admin {{
         +permissions: String
     }}
     class LibraryService {{
         +borrowBook() Boolean
     }}
     User <|-- Admin
     LibraryService ..> User
7. 确保类之间的关系清晰准确，继承方向正确
8. 只输出Mermaid代码，不要markdown代码块标记

示例格式（**严格按照此格式，特别是方法定义**）：
classDiagram
    class User {{
        +id: String
        +username: String
        +email: String
        +login() Boolean
        +register() Boolean
        +updateProfile() Boolean
    }}
    class Admin {{
        +permissions: String
        +manageUsers() Boolean
    }}
    User <|-- Admin

**重要提醒**：
- 属性用冒号：+id: String ✅
- 方法用空格（不用冒号）：+login() Boolean ✅
- 方法用冒号是错误：+login(): Boolean ❌
- 关系用标准符号：User <|-- Admin ✅
- 不要用错误符号：Book --|> Category ❌，应该用 Book --> Category

请生成详细的类图代码（**特别注意方法定义绝对不能使用冒号**）：
"""


# 状态图提示
GENERATION_STATE_DIAGRAM_PROMPT_TEMPLATE = """请根据以下需求生成详细的Mermaid状态图代码。

需求：
{requirements}

要求：
1. 使用标准的Mermaid stateDiagram-v2语法
2. 第一行必须是：stateDiagram-v2
3. 定义状态：
   - [*] 表示起始状态
   - [*] 表示结束状态
   - state 状态名 {{}} 表示状态
   - state 状态名 {{\n  状态描述\n  }} 表示有内容的状态
4. 定义状态转换：
   - 状态A --> 状态B : 转换条件
   - 可以添加注释：状态A --> 状态B : 转换条件/动作
5. 可以定义嵌套状态：
   - state 复合状态 {{
   -   state 子状态1
   -   state 子状态2
   - }}
6. 确保状态转换逻辑完整清晰
7. 只输出Mermaid代码，不要markdown代码块标记

请生成详细的状态图代码：
"""


# 饼图提示
GENERATION_PIE_CHART_PROMPT_TEMPLATE = """请根据以下需求生成详细的Mermaid饼图代码。

需求：
{requirements}

要求：
1. 使用标准的Mermaid pie语法
2. 第一行必须是：pie title 图表标题
3. 定义数据项：
   - "标签" : 数值
   - 例如："苹果" : 30
4. 数值可以是整数或小数
5. 确保所有数据项的总和合理
6. 标签使用中文
7. 只输出Mermaid代码，不要markdown代码块标记

请生成详细的饼图代码：
"""


# 象限图提示
GENERATION_QUADRANT_CHART_PROMPT_TEMPLATE = """请根据以下需求生成详细的Mermaid象限图代码。

需求：
{requirements}

要求：
1. 使用标准的Mermaid quadrantChart语法（Mermaid 10.9.4版本）
2. 第一行必须是：quadrantChart
3. 定义象限标题（可选）：title 象限图标题
4. 定义坐标轴（必须使用箭头格式）：
   - x-axis 左端标签 --> 右端标签
   - y-axis 下端标签 --> 上端标签
   - 例如：x-axis Low --> High 或 x-axis 低增长率 --> 高增长率
   - 例如：y-axis Low --> High 或 y-axis 低市场份额 --> 高市场份额
   - **重要**：必须使用 " --> " 格式，不能使用括号或其他格式
5. 定义象限标签：
   - quadrant-1 第一象限标签（右上象限）
   - quadrant-2 第二象限标签（左上象限）
   - quadrant-3 第三象限标签（右下象限）
   - quadrant-4 第四象限标签（左下象限）
6. 定义数据点：
   - 格式：名称: [x坐标, y坐标]
   - 坐标范围通常是0到1之间的小数
   - **重要**：点名称不能使用中文"点"字前缀，直接使用英文或中文名称
   - 正确示例：A: [0.5, 0.8] 或 产品A: [0.5, 0.8]
   - 错误示例：点A: [0.5, 0.8]（不要使用"点"前缀）
7. 确保数据点分布在合适的象限
8. 只输出Mermaid代码，不要markdown代码块标记

**关键语法要求**：
- x-axis 和 y-axis 必须使用 " --> " 格式（两端标签用箭头连接）
- 数据点名称不要使用"点"前缀
- 坐标值应该是0到1之间的浮点数

请生成详细的象限图代码：
"""


# 用户旅程图提示
GENERATION_JOURNEY_PROMPT_TEMPLATE = """请根据以下需求生成详细的Mermaid用户旅程图代码。

需求：
{requirements}

要求：
1. 使用标准的Mermaid journey语法
2. 第一行必须是：journey
3. 定义标题：title 旅程标题
4. 定义阶段和步骤：
   - section 阶段名称
   - 步骤名称: 情感状态: 参与者, 分数
   - 情感状态：happy, sad, angry, neutral, excited, disappointed, surprised
   - 参与者：用户或系统
   - 分数：1-5的整数
5. 例如：
   - section 浏览阶段
   - 浏览商品: happy: 用户, 4
   - 查看详情: neutral: 用户, 3
6. 确保旅程步骤完整连贯
7. 情感状态要符合用户在该步骤的真实感受
8. 只输出Mermaid代码，不要markdown代码块标记

请生成详细的用户旅程图代码：
"""


# 错误解释提示
GENERATION_ERROR_EXPLANATION_PROMPT_TEMPLATE = """请分析以下Mermaid代码的语法错误，并提供详细的解释和修复建议。

错误信息：
{error_message}

错误代码片段：
{code_snippet}

完整代码：
```mermaid
{mermaid_code}
```

图表类型：{diagram_type}

请按照以下格式回答：

## 错误原因分析
[详细说明为什么会出现这个错误]

## 具体问题位置
[指出问题出现在哪些行]

## 修复建议
[提供修复说明]

## 修复后的完整代码
```mermaid
[这里提供完整的修复后的Mermaid代码，必须包含原始代码的所有内容，只修复错误部分，不要有任何markdown格式标记，直接是纯Mermaid代码。请确保代码完整，不要截断任何部分。

{type_specific_notes}]
```

## 相关语法规则
[简要说明相关的Mermaid语法规则]

请用中文回答，格式清晰易懂。最重要的是在"修复后的完整代码"部分提供完整的、可以直接使用的修复后的代码。

**关键要求**：
{type_specific_requirements}
3. 必须提供完整的代码，包含所有原始代码的内容，只修复错误部分
"""


# 图表类型特定的修复提示
TYPE_SPECIFIC_NOTES_CLASS_DIAGRAM = """**重要提醒（类图专用，必须严格遵守）**：
- 所有类定义必须使用 "class 类名 {{" 格式，例如：class User {{、class Admin {{
- 绝对不要遗漏 class 关键字，错误的示例：User {{、Admin {{，正确的示例：class User {{、class Admin {{
- 修复时只移除错误的前缀或非法字符，但必须保留并确保 class 关键字存在
- 确保所有类定义都有 class 关键字，所有关系定义都在类定义之后"""


TYPE_SPECIFIC_NOTES_QUADRANT_CHART = """**重要提醒（象限图专用，必须严格遵守）**：
- x-axis 和 y-axis 的标签如果包含中文，必须使用引号包裹，例如：x-axis "低增长率" --> "高增长率"
- quadrant-1 到 quadrant-4 的标签如果包含中文，必须使用引号包裹，例如：quadrant-1 "明星产品"
- 数据点坐标必须是0到1之间的浮点数
- 数据点名称不需要引号（除非包含特殊字符）"""


TYPE_SPECIFIC_NOTES_DEFAULT = """**重要提醒**：
- 请确保所有语法符合Mermaid官方规范
- 修复时只修改错误部分，保持其他内容不变"""


# 图表类型特定的修复要求
TYPE_SPECIFIC_REQUIREMENTS_CLASS_DIAGRAM = """1. 对于类图，所有类定义必须包含 "class" 关键字，格式：class 类名 {{ 或 class 类名 {{
2. 绝对不要遗漏 class 关键字，错误的示例：User {{、Admin {{，正确的示例：class User {{、class Admin {{"""


TYPE_SPECIFIC_REQUIREMENTS_QUADRANT_CHART = """1. 对于象限图，x-axis 和 y-axis 的中文标签必须使用引号包裹，例如：x-axis "低增长率" --> "高增长率"
2. quadrant-1 到 quadrant-4 的中文标签必须使用引号包裹，例如：quadrant-1 "明星产品"
"""


TYPE_SPECIFIC_REQUIREMENTS_DEFAULT = """1. 请确保语法符合Mermaid官方规范
2. 修复时保持代码完整性"""

