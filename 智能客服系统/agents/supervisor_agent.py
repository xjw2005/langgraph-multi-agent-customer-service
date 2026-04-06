import datetime
import json
import os
from typing import Annotated, TypedDict, List, Dict, Optional
import operator
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# define model
model = init_chat_model(
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    model_provider="openai",
    temperature=0.1,
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    max_retries=2,
)

class SupervisorAgentState(TypedDict):
    """3层记忆体系 - LangGraph多Agent标准架构"""

    # ==========================
    # 1. 短期记忆：对话历史（所有人都能看）
    # ==========================
    messages: Annotated[List[BaseMessage], operator.add]

    # ==========================
    # 2. 长期记忆：用户信息（永久保存）
    # ==========================
    user_id: str                 # 用户唯一ID
    user_name: str               # 用户名
    learned_facts: Annotated[List[str], lambda old, new: list(set(old + new))]  # 去重合并
    # 例子：["宝宝6个月大", "母乳喂养", "过敏：牛奶"]

    # ==========================
    # 3. 中期记忆：用户偏好
    # ==========================
    preferences: Annotated[Dict[str, str], lambda old, new: {**old, **new}]
    # 例子：{"style": "简洁专业", "tone": "温柔"}

    # ==========================
    # 任务控制（路由用）
    # ==========================
    session_id: str             # 会话ID
    message_count: Annotated[int, lambda old, new: old + new]
    next_agent: Optional[str]    # 下一个执行的Agent
    is_completed: bool          # 是否结束
    final_answer: Optional[str] # 最终回答

    # ==========================
    # Supervisor 工作状态（最小化）
    # ==========================
    selected_worker: Optional[str]                 # 选中的Worker
    user_intent_analysis: Optional[Dict[str, any]] # 用户意图分析结果
    key_information: Optional[Dict[str, any]]      # Worker处理结果和关键信息


# node functions
def supervisor_node(state: SupervisorAgentState) -> dict:
    """Supervisor 节点 - 分析用户消息并选择合适的 Worker"""

    messages = state.get("messages", [])
    user_name = state.get("user_name", "用户")
    facts = state.get("learned_facts", [])
    preferences = state.get("preferences", {})

    # 获取最新的用户消息
    user_message = ""
    if messages:
        last_message = messages[-1]
        if hasattr(last_message, 'content'):
            user_message = last_message.content

    prompt = f"""
    你是一个专业的客服意图识别专家。请分析用户消息，识别其真实意图，选择调用以下任意一个子Agent执行专门任务。

    用户信息：
    - 姓名：{user_name}
    - 已知事实：{facts}
    - 用户偏好：{preferences}

    可调用的子Agent：
    1. qa_worker - 专业问答Worker，基础聊天，育儿知识，产品使用指导
    2. product_recommendation_worker - 商品推荐Worker，高端商品推荐、个性化选择建议
    3. order_worker - 订单服务Worker，订单查询、修改、取消
    4. refund_worker - 退款服务Worker，退货、换货、退款等
    5. payment_worker - 支付服务Worker，支付失败、退款、账单等
    6. logistics_worker - 物流服务Worker，配送状态、地址修改、配送时间等
    7. human_worker - 人工服务Worker，明确要求人工客服

    用户消息：{user_message}

    **重要：你必须只返回一个有效的JSON对象，不要包含任何解释、前缀或后缀文本。**

    JSON格式：
    {{
        "intent": "意图类型",
        "selected_worker": "选择的Worker名称",
        "confidence": 0.95,
        "reasoning": "选择理由"
    }}
    """

    response = model.invoke([HumanMessage(content=prompt)])

    try:
        result = json.loads(response.content)
        # 模型若漏掉字段会得到 None，不能用默认值 "qa_worker"（state.get 对已存在的 None 不会回退）
        selected_worker = result.get("selected_worker") or "qa_worker"
        intent = result.get("intent", "general_inquiry")
        confidence = result.get("confidence", 0.8)
        reasoning = result.get("reasoning", "默认选择")

    except json.JSONDecodeError:
        # 如果解析失败，使用默认值
        selected_worker = "qa_worker"
        intent = "general_inquiry"
        confidence = 0.5
        reasoning = "JSON解析失败，使用默认选择"

    return {
        "selected_worker": selected_worker,
        "current_task": user_message,
        "task_complexity": "simple",
        "task_priority": "medium",
        "available_workers": ["qa_worker", "product_recommendation_worker", "order_worker", "refund_worker", "payment_worker", "logistics_worker", "human_worker"],
        "active_workers": [selected_worker],
        "worker_assignments": {selected_worker: user_message},
        "worker_status": {selected_worker: "busy"},
        "current_step": 1,
        "total_steps": 1,
        "quality_threshold": 0.7,
        "max_retries": 2,
        "routing_strategy": "llm_based",
        "context_summary": f"选择 {selected_worker} 处理: {user_message[:50]}...",
        "user_intent_analysis": {
            "intent": intent,
            "confidence": confidence,
            "reasoning": reasoning
        },
        "message_count": 0,  # 不增加消息计数，因为没有添加新的用户可见消息
        # 不添加SystemMessage到messages，避免污染worker的对话历史
    }


