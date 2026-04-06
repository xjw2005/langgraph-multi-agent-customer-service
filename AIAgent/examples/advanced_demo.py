import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.main_graph import CustomerServiceSystem
from config.database import db_manager
import time
import json

def advanced_demo():
    """高级功能演示"""
    print("🚀 智能客服系统高级功能演示")
    print("=" * 60)

    # 初始化系统
    print("📊 初始化系统...")
    db_manager.insert_sample_data()
    cs_system = CustomerServiceSystem()

    # 演示1: 多轮对话和上下文保持
    print("\n🎯 演示1: 多轮对话和上下文保持")
    print("=" * 40)

    user_id = "user_001"
    session_id = "demo_session_001"

    conversation_flow = [
        "你好，我想查询订单",
        "ORD001",
        "这个订单什么时候能到？",
        "可以修改收货地址吗？"
    ]

    for i, message in enumerate(conversation_flow, 1):
        print(f"\n轮次 {i}:")
        print(f"👤 用户: {message}")

        result = cs_system.process_message(
            user_id=user_id,
            message=message,
            session_id=session_id
        )

        print(f"🤖 客服: {result['response']}")
        print(f"📋 意图: {result.get('intent', '未识别')}")
        time.sleep(1)

    # 演示2: 历史回溯功能
    print("\n\n🎯 演示2: 对话历史回溯")
    print("=" * 40)

    history = cs_system.get_conversation_history(session_id)
    print(f"📚 会话 {session_id} 的对话历史:")
    for record in history:
        print(f"   👤 用户: {record['message']}")
        print(f"   🤖 客服: {record['response']}")
        print(f"   📊 意图: {record['intent']} | 置信度: {record['confidence_score']:.2f}")
        print("   " + "-" * 30)

    # 演示3: 用户画像和偏好学习
    print("\n\n🎯 演示3: 用户画像和偏好学习")
    print("=" * 40)

    # 模拟用户偏好学习
    preference_messages = [
        "我比较喜欢苹果的产品",
        "预算在5000-10000之间",
        "主要用来工作和娱乐"
    ]

    for message in preference_messages:
        print(f"👤 用户偏好: {message}")
        result = cs_system.process_message(
            user_id=user_id,
            message=message,
            session_id=session_id
        )
        print(f"🤖 客服: {result['response']}")

    # 查看用户摘要
    user_summary = cs_system.get_user_summary(user_id)
    print(f"\n📊 用户 {user_id} 的对话摘要:")
    print(f"   • 总对话数: {user_summary.get('total_conversations', 0)}")
    print(f"   • 平均置信度: {user_summary.get('average_confidence', 0):.2f}")
    print("   • 意图分布:")
    for intent_stat in user_summary.get('intent_distribution', []):
        print(f"     - {intent_stat['intent']}: {intent_stat['count']} 次")

    # 演示4: 复杂业务场景处理
    print("\n\n🎯 演示4: 复杂业务场景处理")
    print("=" * 40)

    complex_scenarios = [
        {
            "user_id": "user_002",
            "message": "我的订单ORD002有问题，商品质量不好，我要退货退款",
            "description": "复杂退款场景"
        },
        {
            "user_id": "user_003",
            "message": "帮我对比一下iPhone 15和MacBook Pro，我不知道买哪个好",
            "description": "商品对比咨询"
        },
        {
            "user_id": "user_001",
            "message": "我的支付失败了，但是钱被扣了，怎么办？"    "description": "支付问题处理"
        }
    ]

    for scenario in complex_scenarios:
        print(f"\n📝 场景: {scenario['description']}")
        print(f"👤 用户 ({scenario['user_id']}): {scenario['message']}")

        result = cs_system.process_message(
            user_id=scenario['user_id'],
            message=scenario['message']
        )

        print(f"🤖 客服: {result['response']}")
        print(f"📋 处理结果:")
        print(f"   • 意图: {result.get('intent', '未识别')}")
        print(f"   • Agent: {result.get('agent_used', '未知')}")
        print(f"   • 置信度: {result.get('confidence', 0):.2f}"print(f"   • 需要人工: {'是' if result.get('requires_human') else '否'}")

        if result.get('processing_steps'):
            print("   • 处理步骤:")
            for step in result['processing_steps']:
                print(f"     - {step}")

        time.sleep(1)

    # 演示5: 人工介入和中断恢复
    print("\n\n🎯 演示5: 人工介入机制")
    print("=" * 40)

    # 模拟需要人工介入的场景
    human_required_message = "我要投诉你们的服务，这个问题太复杂了，我要找你们经理"
    print(f"👤 用户: {human_required_message}")

    result = cs_system.process_message(
        user_id="user_004",
        message=human_required_message
    )

    print(f"🤖 客服: {result['response']}")
    if result.get('requires_human'):
        print("⚠️ 系统检测到需要人工介入")
        print("📞 正在转接人工客服...")

    # 演示6: 性能监控和统计
    print("\n\n🎯 演示6: 系统性能统计")
    print("=" * 40)

    stats = cs_system.get_system_stats()
    print("📊 系统运行统计:")
    for key, value in stats.items():
        print(f"   • {key}: {value}")

    # 模拟性能测试
    print("\n⚡ 性能测试 (处理10条消息):")
    start_time = time.time()

    for i in range(10):
        cs_system.process_message(
            user_id=f"test_user_{i}",
            message=f"测试消息 {i+1}: 查询商品信息"
        )

    total_time = time.time() - start_time
    avg_time = total_time / 10

    print(f"   • 总处理时间: {total_time:.2f}秒")
    print(f"   • 平均响应时间: {avg_time:.2f}秒")
    print(f"   • 每秒处理能力: {10/total_time:.1f} 消息/秒")

    print("\n✅ 高级功能演示完成！")
    print("\n🎉 系统特性总结:")
    print("   ✓ 多Agent协作处理")
    print("   ✓ 智能意图识别和路由")
    print("   ✓ 完整的对话历史管理")
    print("   ✓ 用户偏好学习")
    print("   ✓ 复杂业务场景处理")
    print("   ✓ 人工介入机制")
    print("   ✓ 数据持久化和状态恢复")
    print("   ✓ 性能监控和统计")

if __name__ == "__main__":
    advanced_demo()