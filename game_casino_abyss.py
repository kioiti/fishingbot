"""미친 도박: 운명의 심연 — 초저확률 초고배당"""
from __future__ import annotations

import random
from typing import Dict, List, Tuple

ABYSS_MIN_BET = 10_000
ABYSS_MAX_BET = 500_000
ABYSS_POT_RATE = 0.04  # 베팅의 4%가 심연 잭팟 적립
MAX_PAYOUT_CAP = 80_000_000  # 1회 최대 지급 8천만

# (이름, 배율, 가중치) — 가중치 합 10000 기준
ABYSS_OUTCOMES: List[Tuple[str, float, int]] = [
    ("💀 심연에 삼켜짐", 0.0, 6200),
    ("🕳️ 깊은 추락", 0.15, 1100),
    ("😰 손실 회수", 0.45, 900),
    ("😐 아무 일도", 0.85, 700),
    ("🙂 작은 반짝", 1.5, 550),
    ("😄 괜찮은 날", 3.0, 320),
    ("🔥 불타오름", 8.0, 150),
    ("⚡ 번개 명중", 25.0, 55),
    ("👑 전설의 심연", 100.0, 18),
    ("🌌 우주 대박", 500.0, 5),
    ("☄️ 신의 눈동자", 2000.0, 2),
]

# 심연 잭팟 풀 전체 획득 (베팅과 별도)
ABYSS_POT_JACKPOT_CHANCE = 0.0008  # 0.08%


def default_abyss_pot() -> dict:
    return {"pot": 0}


def roll_abyss(bet: int) -> dict:
    weights = [w for _, _, w in ABYSS_OUTCOMES]
    idx = random.choices(range(len(ABYSS_OUTCOMES)), weights=weights, k=1)[0]
    name, mult, _ = ABYSS_OUTCOMES[idx]
    pot_hit = random.random() < ABYSS_POT_JACKPOT_CHANCE
    return {
        "tier": name,
        "mult": float(mult),
        "pot_hit": pot_hit,
        "index": idx,
    }


def calc_payout(bet: int, mult: float, pot_amount: int = 0, pot_hit: bool = False) -> int:
    base = int(bet * mult)
    if pot_hit and pot_amount > 0:
        base += int(pot_amount)
    return min(MAX_PAYOUT_CAP, max(0, base))


def odds_table_text() -> str:
    total = sum(w for _, _, w in ABYSS_OUTCOMES)
    lines = ["**☄️ 운명의 심연 — 등급별 확률**"]
    for name, mult, w in ABYSS_OUTCOMES:
        pct = w / total * 100
        mult_txt = "전멸" if mult <= 0 else f"x{mult:g}"
        lines.append(f"- {name}: **{pct:.2f}%** ({mult_txt})")
    lines.append(
        f"- 🎰 **심연 잭팟 풀** 단독 당첨: **{ABYSS_POT_JACKPOT_CHANCE*100:.3f}%** (풀 전액 + 기본 배당)"
    )
    lines.append(f"- 베팅 **{ABYSS_MIN_BET:,}~{ABYSS_MAX_BET:,}원** · 1회 최대 지급 **{MAX_PAYOUT_CAP:,}원**")
    return "\n".join(lines)
