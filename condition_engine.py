"""
Condition Engine

baseline → score → penalty → final condition score
"""

from pydantic import BaseModel
from typing import Optional
import json

# 기존 모듈 import
from baseline import Baseline
from score import compute_scores, DailyMetrics
from penalty import compute_penalties


# ----------------------------
# Result Model
# ----------------------------

class ConditionResult(BaseModel):
    preliminary_score: float
    penalty: float
    final_score: float

    state: str
    recommendation: str

    components: dict
    penalties: dict

    warning: Optional[str] = None


# ----------------------------
# Utility
# ----------------------------

def clamp(value, low=0, high=100):
    return max(low, min(value, high))


# ----------------------------
# Main Engine
# ----------------------------

def compute_condition(
    metrics: DailyMetrics,
    baseline: Baseline,
) -> ConditionResult:

    # 1️⃣ score 계산
    score_result = compute_scores(
        metrics=metrics,
        baseline=baseline,
    )

    # 2️⃣ penalty 계산
    penalty_result = compute_penalties(
        sleep_hours=metrics.sleep_hours,
        resting_hr=metrics.resting_hr,
        baseline_rhr=baseline.rhr,
        spo2=metrics.spo2,
    )

    # 3️⃣ final score
    final_score = score_result.preliminary_score - penalty_result.total_penalty
    final_score = clamp(final_score)

    # 4️⃣ 상태 보정
    state = score_result.state
    if final_score < 40:
        state = "recovery_needed"

    return ConditionResult(
        preliminary_score=score_result.preliminary_score,
        penalty=penalty_result.total_penalty,
        final_score=round(final_score, 2),

        state=state,
        recommendation=score_result.recommendation,

        components=score_result.components.model_dump(),
        penalties=penalty_result.components.model_dump(),

        warning=penalty_result.warning,
    )


# ----------------------------
# Run (테스트용)
# ----------------------------

if __name__ == "__main__":
    import json

    # ✅ baseline 파일 읽기
    with open("result.json") as f:
        baseline_data = json.load(f)

    baseline = Baseline(**baseline_data)

    # ✅ 오늘 데이터 (나중에 CSV/API로 바뀔 부분)
    metrics = DailyMetrics(
        hrv=65,
        sleep_hours=6.5,
        sleep_efficiency=88,
        steps=8000,
        active_minutes=40,
        resting_hr=75,
        spo2=93,
    )

    # 실행
    result = compute_condition(metrics, baseline)

    # 저장
    with open("condition.json", "w") as f:
        json.dump(result.model_dump(), f, indent=2)

    print("Condition Result:")
    print(result.model_dump_json(indent=2))