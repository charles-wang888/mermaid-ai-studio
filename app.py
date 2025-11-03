"""主应用入口 - Streamlit界面"""
import streamlit as st
import streamlit.components.v1 as components
import os
import base64
import html as html_module
import re

from agents.clarification_agent import ClarificationAgent
from agents.generation_agent import GenerationAgent
from config import LLM_CONFIG, DEFAULT_LLM_BACKEND


# 页面配置
st.set_page_config(
    page_title="架构设计图生成工具",
    page_icon="🎨",
    layout="wide"
)

# 支持的图表类型
DIAGRAM_TYPES = {
    "flowchart": {
        "name": "流程图",
        "description": "用于表示流程或者系统的工作原理",
        "icon": "🔄"
    },
    "sequenceDiagram": {
        "name": "时序图",
        "description": "用于显示对象之间的交互顺序",
        "icon": "⏱️"
    },
    "gantt": {
        "name": "甘特图",
        "description": "用于项目管理和调度，显示任务的时间安排",
        "icon": "📅"
    },
    "classDiagram": {
        "name": "类图",
        "description": "用于表示类、接口以及它们的关系，是面向对象建模的工具",
        "icon": "📦"
    },
    "stateDiagram-v2": {
        "name": "状态图",
        "description": "用于描述对象的状态变化",
        "icon": "🔄"
    },
    "pie": {
        "name": "饼图",
        "description": "用于显示比例或者百分比数据",
        "icon": "🥧"
    },
    "quadrantChart": {
        "name": "象限图",
        "description": "用于将数据点分布在4个象限之内，一般用于战略分析",
        "icon": "📊"
    },
    "journey": {
        "name": "用户旅程图",
        "description": "用于描述用户与系统交互的体验和步骤",
        "icon": "🗺️"
    }
}

# 初始化Session State
if 'selected_diagram_type' not in st.session_state:
    st.session_state.selected_diagram_type = None
if 'clarification_agent' not in st.session_state:
    st.session_state.clarification_agent = None
if 'generation_agent' not in st.session_state:
    st.session_state.generation_agent = None
if 'clarification_round' not in st.session_state:
    st.session_state.clarification_round = 0
if 'clarification_history' not in st.session_state:
    st.session_state.clarification_history = []
if 'current_requirement' not in st.session_state:
    st.session_state.current_requirement = ""
if 'clarified_requirements' not in st.session_state:
    st.session_state.clarified_requirements = ""
if 'generated_diagram' not in st.session_state:
    st.session_state.generated_diagram = None
# 新增：TODO列表相关状态
if 'todo_list' not in st.session_state:
    st.session_state.todo_list = []
if 'current_todo_index' not in st.session_state:
    st.session_state.current_todo_index = 0
if 'waiting_for_todo_answer' not in st.session_state:
    st.session_state.waiting_for_todo_answer = False
if 'current_todo_questions' not in st.session_state:
    st.session_state.current_todo_questions = []
if 'confirmation_step' not in st.session_state:
    st.session_state.confirmation_step = False
if 'todo_processed' not in st.session_state:
    st.session_state.todo_processed = set()  # 记录哪些TODO已经自动处理过
if 'auto_generated' not in st.session_state:
    st.session_state.auto_generated = False  # 记录是否已自动生成图表
if 'all_clarification_questions' not in st.session_state:
    st.session_state.all_clarification_questions = []  # 所有需要澄清的问题，格式：[{"todo_index": 0, "todo_title": "...", "questions": [...], "answers": [...]}]
if 'collecting_questions' not in st.session_state:
    st.session_state.collecting_questions = False  # 是否正在收集问题
if 'editable_clarification_history' not in st.session_state:
    st.session_state.editable_clarification_history = []  # 可编辑的澄清历史
if 'show_mermaid_code' not in st.session_state:
    st.session_state.show_mermaid_code = False  # 是否显示Mermaid代码
if 'editable_mermaid_code' not in st.session_state:
    st.session_state.editable_mermaid_code = None  # 可编辑的Mermaid代码
if 'mermaid_error_info' not in st.session_state:
    st.session_state.mermaid_error_info = None  # Mermaid语法错误详细信息
if 'mermaid_ai_explanation' not in st.session_state:
    st.session_state.mermaid_ai_explanation = None  # AI解释和修复建议
if 'mermaid_fixed_code' not in st.session_state:
    st.session_state.mermaid_fixed_code = None  # AI修复后的代码
if 'image_zoom_level' not in st.session_state:
    st.session_state.image_zoom_level = 100  # 图片缩放级别，默认100%（原始大小）


def initialize_agents():
    """初始化智能体"""
    if st.session_state.clarification_agent is None:
        try:
            backend = st.session_state.get('selected_backend', DEFAULT_LLM_BACKEND)
            st.session_state.clarification_agent = ClarificationAgent(
                model_config_name="default",
                backend=backend
            )
            st.session_state.generation_agent = GenerationAgent(
                model_config_name="default",
                backend=backend
            )
        except Exception as e:
            st.error(f"智能体初始化失败: {str(e)}")
            st.info("请确保已正确配置模型连接")


def reset_session():
    """重置会话"""
    st.session_state.selected_diagram_type = None
    st.session_state.clarification_round = 0
    st.session_state.clarification_history = []
    st.session_state.current_requirement = ""
    st.session_state.clarified_requirements = ""
    st.session_state.generated_diagram = None
    st.session_state.todo_list = []
    st.session_state.current_todo_index = 0
    st.session_state.waiting_for_todo_answer = False
    st.session_state.current_todo_questions = []
    st.session_state.confirmation_step = False
    st.session_state.todo_processed = set()
    st.session_state.auto_generated = False
    st.session_state.all_clarification_questions = []
    st.session_state.collecting_questions = False
    st.session_state.editable_clarification_history = []
    st.session_state.show_mermaid_code = False
    st.session_state.editable_mermaid_code = None
    st.session_state.mermaid_error_info = None
    st.session_state.mermaid_ai_explanation = None
    st.session_state.mermaid_fixed_code = None
    st.session_state.image_zoom_level = 100  # 重置缩放级别
    if st.session_state.clarification_agent:
        st.session_state.clarification_agent.clarification_rounds = 0
        st.session_state.clarification_agent.clarified_points = []


def get_current_step():
    """获取当前步骤"""
    if st.session_state.selected_diagram_type is None:
        return 1
    elif not st.session_state.clarified_requirements or not st.session_state.generated_diagram:
        return 2  # 需求澄清阶段（包括TODO、澄清、确认、生成）
    elif not st.session_state.generated_diagram:
        return 3  # 生成中（通常一闪而过）
    else:
        return 3  # 绘制图形（图表已生成）


