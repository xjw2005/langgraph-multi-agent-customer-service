#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
商品推荐系统测试脚本
测试supervisor_agent调用product_recommendation_worker的完整流程
"""

import sys
import os

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, "agents"))

from langchain.messages import HumanMessage
from agents.supervisor_agent import supervisor_app

def test_product_recommendation():
    """测试商品推荐功能"""

    print("=== 商品推荐系统测试 ===\n")

    # 测试配置
    config = {"configurable": {"thread_id": "test-product-rec-001"}}

    # 测试用例1：明确的商品推荐请求
    test_cases = [
        # {
        #     "name": "明确奶粉推荐请求",
        #     "message": "给我推荐一款适合6个月宝宝的奶粉",
        #     "user_name": "张女士",
        #     "facts": ["有一个6个月大的宝宝", "注重营养均衡", "希望提升免疫力"],
        #     "preferences": {
        #         "品牌偏好": "德国品牌",
        #         "喂养方式": "混合喂养",
        #         "有机需求": True
        #     }
        # },
        # {
        #     "name": "一般商品咨询",
        #     "message": "什么牌子的辅食比较好？",
        #     "user_name": "李先生",
        #     "facts": ["有一个8个月大的宝宝", "刚开始添加辅食"],
        #     "preferences": {
        #         "品牌偏好": "有机品牌",
        #         "价格敏感度": "不敏感"
        #     }
        # },
        {
            "name": "育儿知识咨询（应该路由到qa_worker）",
            "message": "6个月宝宝应该怎么添加辅食？",
            "user_name": "王女士",
            "facts": ["有一个6个月大的宝宝", "新手妈妈"],
            "preferences": {}
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"--- 测试用例 {i}: {test_case['name']} ---")
        print(f"用户消息: {test_case['message']}")

        # 构建测试状态
        test_state = {
            "messages": [HumanMessage(content=test_case['message'])],
            "user_name": test_case['user_name'],
            "user_id": f"test_user_{i:03d}",
            "learned_facts": test_case['facts'],
            "preferences": test_case['preferences'],
            "session_id": f"test_session_{i:03d}",
            "message_count": 0
        }

        try:
            # 调用supervisor
            result = supervisor_app.invoke(test_state, config=config)

            # 输出结果
            selected_worker = result.get('selected_worker', 'N/A')
            print(f"✅ 选择的Worker: {selected_worker}")

            if result.get('messages'):
                last_message = result['messages'][-1]
                print(f"📝 回复内容: {last_message.content[:200]}...")

            # 检查worker结果
            worker_results = result.get('worker_results', {})
            if worker_results:
                for worker_name, worker_result in worker_results.items():
                    if isinstance(worker_result, dict):
                        print(f"🔧 {worker_name} 执行结果:")
                        if 'products_recommended' in worker_result:
                            print(f"   推荐产品数量: {worker_result['products_recommended']}")
                        if 'recommendation_type' in worker_result:
                            print(f"   推荐类型: {worker_result['recommendation_type']}")
                        if 'used_rag' in worker_result:
                            print(f"   使用RAG: {worker_result['used_rag']}")

            print(f"✅ 测试完成\n")

        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            print()

def test_product_recommendation_worker_directly():
    """直接测试商品推荐Worker"""

    print("=== 直接测试商品推荐Worker ===\n")

    try:
        from agents.product_recommendation_worker import product_recommendation_app

        test_state = {
            "messages": [HumanMessage(content="推荐一款6个月宝宝的奶粉")],
            "user_name": "测试用户",
            "user_id": "direct_test_001",
            "learned_facts": ["有一个6个月大的宝宝", "注重品质"],
            "preferences": {"品牌偏好": "进口品牌"},
            "session_id": "direct_test_session",
            "message_count": 0
        }

        # 无状态调用
        result = product_recommendation_app.invoke(test_state)

        print("✅ 商品推荐Worker直接调用成功")
        if result.get('messages'):
            print(f"📝 推荐内容: {result['messages'][-1].content[:300]}...")

        worker_results = result.get('worker_results', {})
        if worker_results:
            rec_result = worker_results.get('product_recommendation_worker', {})
            print(f"🔧 推荐产品数量: {rec_result.get('products_recommended', 0)}")
            print(f"🔧 推荐类型: {rec_result.get('recommendation_type', 'N/A')}")

    except Exception as e:
        print(f"❌ 直接测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":

    # 再测试完整的supervisor调用流程
    test_product_recommendation()

    print("🎉 所有测试完成！")