def extract_user_info_node(state: SupervisorAgentState) -> dict:
    """提取用户信息节点 - 从对话中学习用户偏好和事实"""

    contents = state["messages"][-2:]
    prompt = f"""
    从以下客服对话内容中，提取出有效的用户偏好和事实信息，并以严格的json格式返回，不要出现任何其他的字符。

    对话内容：{[str(content) for content in contents]}

    请提取：
    1. 用户的个人信息事实（如：有几个孩子、孩子年龄、居住地区等）
    2. 用户的购物偏好（如：喜欢的品牌、价格范围、购买习惯等）

    返回JSON：
    {{
        "facts": ["事实1", "事实2"],
        "preferences": {{"偏好类型": "偏好值"}}
    }}
    """

    response = model.invoke([HumanMessage(content=prompt)])

    try:
        extracted = json.loads(response.content)
        # 返回提取的信息，LangGraph 会自动合并到状态中
        # learned_facts 使用 lambda old, new: old + new 会自动追加
        # preferences 会直接更新
        return {
            "learned_facts": extracted.get("facts", []),
            "preferences": extracted.get("preferences", {})
        }
    except Exception as e:
        # 如果 JSON 解析失败，则返回空信息，并将错误打印出来
        print(f"[extract_user_info_node] 信息提取/解析失败: {e}\n返回内容: {getattr(response, 'content', '')}")
        return {
            "learned_facts": [],
            "preferences": {}
        }


def call_qa_worker_node(state: SupervisorAgentState) -> dict:
    """调用 QA Worker 节点"""

    # 导入 qa_worker
    try:
        import sys
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        from qa_worker import qa_worker_app

        print(f"[DEBUG] 调用 QA Worker，状态: {list(state.keys())}")

        # 使用无状态调用，避免checkpoint污染
        # 不传递config，让worker进行无状态处理
        qa_result = qa_worker_app.invoke(state)

        print(f"[DEBUG] QA Worker 返回结果: {qa_result.get('messages', [])}")

        # 提取 qa_worker 的回答
        qa_messages = qa_result.get("messages", [])

        return {
            "messages": qa_messages,
            "worker_results": qa_result.get("worker_results", {}),
            "worker_status": {"qa_worker": "completed"},
            "message_count": 1
        }

    except Exception as e:
        print(f"调用 QA Worker 失败: {e}")
        import traceback
        traceback.print_exc()

        error_msg = "抱歉，系统暂时无法处理您的请求，请稍后重试。"
        return {
            "messages": [SystemMessage(content=error_msg)],
            "worker_results": {"qa_worker": {"error": str(e)}},
            "worker_status": {"qa_worker": "error"},
            "message_count": 1
        }


def call_product_recommendation_worker_node(state: SupervisorAgentState) -> dict:
    """调用商品推荐 Worker 节点"""

    # 导入 product_recommendation_worker
    try:
        import sys
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        from product_recommendation_worker import product_recommendation_app

        print(f"[DEBUG] 调用商品推荐 Worker，状态: {list(state.keys())}")

        # 使用无状态调用，避免checkpoint污染
        # 不传递config，让worker进行无状态处理
        recommendation_result = product_recommendation_app.invoke(state)

        print(f"[DEBUG] 商品推荐 Worker 返回结果: {recommendation_result.get('messages', [])}")

        # 提取 product_recommendation_worker 的回答
        recommendation_messages = recommendation_result.get("messages", [])

        return {
            "messages": recommendation_messages,
            "worker_results": recommendation_result.get("worker_results", {}),
            "worker_status": {"product_recommendation_worker": "completed"},
            "message_count": 1
        }

    except Exception as e:
        print(f"调用商品推荐 Worker 失败: {e}")
        import traceback
        traceback.print_exc()

        error_msg = "抱歉，商品推荐系统暂时无法处理您的请求，请稍后重试。"
        return {
            "messages": [SystemMessage(content=error_msg)],
            "worker_results": {"product_recommendation_worker": {"error": str(e)}},
            "worker_status": {"product_recommendation_worker": "error"},
            "message_count": 1
        }