def render_wizard_steps(current_step):
    """渲染Wizard步骤指示器"""
    steps = [
        {"number": 1, "title": "选择图表类型", "icon": "📊"},
        {"number": 2, "title": "需求输入与澄清", "icon": "📝"},
        {"number": 3, "title": "绘制图形", "icon": "🎨"}
    ]
    
    # 计算连接线填充百分比
    num_steps = len(steps)
    connector_width = 0
    if current_step > 1:
        connector_width = round((current_step - 1) * 100 / (num_steps - 1), 2)
    
    # 构建步骤HTML
    steps_html = ""
    for step in steps:
        if step["number"] < current_step:
            circle_class = "completed"
            title_class = "completed"
            display_text = "✓"
        elif step["number"] == current_step:
            circle_class = "active"
            title_class = "active"
            display_text = str(step["number"])  # 改为显示数字而不是emoji
        else:
            circle_class = "pending"
            title_class = "pending"
            display_text = str(step["number"])
        
        step_title = step["title"]
        steps_html += f'<div class="wizard-step"><div class="step-circle {circle_class}">{display_text}</div><div class="step-title {title_class}">{step_title}</div></div>'
    
    # 完整的HTML文档
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
        body {{
            margin: 0;
            padding: 0;
        }}
        .wizard-container {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 30px 20px;
            border-radius: 15px;
            margin: 20px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1), 0 2px 5px rgba(0,0,0,0.05);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            min-height: 130px;
        }}
        .wizard-steps {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: relative;
            padding: 0 20px 20px 20px;
        }}
        .wizard-step {{
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
            z-index: 2;
        }}
        .step-connector {{
            position: absolute;
            top: 30px;
            left: 25px;
            right: 25px;
            height: 4px;
            background: linear-gradient(90deg, #e0e0e0 0%, #d0d0d0 100%);
            z-index: 1;
            border-radius: 10px;
            box-shadow: inset 0 1px 2px rgba(0,0,0,0.1);
        }}
        .step-connector-fill {{
            height: 100%;
            background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
            transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(79, 172, 254, 0.4), inset 0 1px 1px rgba(255,255,255,0.3);
            position: relative;
        }}
        .step-connector-fill::after {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            animation: shimmer 2s infinite;
        }}
        @keyframes shimmer {{
            0% {{ transform: translateX(-100%); }}
            100% {{ transform: translateX(100%); }}
        }}
        .step-circle {{
            width: 55px;
            height: 55px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            font-weight: bold;
            margin-bottom: 12px;
            border: 3px solid;
            background: white;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            z-index: 3;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }}
        .step-circle:hover {{
            transform: scale(1.05);
        }}
        .step-circle.active {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-color: #667eea;
            box-shadow: 0 0 0 6px rgba(102, 126, 234, 0.2), 0 4px 15px rgba(102, 126, 234, 0.4);
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ box-shadow: 0 0 0 6px rgba(102, 126, 234, 0.2), 0 4px 15px rgba(102, 126, 234, 0.4); }}
            50% {{ box-shadow: 0 0 0 8px rgba(102, 126, 234, 0.15), 0 4px 20px rgba(102, 126, 234, 0.5); }}
        }}
        .step-circle.completed {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            border-color: #11998e;
            box-shadow: 0 3px 10px rgba(17, 153, 142, 0.3);
        }}
        .step-circle.pending {{
            background: white;
            color: #999;
            border-color: #d0d0d0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .step-title {{
            font-size: 14px;
            font-weight: 600;
            text-align: center;
            margin-top: 8px;
            color: #333;
            line-height: 1.4;
            padding: 0 5px;
        }}
        .step-title.active {{
            color: #667eea;
            font-weight: 700;
        }}
        .step-title.completed {{
            color: #11998e;
        }}
        .step-title.pending {{
            color: #999;
        }}
        </style>
    </head>
    <body>
        <div class="wizard-container">
            <div class="wizard-steps">
                <div class="step-connector">
                    <div class="step-connector-fill" style="width: {connector_width}%;"></div>
                </div>
                {steps_html}
            </div>
        </div>
    </body>
    </html>
    """
    
    # 使用 components.html 来渲染，增加高度
    components.html(html_content, height=160, scrolling=False)


def main():
    """主界面"""
    st.title("🎨 架构设计图生成工具")
    
    # 显示Wizard步骤指示器
    current_step = get_current_step()
    render_wizard_steps(current_step)
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 配置")
        
        # 模型后端选择
        st.subheader("模型配置")
        available_backends = list(LLM_CONFIG.keys())
        if 'selected_backend' not in st.session_state:
            st.session_state.selected_backend = DEFAULT_LLM_BACKEND
        
        backend = st.selectbox(
            "选择模型后端",
            available_backends,
            index=available_backends.index(st.session_state.selected_backend)
        )
        
        if backend != st.session_state.selected_backend:
            st.session_state.selected_backend = backend
            # 重新初始化智能体
            st.session_state.clarification_agent = None
            st.session_state.generation_agent = None
        
        # 显示当前配置
        backend_config = LLM_CONFIG[backend]
        st.caption(f"模型: {backend_config.get('model_name', 'N/A')}")
        if backend != 'ollama':
            st.caption(f"需要API Key: {'是' if backend_config.get('api_key') == '' else '否'}")
        
        st.info(f"当前后端: **{backend.upper()}**")
        st.markdown("---")
        
        if st.button("🔄 重置会话"):
            reset_session()
            st.rerun()
    
    # 初始化智能体
    initialize_agents()
    
    # 主体内容
    # 第一步：选择图表类型
    if st.session_state.selected_diagram_type is None:
        st.markdown("### 请选择您要生成的图表类型")
        
        # 创建两列布局显示图表类型选择
        cols = st.columns(2)
        for idx, (type_key, type_info) in enumerate(DIAGRAM_TYPES.items()):
            with cols[idx % 2]:
                with st.container():
                    st.markdown(f"### {type_info['icon']} {type_info['name']}")
                    st.caption(type_info['description'])
                    if st.button(f"选择 {type_info['name']}", key=f"select_{type_key}"):
                        st.session_state.selected_diagram_type = type_key
                        st.rerun()
        
        st.markdown("---")
        st.info("💡 提示：选择图表类型后，您就可以输入需求并生成对应的图表了")
    else:
        # 显示已选择的图表类型
        selected_type_info = DIAGRAM_TYPES[st.session_state.selected_diagram_type]
        st.success(f"已选择：{selected_type_info['icon']} {selected_type_info['name']} - {selected_type_info['description']}")
        if st.button("🔙 重新选择图表类型"):
            reset_session()
            st.rerun()
        
        st.markdown("---")
        
        # 连贯的Wizard流程
        
        # 连贯的Wizard流程：需求输入 -> TODO列表 -> 澄清 -> 确认 -> 生成 -> 导出
        diagram_type_name = DIAGRAM_TYPES[st.session_state.selected_diagram_type]['name']
        
        # 阶段1: 需求输入和生成TODO列表
        if not st.session_state.todo_list and not st.session_state.confirmation_step and not st.session_state.generated_diagram:
            st.markdown(f"### 📝 请描述您要生成的**{diagram_type_name}**的具体需求")
            
            placeholder_examples = {
                "flowchart": "例如：设计一个微服务架构的在线商城系统，包含用户服务、商品服务、订单服务和支付服务...",
                "sequenceDiagram": "例如：用户登录系统的交互流程，包括用户、前端、认证服务和数据库之间的交互...",
                "gantt": "例如：软件开发项目计划，包括需求分析、设计、开发、测试、部署等阶段及其时间安排...",
                "classDiagram": "例如：电商系统的类设计，包括User、Product、Order、Payment等类及其关系...",
                "stateDiagram-v2": "例如：订单状态流转，包括待支付、已支付、已发货、已完成、已取消等状态...",
                "pie": "例如：公司各部门人员占比，技术部30%，产品部20%，运营部25%，市场部25%...",
                "quadrantChart": "例如：产品功能优先级矩阵，横轴为重要性，纵轴为紧急度...",
                "journey": "例如：用户在线购物的完整旅程，从浏览商品、加入购物车、下单、支付到收货评价..."
            }
            
            requirement = st.text_area(
                "需求描述",
                value=st.session_state.current_requirement,
                height=150,
                placeholder=placeholder_examples.get(st.session_state.selected_diagram_type, "请详细描述您的需求...")
            )
            
            if st.button("🚀 开始工作分解", type="primary"):
                if requirement:
                    st.session_state.current_requirement = requirement
                    with st.spinner("🤖 AI正在分析需求并生成工作分解列表..."):
                        try:
                            todos = st.session_state.clarification_agent.generate_todo_list(requirement)
                            st.session_state.todo_list = todos
                            st.session_state.current_todo_index = 0
                            st.rerun()
                        except Exception as e:
                            st.error(f"生成TODO列表失败: {str(e)}")
                else:
                    st.warning("请输入需求描述")
        
        # 阶段2: 显示TODO列表并进行澄清
        elif st.session_state.todo_list and not st.session_state.confirmation_step and not st.session_state.generated_diagram:
            st.markdown("### 📋 工作分解列表")
            
            # 显示TODO列表 - 优化后的样式
            for idx, todo in enumerate(st.session_state.todo_list):
                # 使用统一的清理方法清理HTML标签和Markdown符号（适用于所有图表类型）
                title_raw = str(todo.get('title', ''))
                if st.session_state.clarification_agent:
                    # 使用clarification_agent的统一清理方法
                    title_raw = st.session_state.clarification_agent.clean_html_and_markdown(title_raw)
                else:
                    # 如果agent未初始化，使用简单清理作为后备
                    title_raw = re.sub(r'^\*+|\*+$', '', title_raw).strip()
                    title_raw = re.sub(r'<[^>]+>', '', title_raw)
                # 安全地转义HTML特殊字符
                title = html_module.escape(title_raw)
                
                description_raw = str(todo.get('description', '')) if todo.get('description') else ''
                if st.session_state.clarification_agent:
                    # 使用clarification_agent的统一清理方法
                    description_raw = st.session_state.clarification_agent.clean_html_and_markdown(description_raw)
                else:
                    # 如果agent未初始化，使用简单清理作为后备
                    description_raw = re.sub(r'<[^>]+>', '', description_raw)
                description = html_module.escape(description_raw)
                
                # 使用自定义HTML创建带checkbox的内容块
                description_html = f'<div style="font-size: 14px; color: #5a6c7d; line-height: 1.6; margin-top: 6px;">{description}</div>' if description else ''
                
                todo_html = f"""
                <div style="
                    background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
                    border: 2px solid #e0e0e0;
                    border-radius: 12px;
                    padding: 16px 20px;
                    margin: 12px 0;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                    transition: all 0.3s ease;
                ">
                    <div style="display: flex; align-items: flex-start; gap: 12px;">
                        <div style="flex-shrink: 0; margin-top: 2px;">
                            <input type="checkbox" checked disabled style="
                                width: 20px;
                                height: 20px;
                                cursor: default;
                                accent-color: #4facfe;
                            ">
                        </div>
                        <div style="flex: 1;">
                            <div style="
                                font-size: 18px;
                                font-weight: 600;
                                color: #2c3e50;
                                margin-bottom: 8px;
                            ">
                                {title}
                            </div>
                            {description_html}
                        </div>
                    </div>
                </div>
                """
                st.markdown(todo_html, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # 一次性收集所有需要澄清的问题
            if not st.session_state.collecting_questions and not st.session_state.all_clarification_questions:
                # 自动收集所有问题
                with st.spinner("🤖 AI正在分析所有任务，收集需要澄清的问题..."):
                    try:
                        context = {
                            "requirements": st.session_state.current_requirement,
                            "previous_clarifications": st.session_state.clarification_history
                        }
                        result = st.session_state.clarification_agent.collect_all_clarification_questions(
                            st.session_state.todo_list,
                            st.session_state.current_requirement,
                            context
                        )
                        
                        if result.get("type") == "complete":
                            # 所有任务都不需要澄清，直接进入确认步骤
                            for todo in st.session_state.todo_list:
                                todo['status'] = 'completed'
                            st.session_state.confirmation_step = True
                            st.rerun()
                        else:
                            # 收集到问题
                            questions_by_todo = result.get("questions_by_todo", [])
                            # 初始化问题列表，每个问题都有对应的回答字段
                            st.session_state.all_clarification_questions = []
                            for item in questions_by_todo:
                                for q_idx, question in enumerate(item.get("questions", [])):
                                    st.session_state.all_clarification_questions.append({
                                        "todo_index": item.get("todo_index", 0),
                                        "todo_title": item.get("todo_title", ""),
                                        "question": question,
                                        "answer": ""
                                    })
                            st.session_state.collecting_questions = True
                            st.rerun()
                    except Exception as e:
                        st.error(f"收集澄清问题失败: {str(e)}")
            
            # 显示所有问题和回答框
            elif st.session_state.all_clarification_questions:
                total_questions = len(st.session_state.all_clarification_questions)
                st.markdown(f"### ❓ 请回答以下问题以完善需求（共 {total_questions} 个问题，最多 8 个）")
                
                # 按TODO分组显示问题
                current_todo_index = -1
                for q_idx, q_item in enumerate(st.session_state.all_clarification_questions):
                    todo_idx = q_item.get("todo_index", 0)
                    todo_title = q_item.get("todo_title", f"任务 {todo_idx + 1}")
                    # 使用统一的清理方法清理HTML标签和Markdown符号（适用于所有图表类型）
                    if st.session_state.clarification_agent:
                        todo_title = st.session_state.clarification_agent.clean_html_and_markdown(todo_title)
                    else:
                        # 如果agent未初始化，使用简单清理作为后备
                        todo_title = re.sub(r'^\*+|\*+$', '', todo_title).strip()
                        todo_title = re.sub(r'<[^>]+>', '', todo_title)
                    
                    # 如果切换到新的TODO，显示TODO标题
                    if todo_idx != current_todo_index:
                        if current_todo_index >= 0:
                            st.markdown("---")
                        current_todo_index = todo_idx
                        st.markdown(f"**📌 {todo_title}**")
                    
                    # 显示问题
                    st.markdown(f"**Q{q_idx + 1}: {q_item.get('question', '')}**")
                    
                    # 显示对应的回答框
                    answer_key = f"answer_q{q_idx}"
                    answer = st.text_area(
                        f"您的回答：",
                        value=q_item.get('answer', ''),
                        height=80,
                        key=answer_key,
                        label_visibility="collapsed"
                    )
                    # 更新回答
                    st.session_state.all_clarification_questions[q_idx]['answer'] = answer
                    
                    st.markdown("")  # 添加间距
                
                st.markdown("---")
                
                # 检查是否所有问题都已回答
                all_answered = all(q.get('answer', '').strip() for q in st.session_state.all_clarification_questions)
                
                if st.button("✅ 确认所有回答并继续", type="primary", disabled=not all_answered):
                    # 记录所有澄清历史
                    for q_item in st.session_state.all_clarification_questions:
                        st.session_state.clarification_history.append({
                            "question": q_item.get('question', ''),
                            "answer": q_item.get('answer', ''),
                            "todo_index": q_item.get('todo_index', 0)
                        })
                        st.session_state.clarification_agent.add_clarified_point(
                            q_item.get('question', ''),
                            q_item.get('answer', '')
                        )
                    
                    # 标记所有任务为完成
                    for todo in st.session_state.todo_list:
                        todo['status'] = 'completed'
                    
                    # 进入确认步骤
                    st.session_state.confirmation_step = True
                    st.session_state.all_clarification_questions = []
                    st.session_state.collecting_questions = False
                    st.rerun()
                elif not all_answered:
                    st.info("💡 请回答所有问题后再继续")
        
        # 阶段3: 最终需求确认
        elif st.session_state.confirmation_step and not st.session_state.generated_diagram:
            st.markdown("### ✅ 最终需求确认")
            st.info("💡 请检查并确认以下需求信息，您可以直接编辑任何回答进行调整")
            
            # 显示原始需求
            st.markdown("**📝 原始需求：**")
            original_requirement = st.text_area(
                "原始需求",
                value=st.session_state.current_requirement,
                height=100,
                key="edit_original_requirement",
                label_visibility="collapsed"
            )
            st.session_state.current_requirement = original_requirement
            
            st.markdown("---")
            st.markdown("**❓ 需求澄清并确认：**")
            
            # 确保clarification_history是可编辑的状态
            # 如果editable_clarification_history不存在或为空，且clarification_history有数据，则初始化
            if 'editable_clarification_history' not in st.session_state:
                st.session_state.editable_clarification_history = []
            
            # 如果editable_clarification_history为空，但从clarification_history可以初始化
            if len(st.session_state.editable_clarification_history) == 0 and st.session_state.clarification_history:
                for item in st.session_state.clarification_history:
                    st.session_state.editable_clarification_history.append({
                        "question": item.get('question', ''),
                        "answer": item.get('answer', ''),
                        "todo_index": item.get('todo_index', 0)
                    })
            
            # 显示所有问题-回答对，每个都可编辑
            if st.session_state.editable_clarification_history and len(st.session_state.editable_clarification_history) > 0:
                for idx, item in enumerate(st.session_state.editable_clarification_history):
                    st.markdown(f"**Q{idx + 1}: {item.get('question', '')}**")
                    
                    # 可编辑的回答框
                    edited_answer = st.text_area(
                        f"您的回答 Q{idx + 1}",
                        value=item.get('answer', ''),
                        height=80,
                        key=f"edit_answer_{idx}",
                        label_visibility="collapsed"
                    )
                    # 更新回答
                    st.session_state.editable_clarification_history[idx]['answer'] = edited_answer
                    
                    st.markdown("")  # 添加间距
            else:
                # 如果没有澄清问题，显示提示信息
                st.info("💡 当前没有需要澄清的问题，将直接使用原始需求生成图表")
            
            st.markdown("---")
            
            # 按钮区域
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("✅ 确认最终需求并生成图表", type="primary"):
                    # 更新clarification_history为编辑后的内容
                    st.session_state.clarification_history = st.session_state.editable_clarification_history.copy()
                    
                    # 构建完整需求摘要
                    summary = st.session_state.current_requirement + "\n\n"
                    summary += "【澄清后的补充信息】\n"
                    for item in st.session_state.clarification_history:
                        summary += f"Q: {item.get('question', '')}\n"
                        summary += f"A: {item.get('answer', '')}\n\n"
                    
                    st.session_state.clarified_requirements = summary
                    
                    # 生成图表
                    with st.spinner(f"正在生成{diagram_type_name}..."):
                        try:
                            result = st.session_state.generation_agent.generate_diagram(
                                st.session_state.clarified_requirements,
                                diagram_type=st.session_state.selected_diagram_type
                            )
                            st.session_state.generated_diagram = result
                            st.rerun()
                        except Exception as e:
                            st.error(f"图表生成失败: {str(e)}")
            
            with col2:
                if st.button("🔙 返回修改问题"):
                    st.session_state.confirmation_step = False
                    st.session_state.collecting_questions = False
                    # 保留已编辑的内容
                    if 'editable_clarification_history' in st.session_state:
                        # 同步编辑后的内容到clarification_history
                        st.session_state.clarification_history = st.session_state.editable_clarification_history.copy()
                    st.rerun()
        
        # 阶段4: 显示生成的图表和导出
        elif st.session_state.generated_diagram:
            st.markdown("### 🎨 绘制结果")
            
            # 显示图表，使用带边框的容器
            if st.session_state.generated_diagram.get("png_file") and os.path.exists(st.session_state.generated_diagram["png_file"]):
                # 读取图片并转换为base64
                with open(st.session_state.generated_diagram["png_file"], 'rb') as f:
                    image_bytes = f.read()
                    image_base64 = base64.b64encode(image_bytes).decode()
                
                # 缩放控制按钮
                st.markdown("""
                <style>
                div[data-testid*="column"] button[data-testid*="zoom_in_btn"],
                div[data-testid*="column"] button[data-testid*="zoom_out_btn"],
                div[data-testid*="column"] button[data-testid*="zoom_reset_btn"],
                button[data-testid*="zoom_in_btn"],
                button[data-testid*="zoom_out_btn"],
                button[data-testid*="zoom_reset_btn"] {
                    white-space: nowrap !important;
                    overflow: visible !important;
                }
                /* 特别针对重置按钮，确保文字不换行 */
                button[data-testid*="zoom_reset_btn"] {
                    white-space: nowrap !important;
                    min-width: fit-content !important;
                }
                button[data-testid*="zoom_reset_btn"] span {
                    white-space: nowrap !important;
                    display: inline-block !important;
                }
                </style>
                """, unsafe_allow_html=True)
                zoom_col1, zoom_col2, zoom_col3, zoom_col4 = st.columns([1.2, 1.2, 1.2, 6.4])
                with zoom_col1:
                    if st.button("🔍 放大", key="zoom_in_btn", use_container_width=True):
                        # 每次放大 25%
                        st.session_state.image_zoom_level = min(st.session_state.image_zoom_level + 25, 500)
                        st.rerun()
                with zoom_col2:
                    if st.button("🔎 缩小", key="zoom_out_btn", use_container_width=True):
                        # 每次缩小 25%
                        st.session_state.image_zoom_level = max(st.session_state.image_zoom_level - 25, 50)
                        st.rerun()
                with zoom_col3:
                    if st.button("↺ 重置", key="zoom_reset_btn", use_container_width=True):
                        # 重置到原始大小
                        st.session_state.image_zoom_level = 100
                        st.rerun()
                with zoom_col4:
                    st.caption(f"当前缩放: {st.session_state.image_zoom_level}%")
                
                # 使用HTML容器显示图片，带黑色边框并支持缩放
                zoom_scale = st.session_state.image_zoom_level / 100.0
                image_html = f"""
                <style>
                .diagram-container-wrapper {{
                    width: 100%;
                    margin: 10px 0;
                    overflow: auto;
                }}
                .diagram-container {{
                    border: 2px solid #000;
                    border-radius: 5px;
                    padding: 15px;
                    background: white;
                    width: 100%;
                    box-sizing: border-box;
                    display: block;
                    overflow: auto;
                }}
                .diagram-container img {{
                    max-width: none;
                    width: auto;
                    height: auto;
                    display: block;
                    transform: scale({zoom_scale});
                    transform-origin: top left;
                    transition: transform 0.3s ease;
                }}
                </style>
                <div class="diagram-container-wrapper">
                    <div class="diagram-container">
                        <img src="data:image/png;base64,{image_base64}" alt="绘制的图形" />
                    </div>
                </div>
                """
                st.markdown(image_html, unsafe_allow_html=True)
                
                # 图片下方的居中工具栏
                st.markdown("<div style='text-align: center; margin: 15px 0;'>", unsafe_allow_html=True)
                
                # 创建工具栏按钮（居中布局，按钮自适应宽度）
                tool_cols = st.columns([1, 1, 1, 1, 1])
                
                # PNG文件下载
                if st.session_state.generated_diagram.get("png_file"):
                    with open(st.session_state.generated_diagram["png_file"], 'rb') as f:
                        png_data = f.read()
                    with tool_cols[1]:
                        st.download_button(
                            label="📷 下载PNG",
                            data=png_data,
                            file_name=os.path.basename(st.session_state.generated_diagram["png_file"]),
                            mime="image/png",
                            key="download_png_toolbar"
                        )
                
                # 查看Mermaid代码
                with tool_cols[2]:
                    show_code = st.button("📝 查看代码", key="show_code_toolbar")
                    if show_code:
                        st.session_state.show_mermaid_code = not st.session_state.get('show_mermaid_code', False)
                        st.rerun()
                
                # Mermaid代码文件下载（如果有编辑，下载编辑后的代码）
                if st.session_state.generated_diagram.get("mermaid_code"):
                    # 优先使用编辑后的代码，否则使用原始代码
                    download_code = st.session_state.editable_mermaid_code if st.session_state.editable_mermaid_code else st.session_state.generated_diagram.get("mermaid_code", "")
                    download_filename = "diagram.mmd"
                    if st.session_state.generated_diagram.get("mermaid_file"):
                        download_filename = os.path.basename(st.session_state.generated_diagram["mermaid_file"])
                    with tool_cols[3]:
                        st.download_button(
                            label="💾 下载代码",
                            data=download_code.encode('utf-8'),
                            file_name=download_filename,
                            mime="text/plain",
                            key="download_mmd_toolbar"
                        )
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # 显示和编辑Mermaid代码（可折叠）
                if st.session_state.get('show_mermaid_code', False):
                    st.markdown("---")
                    st.markdown("### ✏️ 编辑Mermaid代码")
                    st.info("💡 您可以编辑下面的Mermaid代码，然后点击「重新渲染」按钮生成新的图表")
                    
                    if st.session_state.generated_diagram.get("mermaid_code"):
                        # 初始化可编辑代码（只有在第一次显示时，或者在生成新图表时）
                        # 注意：如果用户编辑了代码，不应该重置错误信息
                        if st.session_state.editable_mermaid_code is None:
                            # 第一次初始化：从生成的图表代码初始化
                            st.session_state.editable_mermaid_code = st.session_state.generated_diagram.get("mermaid_code")
                            # 第一次初始化时，重置错误信息
                            st.session_state.mermaid_error_info = None
                            st.session_state.mermaid_ai_explanation = None
                            st.session_state.mermaid_fixed_code = None
                        elif st.session_state.editable_mermaid_code != st.session_state.generated_diagram.get("mermaid_code") and not st.session_state.mermaid_error_info:
                            # 如果生成的图表代码改变了（重新生成），且当前没有错误信息，才更新代码
                            # 注意：如果已有错误信息，说明用户正在编辑，不要覆盖用户的编辑
                            # 这个逻辑主要用于处理图表重新生成的场景
                            # 但实际上，重新生成图表时会触发页面重新加载，所以这里主要是安全处理
                            pass  # 保留用户编辑的内容
                        
                        # 创建左右分栏布局
                        col_left, col_right = st.columns([1.2, 1])
                        
                        with col_left:
                            st.markdown("#### 📝 代码编辑器")
                            
                            # 获取错误行列表用于高亮显示（需要在text_area之前确定）
                            error_lines_list = []
                            if st.session_state.mermaid_error_info:
                                error_lines_list = st.session_state.mermaid_error_info.get('error_lines', [])
                            
                            # 创建带高亮的代码显示（如果有错误）
                            if error_lines_list:
                                # 生成带高亮的HTML代码（对HTML特殊字符进行转义）
                                import html
                                # 注意：这里使用session_state中的代码，因为edited_code还没获取
                                code_to_highlight = st.session_state.editable_mermaid_code or ""
                                lines = code_to_highlight.split('\n')
                                highlighted_code = []
                                for i, line in enumerate(lines, 1):
                                    escaped_line = html.escape(line)
                                    if i in error_lines_list:
                                        highlighted_code.append(f'<span style="background-color: #ffebee; color: #c62828; padding: 2px 4px; border-left: 3px solid #d32f2f;">{i:4d} | {escaped_line}</span>')
                                    else:
                                        highlighted_code.append(f'<span style="color: #333;">{i:4d} | {escaped_line}</span>')
                                
                                st.markdown(f"""
                                <div style="background-color: #f5f5f5; padding: 10px; border-radius: 5px; font-family: monospace; font-size: 13px; max-height: 300px; overflow-y: auto; margin-bottom: 10px;">
                                    <pre style="margin: 0; white-space: pre-wrap;">{''.join(highlighted_code)}</pre>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            # 可编辑的代码区域（必须先获取用户输入）
                            edited_code = st.text_area(
                                "Mermaid代码编辑器",
                                value=st.session_state.editable_mermaid_code if st.session_state.editable_mermaid_code else "",
                                height=500 if error_lines_list else 400,
                                key="mermaid_code_editor",
                                help="编辑Mermaid代码，然后点击「检查语法」或「重新渲染」按钮",
                                label_visibility="collapsed" if error_lines_list else "visible"
                            )
                            
                            # 立即更新可编辑代码到session_state（确保后续使用最新代码）
                            # 注意：在Streamlit中，text_area的返回值会自动包含用户的最新输入
                            st.session_state.editable_mermaid_code = edited_code
                            
                            # 添加语法检查按钮（在text_area之后，确保使用最新代码）
                            col_check, col_spacer = st.columns([1, 3])
                            with col_check:
                                check_button_clicked = st.button("🔍 检查语法", key="check_syntax_btn")
                            
                            # 将检查逻辑移到按钮外部，使用session_state来触发检查
                            if check_button_clicked:
                                # 从session_state获取最新代码（已经在上面的text_area后更新）
                                # 再次确认使用edited_code的值（这是用户当前输入的最新值）
                                current_code = edited_code if edited_code else (st.session_state.editable_mermaid_code or "")
                                # 强制更新session_state，确保一致性
                                st.session_state.editable_mermaid_code = current_code
                                
                                if not current_code or not current_code.strip():
                                    st.warning("请输入Mermaid代码")
                                else:
                                    # 临时调试信息：显示正在检查的代码（用于排查问题）
                                    # 如果看到这个调试信息，说明代码获取是正常的
                                    with st.expander("🔍 调试信息（点击查看实际检查的代码）", expanded=False):
                                        st.code(current_code[:500], language='mermaid')
                                        st.text(f"代码总长度：{len(current_code)} 字符")
                                    
                                    with st.spinner("正在检查语法..."):
                                        try:
                                            if st.session_state.generation_agent and st.session_state.generation_agent.mermaid_renderer:
                                                # 执行语法检查（使用最新的代码）
                                                is_valid, error_info = st.session_state.generation_agent.mermaid_renderer.validate_syntax_with_details(current_code)
                                                
                                                # 调试信息：检查 mermaid.js 验证是否执行
                                                with st.expander("🔍 调试：mermaid.js 验证状态", expanded=False):
                                                    import logging
                                                    # 获取日志输出
                                                    log_capture = []
                                                    class LogCapture(logging.Handler):
                                                        def emit(self, record):
                                                            log_capture.append(self.format(record))
                                                    handler = LogCapture()
                                                    handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
                                                    logger = logging.getLogger('utils.mermaid_js_validator')
                                                    logger.addHandler(handler)
                                                    logger.setLevel(logging.ERROR)
                                                    # 检查是否有相关错误日志
                                                    if log_capture:
                                                        st.text("最近的错误日志:")
                                                        st.code('\n'.join(log_capture[-5:]), language='text')
                                                    else:
                                                        st.text("未发现错误日志（验证可能成功执行或未执行）")
                                                
                                                # 调试信息：显示检查结果（临时启用以排查问题）
                                                with st.expander("🔍 调试：检查结果详情", expanded=False):
                                                    st.write(f"**检查结果：** {'✅ 语法有效' if is_valid else '❌ 语法无效'}")
                                                    if not is_valid:
                                                        st.write(f"**错误行号：** {error_info.get('error_lines', [])}")
                                                        st.write(f"**错误消息：** {error_info.get('message', '无错误消息')}")
                                                        if error_info.get('code_snippet'):
                                                            st.code(error_info.get('code_snippet'), language='text')
                                                
                                                if not is_valid:
                                                    # 保存错误信息到session_state（确保错误信息被保存）
                                                    st.session_state.mermaid_error_info = error_info
                                                    # 确保错误信息确实被设置了
                                                    # st.info(f"🔍 调试：错误信息已保存，错误行：{error_info.get('error_lines', [])}")
                                                    
                                                    # 使用AI解释错误
                                                    try:
                                                        with st.spinner("🤖 AI正在分析错误并提供修复建议..."):
                                                            ai_explanation = st.session_state.generation_agent.explain_mermaid_error(current_code, error_info)
                                                            st.session_state.mermaid_ai_explanation = ai_explanation
                                                            
                                                            # 提取修复后的代码
                                                            fixed_code = st.session_state.generation_agent.extract_fixed_code_from_explanation(ai_explanation, current_code)
                                                            # 验证修复后的代码是否完整（至少应该是原代码长度的70%）
                                                            if fixed_code and len(fixed_code) >= len(current_code) * 0.7:
                                                                # 对修复后的代码进行自动修复，确保没有遗漏的语法错误（如缺少class关键字）
                                                                if fixed_code.strip().startswith('classDiagram'):
                                                                    fixed_code = st.session_state.generation_agent._fix_class_diagram_syntax(fixed_code)
                                                                    # 再次验证修复后的代码是否有效
                                                                    if st.session_state.generation_agent.mermaid_renderer:
                                                                        is_valid_after_fix, _ = st.session_state.generation_agent.mermaid_renderer.validate_syntax_with_details(fixed_code)
                                                                        if not is_valid_after_fix:
                                                                            # 如果修复后仍有错误，使用原始代码
                                                                            fixed_code = current_code
                                                                st.session_state.mermaid_fixed_code = fixed_code
                                                            else:
                                                                # 代码可能不完整，使用原始代码并在警告中提示
                                                                st.session_state.mermaid_fixed_code = current_code
                                                                st.warning("⚠️ 提取的修复代码可能不完整（长度不足），已保留原始代码，请手动从AI解释中复制完整代码")
                                                    except Exception as ai_error:
                                                        st.session_state.mermaid_ai_explanation = f"AI解释生成失败: {str(ai_error)}"
                                                        st.session_state.mermaid_fixed_code = None
                                                    
                                                    # 刷新页面以显示检查结果（错误信息已在session_state中）
                                                    st.rerun()
                                                else:
                                                    # 语法正确，清除错误信息
                                                    st.session_state.mermaid_error_info = None
                                                    st.session_state.mermaid_ai_explanation = None
                                                    st.session_state.mermaid_fixed_code = None
                                                    # 刷新页面以显示检查结果
                                                    st.rerun()
                                            else:
                                                st.error("图表渲染器未初始化，无法检查语法")
                                        except Exception as e:
                                            import traceback
                                            st.error(f"语法检查失败: {str(e)}")
                                            # 调试信息：输出详细错误
                                            st.exception(e)
                                            # 即使出现异常，也尝试保存错误信息
                                            st.session_state.mermaid_error_info = {
                                                'message': f"语法检查过程出错: {str(e)}",
                                                'line_number': None,
                                                'error_lines': [],
                                                'code_snippet': ''
                                            }
                                            st.rerun()
                            
                            # 如果代码已改变，清除之前的错误信息
                            if edited_code != st.session_state.generated_diagram.get("mermaid_code"):
                                if st.session_state.mermaid_error_info:
                                    # 检查是否仍然有相同的错误
                                    pass  # 保留错误信息直到重新检查
                        
                        with col_right:
                            st.markdown("#### 🔍 语法检查与修复建议")
                            
                            # 显示错误信息和AI解释
                            if st.session_state.mermaid_error_info:
                                error_info = st.session_state.mermaid_error_info
                                error_lines_list = error_info.get('error_lines', [])
                                
                                # 显示错误概要
                                st.error(f"❌ **发现语法错误**")
                                if error_lines_list:
                                    st.warning(f"⚠️ **错误位置**: 第 {', '.join(map(str, error_lines_list))} 行")
                                
                                # 显示错误消息
                                with st.expander("📋 详细错误信息", expanded=True):
                                    st.text(error_info.get('message', '未知错误'))
                                    if error_info.get('code_snippet'):
                                        st.code(error_info.get('code_snippet'), language='text')
                                
                                # 显示AI解释
                                if st.session_state.mermaid_ai_explanation:
                                    with st.expander("🤖 AI 解释与修复建议", expanded=True):
                                        st.markdown(st.session_state.mermaid_ai_explanation)
                                        
                                        # 一键采纳按钮（放在 expander 外部，避免嵌套问题）
                                        if st.session_state.mermaid_fixed_code:
                                            if st.button("✨ 一键采纳修复", key="apply_fix_btn", type="primary"):
                                                # 应用修复后的代码，并进行自动修复以确保语法正确
                                                fixed_code = st.session_state.mermaid_fixed_code
                                                
                                                # 根据图表类型自动修复语法
                                                if st.session_state.generation_agent:
                                                    # 检测图表类型并应用对应的修复方法
                                                    code_first_line = fixed_code.strip().split('\n')[0].strip().lower()
                                                    if code_first_line.startswith('classdiagram'):
                                                        # 类图：应用类图修复
                                                        fixed_code = st.session_state.generation_agent._fix_class_diagram_syntax(fixed_code)
                                                        # 再次验证，如果还有错误，尝试高级修复
                                                        if st.session_state.generation_agent.mermaid_renderer:
                                                            is_valid, error_info = st.session_state.generation_agent.mermaid_renderer.validate_syntax_with_details(fixed_code)
                                                            if not is_valid:
                                                                fixed_code = st.session_state.generation_agent._fix_class_diagram_syntax_advanced(fixed_code, error_info)
                                                    elif code_first_line.startswith('quadrantchart'):
                                                        # 象限图：应用象限图修复
                                                        fixed_code = st.session_state.generation_agent._fix_quadrant_chart_syntax(fixed_code)
                                                    elif code_first_line.startswith('gantt'):
                                                        # 甘特图：应用甘特图修复
                                                        fixed_code = st.session_state.generation_agent._fix_gantt_syntax(fixed_code)
                                                    elif code_first_line.startswith('sequencediagram'):
                                                        # 时序图：应用时序图修复
                                                        fixed_code = st.session_state.generation_agent._fix_sequence_diagram_syntax(fixed_code)
                                                    
                                                    # 通用修复（清理HTML标签和Markdown符号等）
                                                    # 自动检测图表类型
                                                    fixed_code = st.session_state.generation_agent._validate_and_fix_mermaid_code(fixed_code, "")
                                                
                                                st.session_state.editable_mermaid_code = fixed_code
                                                st.session_state.mermaid_error_info = None
                                                st.session_state.mermaid_ai_explanation = None
                                                st.session_state.mermaid_fixed_code = None
                                                st.success("✅ 修复代码已应用到编辑器并进行了自动修复！")
                                                st.rerun()
                                    
                                    # 显示修复后的代码预览（放在 expander 外部）
                                    if st.session_state.mermaid_fixed_code:
                                        with st.expander("👀 查看修复后的代码", expanded=False):
                                            st.code(st.session_state.mermaid_fixed_code, language='mermaid')
                                            st.caption(f"代码长度：{len(st.session_state.mermaid_fixed_code)} 字符（原代码：{len(st.session_state.editable_mermaid_code)} 字符）")
                                else:
                                    st.info("💡 点击「检查语法」或「重新渲染」按钮后，AI将自动分析错误并提供修复建议。")
                            
                            else:
                                st.success("✅ **代码语法正确**")
                                st.info("💡 编辑完代码后，点击「重新渲染」按钮进行语法检查和渲染。")
                        
                        # 重新渲染按钮
                        st.markdown("---")
                        col_render1, col_render2, col_render3 = st.columns([1, 2, 1])
                        with col_render2:
                            if st.button("🔄 重新渲染图表", type="primary", key="rerender_button"):
                                if edited_code and edited_code.strip():
                                    with st.spinner("正在检查语法并重新渲染图表..."):
                                        try:
                                            # 先进行语法检查（获取详细信息）
                                            if st.session_state.generation_agent and st.session_state.generation_agent.mermaid_renderer:
                                                is_valid, error_info = st.session_state.generation_agent.mermaid_renderer.validate_syntax_with_details(edited_code)
                                                
                                                if not is_valid:
                                                    # 保存错误信息
                                                    st.session_state.mermaid_error_info = error_info
                                                    
                                                    # 使用AI解释错误
                                                    with st.spinner("🤖 AI正在分析错误并提供修复建议..."):
                                                        try:
                                                            ai_explanation = st.session_state.generation_agent.explain_mermaid_error(edited_code, error_info)
                                                            st.session_state.mermaid_ai_explanation = ai_explanation
                                                            
                                                            # 提取修复后的代码
                                                            fixed_code = st.session_state.generation_agent.extract_fixed_code_from_explanation(ai_explanation, edited_code)
                                                            # 验证修复后的代码是否完整（至少应该是原代码长度的70%）
                                                            if fixed_code and len(fixed_code) >= len(edited_code) * 0.7:
                                                                # 对修复后的代码进行自动修复，确保没有遗漏的语法错误（如缺少class关键字）
                                                                if fixed_code.strip().startswith('classDiagram'):
                                                                    fixed_code = st.session_state.generation_agent._fix_class_diagram_syntax(fixed_code)
                                                                    # 再次验证修复后的代码是否有效
                                                                    if st.session_state.generation_agent.mermaid_renderer:
                                                                        is_valid_after_fix, _ = st.session_state.generation_agent.mermaid_renderer.validate_syntax_with_details(fixed_code)
                                                                        if not is_valid_after_fix:
                                                                            # 如果修复后仍有错误，使用原始代码
                                                                            fixed_code = edited_code
                                                                st.session_state.mermaid_fixed_code = fixed_code
                                                            else:
                                                                # 代码可能不完整，使用原始代码并在警告中提示
                                                                st.session_state.mermaid_fixed_code = edited_code
                                                                st.warning("⚠️ 提取的修复代码可能不完整（长度不足），已保留原始代码，请手动从AI解释中复制完整代码")
                                                        except Exception as ai_error:
                                                            st.session_state.mermaid_ai_explanation = f"AI解释生成失败: {str(ai_error)}"
                                                            st.session_state.mermaid_fixed_code = None
                                                    
                                                    st.rerun()  # 刷新页面以显示错误信息和AI解释
                                                else:
                                                    # 语法正确，清除错误信息
                                                    st.session_state.mermaid_error_info = None
                                                    st.session_state.mermaid_ai_explanation = None
                                                    st.session_state.mermaid_fixed_code = None
                                                    
                                                    # 进行渲染
                                                    from datetime import datetime
                                                    output_dir = "output"
                                                    os.makedirs(output_dir, exist_ok=True)
                                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                                    
                                                    # 更新mermaid文件
                                                    if st.session_state.generated_diagram.get("mermaid_file"):
                                                        mmd_file = st.session_state.generated_diagram["mermaid_file"]
                                                    else:
                                                        mmd_file = os.path.join(output_dir, f"diagram_{timestamp}.mmd")
                                                    
                                                    with open(mmd_file, 'w', encoding='utf-8') as f:
                                                        f.write(edited_code)
                                                    
                                                    # 重新渲染PNG（使用原有文件名以覆盖）
                                                    if st.session_state.generated_diagram.get("png_file"):
                                                        png_file = st.session_state.generated_diagram["png_file"]
                                                    else:
                                                        png_file = os.path.join(output_dir, f"diagram_{timestamp}.png")
                                                    
                                                    try:
                                                        st.session_state.generation_agent.mermaid_renderer.render_to_png(edited_code, png_file, validate=False)
                                                        
                                                        # 更新session_state
                                                        st.session_state.generated_diagram["mermaid_code"] = edited_code
                                                        st.session_state.generated_diagram["mermaid_file"] = mmd_file
                                                        st.session_state.generated_diagram["png_file"] = png_file
                                                        
                                                        st.success("✅ 图表重新渲染成功！页面将自动刷新以显示新图表。")
                                                        st.rerun()
                                                    except Exception as render_error:
                                                        st.error(f"渲染失败: {str(render_error)}\n\n可能是渲染器配置问题，请检查Playwright是否正常安装。")
                                            else:
                                                st.error("渲染器未初始化，请刷新页面重试")
                                        except Exception as e:
                                            st.error(f"重新渲染失败: {str(e)}")
                                else:
                                    st.warning("请输入有效的Mermaid代码")
                    else:
                        st.info("Mermaid代码未生成")
            else:
                st.warning("⚠️ PNG图片未生成，请检查Mermaid渲染是否正常")
                # 如果没有PNG，仍然显示代码下载选项
                if st.session_state.generated_diagram.get("mermaid_file") and os.path.exists(st.session_state.generated_diagram["mermaid_file"]):
                    st.markdown("### 📤 导出选项")
                    with open(st.session_state.generated_diagram["mermaid_file"], 'r', encoding='utf-8') as f:
                        mmd_content = f.read()
                    st.download_button(
                        label="⬇️ 下载Mermaid代码",
                        data=mmd_content.encode('utf-8'),
                        file_name=os.path.basename(st.session_state.generated_diagram["mermaid_file"]),
                        mime="text/plain",
                    )


if __name__ == "__main__":
    main()
