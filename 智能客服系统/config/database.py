import sqlite3
import os
from typing import Optional
from config.settings import settings

class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.DATABASE_PATH
        self.init_database()

    def init_database(self):
        """初始化数据库表结构"""
        # 确保数据目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 用户表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT,
                    email TEXT,
                    phone TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 订单表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    product_id TEXT,
                    product_name TEXT,
                    quantity INTEGER,
                    price DECIMAL(10,2),
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)

            # 商品表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    product_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    price DECIMAL(10,2),
                    stock INTEGER DEFAULT 0,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 对话历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    user_id TEXT,
                    message TEXT,
                    response TEXT,
                    intent TEXT,
                    agent_used TEXT,
                    confidence_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)

            # 用户偏好表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT,
                    preference_key TEXT,
                    preference_value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, preference_key),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)

            # 物流信息表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logistics (
                    tracking_id TEXT PRIMARY KEY,
                    order_id TEXT,
                    status TEXT,
                    current_location TEXT,
                    estimated_delivery TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES orders (order_id)
                )
            """)

            # 退款记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS refunds (
                    refund_id TEXT PRIMARY KEY,
                    order_id TEXT,
                    user_id TEXT,
                    amount DECIMAL(10,2),
                    reason TEXT,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES orders (order_id),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)

            conn.commit()
            print("✅ 数据库初始化完成")

    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def insert_sample_data(self):
        """插入示例数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 示例用户
            users_data = [
                ("user_001", "张三", "zhangsan@email.com", "13800138001"),
                ("user_002", "李四", "lisi@email.com", "13800138002"),
                ("user_003", "王五", "wangwu@email.com", "13800138003"),
            ]

            cursor.executemany("""
                INSERT OR REPLACE INTO users (user_id, username, email, phone)
                VALUES (?, ?, ?, ?)
            """, users_data)

            # 示例商品
            products_data = [
                ("prod_001", "iPhone 15", "最新款苹果手机", 7999.00, 50, "电子产品"),
                ("prod_002", "MacBook Pro", "专业笔记本电脑", 15999.00, 20, "电子产品"),
                ("prod_003", "AirPods Pro", "无线降噪耳机", 1999.00, 100, "电子产品"),
                ("prod_004", "Nike运动鞋", "舒适运动鞋", 899.00, 200, "服装鞋帽"),
            ]

            cursor.executemany("""
                INSERT OR REPLACE INTO products (product_id, name, description, price, stock, category)
                VALUES (?, ?, ?, ?, ?, ?)
            """, products_data)

            # 示例订单
            orders_data = [
                ("ORD001", "user_001", "prod_001", "iPhone 15", 1, 7999.00, "已发货"),
                ("ORD002", "user_002", "prod_003", "AirPods Pro", 2, 1999.00, "已完成"),
                ("ORD003", "user_001", "prod_004", "Nike运动鞋", 1, 899.00, "处理中"),
                ("ORD004", "user_003", "prod_002", "MacBook Pro", 1, 15999.00, "已取消"),
            ]

            cursor.executemany("""
                INSERT OR REPLACE INTO orders (order_id, user_id, product_id, product_name, quantity, price, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, orders_data)

            # 示例物流信息
            logistics_data = [
                ("TRK001", "ORD001", "运输中", "北京分拣中心", "2024-04-05 14:00:00"),
                ("TRK002", "ORD002", "已送达", "用户签收", "2024-04-03 10:30:00"),
                ("TRK003", "ORD003", "已揽收", "上海仓库", "2024-04-04 16:00:00"),
            ]

            cursor.executemany("""
                INSERT OR REPLACE INTO logistics (tracking_id, order_id, status, current_location, estimated_delivery)
                VALUES (?, ?, ?, ?, ?)
            """, logistics_data)

            conn.commit()
            print("✅ 示例数据插入完成")

# 全局数据库管理器实例
db_manager = DatabaseManager()

if __name__ == "__main__":
    # 初始化数据库并插入示例数据
    db_manager.insert_sample_data()
    print("🎯 数据库设置完成！")