def call_other_worker_node(state: SupervisorAgentState) -> dict:
    """调用其他 Worker 节点（暂时模拟）"""

    selected_worker = state.get("selected_worker", "qa_worker")
    user_name = state.get("user_name", "用户")

    # 模拟不同 Worker 的回答
    worker_responses = {
        "order_worker": f"好的{user_name}，我来帮您查询订单信息。请提供您的订单号，我会为您详细查询订单状态。",
        "product_worker": f"{user_name}您好！我来为您推荐合适的产品。请告诉我您的具体需求，比如宝宝年龄、预算范围等，我会为您精心挑选。",
        "refund_worker": f"{user_name}，我理解您的退货需求。请提供订单号和退货原因，我会为您快速处理退货申请。",
        "payment_worker": f"{user_name}，关于支付问题我来协助您解决。请描述具体的支付问题，我会提供相应的解决方案。",
        "logistics_worker": f"{user_name}您好，我来帮您查询物流信息。请提供订单号或快递单号，我会为您跟踪配送进度。",
        "human_worker": f"{user_name}，正在为您转接人工客服，请稍候..."
    }

    response_content = worker_responses.get(selected_worker, f"好的{user_name}，我来为您处理这个问题。")

    return {
        "messages": [SystemMessage(content=response_content)],
        "worker_results": {
            selected_worker: {
                "content": response_content,
                "simulated": True
            }
        },
        "worker_status": {selected_worker: "completed"},
        "message_count": 1
    }


def synthesize_response_node(state: SupervisorAgentState) -> dict:
    """合成最终回复节点 - 清洗worker回复，去除思考过程和内部信息"""

    messages = state.get("messages", [])
    user_name = state.get("user_name", "用户")
    selected_worker = state.get("selected_worker", "qa_worker")

    # 提取worker的原始回复
    worker_reply = ""
    if messages:
        for msg in reversed(messages):
            if hasattr(msg, 'content') and msg.content:
                worker_reply = msg.content
                break

    # 如果有worker回复，进行清洗
    if worker_reply:
        clean_prompt = f"""
        你是一个专业的客服回复清洗专家。并且具有这些能力：
        请将以下AI助手的回复进行清洗，去除不应该展示给客户的内容。

        原始回复：
        {worker_reply}

        清洗要求：
        1. 去除所有思考过程、推理步骤、内部分析
        2. 去除提及"qa_worker"、"worker"、"agent"等内部术语
        3. 去除"因此，指派给..."、"根据分析..."等路由说明
        4. 去除用"---"分隔的内部说明部分
        5. 保留对客户有用的核心信息和建议
        6. 保持友好、专业的客服语调
        7. 确保回复完整、连贯，直接回答客户问题

        只返回清洗后的客户回复内容，不要包含任何解释或前缀：
        """

        try:
            clean_response = model.invoke([HumanMessage(content=clean_prompt)])
            cleaned_content = clean_response.content.strip()

            # 创建清洗后的消息
            from langchain_core.messages import AIMessage
            cleaned_message = AIMessage(content=cleaned_content)

            # 替换原始消息
            cleaned_messages = []
            for msg in messages:
                if hasattr(msg, 'content') and msg.content == worker_reply:
                    cleaned_messages.append(cleaned_message)
                else:
                    cleaned_messages.append(msg)

            messages = cleaned_messages

        except Exception as e:
            print(f"回复清洗失败，使用原始回复: {e}")

    # 返回清洗后的结果
    if selected_worker == "qa_worker":
        return {
            "messages": messages,
            "context_summary": f"QA Worker 为 {user_name} 提供了专业回答（已清洗）",
            "conversation_stage": "completed",
            "is_completed": True
        }

    if selected_worker == "product_recommendation_worker":
        return {
            "messages": messages,
            "context_summary": f"商品推荐 Worker 为 {user_name} 提供了高端产品推荐（已清洗）",
            "conversation_stage": "completed",
            "is_completed": True
        }

    # 其他 Worker 的回答也进行清洗
    return {
        "messages": messages,
        "context_summary": f"{selected_worker} 为 {user_name} 处理了请求（已清洗）",
        "conversation_stage": "completed",
        "is_completed": True
    }


def route_to_worker(state: SupervisorAgentState) -> str:
    """路由到对应的 Worker"""
    selected_worker = state.get("selected_worker", "qa_worker")

    if selected_worker == "qa_worker":
        return "call_qa_worker"
    elif selected_worker == "product_recommendation_worker":
        return "call_product_recommendation_worker"
    else:
        return "call_other_worker"


def should_extract_info(state: SupervisorAgentState) -> str:
    """判断是否需要提取用户信息"""
    contents = state.get("messages", [])[-2:]
    if len(contents) < 2:
        return "end"

    prompt = f"""
    从以下客服对话内容中，判断是否包含有价值的用户个人信息或购物偏好。

    对话内容：{[str(content) for content in contents]}

    如果包含用户的个人信息（如年龄、孩子情况、地址等）或购物偏好（如品牌偏好、价格敏感度等），返回true，否则返回false。

    返回严格的true或false
    """

    try:
        response = model.invoke([HumanMessage(content=prompt)])
        if "true" in response.content.lower():
            return "extract"
    except:
        pass

    return "end"


