"""
JSON 修正管道 — 从 LLM 原始输出中提取合法的结构化对象

四层修正逻辑（按顺序执行，任一层成功就跳过后续）：
1. 直接 json.loads
2. 去除 Markdown 代码块标记后解析
3. 正则提取大括号内容后解析
4. Pydantic 字段级校验 + 缺失字段补默认值

用法：
    from fixer import parse_and_fix
    result = parse_and_fix(raw_output, MyModel)
    # result 是合法的 MyModel 对象

依赖：pydantic v2
"""

import json
import re
import logging
from typing import Type, TypeVar, Optional
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def _try_json_loads(text: str) -> Optional[dict]:
    """第一层：直接解析"""
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, TypeError):
        pass
    return None


def _strip_markdown(text: str) -> Optional[dict]:
    """第二层：去除 Markdown 代码块标记"""
    text = text.strip()
    if not text.startswith("```"):
        return None
    lines = text.split("\n")
    # 去掉首尾的 ``` 行
    lines = [l for l in lines if not l.strip().startswith("```")]
    cleaned = "\n".join(lines)
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, TypeError):
        pass
    return None


def _extract_braces(text: str) -> Optional[dict]:
    """第三层：正则提取大括号内容"""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    chunk = text[start:end + 1]
    try:
        data = json.loads(chunk)
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, TypeError):
        pass
    return None


def _get_default_for_field(field) -> object:
    """根据 Pydantic 字段类型生成默认值"""
    annotation = field.annotation
    # 处理 Optional (Union[X, None])
    origin = getattr(annotation, "__origin__", None)
    if origin is type(None):
        return None
    # 基本类型
    type_map = {
        str: "unknown",
        int: 0,
        float: 0.5,
        bool: False,
        type(None): None,
    }
    for t, default in type_map.items():
        if annotation is t:
            return default
    # Optional 类型（typing.Optional[X] → Union[X, None]）
    if hasattr(annotation, "__args__"):
        args = annotation.__args__
        for arg in args:
            if arg is type(None):
                continue
            for t, default in type_map.items():
                if arg is t:
                    return default
        return None
    # list / dict 等容器类型
    return None


def _pydantic_fix(data: dict, model_class: Type[T]) -> Optional[T]:
    """第四层：Pydantic 校验 + 缺失字段补默认值"""
    if not data:
        data = {}
    # 补全缺失字段
    for field_name, field_info in model_class.model_fields.items():
        if field_name not in data:
            data[field_name] = _get_default_for_field(field_info)
    try:
        return model_class(**data)
    except (ValidationError, TypeError) as e:
        logger.warning("Pydantic 校验失败: %s", e)
        # 最后兜底：强制构造一个全默认值的对象
        defaults = {}
        for field_name, field_info in model_class.model_fields.items():
            defaults[field_name] = _get_default_for_field(field_info)
        try:
            return model_class(**defaults)
        except Exception:
            return None


def parse_and_fix(raw_output: str, model_class: Type[T]) -> T:
    """
    从 LLM 原始输出中提取合法的结构化对象

    参数:
        raw_output: LLM 返回的原始字符串
        model_class: Pydantic Model 类

    返回:
        合法的 model_class 实例。如果四层修正全部失败，
        返回一个所有字段为默认值的对象，不会抛异常。

    示例:
        >>> from pydantic import BaseModel
        >>> class Alert(BaseModel):
        ...     alert_type: str
        ...     severity: str
        ...     confidence: float
        >>> raw = '```json\\n{"alert_type": "sql_injection", "severity": "high", "confidence": 0.95}\\n```'
        >>> result = parse_and_fix(raw, Alert)
        >>> result.alert_type
        'sql_injection'
    """
    if not raw_output or not raw_output.strip():
        logger.warning("LLM 输出为空，返回默认对象")
        return _pydantic_fix({}, model_class)

    text = raw_output.strip()

    # 第一层：直接解析
    data = _try_json_loads(text)
    if data:
        logger.info("JSON 解析成功（直接解析）")
        return _pydantic_validate(data, model_class)

    # 第二层：去除 Markdown
    data = _strip_markdown(text)
    if data:
        logger.info("JSON 解析成功（去除Markdown）")
        return _pydantic_validate(data, model_class)

    # 第三层：提取大括号
    data = _extract_braces(text)
    if data:
        logger.info("JSON 解析成功（提取大括号）")
        return _pydantic_validate(data, model_class)

    # 第四层：全部失败，返回默认对象
    logger.warning("JSON 解析全部失败，返回默认对象 | raw=%s", text[:100])
    return _pydantic_fix({}, model_class)


def _pydantic_validate(data: dict, model_class: Type[T]) -> T:
    """用 Pydantic 校验数据，失败则走修正"""
    try:
        return model_class(**data)
    except (ValidationError, TypeError):
        return _pydantic_fix(data, model_class)
