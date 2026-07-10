#!/usr/bin/env python3
"""
向量知识库管理脚本 — 增删改查 + 语义检索

用法：
    python kb.py init --path ./data/my_kb
    python kb.py add --path ./data/my_kb --type faq --title "标题" --content "内容"
    python kb.py search --path ./data/my_kb --query "搜索文本" --top-k 3
    python kb.py list --path ./data/my_kb
    python kb.py update --path ./data/my_kb --id <uuid> --title "新标题" --content "新内容"
    python kb.py status --path ./data/my_kb --id <uuid> --status inactive
    python kb.py delete --path ./data/my_kb --id <uuid>

也可作为模块导入：
    from kb import VectorKB
    kb = VectorKB("./data/my_kb")
    kb.add(type="faq", title="标题", content="内容")
    results = kb.search("搜索文本")

依赖：chromadb, sentence-transformers, pydantic
"""

import argparse
import json
import os
import sys
import uuid as uuid_module
from datetime import datetime
from typing import List, Optional, Dict, Any

import chromadb
from sentence_transformers import SentenceTransformer


class VectorKB:
    """向量知识库管理器"""

    def __init__(self, path: str, collection_name: str = "knowledge"):
        """
        初始化知识库

        参数:
            path: 知识库存储目录
            collection_name: ChromaDB collection 名称
        """
        os.makedirs(path, exist_ok=True)
        self.path = path
        self.json_file = os.path.join(path, "knowledge.json")

        # 加载 Embedding 模型
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

        # 初始化 ChromaDB
        db_path = os.path.join(path, "chroma_db")
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "向量知识库"}
        )

        # 加载 JSON 元数据
        self._load_store()

    def _load_store(self):
        """从 JSON 文件加载知识元数据"""
        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, "r", encoding="utf-8") as f:
                    self.store = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.store = {"entries": []}
        else:
            self.store = {"entries": []}

    def _save_store(self):
        """保存知识元数据到 JSON 文件"""
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(self.store, f, ensure_ascii=False, indent=2)

    def _embed(self, text: str) -> List[float]:
        """生成文本向量"""
        return self.embedder.encode(text).tolist()

    def add(
        self, type: str, title: str, content: str,
        tags: List[str] = None
    ) -> dict:
        """
        添加知识条目（热更新，立即生效）

        返回: {"id": "uuid", "message": "添加成功"}
        """
        entry_id = str(uuid_module.uuid4())
        entry = {
            "id": entry_id,
            "type": type,
            "title": title,
            "content": content,
            "source": "manual",
            "confidence": 1.0,
            "status": "active",
            "tags": tags or [],
            "created_at": datetime.now().isoformat()
        }

        # 写 JSON
        self.store["entries"].append(entry)
        self._save_store()

        # 写 ChromaDB
        doc_text = f"{title}\n{content}"
        self.collection.add(
            ids=[entry_id],
            embeddings=[self._embed(doc_text)],
            documents=[doc_text],
            metadatas=[{
                "type": type,
                "title": title,
                "source": "manual",
                "confidence": 1.0,
                "status": "active",
                "created_at": entry["created_at"]
            }]
        )

        return {"id": entry_id, "message": "添加成功，已立即生效"}

    def search(
        self, query: str, top_k: int = 3,
        threshold: float = 1.5, fetch_k: int = 10
    ) -> List[dict]:
        """
        语义检索（带距离阈值过滤和相似度评分）

        参数:
            query: 检索文本
            top_k: 返回条数
            threshold: 距离阈值，超过的不返回
            fetch_k: 候选数（先取 fetch_k 条再过滤）

        返回: [{"title":"...", "content":"...", "similarity":87, ...}, ...]
              按相似度从高到低排序
        """
        results = self.collection.query(
            query_embeddings=[self._embed(query)],
            n_results=fetch_k,
            where={"status": "active"}
        )

        matched = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                distance = results["distances"][0][i]
                if distance > threshold:
                    continue
                similarity = max(0, round(100 * (1 - distance / threshold)))
                meta = results["metadatas"][0][i]
                matched.append({
                    "id": results["ids"][0][i],
                    "title": meta.get("title", ""),
                    "content": doc,
                    "metadata": meta,
                    "distance": round(distance, 4),
                    "similarity": similarity
                })
                if len(matched) >= top_k:
                    break

        matched.sort(key=lambda x: x["similarity"], reverse=True)
        return matched

    def update(
        self, entry_id: str, type: str, title: str,
        content: str, tags: List[str] = None
    ) -> dict:
        """更新知识条目（热更新，先删后加）"""
        for e in self.store["entries"]:
            if e["id"] == entry_id:
                e["type"] = type
                e["title"] = title
                e["content"] = content
                e["tags"] = tags or []
                self._save_store()

                # 先删后加更新 ChromaDB
                try:
                    self.collection.delete(ids=[entry_id])
                except Exception:
                    pass
                doc_text = f"{title}\n{content}"
                self.collection.add(
                    ids=[entry_id],
                    embeddings=[self._embed(doc_text)],
                    documents=[doc_text],
                    metadatas=[{
                        "type": type,
                        "title": title,
                        "source": e.get("source", "manual"),
                        "confidence": e.get("confidence", 1.0),
                        "status": e.get("status", "active"),
                        "created_at": e.get("created_at", "")
                    }]
                )
                return {"id": entry_id, "message": "更新成功，已立即生效"}

        return {"error": "未找到该条目"}

    def update_status(self, entry_id: str, status: str) -> dict:
        """更新状态（软删除/恢复，先删后加更新 metadata）"""
        if status not in ("active", "inactive"):
            return {"error": "status 必须是 active 或 inactive"}

        for e in self.store["entries"]:
            if e["id"] == entry_id:
                old_status = e.get("status", "active")
                e["status"] = status
                self._save_store()

                try:
                    self.collection.delete(ids=[entry_id])
                except Exception:
                    pass
                doc_text = f"{e['title']}\n{e['content']}"
                self.collection.add(
                    ids=[entry_id],
                    embeddings=[self._embed(doc_text)],
                    documents=[doc_text],
                    metadatas=[{
                        "type": e["type"],
                        "title": e["title"],
                        "source": e.get("source", "manual"),
                        "confidence": e.get("confidence", 1.0),
                        "status": status,
                        "created_at": e.get("created_at", "")
                    }]
                )
                action = "禁用" if status == "inactive" else "启用"
                return {"id": entry_id, "message": f"{action}成功，已立即生效"}

        return {"error": "未找到该条目"}

    def delete(self, entry_id: str) -> dict:
        """硬删除知识条目"""
        self.store["entries"] = [
            e for e in self.store["entries"] if e["id"] != entry_id
        ]
        self._save_store()
        try:
            self.collection.delete(ids=[entry_id])
        except Exception:
            pass
        return {"id": entry_id, "message": "删除成功"}

    def list_all(self, type_filter: Optional[str] = None) -> List[dict]:
        """列出全部知识条目，支持按类型筛选"""
        entries = self.store["entries"]
        if type_filter and type_filter != "all":
            entries = [e for e in entries if e["type"] == type_filter]
        return entries

    def get_by_id(self, entry_id: str) -> Optional[dict]:
        """根据 ID 获取单条知识"""
        for e in self.store["entries"]:
            if e["id"] == entry_id:
                return e
        return None

    def count(self) -> int:
        """获取知识条目总数"""
        return len(self.store["entries"])


