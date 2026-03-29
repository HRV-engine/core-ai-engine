"""
Baseline Engine

사용자의 최근 데이터를 기반으로 개인 기준값(baseline)을 계산한다.

지원 baseline
- HRV
- Resting Heart Rate
- Sleep Duration
- Steps

알고리즘
1. 최근 N일 데이터 사용 (default 14)
2. 최소 데이터 수 확인 (default 7)
3. 이상치 제거 (z-score)
4. EMA 적용 (HRV)
"""

from typing import List, Optional
from pydantic import BaseModel
import numpy as np
import json


# ----------------------------
# Config
# ----------------------------

LOOKBACK_DAYS = 14
MIN_PERIODS = 7
DECAY = 0.9
ALPHA = 1 - DECAY
Z_THRESHOLD = 3


# ----------------------------
# Data Models
# ----------------------------

class HRVRecord(BaseModel):
    date: str
    value: float


class RHRRecord(BaseModel):
    date: str
    value: float


class SleepRecord(BaseModel):
    date: str
    hours: float


class StepRecord(BaseModel):
    date: str
    steps: int


class BaselineResult(BaseModel):
    hrv: Optional[float] = None
    rhr: Optional[float] = None
    sleep: Optional[float] = None
    steps: Optional[float] = None


# ----------------------------
# Utility Functions
# ----------------------------

def clamp(value, low, high):
    return max(low, min(value, high))


def remove_outliers_zscore(values: List[float]) -> List[float]:
    """
    Z-score 기반 이상치 제거
    """
    if len(values) < 2:
        return values

    arr = np.array(values)
    mean = np.mean(arr)
    std = np.std(arr)

    if std == 0:
        return values

    z_scores = np.abs((arr - mean) / std)
    filtered = arr[z_scores <= Z_THRESHOLD]

    return filtered.tolist()


def ema(values: List[float], alpha: float = ALPHA) -> Optional[float]:
    """
    Exponential Moving Average
    """
    if not values:
        return None

    ema_value = values[0]

    for v in values[1:]:
        ema_value = alpha * v + (1 - alpha) * ema_value

    return float(round(ema_value, 2))


# ----------------------------
# Default Baseline (초기 사용자용)
# ----------------------------

def default_baseline(metric: str) -> float:
    defaults = {
        "hrv": 60.0,
        "rhr": 70.0,
        "sleep": 7.0,
        "steps": 7000.0,
    }
    return defaults.get(metric, 0.0)


# ----------------------------
# Baseline Calculations
# ----------------------------

def compute_hrv_baseline(records: List[HRVRecord]) -> Optional[float]:
    values = [r.value for r in records][-LOOKBACK_DAYS:]

    if len(values) < MIN_PERIODS:
        return default_baseline("hrv")

    values = remove_outliers_zscore(values)
    return ema(values)


def compute_rhr_baseline(records: List[RHRRecord]) -> Optional[float]:
    values = [r.value for r in records][-LOOKBACK_DAYS:]

    if len(values) < MIN_PERIODS:
        return default_baseline("rhr")

    values = remove_outliers_zscore(values)
    return float(round(np.median(values), 2))


def compute_sleep_baseline(records: List[SleepRecord]) -> Optional[float]:
    values = [r.hours for r in records][-LOOKBACK_DAYS:]

    if len(values) < MIN_PERIODS:
        return default_baseline("sleep")

    values = remove_outliers_zscore(values)
    return float(round(np.mean(values), 2))


def compute_steps_baseline(records: List[StepRecord]) -> Optional[float]:
    values = [r.steps for r in records][-LOOKBACK_DAYS:]

    if len(values) < MIN_PERIODS:
        return default_baseline("steps")

    values = remove_outliers_zscore(values)
    return float(round(np.mean(values), 2))


# ----------------------------
# Main Baseline Engine
# ----------------------------

def compute_baseline(
    hrv_records: List[HRVRecord],
    rhr_records: List[RHRRecord],
    sleep_records: List[SleepRecord],
    step_records: List[StepRecord],
) -> BaselineResult:

    return BaselineResult(
        hrv=compute_hrv_baseline(hrv_records),
        rhr=compute_rhr_baseline(rhr_records),
        sleep=compute_sleep_baseline(sleep_records),
        steps=compute_steps_baseline(step_records),
    )


# ----------------------------
# Run (for GitHub Actions)
# ----------------------------

if __name__ == "__main__":
    # 테스트 데이터
    hrv_records = [
        HRVRecord(date="2026-03-01", value=60),
        HRVRecord(date="2026-03-02", value=62),
        HRVRecord(date="2026-03-03", value=58),
        HRVRecord(date="2026-03-04", value=200),  # 이상치
        HRVRecord(date="2026-03-05", value=61),
        HRVRecord(date="2026-03-06", value=59),
        HRVRecord(date="2026-03-07", value=60),
    ]

    rhr_records = [
        RHRRecord(date="2026-03-01", value=70),
        RHRRecord(date="2026-03-02", value=72),
        RHRRecord(date="2026-03-03", value=71),
        RHRRecord(date="2026-03-04", value=90),  # 이상치
        RHRRecord(date="2026-03-05", value=69),
        RHRRecord(date="2026-03-06", value=68),
        RHRRecord(date="2026-03-07", value=70),
    ]

    sleep_records = [
        SleepRecord(date="2026-03-01", hours=7),
        SleepRecord(date="2026-03-02", hours=6.5),
        SleepRecord(date="2026-03-03", hours=8),
        SleepRecord(date="2026-03-04", hours=3),  # 이상치
        SleepRecord(date="2026-03-05", hours=7.5),
        SleepRecord(date="2026-03-06", hours=7),
        SleepRecord(date="2026-03-07", hours=6.8),
    ]

    step_records = [
        StepRecord(date="2026-03-01", steps=6000),
        StepRecord(date="2026-03-02", steps=8000),
        StepRecord(date="2026-03-03", steps=7500),
        StepRecord(date="2026-03-04", steps=20000),  # 이상치
        StepRecord(date="2026-03-05", steps=7000),
        StepRecord(date="2026-03-06", steps=7200),
        StepRecord(date="2026-03-07", steps=6800),
    ]

    result = compute_baseline(
        hrv_records,
        rhr_records,
        sleep_records,
        step_records,
    )

    # 결과 저장
    with open("result.json", "w") as f:
        json.dump(result.dict(), f, indent=2)

    print("Baseline Result:", result.json(indent=2))
