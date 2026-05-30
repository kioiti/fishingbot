"""고위험 도박: 로켓·심연과 비슷한 단판 배당 게임"""
from __future__ import annotations

import random
from typing import List, Tuple

RISK_MAX_PAYOUT = 50_000_000

# ── 보물탐사 (!보물탐사) — 3문 중 선택 ─────────────
TREASURE_DIVE_MIN_BET = 5_000
TREASURE_DIVE_OUTCOMES: List[Tuple[str, float]] = [
    ("💀 빈 상자", 0.0),
    ("🪙 동전 주머니", 0.6),
    ("📦 은보물", 1.5),
    ("💎 금보물", 3.5),
    ("👑 전설의 금고", 12.0),
    ("🌌 신화의 유물", 50.0),
]

# ── 어둠의 복도 (!복도) ─────────────────────────
CORRIDOR_MIN_BET = 5_000
CORRIDOR_TRAP_CHANCE = 0.26
CORRIDOR_STEP_MULT = 1.38


def _pick_weighted(outcomes: List[Tuple[str, float, int]]) -> Tuple[str, float]:
    weights = [w for _, _, w in outcomes]
    idx = random.choices(range(len(outcomes)), weights=weights, k=1)[0]
    name, mult, _ = outcomes[idx]
    return name, float(mult)


def roll_treasure_dive(door: int) -> dict:
    """door 1~3. 정답 문은 랜덤, 맞추면 고배율 확률 up."""
    door = max(1, min(3, int(door)))
    winning = random.randint(1, 3)
    weights = [30, 22, 16, 10, 4, 1]
    mults = [o[1] for o in TREASURE_DIVE_OUTCOMES]
    labels = [o[0] for o in TREASURE_DIVE_OUTCOMES]
    idx = random.choices(range(len(labels)), weights=weights, k=1)[0]
    if door != winning:
        idx = min(idx, 1)
    mult = mults[idx]
    label = labels[idx]
    return {
        "tier": label,
        "mult": mult,
        "door": door,
        "winning_door": winning,
        "hit": door == winning,
    }


def treasure_dive_help_text() -> str:
    return (
        "**🗺️ 보물탐사** — 바다 유적에서 문 3개 중 하나를 고른다\n"
        f"- 사용법: `!보물탐사 <베팅> <1|2|3>` (예: `!보물탐사 10000 2`)\n"
        f"- 최소 **{TREASURE_DIVE_MIN_BET:,}원**\n"
        "- **맞는 문**이면 대박 확률 ↑ · 틀리면 손실 위험 큼"
    )


def roll_corridor(steps: int) -> dict:
    steps = max(1, min(5, int(steps)))
    mult = 1.0
    log: List[str] = []
    for i in range(steps):
        if random.random() < CORRIDOR_TRAP_CHANCE:
            return {
                "tier": f"💀 {i + 1}번째 구간 함정!",
                "mult": 0.0,
                "steps": steps,
                "survived": i,
                "log": log + [f"{i + 1}구간에서 함정 발동"],
            }
        mult *= CORRIDOR_STEP_MULT
        log.append(f"{i + 1}구간 통과 (x{mult:.2f})")
    return {
        "tier": f"🏁 복도 끝 ({steps}구간 생존)",
        "mult": mult,
        "steps": steps,
        "survived": steps,
        "log": log,
    }


def calc_risk_payout(bet: int, mult: float) -> int:
    if mult <= 0:
        return 0
    return min(RISK_MAX_PAYOUT, max(0, int(bet * mult)))


def corridor_help_text() -> str:
    survive_all = CORRIDOR_STEP_MULT ** 5
    return (
        "**🚪 어둠의 복도**\n"
        f"- 사용법: `!복도 <베팅> <구간 1~5>`\n"
        f"- 구간마다 **{(1 - CORRIDOR_TRAP_CHANCE) * 100:.0f}%** 생존 시 배율 x{CORRIDOR_STEP_MULT:g} 누적\n"
        f"- 5구간 전부 통과 시 약 **x{survive_all:.1f}** (함정 시 전액 손실)\n"
        f"- 최소 베팅 **{CORRIDOR_MIN_BET:,}원**"
    )
