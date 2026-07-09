import json
import uuid
from typing import List, Optional
from core.models import KnowledgeEntry, KnowledgeType
from core.rag_engine import RAGEngine
from config import config
from utils.logger import logger


class KnowledgeManager:
    """知识管理服务：CRUD + 热更新"""

    def __init__(self, rag_engine: RAGEngine):
        self.rag = rag_engine
        self._load_store()

    def _load_store(self):
        """从 JSON 文件加载知识元数据"""
        try:
            with open(config.KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
                self.store: dict = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.store = {"entries": []}

    def _save_store(self):
        """保存知识元数据到 JSON 文件"""
        with open(config.KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.store, f, ensure_ascii=False, indent=2)

    def add(
        self, type: str, title: str, content: str,
        source: str = "manual", tags: List[str] = None
    ) -> KnowledgeEntry:
        """添加知识条目（热更新，立即生效）"""
        entry = KnowledgeEntry(
            id=str(uuid.uuid4()),
            type=KnowledgeType(type),
            title=title,
            content=content,
            source=source,
            tags=tags or []
        )
        # 写入 JSON 元数据
        self.store["entries"].append(entry.model_dump())
        self._save_store()
        # 写入 ChromaDB 向量库（立即生效）
        self.rag.add_knowledge(entry)
        logger.info("知识新增 | id=%s | type=%s | title=%s | source=%s", entry.id, type, title, source)
        return entry

    def delete(self, knowledge_id: str) -> bool:
        """删除知识条目（硬删除，立即生效）"""
        self.store["entries"] = [
            e for e in self.store["entries"]
            if e["id"] != knowledge_id
        ]
        self._save_store()
        self.rag.delete_knowledge(knowledge_id)
        logger.info("知识删除 | id=%s", knowledge_id)
        return True

    def update_status(self, knowledge_id: str, status: str) -> bool:
        """更新知识条目状态（软删除/恢复，立即生效）"""
        for e in self.store["entries"]:
            if e["id"] == knowledge_id:
                old_status = e.get("status", "active")
                e["status"] = status
                self._save_store()
                # 先删后加，更新 ChromaDB 中的 metadata
                self.rag.delete_knowledge(knowledge_id)
                entry = KnowledgeEntry(**e)
                self.rag.add_knowledge(entry)
                logger.info("状态变更 | id=%s | %s -> %s | title=%s", knowledge_id, old_status, status, e.get("title", ""))
                return True
        logger.warning("状态变更失败：未找到 | id=%s", knowledge_id)
        return False

    def list_all(self, type_filter: Optional[str] = None) -> List[dict]:
        """列出所有知识条目，支持按类型筛选"""
        entries = self.store["entries"]
        if type_filter and type_filter != "all":
            entries = [e for e in entries if e["type"] == type_filter]
        return entries

    def get_by_id(self, knowledge_id: str) -> Optional[dict]:
        """根据ID获取知识条目"""
        for e in self.store["entries"]:
            if e["id"] == knowledge_id:
                return e
        return None

    def init_from_json(self):
        """从 JSON 文件批量初始化知识库到 ChromaDB"""
        count = 0
        for entry_data in self.store["entries"]:
            entry = KnowledgeEntry(**entry_data)
            try:
                self.rag.add_knowledge(entry)
                count += 1
            except Exception as e:
                logger.debug("跳过已存在的知识条目 | id=%s | error=%s", entry.id, e)
        logger.info("知识库初始化完成 | 成功写入 %d/%d 条", count, len(self.store["entries"]))
