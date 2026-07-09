from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from utils.logger import logger

router = APIRouter()

_km = None


def set_km(km):
    global _km
    _km = km


class KnowledgeCreate(BaseModel):
    type: str
    title: str
    content: str
    tags: List[str] = []


class KnowledgeStatusUpdate(BaseModel):
    status: str  # active / inactive


@router.get("/knowledge")
async def list_knowledge(type: Optional[str] = Query(None)):
    """获取知识列表，支持按类型筛选"""
    entries = _km.list_all(type)
    logger.info("API GET /knowledge | filter=%s | 返回%d条", type, len(entries))
    return entries


@router.post("/knowledge")
async def add_knowledge(req: KnowledgeCreate):
    """添加知识条目（热更新，立即生效）"""
    logger.info("API POST /knowledge | type=%s | title=%s", req.type, req.title)
    entry = _km.add(
        type=req.type,
        title=req.title,
        content=req.content,
        tags=req.tags
    )
    return {"id": entry.id, "message": "添加成功，已立即生效"}


@router.delete("/knowledge/{knowledge_id}")
async def delete_knowledge(knowledge_id: str):
    """删除知识条目（硬删除）"""
    logger.info("API DELETE /knowledge/%s", knowledge_id)
    _km.delete(knowledge_id)
    return {"message": "删除成功"}


@router.patch("/knowledge/{knowledge_id}/status")
async def update_knowledge_status(knowledge_id: str, req: KnowledgeStatusUpdate):
    """更新知识条目状态（软删除/恢复）"""
    logger.info("API PATCH /knowledge/%s/status | target_status=%s", knowledge_id, req.status)
    success = _km.update_status(knowledge_id, req.status)
    if not success:
        raise HTTPException(status_code=404, detail="知识条目不存在")
    action = "禁用" if req.status == "inactive" else "启用"
    return {"message": f"{action}成功，已立即生效"}
