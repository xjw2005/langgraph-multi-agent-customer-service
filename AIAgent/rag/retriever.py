# -*- coding: utf-8 -*-
# RAG检索器 - 智能母婴知识检索系统
# 提供多策略检索、重排序和上下文优化功能

import sys
import os

from typing import Dict, List, Any, Optional, Tuple
from rag.vector_store import BabyKnowledgeVectorStore
import re
import jieba
from collections import Counter
import math

class BabyKnowledgeRetriever:
    """
    母婴知识智能检索器

    功能：
    1. 混合检索（向量 + 关键词）
    2. 基于用户画像的个性化检索
    3. 结果重排序和去重
    4. 上下文相关性优化
    """

    def __init__(self, vector_store: BabyKnowledgeVectorStore):
        """
        初始化检索器

        Args:
            vector_store: 向量存储实例
        """
        self.vector_store = vector_store

        # 月龄关键词映射
        self.age_keywords = {
            "newborn": ["新生儿", "0-1个月", "刚出生", "初生"],
            "infant": ["婴儿", "1-6个月", "小婴儿", "哺乳期"],
            "mobile": ["6-12个月", "会爬", "会坐", "辅食期"],
            "toddler": ["幼儿", "1-2岁", "学步期", "断奶"],
            "preschool": ["学龄前", "2-5岁", "幼儿园", "大孩子"]
        }

        # 领域关键词
        self.domain_keywords = {
            "baby_care": ["护理", "洗澡", "换尿布", "清洁", "保暖", "皮肤"],
            "nutrition": ["喂养", "奶粉", "母乳", "辅食", "营养", "维生素"],
            "development": ["发育", "成长", "里程碑", "智力", "运动", "语言"],
            "products": ["产品", "品牌", "选择", "推荐", "质量", "安全"],
            "safety": ["安全", "防护", "危险", "预防", "急救", "注意"]
        }

        # 权重配置
        self.weights = {
            "vector_similarity": 0.6,    # 向量相似度权重
            "keyword_match": 0.2,        # 关键词匹配权重
            "age_relevance": 0.1,        # 年龄相关性权重
            "authority": 0.1             # 权威性权重
        }

        print("🔍 母婴知识检索器初始化完成")

    def retrieve(self, query: str, domain: Optional[str] = None,
                age_months: Optional[int] = None, top_k: int = 5,
                user_profile: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        执行智能检索

        Args:
            query: 检索查询
            domain: 限定领域
            age_months: 宝宝月龄
            top_k: 返回结果数量
            user_profile: 用户画像

        Returns:
            检索结果列表
        """
        try:
            print(f"🔍 开始检索: {query}")

            # 步骤1: 查询预处理和扩展
            processed_query = self._preprocess_query(query, age_months, user_profile)

            # 步骤2: 多策略检索
            retrieval_results = self._multi_strategy_retrieval(
                processed_query, domain, age_months, top_k * 2  # 检索更多候选
            )

            # 步骤3: 结果重排序
            reranked_results = self._rerank_results(
                retrieval_results, query, age_months, user_profile
            )

            # 步骤4: 去重和最终筛选
            final_results = self._deduplicate_and_filter(reranked_results, top_k)

            print(f"✅ 检索完成，返回 {len(final_results)} 条结果")
            return final_results

        except Exception as e:
            print(f"❌ 检索失败: {e}")
            return []

    def _preprocess_query(self, query: str, age_months: Optional[int] = None,
                         user_profile: Optional[Dict] = None) -> Dict[str, Any]:
        """
        查询预处理和扩展

        Args:
            query: 原始查询
            age_months: 宝宝月龄
            user_profile: 用户画像

        Returns:
            处理后的查询信息
        """
        # 基础分词
        keywords = list(jieba.cut(query))
        keywords = [kw.strip() for kw in keywords if len(kw.strip()) > 1]

        # 提取关键信息
        extracted_info = {
            "original_query": query,
            "keywords": keywords,
            "age_mentions": self._extract_age_mentions(query),
            "domain_hints": self._extract_domain_hints(query),
            "urgency_level": self._detect_urgency(query),
            "question_type": self._classify_question_type(query)
        }

        # 查询扩展
        expanded_query = self._expand_query(query, age_months, user_profile)

        return {
            **extracted_info,
            "expanded_query": expanded_query.get("expanded_query", query),  # 提取字符串而不是字典
            "search_terms": keywords + expanded_query.get("additional_terms", [])
        }

    def _extract_age_mentions(self, query: str) -> List[str]:
        """提取年龄相关信息"""
        age_patterns = [
            r'(\d+)个?月',
            r'(\d+)岁',
            r'新生儿',
            r'婴儿',
            r'幼儿',
            r'宝宝'
        ]

        age_mentions = []
        for pattern in age_patterns:
            matches = re.findall(pattern, query)
            age_mentions.extend(matches)

        return age_mentions

    def _extract_domain_hints(self, query: str) -> List[str]:
        """提取领域提示"""
        domain_hints = []

        for domain, keywords in self.domain_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    domain_hints.append(domain)
                    break

        return list(set(domain_hints))

    def _detect_urgency(self, query: str) -> str:
        """检测紧急程度"""
        urgent_words = ["急", "紧急", "马上", "立即", "快", "赶紧"]
        if any(word in query for word in urgent_words):
            return "high"
        elif any(word in query for word in ["尽快", "着急", "等不及"]):
            return "medium"
        else:
            return "low"

    def _classify_question_type(self, query: str) -> str:
        """分类问题类型"""
        if any(word in query for word in ["推荐", "选择", "哪个好", "买什么"]):
            return "recommendation"
        elif any(word in query for word in ["怎么", "如何", "方法", "步骤"]):
            return "how_to"
        elif any(word in query for word in ["为什么", "原因", "什么是"]):
            return "explanation"
        elif any(word in query for word in ["对比", "比较", "区别"]):
            return "comparison"
        elif any(word in query for word in ["正常吗", "有问题吗", "担心"]):
            return "concern"
        else:
            return "general"

    def _expand_query(self, query: str, age_months: Optional[int] = None,
                     user_profile: Optional[Dict] = None) -> Dict[str, Any]:
        """
        查询扩展

        Args:
            query: 原始查询
            age_months: 宝宝月龄
            user_profile: 用户画像

        Returns:
            扩展后的查询信息
        """
        additional_terms = []

        # 基于月龄扩展
        if age_months is not None:
            age_stage = self._get_age_stage(age_months)
            if age_stage in self.age_keywords:
                additional_terms.extend(self.age_keywords[age_stage])

        # 基于用户画像扩展
        if user_profile:
            # 添加喂养方式相关词汇
            feeding_type = user_profile.get("feeding_type", "")
            if feeding_type:
                additional_terms.append(feeding_type)

            # 添加关注点相关词汇
            concerns = user_profile.get("concerns", [])
            additional_terms.extend(concerns)

            # 添加偏好品牌（如果相关）
            preferred_brands = user_profile.get("preferred_brands", [])
            if any(brand in query for brand in preferred_brands):
                additional_terms.extend(preferred_brands)

        return {
            "additional_terms": list(set(additional_terms)),
            "expanded_query": query + " " + " ".join(additional_terms)
        }

    def _multi_strategy_retrieval(self, processed_query: Dict, domain: Optional[str],
                                 age_months: Optional[int], candidate_count: int) -> List[Dict[str, Any]]:
        """
        多策略检索

        Args:
            processed_query: 处理后的查询
            domain: 限定领域
            age_months: 宝宝月龄
            candidate_count: 候选结果数量

        Returns:
            检索结果
        """
        all_results = []

        # 策略1: 向量相似度检索
        vector_results = self.vector_store.search(
            query=processed_query["expanded_query"],
            domain=domain,
            age_months=age_months,
            top_k=candidate_count,
            min_score=0.3
        )

        for result in vector_results:
            result["retrieval_method"] = "vector"
            all_results.append(result)

        # 策略2: 关键词精确匹配
        keyword_results = self._keyword_search(
            processed_query["keywords"], domain, candidate_count // 2
        )

        for result in keyword_results:
            result["retrieval_method"] = "keyword"
            all_results.append(result)

        # 去重（基于ID）
        seen_ids = set()
        unique_results = []
        for result in all_results:
            if result["id"] not in seen_ids:
                seen_ids.add(result["id"])
                unique_results.append(result)

        return unique_results

    def _keyword_search(self, keywords: List[str], domain: Optional[str], top_k: int) -> List[Dict[str, Any]]:
        """
        关键词搜索

        Args:
            keywords: 关键词列表
            domain: 限定领域
            top_k: 返回数量

        Returns:
            搜索结果
        """
        # 构建关键词查询
        keyword_query = " ".join(keywords)

        # 使用向量存储的搜索功能
        results = self.vector_store.search(
            query=keyword_query,
            domain=domain,
            top_k=top_k,
            min_score=0.2
        )

        # 计算关键词匹配分数
        for result in results:
            content = result["content"].lower()
            match_count = sum(1 for kw in keywords if kw.lower() in content)
            result["keyword_match_score"] = match_count / len(keywords) if keywords else 0

        return results

    def _rerank_results(self, results: List[Dict[str, Any]], original_query: str,
                       age_months: Optional[int], user_profile: Optional[Dict]) -> List[Dict[str, Any]]:
        """
        结果重排序

        Args:
            results: 原始结果
            original_query: 原始查询
            age_months: 宝宝月龄
            user_profile: 用户画像

        Returns:
            重排序后的结果
        """
        for result in results:
            # 计算综合分数
            scores = {
                "vector_similarity": result.get("score", 0.0),
                "keyword_match": result.get("keyword_match_score", 0.0),
                "age_relevance": self._calculate_age_relevance(result, age_months),
                "authority": self._calculate_authority_score(result)
            }

            # 加权计算最终分数
            final_score = sum(
                scores[factor] * weight
                for factor, weight in self.weights.items()
            )

            result["final_score"] = final_score
            result["score_breakdown"] = scores

        # 按最终分数排序
        results.sort(key=lambda x: x["final_score"], reverse=True)
        return results

    def _calculate_age_relevance(self, result: Dict, age_months: Optional[int]) -> float:
        """
        计算年龄相关性分数

        Args:
            result: 检索结果
            age_months: 宝宝月龄

        Returns:
            年龄相关性分数 (0-1)
        """
        if age_months is None:
            return 0.5  # 中性分数

        metadata = result.get("metadata", {})
        age_range = metadata.get("age_range", "通用")

        if age_range == "通用":
            return 0.7

        # 解析年龄范围
        if "-" in age_range:
            try:
                parts = age_range.replace("个月", "").replace("岁", "").split("-")
                if len(parts) == 2:
                    min_age = int(parts[0])
                    max_age = int(parts[1])

                    # 如果第二个数字可能是岁，转换为月
                    if max_age <= 5 and "岁" in age_range:
                        max_age *= 12

                    if min_age <= age_months <= max_age:
                        return 1.0
                    else:
                        # 计算距离相关性
                        distance = min(abs(age_months - min_age), abs(age_months - max_age))
                        return max(0.0, 1.0 - distance / 12.0)  # 距离每12个月减少1.0分
            except:
                pass

        return 0.3  # 默认低相关性

    def _calculate_authority_score(self, result: Dict) -> float:
        """
        计算权威性分数

        Args:
            result: 检索结果

        Returns:
            权威性分数 (0-1)
        """
        metadata = result.get("metadata", {})
        authority = metadata.get("authority", "专业资料")

        authority_scores = {
            "医学专家": 1.0,
            "儿科医生": 1.0,
            "营养师": 0.9,
            "育儿专家": 0.8,
            "专业机构": 0.8,
            "权威指南": 0.9,
            "专业资料": 0.7,
            "经验分享": 0.5,
            "用户贡献": 0.3
        }

        return authority_scores.get(authority, 0.5)

    def _deduplicate_and_filter(self, results: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """
        去重和最终筛选

        Args:
            results: 排序后的结果
            top_k: 最终返回数量

        Returns:
            最终结果
        """
        # 基于内容相似度去重
        final_results = []
        seen_contents = []

        for result in results:
            content = result["content"]

            # 检查是否与已有内容过于相似
            is_duplicate = False
            for seen_content in seen_contents:
                similarity = self._calculate_content_similarity(content, seen_content)
                if similarity > 0.8:  # 相似度阈值
                    is_duplicate = True
                    break

            if not is_duplicate:
                final_results.append(result)
                seen_contents.append(content)

                if len(final_results) >= top_k:
                    break

        return final_results

    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """
        计算内容相似度

        Args:
            content1: 内容1
            content2: 内容2

        Returns:
            相似度分数 (0-1)
        """
        # 简单的基于词汇重叠的相似度计算
        words1 = set(jieba.cut(content1))
        words2 = set(jieba.cut(content2))

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _get_age_stage(self, age_months: int) -> str:
        """根据月龄获取发育阶段"""
        if age_months <= 1:
            return "newborn"
        elif age_months <= 6:
            return "infant"
        elif age_months <= 12:
            return "mobile"
        elif age_months <= 24:
            return "toddler"
        else:
            return "preschool"

    def get_retrieval_stats(self) -> Dict[str, Any]:
        """获取检索统计信息"""
        return {
            "vector_store_stats": self.vector_store.get_all_stats(),
            "weights": self.weights,
            "supported_domains": list(self.domain_keywords.keys()),
            "age_stages": list(self.age_keywords.keys())
        }