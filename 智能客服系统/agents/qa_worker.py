# -*- coding: utf-8 -*-
import json
import os
import sys

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

# 添加当前目录到路径
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 导入 SupervisorAgentState
from supervisor_agent import SupervisorAgentState

# 加载环境变量
load_dotenv()

# define model
model = init_chat_model(
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    model_provider="openai",
    temperature=0.7,  # 提高温度，让模型更愿意生成内容
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    max_retries=2,
    max_tokens=1000,  # 明确设置最大token数
)

# 初始化 RAG 组件 - 集成现有专业检索系统
try:
    # 导入现有的专业 RAG 系统
    import sys
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)

    from rag.vector_store import BabyKnowledgeVectorStore
    from rag.retriever import BabyKnowledgeRetriever

    # 初始化专业检索系统
    vector_store = BabyKnowledgeVectorStore()
    professional_retriever = BabyKnowledgeRetriever(vector_store)

    print("✅ 已集成专业母婴知识检索系统")

except Exception as e:
    print(f"⚠️ 专业检索系统初始化失败，使用备用方案: {e}")

    # 备用方案：使用简单的 Chroma
    try:
        embeddings = OpenAIEmbeddings(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )
        vectorstore = Chroma(
            persist_directory="./chroma_db",
            embedding_function=embeddings
        )
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        professional_retriever = None
    except Exception as e2:
        print(f"⚠️ 备用检索系统也失败: {e2}")
        retriever = None
        professional_retriever = None


# node functions
def rag_decision_node(state: SupervisorAgentState) -> dict:
    """RAG 决策节点 - 判断是否需要检索专业知识"""

    messages = state.get("messages", [])
    facts = state.get("learned_facts", [])
    preferences = state.get("preferences", {})

    # 获取最新用户消息
    user_message = ""
    if messages:
        last_message = messages[-1]
        if hasattr(last_message, 'content'):
            user_message = last_message.content

    prompt = f"""
    判断以下用户消息是否需要专业知识回答（母婴育儿、产品使用、营养搭配等）。
    具有以下能力：
    1、推荐商品的能力
    2、讲解母婴类知识的能力
    3、回答用户问题、解决用户疑惑的能力

    用户消息: {user_message}
    用户背景: {facts}
    用户偏好: {preferences}

    如果需要专业知识回答，返回 true
    如果是普通闲聊、问候、简单确认,或其他完全不相关的问题，比如测试消息等，返回 false

    只返回 true 或 false，不要其他内容。
    """

    try:
        response = model.invoke([HumanMessage(content=prompt)])
        needs_rag = "true" in response.content.lower()
    except:
        needs_rag = True  # 默认使用 RAG

    return {
        "message_count": 1,
        "user_intent_analysis": {
            "needs_professional_knowledge": needs_rag,
            "decision_reasoning": f"基于消息内容判断: {user_message[:50]}..."
        }
    }


def rag_retrieval_node(state: SupervisorAgentState) -> dict:
    """RAG 检索节点 - 使用专业母婴知识检索系统"""

    messages = state.get("messages", [])
    facts = state.get("learned_facts", [])
    preferences = state.get("preferences", {})

    # 获取用户消息
    user_message = ""
    if messages:
        last_message = messages[-1]
        if hasattr(last_message, 'content'):
            user_message = last_message.content

    # 构建用户画像
    user_profile = {}

    # 从 facts 中提取宝宝月龄
    age_months = None
    for fact in facts:
        if "个月" in fact:
            import re
            age_match = re.search(r'(\d+)个月', fact)
            if age_match:
                age_months = int(age_match.group(1))
                break
        elif "岁" in fact:
            age_match = re.search(r'(\d+)岁', fact)
            if age_match:
                age_months = int(age_match.group(1)) * 12
                break

    # 构建用户画像
    if preferences:
        user_profile.update(preferences)

    # 添加从 facts 提取的信息
    user_profile["baby_age_months"] = age_months
    user_profile["user_facts"] = facts

    # 执行专业检索
    knowledge = ""
    retrieval_info = {}

    if professional_retriever:
        try:
            # 使用专业检索系统
            results = professional_retriever.retrieve(
                query=user_message,
                age_months=age_months,
                top_k=3,
                user_profile=user_profile
            )

            if results:
                # 提取检索到的知识
                knowledge_pieces = []
                for result in results:
                    content = result.get("content", "")
                    authority = result.get("metadata", {}).get("authority", "专业资料")

                    knowledge_pieces.append(f"[{authority}] {content}")

                knowledge = "\n\n".join(knowledge_pieces)

                retrieval_info = {
                    "retrieval_method": "professional",
                    "results_count": len(results),
                    "avg_score": sum(r.get("final_score", 0) for r in results) / len(results),
                    "age_matched": age_months is not None
                }

        except Exception as e:
            print(f"专业检索失败: {e}")
            knowledge = ""

    # 备用检索（如果专业检索失败）
    if not knowledge and professional_retriever:
        print("专业检索未获得结果，但专业检索系统可用，跳过备用检索")

    return {
        "key_information": {
            "retrieved_knowledge": knowledge,
            "query_used": user_message,
            "knowledge_available": bool(knowledge),
            "user_profile_used": user_profile,
            "retrieval_info": retrieval_info
        },
        "message_count": 1
    }


