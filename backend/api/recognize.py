from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from utils.logger import logger

router = APIRouter()

# 全局引擎实例，由 main.py 注入
_engine = None


def set_engine(engine):
    global _engine
    _engine = engine


class RecognizeRequest(BaseModel):
    banner: str


class FingerprintResponse(BaseModel):
    service: str
    version: Optional[str] = None
    os: Optional[str] = None
    port: Optional[int] = None
    confidence: float
    raw_banner: str
    matched_knowledge: List[dict] = []


@router.post("/recognize", response_model=FingerprintResponse)
async def recognize(req: RecognizeRequest):
    """单条 Banner 识别"""
    if not req.banner.strip():
        raise HTTPException(status_code=400, detail="Banner 不能为空")
    logger.info("API /recognize | banner长度=%d", len(req.banner))
    result = _engine.recognize(req.banner.strip())
    fp = result.fingerprint
    logger.info("API /recognize 响应 | service=%s | version=%s | 关联知识=%d条",
               fp.service, fp.version, len(result.matched_knowledge))
    return FingerprintResponse(
        service=fp.service,
        version=fp.version,
        os=fp.os,
        port=fp.port,
        confidence=fp.confidence,
        raw_banner=fp.raw_banner,
        matched_knowledge=result.matched_knowledge
    )
