import sqlite3
from typing import List, Dict, Any, Optional
from config.database import db_manager
import json

class DatabaseService:
    """数据库服务类"""

    def __init__(self):
        self.db_manager = db_manager

    def get_connection(self):
        """获取数据库连接"""
        return self.db_manager.get_connection()

    # === 用户相关操作 ===
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """根据用户ID获取用户信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, username, email, phone, created_at, updated_at
                FROM users WHERE user_id = ?
            """, (user_id,))

            row = cursor.fetchone()
            if row:
                return {
                    "user_id": row[0],
                    "username": row[1],
                    "email": row[2],
                    "phone": row[3],
                    "created_at": row[4],
                    "updated_at": row[5]
                }
            return None

    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """获取用户偏好"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT preference_key, preference_value
                FROM user_preferences WHERE user_id = ?
            """, (user_id,))

            preferences = {}
            for row in cursor.fetchall():
                preferences[row[0]] = row[1]

            return preferences

    def save_user_preference(self, user_id: str, key: str, value: str) -> bool:
        """保存用户偏好"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO user_preferences (user_id, preference_key, preference_value)
                    VALUES (?, ?, ?)
                """, (user_id, key, value))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ 保存用户偏好失败: {e}")
            return False

    # === 订单相关操作 ===
    def get_order_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """根据订单ID获取订单信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT order_id, user_id, product_id, product_name, quantity,
                       price, status, created_at, updated_at
                FROM orders WHERE order_id = ?
            """, (order_id,))

            row = cursor.fetchone()
            if row:
                return {
                    "order_id": row[0],
                    "user_id": row[1],
                    "product_id": row[2],
                    "product_name": row[3],
                    "quantity": row[4],
                    "price": float(row[5]),
                    "status": row[6],
                    "created_at": row[7],
                    "updated_at": row[8]
                }
            return None

    def get_orders_by_user_id(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """根据用户ID获取订单列表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT order_id, user_id, product_id, product_name, quantity,
                       price, status, created_at, updated_at
                FROM orders WHERE user_id = ?
                ORDER BY created_at DESC LIMIT ?
            """, (user_id, limit))

            orders = []
            for row in cursor.fetchall():
                orders.append({
                    "order_id": row[0],
                    "user_id": row[1],
                    "product_id": row[2],
                    "product_name": row[3],
                    "quantity": row[4],
                    "price": float(row[5]),
                    "status": row[6],
                    "created_at": row[7],
                    "updated_at": row[8]
                })

            return orders

    def update_order_status(self, order_id: str, new_status: str) -> bool:
        """更新订单状态"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE order_id = ?
                """, (new_status, order_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ 更新订单状态失败: {e}")
            return False

    # === 商品相关操作 ===
    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """根据商品ID获取商品信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT product_id, name, description, price, stock, category, created_at
                FROM products WHERE product_id = ?
            """, (product_id,))

            row = cursor.fetchone()
            if row:
                return {
                    "product_id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "price": float(row[3]),
                    "stock": row[4],
                    "category": row[5],
                    "created_at": row[6]
                }
            return None

    def search_products(self, keywords: str, limit: int = 10) -> List[Dict[str, Any]]:
        """搜索商品"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            search_pattern = f"%{keywords}%"
            cursor.execute("""
                SELECT product_id, name, description, price, stock, category, created_at
                FROM products
                WHERE name LIKE ? OR description LIKE ?
                ORDER BY name LIMIT ?
            """, (search_pattern, search_pattern, limit))

            products = []
            for row in cursor.fetchall():
                products.append({
                    "product_id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "price": float(row[3]),
                    "stock": row[4],
                    "category": row[5],
                    "created_at": row[6]
                })

            return products

    def get_recommended_products(self, category: str = None, price_range: str = "medium", limit: int = 5) -> List[Dict[str, Any]]:
        """获取推荐商品"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 根据价格范围设置条件
            price_conditions = {
                "low": "price < 1000",
                "medium": "price BETWEEN 1000 AND 5000",
                "high": "price > 5000"
            }

            price_condition = price_conditions.get(price_range, price_conditions["medium"])

            if category:
                query = f"""
                    SELECT product_id, name, description, price, stock, category, created_at
                    FROM products
                    WHERE category = ? AND {price_condition} AND stock > 0
                    ORDER BY price LIMIT ?
                """
                cursor.execute(query, (category, limit))
            else:
                query = f"""
                    SELECT product_id, name, description, price, stock, category, created_at
                    FROM products
                    WHERE {price_condition} AND stock > 0
                    ORDER BY price LIMIT ?
                """
                cursor.execute(query, (limit,))

            products = []
            for row in cursor.fetchall():
                products.append({
                    "product_id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "price": float(row[3]),
                    "stock": row[4],
                    "category": row[5],
                    "created_at": row[6]
                })

            return products

    # === 物流相关操作 ===
    def get_logistics_by_order_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """根据订单ID获取物流信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT tracking_id, order_id, status, current_location,
                       estimated_delivery, created_at, updated_at
                FROM logistics WHERE order_id = ?
            """, (order_id,))

            row = cursor.fetchone()
            if row:
                return {
                    "tracking_id": row[0],
                    "order_id": row[1],
                    "status": row[2],
                    "current_location": row[3],
                    "estimated_delivery": row[4],
                    "created_at": row[5],
                    "updated_at": row[6]
                }
            return None

    def get_logistics_by_tracking_id(self, tracking_id: str) -> Optional[Dict[str, Any]]:
        """根据物流单号获取物流信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT tracking_id, order_id, status, current_location,
                       estimated_delivery, created_at, updated_at
                FROM logistics WHERE tracking_id = ?
            """, (tracking_id,))

            row = cursor.fetchone()
            if row:
                return {
                    "tracking_id": row[0],
                    "order_id": row[1],
                    "status": row[2],
                    "current_location": row[3],
                    "estimated_delivery": row[4],
                    "created_at": row[5],
                    "updated_at": row[6]
                }
            return None

    # === 退款相关操作 ===
    def create_refund_request(self, order_id: str, user_id: str, amount: float, reason: str) -> str:
        """创建退款申请"""
        try:
            import uuid
            refund_id = f"REF{uuid.uuid4().hex[:8].upper()}"

            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO refunds (refund_id, order_id, user_id, amount, reason, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (refund_id, order_id, user_id, amount, reason, "待处理"))
                conn.commit()

                return refund_id
        except Exception as e:
            print(f"❌ 创建退款申请失败: {e}")
            return ""

    def get_refund_by_id(self, refund_id: str) -> Optional[Dict[str, Any]]:
        """根据退款ID获取退款信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT refund_id, order_id, user_id, amount, reason, status,
                       created_at, processed_at
                FROM refunds WHERE refund_id = ?
            """, (refund_id,))

            row = cursor.fetchone()
            if row:
                return {
                    "refund_id": row[0],
                    "order_id": row[1],
                    "user_id": row[2],
                    "amount": float(row[3]),
                    "reason": row[4],
                    "status": row[5],
                    "created_at": row[6],
                    "processed_at": row[7]
                }
            return None

    # === 对话历史相关操作 ===
    def save_conversation(self, session_id: str, user_id: str, message: str,
                         response: str, intent: str, agent_used: str, confidence: float) -> bool:
        """保存对话记录"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO conversations
                    (session_id, user_id, message, response, intent, agent_used, confidence_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (session_id, user_id, message, response, intent, agent_used, confidence))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ 保存对话记录失败: {e}")
            return False

    def get_conversation_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取对话历史"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, session_id, user_id, message, response, intent,
                       agent_used, confidence_score, created_at
                FROM conversations
                WHERE session_id = ?
                ORDER BY created_at DESC LIMIT ?
            """, (session_id, limit))

            conversations = []
            for row in cursor.fetchall():
                conversations.append({
                    "id": row[0],
                    "session_id": row[1],
                    "user_id": row[2],
                    "message": row[3],
                    "response": row[4],
                    "intent": row[5],
                    "agent_used": row[6],
                    "confidence_score": row[7],
                    "created_at": row[8]
                })

            return conversations

    def get_user_conversation_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """获取用户对话摘要统计"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    COUNT(*) as total_conversations,
                    AVG(confidence_score) as avg_confidence,
                    intent,
                    COUNT(*) as intent_count
                FROM conversations
                WHERE user_id = ? AND created_at >= datetime('now', '-{} days')
                GROUP BY intent
                ORDER BY intent_count DESC
            """.format(days), (user_id,))

            intent_stats = []
            total_conversations = 0
            total_confidence = 0

            for row in cursor.fetchall():
                if total_conversations == 0:  # 第一行包含总数
                    total_conversations = row[0]
                    total_confidence = row[1] or 0

                intent_stats.append({
                    "intent": row[2],
                    "count": row[3]
                })

            return {
                "total_conversations": total_conversations,
                "average_confidence": total_confidence,
                "intent_distribution": intent_stats
            }