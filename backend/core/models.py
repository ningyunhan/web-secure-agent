from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from enum import Enum


class KnowledgeType(str, Enum):
    FINGERPRINT = "fingerprint"
    VULNERABILITY = "vulnerability"
    SOP = "sop"


class AssetFingerprint(BaseModel):
    """标准化资产指纹输出"""
    service: str = Field(description="服务名称，如 nginx, apache, mysql")
    version: Optional[str] = Field(default=None, description="版本号")
    os: Optional[str] = Field(default=None, description="操作系统")
    port: Optional[int] = Field(default=None, description="端口")
    confidence: float = Field(ge=0.0, le=1.0, description="置信度 0-1")
    raw_banner: str = Field(description="原始 Banner 文本")
    extra_info: Optional[dict] = Field(default=None, description="额外信息")

    @field_validator("confidence")
    @classmethod
    def fix_confidence(cls, v):
        """自动修正：置信度超出范围时截断"""
        if v < 0:
            return 0.0
        if v > 1:
            return 1.0
        return v

    @field_validator("service")
    @classmethod
    def fix_service(cls, v):
        """自动修正：服务名标准化"""
        if not v or v.strip() == "":
            raise ValueError("服务名不能为空")
        return v.strip().lower()


class KnowledgeEntry(BaseModel):
    """知识库条目"""
    id: str = Field(description="唯一ID")
    type: KnowledgeType = Field(description="知识类型")
    title: str = Field(description="标题")
    content: str = Field(description="知识内容")
    source: str = Field(default="manual", description="来源")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="置信度")
    status: str = Field(default="active", description="状态")
    tags: List[str] = Field(default_factory=list, description="标签")


class FingerprintResult(BaseModel):
    """识别结果（含知识来源）"""
    fingerprint: AssetFingerprint
    matched_knowledge: List[dict] = Field(
        default_factory=list,
        description="匹配到的RAG知识条目"
    )
    llm_raw_output: Optional[str] = Field(
        default=None, description="LLM原始输出"
    )
