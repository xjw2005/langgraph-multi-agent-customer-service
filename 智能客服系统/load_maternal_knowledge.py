# 母婴知识数据加载脚本
# 将maternal_child_knowledge.json中的数据转换并加载到RAG系统

import json
import os
from pathlib import Path
from rag.vector_store import BabyKnowledgeVectorStore
from typing import Dict, List, Any

def load_maternal_knowledge_from_json():
    """从JSON文件加载母婴知识数据"""

    # 读取JSON数据
    json_file_path = Path(__file__).parent / "data" / "maternal_child_knowledge.json"

    if not json_file_path.exists():
        print(f"❌ 文件不存在: {json_file_path}")
        return False

    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"✅ 成功读取JSON文件，包含 {data['total']} 条知识")

        # 创建向量存储
        vector_store = BabyKnowledgeVectorStore()

        # 按分类组织数据
        knowledge_by_category = {}

        for item in data['data']:
            category = item['category']
            content = item['content']

            # 将分类映射到RAG系统的领域
            domain_mapping = {
                "备孕与孕期": "baby_care",      # 映射到现有的baby_care领域
                "分娩与产后恢复": "baby_care",   # 映射到现有的baby_care领域
                "新生儿护理": "baby_care",
                "喂养与辅食": "nutrition",
                "生长发育与安全": "development"
            }

            domain = domain_mapping.get(category, "general_care")

            if domain not in knowledge_by_category:
                knowledge_by_category[domain] = []

            # 转换为RAG系统格式
            knowledge_item = {
                "content": content,
                "title": f"{category}知识 - {item['id']}",
                "source": "专业母婴知识库",
                "age_range": get_age_range_for_category(category),
                "authority": "专业机构",
                "keywords": extract_keywords_from_content(content),
                "difficulty": get_difficulty_for_category(category),
                "content_type": "advice",
                "category": category,
                "knowledge_id": item['id']
            }

            knowledge_by_category[domain].append(knowledge_item)

        # 添加到向量存储
        total_added = 0
        for domain, knowledge_list in knowledge_by_category.items():
            success = vector_store.add_knowledge(domain, knowledge_list)
            if success:
                total_added += len(knowledge_list)
                print(f"✅ 成功添加 {len(knowledge_list)} 条 {domain} 知识")
            else:
                print(f"❌ 添加 {domain} 知识失败")

        print(f"\n🎉 知识库更新完成！")
        print(f"总计添加: {total_added} 条新知识")

        # 显示统计信息
        stats = vector_store.get_all_stats()
        print(f"\n📊 知识库统计:")
        for domain, stat in stats.items():
            if isinstance(stat, dict) and "total_count" in stat:
                print(f"- {domain}: {stat['total_count']} 条")

        return True

    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return False

def get_age_range_for_category(category: str) -> str:
    """根据分类获取适用年龄范围"""
    age_mapping = {
        "备孕与孕期": "孕期",
        "分娩与产后恢复": "产后0-6个月",
        "新生儿护理": "0-3个月",
        "喂养与辅食": "0-24个月",
        "生长发育与安全": "0-36个月"
    }
    return age_mapping.get(category, "通用")

def get_difficulty_for_category(category: str) -> str:
    """根据分类获取难度级别"""
    difficulty_mapping = {
        "备孕与孕期": "intermediate",
        "分娩与产后恢复": "advanced",
        "新生儿护理": "basic",
        "喂养与辅食": "intermediate",
        "生长发育与安全": "basic"
    }
    return difficulty_mapping.get(category, "basic")

def extract_keywords_from_content(content: str) -> List[str]:
    """从内容中提取关键词"""
    # 常见的母婴关键词
    common_keywords = [
        "叶酸", "孕期", "备孕", "流产", "饮食", "护肤品", "腹痛", "出血", "睡姿", "体重",
        "药物", "便秘", "产检", "顺产", "剖腹产", "恶露", "哺乳", "产后", "抑郁", "伤口",
        "新生儿", "体温", "脐带", "黄疸", "喂奶", "拍嗝", "睡眠", "衣物", "视觉", "枕头",
        "大便", "亲吻", "母乳", "配方奶", "冲奶", "辅食", "米粉", "过敏", "盐糖", "坚果",
        "身高", "体重", "头围", "出牙", "疫苗", "翻身", "爬行", "防护", "玩具", "热水",
        "洗澡", "说话", "屏幕", "发烧", "抽搐", "呼吸"
    ]

    # 提取内容中出现的关键词
    found_keywords = []
    for keyword in common_keywords:
        if keyword in content:
            found_keywords.append(keyword)

    # 如果没有找到关键词，根据内容长度添加通用标签
    if not found_keywords:
        if "孕" in content:
            found_keywords.append("孕期")
        if "宝宝" in content or "婴儿" in content:
            found_keywords.append("婴儿护理")
        if "喂" in content or "奶" in content:
            found_keywords.append("喂养")

    return found_keywords[:5]  # 最多返回5个关键词

def test_knowledge_search():
    """测试新加载的知识搜索功能"""
    print("\n🔍 测试知识搜索功能...")

    vector_store = BabyKnowledgeVectorStore()

    test_queries = [
        "备孕需要补充叶酸吗",
        "新生儿黄疸怎么办",
        "什么时候添加辅食",
        "产后恶露多久正常",
        "宝宝发烧怎么处理"
    ]

    for query in test_queries:
        print(f"\n搜索: {query}")
        results = vector_store.search(query, top_k=2)

        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['metadata']['title']}")
            print(f"     相关度: {result['score']:.3f}")
            print(f"     分类: {result['metadata'].get('category', '未知')}")
            print(f"     内容: {result['content'][:80]}...")

if __name__ == "__main__":
    print("🚀 开始加载母婴知识数据...")

    # 加载知识数据
    success = load_maternal_knowledge_from_json()

    if success:
        # 测试搜索功能
        test_knowledge_search()
        print("\n✅ 母婴知识数据加载和测试完成！")
    else:
        print("\n❌ 母婴知识数据加载失败！")