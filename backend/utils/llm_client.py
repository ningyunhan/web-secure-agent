from openai import OpenAI
from config import config
from utils.logger import logger


def get_llm_client() -> OpenAI:
    """根据配置创建 LLM 客户端"""
    if config.LLM_PROVIDER == "ollama":
        logger.info("使用 Ollama 本地模型 | url=%s", config.OLLAMA_BASE_URL)
        return OpenAI(
            base_url=config.OLLAMA_BASE_URL,
            api_key="ollama"
        )
    logger.info("使用云端 LLM | provider=%s | model=%s | url=%s",
               config.LLM_PROVIDER, config.LLM_MODEL, config.OPENAI_BASE_URL)
    return OpenAI(
        api_key=config.OPENAI_API_KEY,
        base_url=config.OPENAI_BASE_URL
    )


def chat_completion(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.1
) -> str:
    """调用 LLM 并返回文本结果"""
    import time
    client = get_llm_client()
    start = time.time()
    try:
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature
        )
        elapsed = time.time() - start
        result = response.choices[0].message.content
        tokens = {
            "prompt": getattr(response.usage, "prompt_tokens", "N/A"),
            "completion": getattr(response.usage, "completion_tokens", "N/A"),
        } if hasattr(response, "usage") and response.usage else {}
        logger.info("LLM 调用成功 | model=%s | 耗时=%.2fs | prompt_tokens=%s | completion_tokens=%s",
                   config.LLM_MODEL, elapsed, tokens.get("prompt"), tokens.get("completion"))
        return result
    except Exception as e:
        elapsed = time.time() - start
        logger.error("LLM 调用失败 | model=%s | 耗时=%.2fs | error=%s", config.LLM_MODEL, elapsed, e, exc_info=True)
        raise
