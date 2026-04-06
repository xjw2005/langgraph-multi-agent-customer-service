import sqlite3
import json
import os
import re
from typing import Dict, List, Any
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage
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
    temperature=0.3,
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    max_retries=2,
)

# 加载商品数据
def load_product_data():
    """加载商品数据"""
    try:
        data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "extended_products.json")
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("products", [])
    except Exception as e:
        print(f"加载商品数据失败: {e}")
        return []

# 全局加载商品数据
PRODUCTS_DATA = load_product_data()

def extract_age_from_facts(facts: List[str]) -> int:
    """从用户事实中提取宝宝月龄"""
    for fact in facts:
        # 匹配 "X个月" 格式
        month_match = re.search(r'(\d+)个月', fact)
        if month_match:
            return int(month_match.group(1))

        # 匹配 "X岁" 格式
        year_match = re.search(r'(\d+)岁', fact)
        if year_match:
            return int(year_match.group(1)) * 12

    return None

def parse_age_range(age_range_str: str) -> tuple:
    """解析年龄范围字符串，返回(min_months, max_months)"""
    if not age_range_str:
        return (0, 999)

    # 匹配 "3-6个月" 格式
    month_range_match = re.search(r'(\d+)-(\d+)个月', age_range_str)
    if month_range_match:
        return (int(month_range_match.group(1)), int(month_range_match.group(2)))

    # 匹配 "6个月+" 格式
    month_plus_match = re.search(r'(\d+)个月\+', age_range_str)
    if month_plus_match:
        return (int(month_plus_match.group(1)), 999)

    # 匹配 "1-2岁" 格式
    year_range_match = re.search(r'(\d+)-(\d+)岁', age_range_str)
    if year_range_match:
        return (int(year_range_match.group(1)) * 12, int(year_range_match.group(2)) * 12)

    return (0, 999)

# node functions
def recommendation_strategy_node(state: SupervisorAgentState) -> dict:
    """推荐策略分析节点 - 分析用户需求并制定推荐策略"""

    messages = state.get("messages", [])
    facts = state.get("learned_facts", [])
    preferences = state.get("preferences", {})

    # 获取最新用户消息
    user_message = ""
    if messages:
        last_message = messages[-1]
        if hasattr(last_message, 'content'):
            user_message = last_message.content

    # 提取宝宝月龄
    baby_age_months = extract_age_from_facts(facts)

    prompt = f"""
    作为高端母婴产品推荐专家，请分析用户需求并制定推荐策略。

    用户消息: {user_message}
    用户背景: {facts}
    用户偏好: {preferences}
    宝宝月龄: {baby_age_months}个月 (如果已知)

    请分析用户的核心需求，并返回严格的JSON格式：
    {{
        "recommendation_type": "按年龄推荐|按功能推荐|按品牌推荐|综合推荐",
        "key_requirements": ["需求1", "需求2"],
        "target_categories": ["目标商品类别"],
        "priority_factors": ["品质", "功能", "品牌", "认证"],
        "personalization_tags": ["个性化标签"]
    }}
    """

    try:
        response = model.invoke([HumanMessage(content=prompt)])

        print(f"[DEBUG] 策略分析AI原始回复: '{response.content}'")
        print(f"[DEBUG] 回复长度: {len(response.content) if response.content else 0}")

        # 尝试清理和提取JSON
        content = response.content.strip()

        # 处理可能的markdown格式
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end != -1:
                content = content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            if end != -1:
                content = content[start:end].strip()

        # 尝试找到JSON对象
        if not content.startswith('{'):
            start = content.find('{')
            if start != -1:
                end = content.rfind('}')
                if end != -1 and end > start:
                    content = content[start:end+1]

        print(f"[DEBUG] 处理后的JSON内容: '{content}'")
        strategy = json.loads(content)
        print(f"[DEBUG] ✅ 成功解析策略JSON: {strategy}")

    except json.JSONDecodeError as e:
        print(f"[DEBUG] ❌ JSON解析失败: {e}")
        print(f"[DEBUG] 使用默认策略")
        # 默认策略
        strategy = {
            "recommendation_type": "综合推荐",
            "key_requirements": ["营养均衡", "易消化"],
            "target_categories": ["奶粉", "辅食"],
            "priority_factors": ["品质", "认证"],
            "personalization_tags": ["高端定位"]
        }
    except Exception as e:
        print(f"[DEBUG] ❌ 其他错误: {e}")
        print(f"[DEBUG] 使用默认策略")
        # 默认策略
        strategy = {
            "recommendation_type": "综合推荐",
            "key_requirements": ["营养均衡", "易消化"],
            "target_categories": ["奶粉", "辅食"],
            "priority_factors": ["品质", "认证"],
            "personalization_tags": ["高端定位"]
        }

    return {
        "message_count": 1,"user_intent_analysis": {
            "recommendation_strategy": strategy,
            "baby_age_months": baby_age_months,
            "analysis_reasoning": f"基于用户需求分析: {user_message[:50]}..."
        }
    }

