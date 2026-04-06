from typing import TypedDict, Annotated, List, Dict, Any, Optional
try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired

from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage

class CustomerServiceState(TypedDict):
    """智能客服系统的核心状态"""

    # === 用户信息 ===
    user_id: str
    session_id: str
    messages: Annotated[List[BaseMessage], add_messages]

    # === 对话上下文 ===
    current_intent: str  # "order_query", "product_info", "refund_request" 等
    selected_agent: str  # 当前处理的Agent名称
    conversation_stage: str  # "greeting", "processing", "completed" 等

    # === 业务数据 ===
    user_profile: Dict[str, Any]  # 用户档案信息
    order_info: Dict[str, Any]    # 订单相关信息
    product_info: Dict[str, Any]  # 商品相关信息
    logistics_info: Dict[str, Any] # 物流信息
    payment_info: Dict[str, Any]   # 支付信息

    # === Agent处理结果 ===
    agent_results: Dict[str, Any]  # 各Agent的处理结果
    routing_confidence: float      # 路由置信度
    processing_confidence: float   # 处理置信度

    # === 系统控制 ===
    requires_human: bool           # 是否需要人工介入
    is_completed: bool            # 对话是否完成
    error_message: Optional[str]   # 错误信息

    # === 历史和追踪 ===
    conversation_history: List[Dict[str, Any]]  # 完整对话历史
    processing_steps: List[str]    # 处理步骤记录
    agent_chain: List[str]         # Agent调用链

    # === 性能监控 ===
    start_time: float             # 处理开始时间
    processing_time: float        # 总处理时间
    agent_performance: Dict[str, float]  # 各Agent性能指标

    # === Supervisor–Worker 扩展（设计文档 2026-04-05）===
    supervisor_plan: NotRequired[Dict[str, Any]]
    current_round: NotRequired[int]
    max_rounds: NotRequired[int]
    worker_results: NotRequired[Dict[str, Any]]
    active_workers: NotRequired[List[str]]
    worker_confidence: NotRequired[Dict[str, float]]
    completion_criteria: NotRequired[Dict[str, Any]]
    next_action: NotRequired[str]
    task_complexity: NotRequired[str]
    next_worker: NotRequired[str]
    task_completed: NotRequired[bool]
    task_analysis: NotRequired[Dict[str, Any]]
    draft_reply: NotRequired[str]
    worker_dependencies: NotRequired[Dict[str, List[str]]]
    parallel_execution: NotRequired[bool]

class OrderQueryState(TypedDict):
    """订单查询子状态"""
    order_id: str
    user_id: str
    query_type: str  # "status", "logistics", "modify", "cancel"
    order_details: Dict[str, Any]
    logistics_details: Dict[str, Any]
    available_actions: List[str]

class ProductInfoState(TypedDict):
    """商品信息子状态"""
    product_id: Optional[str]
    product_name: Optional[str]
    search_query: str
    product_list: List[Dict[str, Any]]
    selected_product: Dict[str, Any]
    recommendation_reason: str

class RefundState(TypedDict):
    """退款处理子状态"""
    refund_id: Optional[str]
    order_id: str
    refund_reason: str
    refund_amount: float
    refund_status: str
    approval_required: bool
    processing_steps: List[str]

class PaymentState(TypedDict):
    """支付处理子状态"""
    payment_id: Optional[str]
    order_id: str
    payment_method: str
    payment_status: str
    issue_type: str  # "failed", "refund", "dispute"
    resolution_steps: List[str]

class LogisticsState(TypedDict):
    """物流查询子状态"""
    tracking_id: str
    order_id: str
    current_status: str
    location_history: List[Dict[str, Any]]
    estimated_delivery: str
    delivery_options: List[str]

# 意图枚举
class Intent:
    """用户意图枚举"""
    ORDER_QUERY = "order_query"
    PRODUCT_INFO = "product_info"
    REFUND_REQUEST = "refund_request"
    PAYMENT_ISSUE = "payment_issue"
    LOGISTICS_QUERY = "logistics_query"
    COMPLAINT = "complaint"
    GENERAL_INQUIRY = "general_inquiry"
    HUMAN_HANDOFF = "human_handoff"

# Agent类型枚举
class AgentType:
    """Agent类型枚举"""
    ROUTER = "router_agent"
    ORDER = "order_agent"
    PRODUCT = "product_agent"
    REFUND = "refund_agent"
    PAYMENT = "payment_agent"
    LOGISTICS = "logistics_agent"
    HUMAN = "human_agent"
    HISTORY = "history_agent"

# 对话阶段枚举
class ConversationStage:
    """对话阶段枚举"""
    GREETING = "greeting"
    INTENT_RECOGNITION = "intent_recognition"
    INFORMATION_GATHERING = "information_gathering"
    PROCESSING = "processing"
    AGENT_PROCESSING = "agent_processing"  # 添加缺失的属性
    CONFIRMATION = "confirmation"
    COMPLETED = "completed"
    ESCALATED = "escalated"
    ERROR = "error"  # 添加缺失的属性