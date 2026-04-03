import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.main_graph import CustomerServiceSystem
from config.database import db_manager
import time

def main():
    """基础演示程序"""
    print("🚀 智能客服系统基础演示")
    print("=" * 50)

    # 初始化数据库
    print("📊 初始化数据库...")
    db_manager.insert_sample_data()

    # 创建客服系统
    print("🤖 启动客服系统...")
    cs_system = CustomerServiceSystem()

    # 测试用例
    test_cases = [
        {
            "user_id": "user_001",
            "message": "你好，我想查询我的订单",
            "description": "基础问候 + 订单查询意图"
        },
        {
            "user_id": "user_001",
            "message": "我的订单号是 ORD001",
            "description": "具体订单查询"
        },
        {
            "user_id": "user_002",
            "message": "有什么好的手机推荐吗？",
            "description": "商品推荐咨询"
        },
        {
            "user_id": "user_002",
            "message": "iPhone 15 的详细信息",
            "description": "具体商品详情查询"
        },
        {
            "user_id": "user_003",
            "message": "我要取消订单 ORD003",
            "description": "订单取消请求"
        }
    ]

    print("\n🎯 开始测试对话...")
    print("=" * 50)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n【测试 {i}】{test_case['description']}")
        print(f"👤 用户 ({test_case['user_id']}): {test_case['message']}")

        # 处理消息
        start_time = time.time()
        result = cs_system.process_message(
            user_id=test_case['user_id'],
            message=test_case['message']
        )
        processing_time = time.time() - start_time

        # 显示结果
        print(f"🤖 客服: {result['response']}")
        print(f"📋 意图: {result.get('intent', '未识别')}")
        print(f"🔧 使用Agent: {result.get('agent_used', '未知')}")
        print(f"📊 置信度: {result.get('confidence', 0):.2f}")
        print(f"⏱️ 处理时间: {processing_time:.2f}秒")

        if result.get('requires_human'):
            print("⚠️ 需要人工介入")

        if result.get('processing_steps'):
            print("🔍 处理步骤:")
            for step in result['processing_steps']:
                print(f"   • {step}")

        print("-" * 30)
        time.sleep(1)  # 模拟真实对话间隔

    print("\n📈 系统统计信息:")
    stats = cs_system.get_system_stats()
    for key, value in stats.items():
        print(f"   • {key}: {value}")

    print("\n✅ 基础演示完成！")
    print("\n💡 提示:")
    print("   • 可以查看数据库文件了解数据持久化")
    print("   • 运行 advanced_demo.py 体验更多高级功能")
    print("   • 查看 examples/ 目录了解更多用法")

if __name__ == "__main__":
    main()