from fastapi import APIRouter
import json
import time
from config import config
from utils.evaluator import Evaluator
from utils.logger import logger

router = APIRouter()

_engine = None


def set_engine(engine):
    global _engine
    _engine = engine


@router.get("/batch-test/run")
async def run_batch_test():
    """运行批量测试，返回 LLM 方案与正则方案的对比结果"""
    logger.info("API /batch-test/run 开始批量测试")
    start = time.time()

    with open(config.TEST_DATA_FILE, "r", encoding="utf-8") as f:
        test_data = json.load(f)

    banners = [item["banner"] for item in test_data]
    ground_truth = [
        {"service": item["service"], "version": item.get("version")}
        for item in test_data
    ]

    # LLM 方案
    logger.info("开始 LLM 方案测试，共 %d 条...", len(banners))
    llm_preds = [_engine.recognize(b).fingerprint for b in banners]
    llm_result = Evaluator.evaluate(llm_preds, ground_truth)
    logger.info("LLM 方案完成 | service_acc=%.2f | version_acc=%.2f",
               llm_result["service_accuracy"], llm_result["version_accuracy"])

    # 纯正则方案
    logger.info("开始正则方案测试...")
    regex_preds = [_engine.recognize_regex(b) for b in banners]
    regex_result = Evaluator.evaluate(regex_preds, ground_truth)
    logger.info("正则方案完成 | service_acc=%.2f | version_acc=%.2f",
               regex_result["service_accuracy"], regex_result["version_accuracy"])

    total_time = time.time() - start
    logger.info("API /batch-test/run 完成 | 总耗时=%.1fs | LLM vs 正则: %.0f%% vs %.0f%%",
               total_time,
               llm_result["service_accuracy"] * 100,
               regex_result["service_accuracy"] * 100)

    return {
        "total": llm_result["total"],
        "llm": {
            "service_accuracy": llm_result["service_accuracy"],
            "version_accuracy": llm_result["version_accuracy"],
        },
        "regex": {
            "service_accuracy": regex_result["service_accuracy"],
            "version_accuracy": regex_result["version_accuracy"],
        },
        "details": [
            {
                "banner": llm_d["banner"],
                "llm_service": llm_d["pred_service"],
                "regex_service": reg_d["pred_service"],
                "true_service": llm_d["true_service"],
                "llm_correct": llm_d["service_correct"],
                "regex_correct": reg_d["service_correct"],
            }
            for llm_d, reg_d in zip(
                llm_result["details"], regex_result["details"]
            )
        ]
    }
