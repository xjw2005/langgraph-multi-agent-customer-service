from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from core.states import CustomerServiceState, AgentType, ConversationStage
from core.router import RouterAgent
from agents.order_agent import OrderAgent
from agents.product_agent import ProductAgent
from services.database_service import DatabaseService
from config.settings import settings
from langchain_core.messages import HumanMessage, AIMessage
import sqlite3
import time
import uuid

class CustomerServiceSystem:
    """智能客服系统主类"""

    def __init__(self):
        self.db_service = DatabaseService()
        self.router_agent = RouterAgent()
        self.order_agent = OrderAgent()
        self.product_agent = ProductAgent()

        # 创建检查点存储
        self.checkpointer = SqliteSaver(
            sqlite3.connect(settings.DATABASE_PATH.replace('.db', '_checkpoints.db'),
                          check_same_thread=False)
        )

        # 构建主工作流
        self.app = self._build_main_graph()
        print("🤖 智能客服系统初始化完成")

    def _build_main_graph(self) -> StateGraph:
        """构建主工作流图"""
        print("🔧 构建客服系统工作流...")

        # 创建状态图
        graph = StateGraph(CustomerServiceState)

        # 添加节点
        graph.add_node("router", self._router_node)
        graph.add_node("order_agent", self._order_agent_node)
        graph.add_node("product_agent", self._product_agent_node)
        graph.add_node("human_handoff", self._human_handoff_node)
        graph.add_node("history_recorder", self._history_recorder_node)
        graph.add_node("response_generator", self._response_generator_node)

        # 设置入口点
        graph.add_edge(START, "router")

        # 路由后的条件边
        graph.add_conditional_edges(
            "router",
            self._route_to_agent,
            {
                AgentType.ORDER: "order_agent",
                AgentType.PRODUCT: "product_agent",
                AgentType.HUMAN: "human_handoff"
            }
        )

        # Agent处理后的边
        graph.add_edge("order_agent", "response_generator")
        graph.add_edge("product_agent", "response_generator")
        graph.add_edge("human_handoff", "response_generator")

        # 响应生成后记录历史
        graph.add_edge("response_generator", "history_recorder")
        graph.add_edge("history_recorder", END)

        # 编译图
        compiled_graph = graph.compile(
            checkpointer=self.checkpointer,
            interrupt_before=["human_handoff"]  # 人工介入前中断
        )

        print("✅ 工作流构建完成")
        return compiled_graph

    def _router_node(self, state: CustomerServiceState) -> dict:
        """路由节点"""
        return self.router_agent.route_message(state)

    def _order_agent_node(self, state: CustomerServiceState) -> dict:
        """订单Agent节点"""
        return self.order_agent.process(state)

    def _product_agent_node(self, state: CustomerServiceState) -> dict:
        """商品Agent节点"""
        return self.product_agent.process(state)

    def _human_handoff_node(self, state: CustomerServiceState) -> dict:
        """人工转接节点"""
        print("👨‍💼 转接人工客服...")

        processing_steps = state.get("processing_steps", [])
        processing_steps.append("系统: 已转接人工客服")

        return {
            "requires_human": True,
            "conversation_stage": ConversationStage.ESCALATED,
            "processing_steps": processing_steps,
            "messages": [AIMessage(content="正在为您转接人工客服，请稍候...")]
        }

    def _history_recorder_node(self, state: CustomerServiceState) -> dict:
        """历史记录节点"""
        try:
            # 提取对话信息
            messages = state.get("messages", [])
            if len(messages) >= 2:
                user_message = messages[-2].content if len(messages) >= 2 else ""
                ai_response = messages[-1].content if messages else ""

                # 保存对话记录
                self.db_service.save_conversation(
                    session_id=state.get("session_id", ""),
                    user_id=state.get("user_id", ""),
                    message=user_message,
                    response=ai_response,
                    intent=state.get("current_intent", ""),
                    agent_used=state.get("selected_agent", ""),
                    confidence=state.get("processing_confidence", 0.0)
                )

            processing_steps = state.get("processing_steps", [])
            processing_steps.append("系统: 对话记录已保存")

            return {
                "processing_steps": processing_steps,
                "is_completed": True
            }

        except Exception as e:
            print(f"❌ 历史记录保存失败: {e}")
            return {"processing_steps": state.get("processing_steps", [])}

    def _response_generator_node(self, state: CustomerServiceState) -> dict:
        """响应生成节点"""
        # 检查是否需要生成额外响应
        messages = state.get("messages", [])

        # 如果Agent已经生成了响应，直接返回
        if messages and isinstance(messages[-1], AIMessage):
            return {}

        # 生成默认响应
        default_response = "感谢您的咨询，如有其他问题请随时联系我们。"
        return {
            "messages": [AIMessage(content=default_response)]
        }

    def _route_to_agent(self, state: CustomerServiceState) -> str:
        """路由决策函数"""
        # 检查是否需要人工介入
        if self.router_agent.should_escalate_to_human(state):
            return AgentType.HUMAN

        # 根据选择的Agent路由
        selected_agent = state.get("selected_agent", AgentType.PRODUCT)
        return selected_agent

    def process_message(self, user_id: str, message: str, session_id: str = None) -> dict:
        """处理用户消息的主入口"""
        print(f"📨 处理用户 {user_id} 的消息: {message}")

        # 生成会话ID
        if not session_id:
            session_id = f"session_{uuid.uuid4().hex[:8]}"

        # 获取用户档案
        user_profile = self.db_service.get_user_by_id(user_id) or {}
        user_preferences = self.db_service.get_user_preferences(user_id)

        # 构建初始状态
        initial_state = {
            "user_id": user_id,
            "session_id": session_id,
            "messages": [HumanMessage(content=message)],
            "user_profile": user_profile,
            "conversation_stage": ConversationStage.INTENT_RECOGNITION,
            "processing_steps": [],
            "agent_chain": [],
            "start_time": time.time(),
            "requires_human": False,
            "is_completed": False
        }

        # 合并用户偏好
        if user_preferences:
            initial_state["user_profile"].update(user_preferences)

        try:
            # 配置检查点
            config = {"configurable": {"thread_id": session_id}}

            # 执行工作流
            result = self.app.invoke(initial_state, config=config)

            # 提取响应
            response_message = ""
            if result.get("messages"):
                last_message = result["messages"][-1]
                if isinstance(last_message, AIMessage):
                    response_message = last_message.content

            # 构建返回结果
            return {
                "response": response_message,
                "session_id": session_id,
                "intent": result.get("current_intent", ""),
                "agent_used": result.get("selected_agent", ""),
                "confidence": result.get("processing_confidence", 0.0),
                "requires_human": result.get("requires_human", False),
                "processing_time": time.time() - initial_state["start_time"],
                "processing_steps": result.get("processing_steps", [])
            }

        except Exception as e:
            print(f"❌ 处理消息失败: {e}")
            return {
                "response": "抱歉，系统暂时无法处理您的请求，请稍后重试或联系人工客服。",
                "session_id": session_id,
                "error": str(e),
                "requires_human": True
            }

    def get_conversation_history(self, session_id: str) -> list:
        """获取对话历史"""
        return self.db_service.get_conversation_history(session_id)

    def get_user_summary(self, user_id: str) -> dict:
        """获取用户对话摘要"""
        return self.db_service.get_user_conversation_summary(user_id)

    def continue_conversation(self, session_id: str, user_input: str = None) -> dict:
        """继续中断的对话"""
        try:
            config = {"configurable": {"thread_id": session_id}}

            # 如果有用户输入，更新状态
            if user_input:
                current_state = self.app.get_state(config)
                self.app.update_state(config, {
                    "messages": [HumanMessage(content=user_input)]
                })

            # 继续执行
            result = self.app.invoke(None, config=config)

            # 提取响应
            response_message = ""
            if result.get("messages"):
                last_message = result["messages"][-1]
                if isinstance(last_message, AIMessage):
                    response_message = last_message.content

            return {
                "response": response_message,
                "session_id": session_id,
                "requires_human": result.get("requires_human", False)
            }

        except Exception as e:
            print(f"❌ 继续对话失败: {e}")
            return {
                "response": "对话继续失败，请重新开始。",
                "session_id": session_id,
                "error": str(e)
            }

    def get_system_stats(self) -> dict:
        """获取系统统计信息"""
        # 这里可以添加系统性能统计
        return {
            "total_agents": 3,
            "active_sessions": 0,  # 可以从检查点数据库查询
            "system_status": "运行中"
        }