def premium_product_matching_node(state: SupervisorAgentState) -> dict:
    """AI智能商品匹配节点 - 让AI基于客户特征进行选品"""

    import json  # 在函数开头导入

    messages = state.get("messages", [])
    user_name = state.get("user_name", "客户")
    learned_facts = state.get("learned_facts", [])
    preferences = state.get("preferences", {})

    # 获取策略分析结果
    intent_analysis = state.get("user_intent_analysis", {})
    strategy = intent_analysis.get("recommendation_strategy", {})
    baby_age_months = intent_analysis.get("baby_age_months")

    print(f"[DEBUG] 获取到的策略分析: {strategy}")
    print(f"[DEBUG] 宝宝年龄: {baby_age_months}个月")

    # 获取用户消息
    user_message = ""
    if messages:
        last_message = messages[-1]
        if hasattr(last_message, 'content'):
            user_message = last_message.content

    # 构建客户画像
    customer_profile = f"""
    客户信息：
    - 姓名：{user_name}
    - 已知事实：{', '.join(learned_facts) if learned_facts else '无'}
    - 偏好信息：{', '.join([f'{k}:{v}' for k, v in preferences.items()]) if preferences else '无'}
    - 当前需求：{user_message}
    - 宝宝年龄：{baby_age_months}个月 (如果已知)

    推荐策略分析：
    - 推荐类型：{strategy.get('recommendation_type', '未分析')}
    - 核心需求：{', '.join(strategy.get('key_requirements', []))}
    - 目标类别：{', '.join(strategy.get('target_categories', []))}
    - 优先因素：{', '.join(strategy.get('priority_factors', []))}
    - 个性化标签：{', '.join(strategy.get('personalization_tags', []))}
    """

    # 构建结构化商品信息 - 更高效的JSON格式
    products_data = []
    for i, product in enumerate(PRODUCTS_DATA):
        product_info = {
            "index": i + 1,
            "name": product.get('name', '未知商品'),
            "brand": product.get('brand', '未知'),
            "price": product.get('price', 0),
            "age_range": product.get('age_range', '未知'),
            "origin_country": product.get('origin_country', '未知'),
            "expert_rating": product.get('expert_rating', 0),
            "user_rating": product.get('user_rating', 0),
            "certifications": product.get('certifications', []),
            "premium_features": product.get('premium_features', []),
            "suitable_conditions": product.get('suitable_conditions', [])
        }
        products_data.append(product_info)

    # AI选品prompt - 使用结构化数据和策略分析
    selection_prompt = f"""
    你是一位专业的母婴产品推荐专家。请基于客户特征、需求分析和推荐策略，从商品数据中智能选择最适合的3-5个商品。

    {customer_profile}

    商品数据（JSON格式）：
    {json.dumps(products_data, ensure_ascii=False, indent=2)}

    **重要指导原则：**
    1. 严格按照推荐策略中的"推荐类型"进行选品
    2. 优先满足"核心需求"中列出的要求
    3. 重点关注"优先因素"（品质、功能、品牌、认证等）
    4. 确保商品符合"目标类别"范围
    5. 体现"个性化标签"的定位要求

    请深度分析客户的具体需求、宝宝年龄、品牌偏好等因素，结合推荐策略进行精准选品。

    必须返回严格的JSON格式，不要包含任何其他的乱起八糟的字符什么到包括（json）字样：
    {{
        "selected_products": [
            {{
                "product_index": 商品序号(1-{len(PRODUCTS_DATA)}),
                "match_score": 匹配度评分(1-100),
                "recommendation_reason": "详细推荐理由"
            }}
        ],
        "analysis": "客户需求深度分析"
    }}
    """

    # 调用AI进行选品 - 必须成功
    response = model.invoke([HumanMessage(content=selection_prompt)])

    print(f"[DEBUG] AI原始回复: '{response.content}'")
    print(f"[DEBUG] 回复长度: {len(response.content) if response.content else 0}")

    # 解析AI的选品结果
    try:
        if not response.content or not response.content.strip():
            raise ValueError("AI返回空内容")

        content = response.content.strip()

        # 尝试提取JSON（处理可能的markdown格式）
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end != -1:
                content = content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            if end != -1:
                content = content[start:end].strip()

        # 尝试找到JSON对象
        if not content.startswith('{'):
            start = content.find('{')
            if start != -1:
                end = content.rfind('}')
                if end != -1 and end > start:
                    content = content[start:end+1]

        print(f"[DEBUG] 处理后的JSON内容: '{content}'")
        selection_result = json.loads(content)

    except (json.JSONDecodeError, ValueError) as e:
        print(f"[ERROR] 解析失败: {e}")
        # 创建默认结果
        selection_result = {
            "selected_products": [
                {"product_index": 1, "match_score": 80, "recommendation_reason": "默认推荐"}
            ],
            "analysis": f"AI解析失败: {str(e)}"
        }

    # 构建匹配的商品列表
    matched_products = []
    print(f"[DEBUG] PRODUCTS_DATA长度: {len(PRODUCTS_DATA)}")
    print(f"[DEBUG] AI推荐的商品: {selection_result.get('selected_products', [])}")

    for item in selection_result.get("selected_products", []):
        product_index = item.get("product_index", 1) - 1  # 转换为0索引
        print(f"[DEBUG] 处理商品索引: {item.get('product_index')} -> {product_index}")

        if 0 <= product_index < len(PRODUCTS_DATA):
            matched_products.append({
                "product": PRODUCTS_DATA[product_index],
                "match_score": item.get("match_score", 50),
                "match_reasons": [item.get("recommendation_reason", "AI推荐")]
            })
            print(f"[DEBUG] 成功添加商品: {PRODUCTS_DATA[product_index].get('name', '未知')}")
        else:
            print(f"[DEBUG] 商品索引超出范围: {product_index}, 数据长度: {len(PRODUCTS_DATA)}")

    print(f"[DEBUG] 最终匹配商品数量: {len(matched_products)}")

    return {
        "key_information": {
            "matched_products": matched_products,
            "total_matches": len(matched_products),
            "ai_analysis": selection_result.get("analysis", ""),
            "query_used": user_message,
            "selection_method": "ai_intelligent"
        },
        "message_count": 1
    }

