#!/usr/bin/env python3
"""
LLM 结构化输出分析脚本 — 闭环执行，直接返回结果

用法：
    echo "待分析文本" | python analyze.py \
        --system-prompt "你是XXX专家，提取XXX，输出JSON" \
        --schema '{"field1":"string","field2":"number"}'

    或通过 --input 参数传入：
        python analyze.py --input "待分析文本" --system-prompt "..." --schema '...'

输出：标准 JSON 到 stdout

依赖：openai, pydantic
"""

import argparse
import json
import os
import sys

from typing import Optional

from openai import OpenAI
from pydantic import BaseModel, create_model

# 同目录下的 fixer.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fixer import parse_and_fix


# 类型映射表
TYPE_MAP = {
    "string": str,
    "str": str,
    "number": float,
    "float": float,
    "int": int,
    "integer": int,
    "boolean": bool,
    "bool": bool,
}


def build_model(schema: dict) -> type:
    """根据 schema dict 动态创建 Pydantic Model"""
    fields = {}
    for name, type_str in schema.items():
        py_type = TYPE_MAP.get(type_str.lower(), str)
        fields[name] = (py_type, ...)
    return create_model("DynamicModel", **fields)


def analyze(
    text: str,
    system_prompt: str,
    schema: dict,
    api_key: str,
    base_url: str,
    model: str,
    temperature: float,
) -> dict:
    """调用 LLM 并返回结构化结果"""
    # 构建 Pydantic Model
    model_class = build_model(schema)

    # 确保 prompt 末尾有 JSON 输出要求
    if "只输出" not in system_prompt and "JSON" not in system_prompt.upper():
        system_prompt += "\n只输出JSON，不要输出其他内容。"

    # 调用 LLM
    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        temperature=temperature,
    )
    raw_output = response.choices[0].message.content

    # 修正管道
    result = parse_and_fix(raw_output, model_class)

    return result.model_dump()


def main():
    parser = argparse.ArgumentParser(description="LLM 结构化输出分析")
    parser.add_argument(
        "--system-prompt", required=True,
        help="系统提示词（LLM角色 + 输出要求）"
    )
    parser.add_argument(
        "--input",
        help="待分析文本（如不提供则从 stdin 读取）"
    )
    parser.add_argument(
        "--schema", required=True,
        help='JSON schema，如 \'{"name":"string","age":"number"}\''
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("OPENAI_API_KEY", ""),
        help="API Key（默认从环境变量 OPENAI_API_KEY 读取）"
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1"),
        help="API Base URL（默认从环境变量 OPENAI_BASE_URL 读取）"
    )
    parser.add_argument(
        "--model",
        default=os.getenv("LLM_MODEL", "deepseek-chat"),
        help="模型名（默认从环境变量 LLM_MODEL 读取）"
    )
    parser.add_argument(
        "--temperature",
        type=float, default=0.1,
        help="温度参数（默认 0.1）"
    )

    args = parser.parse_args()

    # 获取输入文本
    if args.input:
        text = args.input
    else:
        text = sys.stdin.read().strip()

    if not text:
        print(json.dumps({"error": "输入文本为空"}, ensure_ascii=False))
        sys.exit(1)

    if not args.api_key:
        print(json.dumps({"error": "缺少 API Key，请设置环境变量 OPENAI_API_KEY 或通过 --api-key 传入"}, ensure_ascii=False))
        sys.exit(1)

    # 解析 schema
    try:
        schema = json.loads(args.schema)
    except json.JSONDecodeError:
        print(json.dumps({"error": "schema 格式错误，应为合法 JSON"}, ensure_ascii=False))
        sys.exit(1)

    # 执行分析
    try:
        result = analyze(
            text=text,
            system_prompt=args.system_prompt,
            schema=schema,
            api_key=args.api_key,
            base_url=args.base_url,
            model=args.model,
            temperature=args.temperature,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
