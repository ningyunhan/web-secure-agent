import json
import re
import time
from typing import Optional
from core.models import AssetFingerprint, FingerprintResult
from core.rag_engine import RAGEngine
from utils.llm_client import chat_completion
from utils.logger import logger

SYSTEM_PROMPT = """你是网络安全资产指纹识别专家。
根据给定的网络Banner文本，识别出资产的标准化指纹信息。

输出要求：
1. 必须输出合法JSON，字段包括：service, version, os, port, confidence, raw_banner
2. service: 服务名称（小写），如 nginx, apache, openssh, mysql, redis
3. version: 版本号（如有），无则为null
4. os: 操作系统（如能判断），无则为null
5. port: 端口号（如能从Banner中提取），无则为null
6. confidence: 置信度0-1，表示你对识别结果的把握程度
7. raw_banner: 原始Banner文本

如果Banner被伪装或格式非标准，请尽力根据语义推断真实服务。
只输出JSON，不要输出其他内容。"""

SYSTEM_PROMPT_WITH_RAG = """你是网络安全资产指纹识别专家。
根据给定的网络Banner文本和参考知识库信息，识别出资产的标准化指纹信息。

参考知识库（请优先参考这些知识进行识别）：
{rag_context}

输出要求：
1. 必须输出合法JSON，字段包括：service, version, os, port, confidence, raw_banner
2. service: 服务名称（小写），如 nginx, apache, openssh, mysql, redis
3. version: 版本号（如有），无则为null
4. os: 操作系统（如能判断），无则为null
5. port: 端口号（如能从Banner中提取），无则为null
6. confidence: 置信度0-1，表示你对识别结果的把握程度
7. raw_banner: 原始Banner文本

如果Banner被伪装或格式非标准，请结合知识库信息尽力推断真实服务。
只输出JSON，不要输出其他内容。"""

# 纯正则方案（用于对比）
REGEX_RULES = [
    {"pattern": r"nginx/([\d.]+)", "service": "nginx", "version_group": 1},
    {"pattern": r"apache/([\d.]+)", "service": "apache", "version_group": 1},
    {"pattern": r"SSH-([\d.]+)-OpenSSH_([\w.]+)", "service": "openssh", "version_group": 2},
    {"pattern": r"mysql.*?([\d.]+)", "service": "mysql", "version_group": 1},
    {"pattern": r"redis.*?v?=([\d.]+)", "service": "redis", "version_group": 1},
    {"pattern": r"PostgreSQL([\d.]+)", "service": "postgresql", "version_group": 1},
]


class FingerprintEngine:
    """指纹识别引擎"""

    def __init__(self, rag_engine: RAGEngine):
        self.rag = rag_engine

    def recognize(self, banner: str) -> FingerprintResult:
        """使用 LLM 识别指纹，再用 RAG 检索关联知识"""
        logger.info("开始识别 | banner=%s", banner[:80] + ("..." if len(banner) > 80 else ""))
        start = time.time()

        # 1. 直接调用 LLM 识别指纹
        system = SYSTEM_PROMPT
        raw_output = chat_completion(system, f"Banner:\n{banner}")
        llm_time = time.time() - start
        logger.info("LLM 返回 | 耗时=%.2fs | output=%s", llm_time, raw_output[:100] + ("..." if len(raw_output) > 100 else ""))

        # 2. 解析并校验输出
        fingerprint = self._parse_and_fix(raw_output, banner)
        logger.info("指纹解析完成 | service=%s version=%s os=%s confidence=%.2f",
                   fingerprint.service, fingerprint.version, fingerprint.os, fingerprint.confidence)

        # 3. 用识别结果检索关联知识（漏洞情报、SOP等）
        query = f"{fingerprint.service} {fingerprint.version or ''}"
        matched = self.rag.search(query)
        total_time = time.time() - start
        logger.info("RAG 检索完成 | query='%s' | 命中%d条 | 总耗时=%.2fs", query, len(matched), total_time)

        return FingerprintResult(
            fingerprint=fingerprint,
            matched_knowledge=matched,
            llm_raw_output=raw_output
        )

    def recognize_regex(self, banner: str) -> AssetFingerprint:
        """纯正则方案识别（用于对比）"""
        for rule in REGEX_RULES:
            match = re.search(rule["pattern"], banner, re.IGNORECASE)
            if match:
                version = None
                if rule["version_group"] <= len(match.groups()):
                    version = match.group(rule["version_group"])
                logger.debug("正则匹配 | service=%s version=%s", rule["service"], version)
                return AssetFingerprint(
                    service=rule["service"],
                    version=version,
                    os=None,
                    port=None,
                    confidence=0.7,
                    raw_banner=banner
                )
        logger.warning("正则未匹配 | banner=%s", banner[:80])
        return AssetFingerprint(
            service="unknown",
            version=None,
            os=None,
            port=None,
            confidence=0.1,
            raw_banner=banner
        )

    def _parse_and_fix(self, raw_output: str, banner: str) -> AssetFingerprint:
        """解析 LLM 输出，自动修正格式错误"""
        json_str = raw_output.strip()

        # 去除可能的 markdown 代码块标记
        if json_str.startswith("```"):
            lines = json_str.split("\n")
            json_str = "\n".join(
                l for l in lines if not l.startswith("```")
            )

        # 第一次尝试直接解析
        data = None
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            # 第二次尝试：提取大括号内容
            logger.warning("LLM 输出 JSON 解析失败，尝试提取大括号内容")
            start = raw_output.find("{")
            end = raw_output.rfind("}")
            if start != -1 and end != -1:
                try:
                    data = json.loads(raw_output[start:end + 1])
                    logger.info("JSON 提取修复成功")
                except json.JSONDecodeError:
                    logger.error("JSON 解析完全失败，使用默认值", exc_info=True)
                    data = None

        if data is None:
            data = {}
            logger.warning("LLM 输出无法解析为 JSON，返回默认指纹")

        # 补全缺失字段
        data["raw_banner"] = banner
        data.setdefault("service", "unknown")
        data.setdefault("version", None)
        data.setdefault("os", None)
        data.setdefault("port", None)
        data.setdefault("confidence", 0.5)

        # Pydantic 自动校验 + 修正
        return AssetFingerprint(**data)
