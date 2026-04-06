# RAG向量存储 - 母婴知识库向量数据库
# 基于Chroma的专业母婴知识向量存储和检索系统

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import Dict, List, Any, Optional
import json
import os
from pathlib import Path
import hashlib
from langchain_openai import OpenAIEmbeddings
import numpy as np
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class OpenAIEmbeddingFunction:
    """OpenAI嵌入函数适配器"""

    def __init__(self):
        try:
            # 使用SiliconFlow的嵌入模型
            self.embeddings = OpenAIEmbeddings(
                model=os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002"),
                openai_api_key=os.getenv("EMBEDDING_API_KEY"),
                openai_api_base=os.getenv("EMBEDDING_BASE_URL", "https://api.siliconflow.cn/v1")
            )
            print("使用SiliconFlow嵌入模型")
        except Exception as e:
            print(f"警告: 无法初始化嵌入模型: {e}")
            print("使用默认嵌入函数")
            self.embeddings = None

    def name(self) -> str:
        """返回嵌入函数名称"""
        return "openai_embedding_function"

    def __call__(self, input: List[str]) -> List[List[float]]:
        """嵌入函数调用接口"""
        try:
            if self.embeddings:
                embeddings = self.embeddings.embed_documents(input)
                return embeddings
            else:
                # 使用简单的哈希向量作为fallback
                return self._simple_embedding(input)
        except Exception as e:
            print(f"嵌入生成失败: {e}")
            return self._simple_embedding(input)

    def _simple_embedding(self, texts: List[str]) -> List[List[float]]:
        """简单的哈希嵌入作为fallback"""
        embeddings = []
        for text in texts:
            # 使用文本哈希生成简单向量
            hash_val = hash(text)
            vector = [float((hash_val >> i) & 1) for i in range(384)]  # 384维向量
            embeddings.append(vector)
        return embeddings

