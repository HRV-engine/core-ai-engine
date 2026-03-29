
"""
Penalty Engine

건강 신호를 기반으로 컨디션 점수에 감점을 적용한다.

pip install pydantic
"""

from typing import Optional
from pydantic import BaseModel
import json


# ----------------------------
# Config
# ----------------------------

RHR_SCALE = 1.5
RHR_MAX_PENALTY = 12

SLEEP_DEBT_MAX = 8
TARGET_SLEEP = 8

SPO2_SCALE = 1.5
SPO2_MAX_PENALTY = 5

CRITICAL_SPO2 = 90


# ----------------------------
# Models
# ----------------------------

class PenaltyComponents(BaseModel):
    rhr_penalty: float = 0
    sleep_debt_penalty: float = 0
    spo2_penalty: float = 0


class PenaltyResult(BaseModel):
    total_penalty: float
    components: PenaltyComponents
    warning: Optional[str] = None


# ----------------------------
# Utility
# ----------------------------

def clamp(value, low, high):
    return max(low, min(value, high))


# ----------------------------
# Penalty Calculations
# ----------------------------

def compute_rhr_penalty(
    resting_hr: Optional[float],
    baseline_rhr: Optional[float],
) -> float:

    if resting_hr is None or baseline_rhr is None:
        return 0

    delta = resting_hr - baseline_rhr

    if delta <= 0:
        return 0

    penalty = delta * RHR_SCALE

    return clamp(penalty, 0, RHR_MAX_PENALTY)


def compute_sleep_debt_penalty(
    sleep_hours: float
) -> float:

    sleep_debt = max(0, TARGET_SLEEP - sleep_hours)
    penalty = (sleep_debt * 60) / 15

    return clamp(penalty, 0, SLEEP_DEBT_MAX)


def compute_spo2_penalty(
    spo2: Optional[float]
) -> float:

    if spo2 is None:
        return 0

    if spo2 >= 95:
        return 0

    penalty = (95 - spo2) * SPO2_SCALE

    return clamp(penalty, 0, SPO2_MAX_PENALTY)


# ----------------------------
# Critical Warning
# ----------------------------

def check_critical_warning(spo2: Optional[float]) -> Optional[str]:

    if spo2 is None:
        return None

    if spo2 < CRITICAL_SPO2:
        return "Critical: SpO2 extremely low. Consider medical attention."

    return None


# ----------------------------
# Main Penalty Engine
# ----------------------------

def compute_penalties(
    sleep_hours: float,
    resting_hr: Optional[float],
    baseline_rhr: Optional[float],
    spo2: Optional[float],
) -> PenaltyResult:

    rhr_penalty = compute_rhr_penalty(resting_hr, baseline_rhr)
    sleep_penalty = compute_sleep_debt_penalty(sleep_hours)
    spo2_penalty = compute_spo2_penalty(spo2)

    total = rhr_penalty + sleep_penalty + spo2_penalty

    components = PenaltyComponents(
        rhr_penalty=round(rhr_penalty, 2),
        sleep_debt_penalty=round(sleep_penalty, 2),
        spo2_penalty=round(spo2_penalty, 2),
    )

    warning = check_critical_warning(spo2)

    return PenaltyResult(
        total_penalty=round(total, 2),
        components=components,
        warning=warning,
    )


# ----------------------------
# Run (테스트용)
# ----------------------------

if __name__ == "__main__":
    # 테스트 데이터
    sleep_hours = 6.5
    resting_hr = 75
    baseline_rhr = 70
    spo2 = 93

    result = compute_penalties(
        sleep_hours,
        resting_hr,
        baseline_rhr,
        spo2,
    )

    # 저장
    with open("penalty.json", "w") as f:
        json.dump(result.model_dump(), f, indent=2)

    print("Penalty Result:")
    print(result.model_dump_json(indent=2))