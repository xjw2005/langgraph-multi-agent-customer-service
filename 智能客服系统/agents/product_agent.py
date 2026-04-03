from typing import Dict, Any
from langchain_core.messages import AIMessage
from agents.base_agent import BaseAgent
from core.states import CustomerServiceState, AgentType
from services.database_service import DatabaseService
import json
import time

class ProductAgent(BaseAgent):
    """商品信息Agent"""

    def __init__(self):
        super().__init__(AgentType.PRODUCT)
        self.db_service = DatabaseService()

    def process(self, state: CustomerServiceState) -> Dict[str, Any]:
        """处理商品相关请求"""
        start_time = time.time()
        print(f"🛍️ {self.agent_name} 开始处理商品咨询...")

        try:
            user_message = self._extract_user_message(state)

            # 分析商品操作类型
            operation_type = self._analyze_product_operation(user_message)
            print(f"🔍 商品操作类型: {operation_type}")

            # 根据操作类型处理
            if operation_type == "search":
                result = self._handle_product_search(user_message, state)
            elif operation_type == "detail":
                result = self._handle_product_detail(user_message, state)
            elif operation_type == "recommend":
                result = self._handle_product_recommend(user_message, state)
            elif operation_type == "compare":
                result = self._handle_product_compare(user_message, state)
            elif operation_type == "stock":
                result = self._handle_stock_inquiry(user_message, state)
            else:
                result = self._handle_general_product_inquiry(user_message, state)

            # 记录性能
            processing_time = self._measure_performance(start_time)
            result["processing_time"] = processing_time

            # 更新处理步骤
            result["processing_steps"] = self._record_processing_step(
                state, f"完成商品{operation_type}操作，耗时{processing_time:.2f}秒"
            )
            result["agent_chain"] = self._update_agent_chain(state)

            return result

        except Exception as e:
            print(f"❌ 商品Agent处理失败: {e}")
            return self._create_error_response(f"商品信息处理失败: {str(e)}")

    def _analyze_product_operation(self, user_message: str) -> str:
        """分析商品操作类型"""
        message_lower = user_message.lower()

        if any(keyword in message_lower for keyword in ["搜索", "找", "查找", "有没有", "寻找"]):
            return "search"
        elif any(keyword in message_lower for keyword in ["详情", "介绍", "参数", "规格", "怎么样"]):
            return "detail"
        elif any(keyword in message_lower for keyword in ["推荐", "建议", "什么好", "哪个好"]):
            return "recommend"
        elif any(keyword in message_lower for keyword in ["对比", "比较", "区别", "差异"]):
            return "compare"
        elif any(keyword in message_lower for keyword in ["库存", "有货", "现货", "缺货"]):
            return "stock"
        else:
            return "general"

    def _handle_product_search(self, user_message: str, state: CustomerServiceState) -> Dict[str, Any]:
        """处理商品搜索"""
        # 提取搜索关键词
        search_keywords = self._extract_search_keywords(user_message)
        print(f"🔍 搜索关键词: {search_keywords}")

        # 搜索商品
        products = self.db_service.search_products(search_keywords)

        if not products:
            response = f"抱歉，没有找到与 '{search_keywords}' 相关的商品。您可以尝试其他关键词或浏览我们的热门商品。"
            return {
                "messages": [AIMessage(content=response)],
                "processing_confidence": 0.8,
                "product_info": {"search_keywords": search_keywords, "results": []}
            }

        # 生成搜索结果响应
        response = self._generate_search_results_response(products, search_keywords)

        return {
            "messages": [AIMessage(content=response)],
            "processing_confidence": 0.9,
            "product_info": {"search_keywords": search_keywords, "results": products}
        }

    def _handle_product_detail(self, user_message: str, state: CustomerServiceState) -> Dict[str, Any]:
        """处理商品详情查询"""
        # 提取商品标识
        product_id = self._extract_product_id(user_message, state)

        if not product_id:
            # 尝试通过商品名称搜索
            product_name = self._extract_product_name(user_message)
            if product_name:
                products = self.db_service.search_products(product_name)
                if products:
                    product_info = products[0]  # 取第一个匹配结果
                else:
                    return self._request_product_specification(state)
            else:
                return self._request_product_specification(state)
        else:
            product_info = self.db_service.get_product_by_id(product_id)

        if not product_info:
            response = "抱歉，没有找到您询问的商品信息。请提供正确的商品名称或商品编号。"
            return {
                "messages": [AIMessage(content=response)],
                "processing_confidence": 0.7
            }

        # 生成详细信息响应
        response = self._generate_product_detail_response(product_info)

        return {
            "messages": [AIMessage(content=response)],
            "processing_confidence": 0.95,
            "product_info": {"selected_product": product_info}
        }

    def _handle_product_recommend(self, user_message: str, state: CustomerServiceState) -> Dict[str, Any]:
        """处理商品推荐"""
        # 分析用户需求
        user_preferences = self._analyze_user_preferences(user_message, state)

        # 获取推荐商品
        recommended_products = self.db_service.get_recommended_products(
            category=user_preferences.get("category"),
            price_range=user_preferences.get("price_range"),
            limit=3
        )

        if not recommended_products:
            response = "抱歉，暂时没有合适的商品推荐。请告诉我您的具体需求，我会为您提供更精准的推荐。"
            return {
                "messages": [AIMessage(content=response)],
                "processing_confidence": 0.6
            }

        # 生成推荐响应
        response = self._generate_recommendation_response(recommended_products, user_preferences)

        return {
            "messages": [AIMessage(content=response)],
            "processing_confidence": 0.85,
            "product_info": {"recommendations": recommended_products, "preferences": user_preferences}
        }

    def _handle_product_compare(self, user_message: str, state: CustomerServiceState) -> Dict[str, Any]:
        """处理商品对比"""
        # 提取要对比的商品
        product_names = self._extract_comparison_products(user_message)

        if len(product_names) < 2:
            response = "请告诉我您想对比哪两个或多个商品，我来为您详细分析它们的区别。"
            return {
                "messages": [AIMessage(content=response)],
                "processing_confidence": 0.8
            }

        # 获取商品信息
        products_to_compare = []
        for name in product_names:
            products = self.db_service.search_products(name)
            if products:
                products_to_compare.append(products[0])

        if len(products_to_compare) < 2:
            response = "抱歉，无法找到足够的商品进行对比。请提供更准确的商品名称。"
            return {
                "messages": [AIMessage(content=response)],
                "processing_confidence": 0.7
            }

        # 生成对比响应
        response = self._generate_comparison_response(products_to_compare)

        return {
            "messages": [AIMessage(content=response)],
            "processing_confidence": 0.9,
            "product_info": {"comparison_products": products_to_compare}
        }

    def _handle_stock_inquiry(self, user_message: str, state: CustomerServiceState) -> Dict[str, Any]:
        """处理库存查询"""
        product_name = self._extract_product_name(user_message)

        if not product_name:
            response = "请告诉我您想查询哪个商品的库存情况。"
            return {
                "messages": [AIMessage(content=response)],
                "processing_confidence": 0.8
            }

        products = self.db_service.search_products(product_name)
        if not products:
            response = f"抱歉，没有找到 '{product_name}' 相关的商品。"
            return {
                "messages": [AIMessage(content=response)],
                "processing_confidence": 0.7
            }

        product = products[0]
        stock = product.get("stock", 0)

        if stock > 10:
            stock_status = "现货充足"
        elif stock > 0:
            stock_status = f"库存紧张，仅剩 {stock} 件"
        else:
            stock_status = "暂时缺货"

        response = f"📦 {product.get('name')} 库存状态：{stock_status}\n\n如需购买，建议尽快下单哦！"

        return {
            "messages": [AIMessage(content=response)],
            "processing_confidence": 0.95,
            "product_info": {"selected_product": product, "stock_status": stock_status}
        }

    def _handle_general_product_inquiry(self, user_message: str, state: CustomerServiceState) -> Dict[str, Any]:
        """处理一般商品咨询"""
        system_prompt = """
你是专业的商品顾问，请根据用户的问题提供帮助。

常见问题处理：
1. 商品使用方法 - 提供详细使用指导
2. 商品保修政策 - 介绍保修条款
3. 商品适用性 - 分析是否适合用户需求
4. 购买建议 - 提供专业购买建议

请提供专业、详细的回复。
"""

        context = self._build_context_summary(state)
        response = self._generate_response(system_prompt, f"用户问题: {user_message}\n{context}")

        return {
            "messages": [AIMessage(content=response)],
            "processing_confidence": 0.8
        }

    def _extract_search_keywords(self, user_message: str) -> str:
        """提取搜索关键词"""
        # 移除常见的搜索词汇
        stop_words = ["搜索", "找", "查找", "有没有", "寻找", "我想要", "我要", "帮我"]

        keywords = user_message
        for word in stop_words:
            keywords = keywords.replace(word, "")

        return keywords.strip()

    def _extract_product_id(self, user_message: str, state: CustomerServiceState) -> str:
        """提取商品ID"""
        import re
        # 匹配商品ID模式
        product_pattern = r'(prod_\w+|商品编号[：:]\s*(\w+))'
        matches = re.findall(product_pattern, user_message, re.IGNORECASE)

        if matches:
            return matches[0][0] or matches[0][1]

        # 从状态中获取
        if state.get("product_info", {}).get("selected_product", {}).get("product_id"):
            return state["product_info"]["selected_product"]["product_id"]

        return ""

    def _extract_product_name(self, user_message: str) -> str:
        """提取商品名称"""
        # 简单的商品名称提取逻辑
        common_products = ["iPhone", "MacBook", "AirPods", "iPad", "Nike", "Adidas"]

        for product in common_products:
            if product.lower() in user_message.lower():
                return product

        # 提取引号中的内容
        import re
        quoted_text = re.findall(r'["""](.*?)["""]', user_message)
        if quoted_text:
            return quoted_text[0]

        return ""

    def _analyze_user_preferences(self, user_message: str, state: CustomerServiceState) -> Dict[str, Any]:
        """分析用户偏好"""
        preferences = {}

        message_lower = user_message.lower()

        # 分析价格偏好
        if any(word in message_lower for word in ["便宜", "实惠", "经济"]):
            preferences["price_range"] = "low"
        elif any(word in message_lower for word in ["高端", "贵", "奢侈"]):
            preferences["price_range"] = "high"
        else:
            preferences["price_range"] = "medium"

        # 分析类别偏好
        if any(word in message_lower for word in ["手机", "电话", "iphone"]):
            preferences["category"] = "电子产品"
        elif any(word in message_lower for word in ["鞋", "运动鞋", "nike"]):
            preferences["category"] = "服装鞋帽"

        return preferences

    def _extract_comparison_products(self, user_message: str) -> list:
        """提取要对比的商品"""
        # 简单的商品提取逻辑
        products = []
        common_products = ["iPhone 15", "MacBook Pro", "AirPods Pro", "Nike运动鞋"]

        for product in common_products:
            if product.lower() in user_message.lower():
                products.append(product)

        return products

    def _request_product_specification(self, state: CustomerServiceState) -> Dict[str, Any]:
        """请求用户提供商品规格"""
        response = "请告诉我您想了解哪个商品的详细信息，可以提供商品名称或商品编号。"
        return {
            "messages": [AIMessage(content=response)],
            "processing_confidence": 0.9
        }

    def _generate_search_results_response(self, products: list, keywords: str) -> str:
        """生成搜索结果响应"""
        response_parts = [f"🔍 为您找到 {len(products)} 个相关商品："]

        for i, product in enumerate(products[:5], 1):  # 最多显示5个结果
            response_parts.append(
                f"{i}. {product.get('name')} - ¥{product.get('price')} "
                f"(库存: {product.get('stock')}件)"
            )

        if len(products) > 5:
            response_parts.append(f"... 还有 {len(products) - 5} 个相关商品")

        response_parts.append("\n如需了解详细信息，请告诉我商品名称。")
        return "\n".join(response_parts)

    def _generate_product_detail_response(self, product: dict) -> str:
        """生成商品详情响应"""
        response_parts = [
            f"📱 {product.get('name')} 详细信息：",
            f"💰 价格：¥{product.get('price')}",
            f"📦 库存：{product.get('stock')}件",
            f"🏷️ 分类：{product.get('category')}",
            f"📝 描述：{product.get('description', '暂无描述')}"
        ]

        # 添加购买建议
        stock = product.get('stock', 0)
        if stock > 0:
            response_parts.append("\n✅ 现货供应，支持立即下单！")
        else:
            response_parts.append("\n❌ 暂时缺货，可预订或选择其他商品。")

        return "\n".join(response_parts)

    def _generate_recommendation_response(self, products: list, preferences: dict) -> str:
        """生成推荐响应"""
        response_parts = ["🎯 根据您的需求，为您推荐以下商品："]

        for i, product in enumerate(products, 1):
            response_parts.append(
                f"{i}. {product.get('name')} - ¥{product.get('price')}\n"
                f"   {product.get('description', '优质商品')}"
            )

        response_parts.append(f"\n推荐理由：基于您的{preferences.get('price_range', '中等')}价位偏好")
        return "\n".join(response_parts)

    def _generate_comparison_response(self, products: list) -> str:
        """生成对比响应"""
        response_parts = ["📊 商品对比分析："]

        for i, product in enumerate(products, 1):
            response_parts.append(
                f"{i}. {product.get('name')}\n"
                f"   价格：¥{product.get('price')}\n"
                f"   库存：{product.get('stock')}件\n"
                f"   特点：{product.get('description', '暂无描述')}"
            )

        response_parts.append("\n💡 建议：请根据您的预算和需求选择最适合的商品。")
        return "\n".join(response_parts)