def qa_response_node(state: SupervisorAgentState) -> dict:
    """QA 回答节点 - 生成最终回答"""

    messages = state.get("messages", [])
    user_name = state.get("user_name", "用户")
    facts = state.get("learned_facts", [])
    preferences = state.get("preferences", {})

    # 获取检索到的知识
    key_info = state.get("key_information", {})
    knowledge = key_info.get("retrieved_knowledge", "")

    # 获取用户消息
    user_message = ""
    if messages:
        last_message = messages[-1]
        if hasattr(last_message, 'content'):
            user_message = last_message.content

    # 构建用户上下文
    user_context = ""
    if facts:
        user_context += f"用户背景: {', '.join(facts)}\n"
    if preferences:
        user_context += f"用户偏好: {', '.join([f'{k}:{v}' for k, v in preferences.items()])}\n"

    # 构建系统提示
    system_prompt = f"""你是专业的母婴客服专家，正在为 {user_name} 提供服务。

{f"用户信息: {user_context}" if user_context else ""}

{f"相关知识: {knowledge}" if knowledge else ""}

请友好、自然地回答用户的问题。如果用户的消息不清楚，请礼貌地询问更多信息。
只输出给用户看的一段话，不要写自我评价、路由说明，不要提及 qa_worker 等内部模块名，不要用 --- 分段。"""

    # 获取对话历史
    recent_messages = messages[-6:] if len(messages) > 6 else messages
    conversation = [SystemMessage(content=system_prompt)] + recent_messages

    try:
        response = model.invoke(conversation)

        return {
            "messages": [response],
            "message_count": 1,
            "worker_results": {
                "qa_worker": {
                    "content": response.content,
                    "used_rag": bool(knowledge),
                    "user_context_applied": bool(user_context),
                    "knowledge_source": "retrieval" if knowledge else "general"
                }
            },
            "worker_status": {"qa_worker": "completed"},
            "context_summary": f"QA Worker 完成回答: {user_message[:30]}..."
        }

    except Exception as e:
        error_msg = f"抱歉，我暂时无法回答您的问题，请稍后重试。"

        return {
            "messages": [SystemMessage(content=error_msg)],
            "message_count": 1,
            "worker_results": {
                "qa_worker": {
                    "content": error_msg,
                    "error": str(e),
                    "used_rag": False
                }
            },
            "worker_status": {"qa_worker": "error"}
        }


def should_use_rag(state: SupervisorAgentState) -> str:
    """条件边函数 - 决定是否使用 RAG"""
    intent_analysis = state.get("user_intent_analysis", {})
    needs_rag = intent_analysis.get("needs_professional_knowledge", True)

    if needs_rag:
        return "rag_retrieval"
    return "direct_response"


# create graph
qa_worker_graph = StateGraph(SupervisorAgentState)

qa_worker_graph.add_node("rag_decision", rag_decision_node)
qa_worker_graph.add_node("rag_retrieval", rag_retrieval_node)
qa_worker_graph.add_node("direct_response", qa_response_node)

qa_worker_graph.add_edge(START, "rag_decision")
qa_worker_graph.add_conditional_edges(
    "rag_decision",
    should_use_rag,
    {
        "rag_retrieval": "rag_retrieval",
        "direct_response": "direct_response",
    },
)
qa_worker_graph.add_edge("rag_retrieval", "direct_response")
qa_worker_graph.add_edge("direct_response", END)

# compile
qa_worker_app = qa_worker_graph.compile()


# Test
if __name__ == "__main__":
    config = {"configurable": {"thread_id": "user-chen"}}

    test_state = {
        "messages": [HumanMessage(content="宝宝6个月了，可以添加什么辅食？")],
        "user_name": "李妈妈",
        "user_id": "user222",
        "learned_facts": ["有一个6个月大的宝宝", "是新手妈妈"],
        "preferences": {"喂养方式": "母乳+辅食", "品牌偏好": "有机食品"},
        "session_id": "test_session1",
        "message_count": 0
    }

    print("QA Worker 测试开始...")
    result = qa_worker_app.invoke(test_state, config=config)

    print("\n=== 测试结果 ===")
    if result.get("messages"):
        print(f"回答: {result['messages'][-1].content}")

    worker_result = result.get("worker_results", {}).get("qa_worker", {})
    print(f"使用了 RAG: {worker_result.get('used_rag', False)}")
    print(f"应用了用户上下文: {worker_result.get('user_context_applied', False)}")
