"""
Condition Score Engine

사용자의 오늘 데이터와 baseline을 이용해
컨디션 점수를 계산한다.
"""

from typing import Optional
from pydantic import BaseModel
import json


# ----------------------------
# Config
# ----------------------------

HRV_WEIGHT = 0.40
SLEEP_WEIGHT = 0.35
ACTIVITY_WEIGHT = 0.25

TARGET_SLEEP_HOURS = 8
TARGET_STEPS = 10000


# ----------------------------
# Data Models
# ----------------------------

class Baseline(BaseModel):
    hrv: Optional[float]
    rhr: Optional[float]
    sleep: Optional[float]
    steps: Optional[float]


class DailyMetrics(BaseModel):
    hrv: float
    sleep_hours: float
    sleep_efficiency: float
    steps: int
    active_minutes: int

    resting_hr: Optional[float] = None
    spo2: Optional[float] = None


class ComponentScores(BaseModel):
    hrv: float
    sleep: float
    activity: float


class ScoreResult(BaseModel):
    components: ComponentScores
    preliminary_score: float
    final_score: float
    state: str
    recommendation: str


# ----------------------------
# Utility
# ----------------------------

def clamp(value, low, high):
    return max(low, min(value, high))


# ----------------------------
# Component Scores
# ----------------------------

def compute_hrv_score(hrv_today: float, baseline_hrv: Optional[float]) -> float:
    if baseline_hrv is None or baseline_hrv == 0:
        return 50.0

    raw = (hrv_today / baseline_hrv) * 100
    return clamp(raw, 0, 100)


def compute_sleep_score(hours: float, efficiency: float) -> float:
    sleep_component = (hours / TARGET_SLEEP_HOURS) * 70
    efficiency_component = (efficiency / 100) * 30
    score = sleep_component + efficiency_component

    return clamp(score, 0, 100)


def compute_activity_score(steps: int, target_steps: int = TARGET_STEPS) -> float:
    score = 100 - abs(steps - target_steps) / 100
    return clamp(score, 0, 100)


# ----------------------------
# Composite Score
# ----------------------------

def compute_preliminary_score(
    hrv_score: float,
    sleep_score: float,
    activity_score: float,
) -> float:

    score = (
        hrv_score * HRV_WEIGHT
        + sleep_score * SLEEP_WEIGHT
        + activity_score * ACTIVITY_WEIGHT
    )

    return round(score, 2)


# ----------------------------
# State Classification
# ----------------------------

def classify_state(score: float) -> str:
    if score >= 80:
        return "excellent"
    elif score >= 60:
        return "good"
    elif score >= 40:
        return "tired"
    else:
        return "recovery_needed"


# ----------------------------
# Recommendation Engine
# ----------------------------

def generate_recommendation(state: str) -> str:
    mapping = {
        "excellent": "High intensity workout is recommended.",
        "good": "Moderate intensity exercise is suitable today.",
        "tired": "Light activity such as walking or stretching.",
        "recovery_needed": "Prioritize rest and recovery.",
    }

    return mapping[state]


# ----------------------------
# Main Score Engine
# ----------------------------

def compute_scores(
    metrics: DailyMetrics,
    baseline: Baseline,
) -> ScoreResult:

    hrv_score = compute_hrv_score(metrics.hrv, baseline.hrv)

    sleep_score = compute_sleep_score(
        metrics.sleep_hours,
        metrics.sleep_efficiency,
    )

    activity_score = compute_activity_score(
        metrics.steps,
        int(baseline.steps) if baseline.steps else TARGET_STEPS,
    )

    preliminary = compute_preliminary_score(
        hrv_score,
        sleep_score,
        activity_score,
    )

    state = classify_state(preliminary)
    recommendation = generate_recommendation(state)

    components = ComponentScores(
        hrv=round(hrv_score, 2),
        sleep=round(sleep_score, 2),
        activity=round(activity_score, 2),
    )

    return ScoreResult(
        components=components,
        preliminary_score=preliminary,
        final_score=preliminary,
        state=state,
        recommendation=recommendation,
    )


# ----------------------------
# Run (테스트용 / Actions용)
# ----------------------------

if __name__ == "__main__":
    # baseline (baseline.py 결과라고 가정)
    baseline = Baseline(
        hrv=60,
        rhr=70,
        sleep=7,
        steps=7000,
    )

    # 오늘 데이터
    metrics = DailyMetrics(
        hrv=65,
        sleep_hours=7.5,
        sleep_efficiency=90,
        steps=8500,
        active_minutes=45,
    )

    result = compute_scores(metrics, baseline)

    # 저장
    with open("score.json", "w") as f:
        json.dump(result.model_dump(), f, indent=2)

    print("Score Result:")
    print(result.model_dump_json(indent=2))
