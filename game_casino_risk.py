"""고위험 도박: 로켓·심연과 비슷한 단판 배당 게임"""
from __future__ import annotations

import random
from typing import List, Tuple

RISK_MAX_PAYOUT = 50_000_000

# ── 마녀의 솥 (!솥) ─────────────────────────────
CAULDRON_MIN_BET = 5_000
CAULDRON_OUTCOMES: List[Tuple[str, float, int]] = [
    ("☠️ 솥이 폭발", 0.0, 4500),
    ("🫧 거품만", 0.35, 1800),
    ("🧪 희미한 연기", 0.75, 1400),
    ("💚 초록 물약", 1.8, 1200),
    ("💜 보라 물약", 4.0, 650),
    ("🌟 황금 물약", 12.0, 320),
    ("🔮 대마법사의 비약", 45.0, 100),
    ("👁️ 운명의 눈", 200.0, 30),
]

# ── 행운 핀볼 (!핀볼) ───────────────────────────
PINBALL_MIN_BET = 3_000
PINBALL_SLOTS: List[Tuple[str, float, int]] = [
    ("💀 바닥 구멍", 0.0, 3500),
    ("😢 0.5배", 0.5, 2000),
    ("🙂 1.2배", 1.2, 1800),
    ("😄 2.0배", 2.0, 1400),
    ("🔥 4.5배", 4.5, 800),
    ("⭐ 10배", 10.0, 350),
    ("👑 잭팟 레인", 35.0, 120),
    ("🌈 무지개 핀", 120.0, 30),
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


def roll_cauldron() -> dict:
    name, mult = _pick_weighted(CAULDRON_OUTCOMES)
    return {"tier": name, "mult": mult}


def roll_pinball() -> dict:
    name, mult = _pick_weighted(PINBALL_SLOTS)
    return {"tier": name, "mult": mult}


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


def cauldron_odds_text() -> str:
    total = sum(w for _, _, w in CAULDRON_OUTCOMES)
    lines = ["**🧪 마녀의 솥 — 등급별 확률**"]
    for name, mult, w in CAULDRON_OUTCOMES:
        pct = w / total * 100
        mtxt = "전멸" if mult <= 0 else f"x{mult:g}"
        lines.append(f"- {name}: **{pct:.2f}%** ({mtxt})")
    lines.append(f"- 최소 베팅 **{CAULDRON_MIN_BET:,}원**")
    return "\n".join(lines)


def pinball_odds_text() -> str:
    total = sum(w for _, _, w in PINBALL_SLOTS)
    lines = ["**🎱 행운 핀볼 — 슬롯 확률**"]
    for name, mult, w in PINBALL_SLOTS:
        pct = w / total * 100
        mtxt = "전멸" if mult <= 0 else f"x{mult:g}"
        lines.append(f"- {name}: **{pct:.2f}%** ({mtxt})")
    lines.append(f"- 최소 베팅 **{PINBALL_MIN_BET:,}원**")
    return "\n".join(lines)


def corridor_help_text() -> str:
    survive_all = CORRIDOR_STEP_MULT ** 5
    return (
        "**🚪 어둠의 복도**\n"
        f"- 사용법: `!복도 <베팅> <구간 1~5>`\n"
        f"- 구간마다 **{(1 - CORRIDOR_TRAP_CHANCE) * 100:.0f}%** 생존 시 배율 x{CORRIDOR_STEP_MULT:g} 누적\n"
        f"- 5구간 전부 통과 시 약 **x{survive_all:.1f}** (함정 시 전액 손실)\n"
        f"- 최소 베팅 **{CORRIDOR_MIN_BET:,}원**"
    )