# create graph
supervisor_graph = StateGraph(SupervisorAgentState)

supervisor_graph.add_node("supervisor", supervisor_node)
supervisor_graph.add_node("extract_user_info", extract_user_info_node)
supervisor_graph.add_node("call_qa_worker", call_qa_worker_node)
supervisor_graph.add_node("call_product_recommendation_worker", call_product_recommendation_worker_node)
supervisor_graph.add_node("call_other_worker", call_other_worker_node)
supervisor_graph.add_node("synthesize_response", synthesize_response_node)

supervisor_graph.add_edge(START, "supervisor")
supervisor_graph.add_conditional_edges(
    "supervisor",
    should_extract_info,
    {
        "extract": "extract_user_info",
        "end": "route_worker",
    },
)
supervisor_graph.add_edge("extract_user_info", "route_worker")

# 添加虚拟的 route_worker 节点用于路由
def route_worker_node(state: SupervisorAgentState) -> dict:
    """路由节点 - 不做任何处理，只用于条件路由"""
    _ = state  # 避免未使用参数警告
    return {"message_count": 0}

supervisor_graph.add_node("route_worker", route_worker_node)
supervisor_graph.add_conditional_edges(
    "route_worker",
    route_to_worker,
    {
        "call_qa_worker": "call_qa_worker",
        "call_product_recommendation_worker": "call_product_recommendation_worker",
        "call_other_worker": "call_other_worker",
    },
)

supervisor_graph.add_edge("call_qa_worker", "synthesize_response")
supervisor_graph.add_edge("call_product_recommendation_worker", "synthesize_response")
supervisor_graph.add_edge("call_other_worker", "synthesize_response")
supervisor_graph.add_edge("synthesize_response", END)

# use SQLiteCheckpoint - 全局记忆保存（3层记忆体系）
from langgraph.checkpoint.memory import MemorySaver
checkpointer = MemorySaver()  # 全局保存所有记忆：messages + learned_facts + preferences

# compile
supervisor_app = supervisor_graph.compile(checkpointer=checkpointer)

if __name__ == "__main__":
    print("=== 简单测试 ===")
    from datetime import datetime

    config = {"configurable": {"thread_id": f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"}}

    # 简单测试：第一次提问
    print("第一次调用: 你好")
    first_result = supervisor_app.invoke({
        "messages": [HumanMessage(content="1111111111111")]}, config=config)

    print("=== 第一次AI回复内容预览 ===")
    # 看看所有的messages
    import pprint
    pprint.pprint(f"所有的messages: {first_result['messages']}")
    # if "messages" in first_result and len(first_result["messages"]) > 0:
    #     last_msg = None
    #     for msg in reversed(first_result["messages"]):
    #         if hasattr(msg, "content"):
    #             last_msg = msg.content
    #             break
    #         elif isinstance(msg, dict) and "content" in msg:
    #             last_msg = msg["content"]
    #             break
    #     print(f"AI回复内容: {last_msg}")
    # else:
    #     print("没有AI回复内容。")

    # # 第二次提问，测试AI的上下文记忆能力
    # print("第二次调用：你还记得我刚刚问了什么吗？")
    # second_result = supervisor_app.invoke({
    #     "messages": [
    #         HumanMessage(content="123"),
    #         HumanMessage(content="你还记得我刚刚问了什么吗？")
    #     ],
    #     "user_name": "李先生",
    #     "user_id": "user_001",
    #     "learned_facts": ["有一个6个月大的宝宝", "注重乳源纯净", "希望提升免疫力"],
    #     "preferences": {
    #         "品牌偏好": "德国品牌",
    #         "喂养方式": "混合喂养",
    #         "渠道偏好": "跨境购",
    #         "乳糖耐受": True,
    #         "有机需求": True
    #     },
    #     "session_id": "test_session_001",
    #     "message_count": 2,
    # }, config=config)

    # print("=== 第二次AI回复内容预览 ===")
    # if "messages" in second_result and len(second_result["messages"]) > 0:
    #     last_msg = None
    #     for msg in reversed(second_result["messages"]):
    #         if hasattr(msg, "content"):
    #             last_msg = msg.content
    #             break
    #         elif isinstance(msg, dict) and "content" in msg:
    #             last_msg = msg["content"]
    #             break
    #     print(f"AI回复内容: {last_msg}")
    # else:
    #     print("没有AI回复内容。")
    