def main():
    parser = argparse.ArgumentParser(description="向量知识库管理")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # init
    p_init = subparsers.add_parser("init", help="初始化知识库")
    p_init.add_argument("--path", required=True, help="知识库存储目录")

    # add
    p_add = subparsers.add_parser("add", help="添加知识条目")
    p_add.add_argument("--path", required=True)
    p_add.add_argument("--type", required=True, help="知识类型")
    p_add.add_argument("--title", required=True, help="标题")
    p_add.add_argument("--content", required=True, help="内容")
    p_add.add_argument("--tags", default="", help="标签（逗号分隔）")

    # search
    p_search = subparsers.add_parser("search", help="语义检索")
    p_search.add_argument("--path", required=True)
    p_search.add_argument("--query", required=True, help="检索文本")
    p_search.add_argument("--top-k", type=int, default=3, help="返回条数")
    p_search.add_argument("--threshold", type=float, default=1.5, help="距离阈值")
    p_search.add_argument("--fetch-k", type=int, default=10, help="候选数")

    # list
    p_list = subparsers.add_parser("list", help="列出全部知识")
    p_list.add_argument("--path", required=True)
    p_list.add_argument("--type", default=None, help="按类型筛选")

    # update
    p_update = subparsers.add_parser("update", help="更新知识条目")
    p_update.add_argument("--path", required=True)
    p_update.add_argument("--id", required=True)
    p_update.add_argument("--type", required=True)
    p_update.add_argument("--title", required=True)
    p_update.add_argument("--content", required=True)
    p_update.add_argument("--tags", default="")

    # status
    p_status = subparsers.add_parser("status", help="更新状态")
    p_status.add_argument("--path", required=True)
    p_status.add_argument("--id", required=True)
    p_status.add_argument("--status", required=True, choices=["active", "inactive"])

    # delete
    p_delete = subparsers.add_parser("delete", help="删除知识条目")
    p_delete.add_argument("--path", required=True)
    p_delete.add_argument("--id", required=True)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # init 命令不需要加载 Embedding 模型
    if args.command == "init":
        os.makedirs(args.path, exist_ok=True)
        # 创建空的 JSON 文件
        json_file = os.path.join(args.path, "knowledge.json")
        if not os.path.exists(json_file):
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump({"entries": []}, f, ensure_ascii=False, indent=2)
        print(json.dumps({"message": f"知识库已初始化: {args.path}"}, ensure_ascii=False))
        return

    # 其他命令需要初始化 VectorKB
    kb = VectorKB(args.path)

    if args.command == "add":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []
        result = kb.add(type=args.type, title=args.title, content=args.content, tags=tags)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "search":
        results = kb.search(
            query=args.query, top_k=args.top_k,
            threshold=args.threshold, fetch_k=args.fetch_k
        )
        print(json.dumps(results, ensure_ascii=False, indent=2))

    elif args.command == "list":
        results = kb.list_all(type_filter=args.type)
        print(json.dumps(results, ensure_ascii=False, indent=2))

    elif args.command == "update":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []
        result = kb.update(
            entry_id=args.id, type=args.type,
            title=args.title, content=args.content, tags=tags
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "status":
        result = kb.update_status(entry_id=args.id, status=args.status)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "delete":
        result = kb.delete(entry_id=args.id)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