class BabyKnowledgeVectorStore:
    """
    母婴知识向量存储系统

    功能：
    1. 存储和管理母婴专业知识向量
    2. 支持按领域、月龄、权威性检索
    3. 知识更新和版本管理
    4. 相似度计算和排序
    """

    def __init__(self, persist_directory: str = "data/chroma_db"):
        """
        初始化向量存储

        Args:
            persist_directory: 持久化存储目录
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # 初始化Chroma客户端
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # 初始化嵌入模型
        self.embedding_function = OpenAIEmbeddingFunction()

        # 知识库集合
        self.collections = {
            "baby_care": None,      # 婴儿护理
            "nutrition": None,      # 营养喂养
            "development": None,    # 发育成长
            "products": None,       # 产品知识
            "safety": None          # 安全指导
        }

        # 初始化集合
        self._initialize_collections()

        print(f"母婴知识向量存储初始化完成 - 存储路径: {self.persist_directory}")

    def _initialize_collections(self):
        """初始化各个知识领域的集合"""
        for domain, _ in self.collections.items():
            collection_name = f"baby_knowledge_{domain}"
            try:
                # 尝试获取现有集合
                collection = self.client.get_collection(name=collection_name)
                print(f"加载现有集合: {domain} - {collection.count()}条知识")
            except Exception as get_error:
                try:
                    # 创建新集合
                    collection = self.client.create_collection(
                        name=collection_name,
                        embedding_function=self.embedding_function,
                        metadata={"domain": domain, "version": "1.0"}
                    )
                    print(f"创建新集合: {domain}")
                except Exception as create_error:
                    if "already exists" in str(create_error):
                        # 集合已存在，直接获取
                        collection = self.client.get_collection(name=collection_name)
                        print(f"使用现有集合: {domain}")
                    else:
                        print(f"创建集合失败: {domain} - {create_error}")
                        continue

            self.collections[domain] = collection

    def _embedding_function(self, input: List[str]) -> List[List[float]]:
        """嵌入函数包装器"""
        try:
            embeddings = self.embeddings.embed_documents(input)
            return embeddings
        except Exception as e:
            print(f"❌ 嵌入生成失败: {e}")
            # 返回零向量作为fallback
            return [[0.0] * 1536 for _ in input]

    def add_knowledge(self, domain: str, knowledge_items: List[Dict[str, Any]]) -> bool:
        """
        添加知识到向量存储

        Args:
            domain: 知识领域
            knowledge_items: 知识条目列表

        Returns:
            是否成功添加
        """
        if domain not in self.collections:
            print(f"❌ 未知领域: {domain}")
            return False

        collection = self.collections[domain]

        try:
            # 准备数据
            documents = []
            metadatas = []
            ids = []

            for item in knowledge_items:
                # 生成唯一ID
                content_hash = hashlib.md5(item["content"].encode()).hexdigest()
                item_id = f"{domain}_{content_hash[:8]}"

                documents.append(item["content"])
                metadatas.append({
                    "source": item.get("source", "未知来源"),
                    "title": item.get("title", ""),
                    "domain": domain,
                    "age_range": item.get("age_range", "通用"),
                    "authority": item.get("authority", "专业资料"),
                    "keywords": json.dumps(item.get("keywords", []), ensure_ascii=False),
                    "last_updated": item.get("last_updated", "2024-12-19"),
                    "difficulty": item.get("difficulty", "basic"),
                    "content_type": item.get("content_type", "advice")
                })
                ids.append(item_id)

            # 批量添加到集合
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

            print(f"✅ 成功添加 {len(knowledge_items)} 条{domain}知识")
            return True

        except Exception as e:
            print(f"❌ 添加知识失败: {e}")
            return False

    def search(self, query: str, domain: Optional[str] = None,
               age_months: Optional[int] = None, top_k: int = 5,
               min_score: float = 0.0) -> List[Dict[str, Any]]:
        """
        搜索相关知识

        Args:
            query: 搜索查询
            domain: 限定搜索领域
            age_months: 宝宝月龄
            top_k: 返回结果数量
            min_score: 最小相似度分数

        Returns:
            搜索结果列表
        """
        try:
            all_results = []

            # 确定搜索范围
            search_domains = [domain] if domain and domain in self.collections else list(self.collections.keys())

            for search_domain in search_domains:
                collection = self.collections[search_domain]

                # 构建查询过滤器
                where_filter = {"domain": search_domain}

                # 添加月龄过滤（如果指定）
                if age_months is not None:
                    # 这里可以添加更复杂的月龄匹配逻辑
                    pass

                # 执行搜索
                collection_count = collection.count()
                if collection_count == 0:
                    continue  # 跳过空集合

                n_results = min(top_k, collection_count)
                if n_results <= 0:
                    continue  # 确保n_results大于0

                results = collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where_filter if where_filter else None
                )

                # 处理结果
                if results["documents"] and results["documents"][0]:
                    for i, doc in enumerate(results["documents"][0]):
                        score = 1 - results["distances"][0][i]  # 转换为相似度分数

                        if score >= min_score:
                            all_results.append({
                                "content": doc,
                                "score": score,
                                "metadata": results["metadatas"][0][i],
                                "id": results["ids"][0][i],
                                "domain": search_domain
                            })

            # 按分数排序并返回top_k
            all_results.sort(key=lambda x: x["score"], reverse=True)
            return all_results[:top_k]

        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            return []

    def get_domain_stats(self, domain: str) -> Dict[str, Any]:
        """
        获取领域统计信息

        Args:
            domain: 知识领域

        Returns:
            统计信息
        """
        if domain not in self.collections:
            return {}

        collection = self.collections[domain]

        try:
            count = collection.count()

            # 获取样本数据分析
            if count > 0:
                sample_results = collection.get(limit=min(100, count))

                # 分析权威性分布
                authorities = [meta.get("authority", "未知") for meta in sample_results["metadatas"]]
                authority_dist = {}
                for auth in authorities:
                    authority_dist[auth] = authority_dist.get(auth, 0) + 1

                # 分析年龄范围分布
                age_ranges = [meta.get("age_range", "通用") for meta in sample_results["metadatas"]]
                age_dist = {}
                for age in age_ranges:
                    age_dist[age] = age_dist.get(age, 0) + 1

                return {
                    "total_count": count,
                    "authority_distribution": authority_dist,
                    "age_range_distribution": age_dist,
                    "last_updated": max([meta.get("last_updated", "2024-01-01") for meta in sample_results["metadatas"]])
                }
            else:
                return {"total_count": 0}

        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")
            return {"error": str(e)}

    def update_knowledge(self, domain: str, knowledge_id: str, updated_content: str, updated_metadata: Dict) -> bool:
        """
        更新知识条目

        Args:
            domain: 知识领域
            knowledge_id: 知识ID
            updated_content: 更新后的内容
            updated_metadata: 更新后的元数据

        Returns:
            是否成功更新
        """
        if domain not in self.collections:
            return False

        collection = self.collections[domain]

        try:
            # 删除旧条目
            collection.delete(ids=[knowledge_id])

            # 添加新条目
            collection.add(
                documents=[updated_content],
                metadatas=[updated_metadata],
                ids=[knowledge_id]
            )

            print(f"✅ 成功更新知识: {knowledge_id}")
            return True

        except Exception as e:
            print(f"❌ 更新知识失败: {e}")
            return False

    def delete_knowledge(self, domain: str, knowledge_id: str) -> bool:
        """
        删除知识条目

        Args:
            domain: 知识领域
            knowledge_id: 知识ID

        Returns:
            是否成功删除
        """
        if domain not in self.collections:
            return False

        collection = self.collections[domain]

        try:
            collection.delete(ids=[knowledge_id])
            print(f"✅ 成功删除知识: {knowledge_id}")
            return True

        except Exception as e:
            print(f"❌ 删除知识失败: {e}")
            return False

    def get_similar_knowledge(self, content: str, domain: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        获取相似知识

        Args:
            content: 参考内容
            domain: 搜索领域
            top_k: 返回数量

        Returns:
            相似知识列表
        """
        return self.search(content, domain=domain, top_k=top_k, min_score=0.7)

    def export_knowledge(self, domain: str, output_path: str) -> bool:
        """
        导出知识到文件

        Args:
            domain: 知识领域
            output_path: 输出文件路径

        Returns:
            是否成功导出
        """
        if domain not in self.collections:
            return False

        collection = self.collections[domain]

        try:
            # 获取所有数据
            all_data = collection.get()

            export_data = {
                "domain": domain,
                "count": len(all_data["documents"]),
                "exported_at": "2024-12-19",
                "knowledge_items": []
            }

            for i, doc in enumerate(all_data["documents"]):
                export_data["knowledge_items"].append({
                    "id": all_data["ids"][i],
                    "content": doc,
                    "metadata": all_data["metadatas"][i]
                })

            # 保存到文件
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            print(f"✅ 成功导出 {domain} 知识到 {output_path}")
            return True

        except Exception as e:
            print(f"❌ 导出失败: {e}")
            return False

    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有领域的统计信息"""
        stats = {}
        total_count = 0

        for domain in self.collections.keys():
            domain_stats = self.get_domain_stats(domain)
            stats[domain] = domain_stats
            total_count += domain_stats.get("total_count", 0)

        stats["total_knowledge_count"] = total_count
        stats["active_domains"] = len([d for d in stats.values() if isinstance(d, dict) and d.get("total_count", 0) > 0])

        return stats

    def reset_domain(self, domain: str) -> bool:
        """
        重置领域数据

        Args:
            domain: 要重置的领域

        Returns:
            是否成功重置
        """
        if domain not in self.collections:
            return False

        try:
            # 删除现有集合
            self.client.delete_collection(f"baby_knowledge_{domain}")

            # 重新创建集合
            collection = self.client.create_collection(
                name=f"baby_knowledge_{domain}",
                embedding_function=self._embedding_function,
                metadata={"domain": domain, "version": "1.0"}
            )

            self.collections[domain] = collection
            print(f"✅ 成功重置 {domain} 领域")
            return True

        except Exception as e:
            print(f"❌ 重置失败: {e}")
            return False