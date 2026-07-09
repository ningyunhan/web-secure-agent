import chromadb
from sentence_transformers import SentenceTransformer
from config import config
from core.models import KnowledgeEntry
from typing import List
from datetime import datetime
from utils.logger import logger


class RAGEngine:
    """知识关联引擎：管理向量数据库并提供语义检索"""

    def __init__(self):
        # 初始化本地 Embedding 模型
        logger.info("正在加载 Embedding 模型 all-MiniLM-L6-v2 ...")
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Embedding 模型加载完成")
        # 初始化 ChromaDB（持久化）
        self.client = chromadb.PersistentClient(
            path=config.CHROMA_DB_PATH
        )
        self.collection = self.client.get_or_create_collection(
            name="security_knowledge",
            metadata={"description": "网络安全知识库"}
        )
        logger.info("ChromaDB 初始化完成 | path=%s | collection=%s | 条目数=%d",
                   config.CHROMA_DB_PATH, "security_knowledge", self.collection.count())

    def _embed(self, text: str) -> List[float]:
        """生成文本的向量表示"""
        return self.embedder.encode(text).tolist()

    def add_knowledge(self, entry: KnowledgeEntry):
        """向向量库添加知识条目"""
        doc_text = f"{entry.title}\n{entry.content}"
        self.collection.add(
            ids=[entry.id],
            embeddings=[self._embed(doc_text)],
            documents=[doc_text],
            metadatas=[{
                "type": entry.type.value,
                "title": entry.title,
                "source": entry.source,
                "confidence": entry.confidence,
                "status": entry.status,
                "created_at": datetime.now().isoformat()
            }]
        )
        logger.debug("向量库写入 | id=%s | type=%s | title=%s", entry.id, entry.type.value, entry.title)

    def delete_knowledge(self, knowledge_id: str):
        """从向量库删除知识条目"""
        self.collection.delete(ids=[knowledge_id])
        logger.debug("向量库删除 | id=%s", knowledge_id)

    def search(self, query: str, top_k: int = None) -> List[dict]:
        """语义检索相关知识"""
        if top_k is None:
            top_k = config.RAG_TOP_K
        results = self.collection.query(
            query_embeddings=[self._embed(query)],
            n_results=top_k,
            where={"status": "active"}
        )
        matched = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                matched.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i]
                })
        logger.debug("向量检索 | query='%s' | top_k=%d | 命中%d条", query, top_k, len(matched))
        return matched

    def build_context(self, matched: List[dict]) -> str:
        """将检索结果构建为 Prompt 上下文"""
        if not matched:
            return ""
        context_parts = []
        for i, item in enumerate(matched, 1):
            context_parts.append(
                f"[知识{i}] 类型:{item['metadata'].get('type', '')} "
                f"标题:{item['metadata'].get('title', '')}\n"
                f"内容:{item['content']}"
            )
        return "\n\n".join(context_parts)

    def get_all_count(self) -> int:
        """获取知识库条目总数"""
        return self.collection.count()