def premium_recommendation_response_node(state: SupervisorAgentState) -> dict:
    """高端推荐生成节点 - 生成符合高端定位的推荐回复"""

    print(f"[DEBUG] 回复节点收到的状态keys: {list(state.keys())}")

    messages = state.get("messages", [])
    user_name = state.get("user_name", "尊贵的客户")
    key_info = state.get("key_information", {})
    matched_products = key_info.get("matched_products", [])

    print(f"[DEBUG] key_information内容: {key_info}")
    print(f"[DEBUG] matched_products数量: {len(matched_products)}")
    print(f"[DEBUG] matched_products内容: {matched_products}")

    # 获取用户消息
    user_message = ""
    if messages:
        last_message = messages[-1]
        if isinstance(last_message, dict) and "content" in last_message:
            user_message = last_message["content"]
        elif hasattr(last_message, 'content'):
            user_message = last_message.content

    if not matched_products:
        # 无匹配商品时的高端话术
        response_content = f"""
{user_name}，感谢您的咨询。

基于您的需求，我正在为您精心甄选最适合的高品质产品。为了给您提供更精准的专业建议，建议您提供以下信息：

✨ 宝宝的月龄或年龄
🌟 特殊的营养需求或偏好
💎 您关注的品质标准

我们的专业团队将为您推荐经过严格筛选的优质产品，确保每一款都符合最高的品质标准。
        """
    else:
        # 生成高端推荐内容
        recommendations = []

        for i, match in enumerate(matched_products[:3], 1):
            product = match["product"]
            reasons = match["match_reasons"]

            # 构建高端推荐文案
            rec_text = f"""
🌟 **{product.get('name', '')}** - {product.get('brand', '')}
✨ 专业特色：{', '.join(product.get('premium_features', [])[:3])}
🏆 权威认证：{', '.join(product.get('certifications', []))}
👶 适龄匹配：{product.get('age_range', '')}
💎 臻选理由：{', '.join(reasons[:2])}
📍 原产地：{product.get('origin_country', '')}
⭐ 专家评分：{product.get('expert_rating', 0)}/5.0

这款产品凭借{product.get('premium_features', ['优质配方'])[0]}，深受专业育儿顾问推崇。
            """
            recommendations.append(rec_text)

        response_content = f"""
{user_name}，为您精心甄选的臻品推荐：

{''.join(recommendations)}

以上推荐均为经过严格筛选的高品质产品，每一款都代表着该领域的专业标准。我们的专业团队基于您的具体需求，从品质、安全性、营养价值等多个维度进行了综合评估。

如需了解更多产品详情或个性化建议，我随时为您提供专业服务。
        """

    try:
        # 使用AI优化回复语言
        optimization_prompt = f"""
        请优化以下商品推荐回复，使其更符合高端定位和专业性：

        原回复：{response_content}

        优化要求：
        1. 语言更加优雅专业,一定要突出高品质的特点
        2. 突出品质和专业性
        3. 避免价格敏感词汇
        4. 体现个性化服务
        5. 保持原有信息完整性

        请直接返回优化后的回复内容。
        """

        optimized_response = model.invoke([HumanMessage(content=optimization_prompt)])
        final_content = optimized_response.content

    except Exception as e:
        print(f"回复优化失败: {e}")
        final_content = response_content

    return {
        "messages": [SystemMessage(content=final_content)],
        "message_count": 1,
        "worker_results": {
            "product_recommendation_worker": {
                "content": final_content,
                "products_recommended": len(matched_products),
                "recommendation_type": "premium",
                "personalized": True
            }
        },
        "worker_status": {"product_recommendation_worker": "completed"},
        "context_summary": f"商品推荐 Worker 为 {user_name} 提供了高端产品推荐"
    }

