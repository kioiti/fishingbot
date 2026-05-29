"""재미 컨텐츠: 펫, 행운판, 토너먼트, 물고기 퀴즈, 출석 연속 등"""
from __future__ import annotations

import datetime
import random
import time
from typing import Dict, List, Optional, Tuple

# ── 펫 ────────────────────────────────────────────
PETS: Dict[str, dict] = {
    "pet_crab": {"name": "🦀 집게벌레", "emoji": "🦀", "desc": "초보의 든든한 동료"},
    "pet_otter": {"name": "🦦 수달", "emoji": "🦦", "desc": "장난꾸러기, 희귀어에 관심"},
    "pet_penguin": {"name": "🐧 펭귄", "emoji": "🐧", "desc": "차가운 바다의 전문가"},
    "pet_dragon": {"name": "🐲 미니 용", "emoji": "🐲", "desc": "전설을 좇는 수호자"},
}

PET_MAX_LEVEL = 20
PET_XP_PER_FEED = 25
PET_FEED_COST = 5000
PET_FEED_FISH_COMMON = 3

# 레벨당 보너스 (낚시 시)
def pet_rarity_bonus(level: int) -> float:
    return min(0.06, level * 0.003)


def pet_shiny_bonus(level: int) -> float:
    return min(0.02, level * 0.001)


def pet_xp_to_level(xp: int) -> int:
    lv = 1
    need = 50
    rem = max(0, xp)
    while lv < PET_MAX_LEVEL and rem >= need:
        rem -= need
        lv += 1
        need = 40 + lv * 15
    return lv


def pet_level_progress(xp: int) -> Tuple[int, int, int]:
    """(level, xp_in_level, xp_for_next)"""
    lv = 1
    need = 50
    rem = max(0, xp)
    while lv < PET_MAX_LEVEL:
        if rem < need:
            return lv, rem, need
        rem -= need
        lv += 1
        need = 40 + lv * 15
    return PET_MAX_LEVEL, 0, 0


# ── 무료 행운판 (일 1회) ──────────────────────────
DAILY_WHEEL_POOL: List[dict] = [
    {"weight": 28, "type": "money", "min": 2000, "max": 12000, "label": "💰 소액"},
    {"weight": 22, "type": "money", "min": 15000, "max": 35000, "label": "💰 중액"},
    {"weight": 18, "type": "item", "id": "bait_worm", "min": 3, "max": 10, "label": "🐛 지렁이"},
    {"weight": 12, "type": "item", "id": "bait_shrimp", "min": 1, "max": 4, "label": "🦐 새우"},
    {"weight": 8, "type": "item", "id": "lucky_coin", "min": 1, "max": 1, "label": "🪙 행운주화"},
    {"weight": 6, "type": "chest", "id": "chest_wood", "min": 1, "max": 2, "label": "📦 나무상자"},
    {"weight": 4, "type": "chest", "id": "chest_silver", "min": 1, "max": 1, "label": "📦 은상자"},
    {"weight": 1.5, "type": "money", "min": 80000, "max": 150000, "label": "🎉 대박"},
    {"weight": 0.5, "type": "item", "id": "scroll_protect", "min": 1, "max": 1, "label": "📜 보호주문서"},
]


def roll_daily_wheel() -> dict:
    weights = [float(x["weight"]) for x in DAILY_WHEEL_POOL]
    return dict(random.choices(DAILY_WHEEL_POOL, weights=weights, k=1)[0])


# ── 주말 낚시 토너먼트 점수 ───────────────────────
TOURNAMENT_SCORE: Dict[str, int] = {
    "common": 5,
    "rare": 15,
    "epic": 40,
    "legendary": 120,
    "mythic": 350,
}

TOURNAMENT_PRIZES = [
    (1, 200_000),
    (2, 120_000),
    (3, 80_000),
    (4, 50_000),
    (5, 30_000),
]


def is_tournament_active() -> bool:
    """금·토·일 토너먼트 시즌"""
    wd = datetime.datetime.now().weekday()
    return wd in (4, 5, 6)


def tournament_weekend_key() -> str:
    """해당 주말 시즌 ID (금요일 기준 주)"""
    return time.strftime("%Y-%W-tourney", time.gmtime())


def fish_tournament_points(rarity: str, is_shiny: bool = False) -> int:
    base = TOURNAMENT_SCORE.get(rarity, 5)
    if is_shiny:
        base = int(base * 1.5)
    return base


# ── 출석 연속 보상 ────────────────────────────────
STREAK_BONUS_TABLE: Dict[int, int] = {
    3: 10_000,
    7: 35_000,
    14: 80_000,
    30: 200_000,
}


def streak_extra_reward(streak: int) -> int:
    bonus = 0
    for days, amt in sorted(STREAK_BONUS_TABLE.items()):
        if streak >= days:
            bonus = max(bonus, amt)
    return bonus + max(0, (streak - 1) * 500)


# ── 물고기 퀴즈 ───────────────────────────────────
QUIZ_REWARD_MIN = 5000
QUIZ_REWARD_MAX = 25000
QUIZ_COOLDOWN_SEC = 300


def pick_quiz_fish(fish_table: list) -> dict:
    """fish_table: list of Fish objects with .id .name .rarity"""
    pool = list(fish_table)
    if not pool:
        return {"id": "?", "name": "물고기", "rarity": "common"}
    f = random.choice(pool)
    return {"id": f.id, "name": f.name, "rarity": f.rarity}


def build_quiz_choices(correct: dict, fish_table: list, n: int = 4) -> List[dict]:
    names = {correct["name"]}
    choices = [correct]
    others = [f for f in fish_table if f.name not in names]
    random.shuffle(others)
    for f in others:
        if len(choices) >= n:
            break
        choices.append({"id": f.id, "name": f.name, "rarity": f.rarity})
        names.add(f.name)
    while len(choices) < n and fish_table:
        f = random.choice(fish_table)
        if f.name not in names:
            choices.append({"id": f.id, "name": f.name, "rarity": f.rarity})
            names.add(f.name)
    random.shuffle(choices)
    return choices


# ── 잭팟 페스타 (금토일) ───────────────────────────
def is_jackpot_festa() -> bool:
    return datetime.datetime.now().weekday() in (4, 5, 6)


JACKPOT_FESTA_MULT = 2.0
