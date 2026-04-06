#!/usr/bin/env python3
"""
快速验证脚本 - 检查项目是否可以正常导入和运行
"""

import sys
import os


# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_imports():
    """测试关键模块导入"""
    print("🔍 测试模块导入...")

    try:
        # 测试配置模块
        from config.settings import settings
        print("✅ 配置模块导入成功")

        # 测试数据库模块
        from config.database import db_manager
        print("✅ 数据库模块导入成功")

        # 测试状态定义
        from core.states import CustomerServiceState, Intent, AgentType
        print("✅ 状态定义导入成功")

        # 测试Agent模块
        from agents.base_agent import BaseAgent
        from agents.order_agent import OrderAgent
        from agents.product_agent import ProductAgent
        print("✅ Agent模块导入成功")

        # 测试服务模块
        from services.database_service import DatabaseService
        print("✅ 服务模块导入成功")

        # 测试核心系统
        from core.main_graph import CustomerServiceSystem
        print("✅ 核心系统导入成功")

        return True

    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_basic_functionality():
    """测试基本功能"""
    print("\n🧪 测试基本功能...")

    try:
        # 初始化数据库
        from config.database import db_manager
        db_manager.insert_sample_data()
        print("✅ 数据库初始化成功")

        # 创建客服系统实例
        from core.main_graph import CustomerServiceSystem
        cs_system = CustomerServiceSystem()
        print("✅ 客服系统创建成功")

        # 测试简单消息处理
        result = cs_system.process_message(
            user_id="test_user",
            message="你好"
        )

        if result.get("response"):
            print("✅ 消息处理成功")
            print(f"   响应: {result['response'][:50]}...")
            return True
        else:
            print("❌ 消息处理失败: 无响应")
            return False

    except Exception as e:
        print(f"❌ 功能测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 智能客服系统验证测试")
    print("=" * 50)

    # 测试导入
    import_success = test_imports()

    if not import_success:
        print("\n❌ 导入测试失败，请检查代码语法")
        return False

    # 测试基本功能
    function_success = test_basic_functionality()

    if function_success:
        print("\n🎉 所有测试通过！项目可以正常运行")
        print("\n📋 下一步:")
        print("   1. 运行 python examples/basic_demo.py")
        print("   2. 运行 python examples/advanced_demo.py")
        return True
    else:
        print("\n❌ 功能测试失败，请检查配置和依赖")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)