# create graph
product_recommendation_graph = StateGraph(SupervisorAgentState)

product_recommendation_graph.add_node("recommendation_strategy", recommendation_strategy_node)
product_recommendation_graph.add_node("product_matching", premium_product_matching_node)
product_recommendation_graph.add_node("recommendation_response", premium_recommendation_response_node)

product_recommendation_graph.add_edge(START, "recommendation_strategy")
product_recommendation_graph.add_edge("recommendation_strategy", "product_matching")
product_recommendation_graph.add_edge("product_matching", "recommendation_response")
product_recommendation_graph.add_edge("recommendation_response", END)

# compile
product_recommendation_app = product_recommendation_graph.compile()

# Test
if __name__ == "__main__":
    config = {"configurable": {"thread_id": "test-product-rec"}}

    test_state = {
        "messages": [HumanMessage(content="我想给6个月的宝宝选择奶粉，有什么推荐吗？")],
        "user_name": "张女士",
        "user_id": "user123",
        "learned_facts": ["有一个6个月大的宝宝", "注重产品品质"],
        "preferences": {"喂养方式": "混合喂养", "品牌偏好": "进口品牌"},
        "session_id": "test_session_product",
        "message_count": 0
    }

    print("商品推荐 Worker 测试开始...")
    result = product_recommendation_app.invoke(test_state, config=config)

    print("\n=== 测试结果 ===")
    if result.get("messages"):
        print(f"推荐回复: {result['messages'][-1].content}")

    worker_result = result.get("worker_results", {}).get("product_recommendation_worker", {})