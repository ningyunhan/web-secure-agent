from core.models import AssetFingerprint
from typing import List


class Evaluator:
    """评估器：计算识别准确率"""

    @staticmethod
    def evaluate(
        predictions: List[AssetFingerprint],
        ground_truth: List[dict]
    ) -> dict:
        """
        计算准确率
        predictions: 识别结果列表
        ground_truth: 标注答案列表，每项含 service, version
        """
        total = len(ground_truth)
        service_correct = 0
        version_correct = 0
        details = []

        for pred, truth in zip(predictions, ground_truth):
            svc_match = pred.service.lower() == truth["service"].lower()
            ver_match = (
                svc_match
                and pred.version is not None
                and truth.get("version") is not None
                and pred.version == truth["version"]
            )
            if svc_match:
                service_correct += 1
            if ver_match:
                version_correct += 1
            details.append({
                "banner": pred.raw_banner[:80],
                "pred_service": pred.service,
                "true_service": truth["service"],
                "pred_version": pred.version,
                "true_version": truth.get("version"),
                "service_correct": svc_match,
                "version_correct": ver_match
            })

        return {
            "total": total,
            "service_accuracy": service_correct / total if total else 0,
            "version_accuracy": version_correct / total if total else 0,
            "details": details
        }
