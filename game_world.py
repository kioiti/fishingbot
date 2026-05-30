"""월드 확장: 지역·날씨·시간대, 월드보스, 파편, 탐험, 수족관, 낚시대 옵션"""
from __future__ import annotations

import datetime
import random
import time
from typing import Callable, Dict, List, Optional, Tuple

from fishing_data import Fish, FISH_TABLE, clamp

# ── KST 시간대 (유령물고기: 밤 12~02시) ─────────────
def kst_now() -> datetime.datetime:
    return datetime.datetime.utcnow() + datetime.timedelta(hours=9)


def kst_hour() -> int:
    return kst_now().hour


def is_ghost_fish_hour() -> bool:
    """KST 0~2시 (자정~새벽 2시) 유령물고기 시간."""
    return kst_hour() in (0, 1, 2)


# ── 지역 전용·시간대·날씨 물고기 ───────────────────
GHOST_FISH_IDS = ("spectral_eel", "phantom_koi", "wraith_shark")

MAP_EXCLUSIVE: Dict[str, List[str]] = {
    "volcano": ("lava_piranha", "phoenix_koi", "storm_ray"),
    "glacier": ("glacier_eel", "moon_jelly", "oarfish"),
    "lab": ("vampire_squid", "timeworn_relic", "nautilus"),
    "abyss": ("abyssal_heart", "kraken_tentacle", "vampire_squid"),
    "cosmic": ("genesis_fish", "cosmic_anchor", "starlight_whale"),
}

# 날씨별 추가 가중 (기존 rarity_bonus 외)
WEATHER_RARITY_EXTRA: Dict[str, Dict[str, float]] = {
    "storm": {"mythic": 0.035, "epic": 0.02},       # 폭우/폭풍 → 심해·신화
    "rain": {"mythic": 0.02, "epic": 0.015},
    "fog": {"legendary": 0.05, "epic": 0.02},       # 안개 → 전설
    "aurora": {"legendary": 0.03, "mythic": 0.02},
    "blood_moon": {"mythic": 0.04, "legendary": 0.03},
}

FRAGMENT_ITEM_ID = "abyss_fragment"
FRAGMENT_CRAFT_COUNT = 100
FRAGMENT_DROP_CHANCE = 0.045

WORLD_BOSS_INFO = {
    "id": "kraken",
    "name": "🐙 대양의 크라켄",
    "desc": "서버 전체가 맞서는 월드 레이드",
    "hp_mult": 12.0,
    "base_reward": 800_000,
    "drop_item": "bait_gold",
    "drop_rate": 0.35,
    "fragment_min": 3,
    "fragment_max": 8,
    "duration_sec": 3 * 3600,
    "cooldown_days": 3,
}

EXPEDITION_HOURS_DEFAULT = 3
EXPEDITION_SEC_PER_HOUR = 3600

SHIP_PARTS = ("engine", "hold", "crew", "radar")
SHIP_PART_NAMES = {
    "engine": "⚙️ 엔진",
    "hold": "📦 저장고",
    "crew": "👥 선원",
    "radar": "📡 레이더",
}

AFFIX_TYPES: Dict[str, dict] = {
    "cooldown": {"name": "낚시 쿨타임", "unit": "초", "min": 0.3, "max": 1.5},
    "legendary": {"name": "전설 확률", "unit": "%", "min": 0.01, "max": 0.05},
    "chest": {"name": "상자 확률", "unit": "%", "min": 0.02, "max": 0.08},
    "boss_dmg": {"name": "보스 피해", "unit": "%", "min": 0.05, "max": 0.20},
    "sell": {"name": "판매가", "unit": "%", "min": 0.03, "max": 0.12},
    "fragment": {"name": "파편 드랍", "unit": "%", "min": 0.01, "max": 0.04},
}

BROADCAST_MYTHIC_CHANCE = 1.0
BROADCAST_LEGENDARY_CHANCE = 0.35


def weather_fishing_hint(weather_id: str) -> str:
    hints = {
        "storm": "⛈️ 폭풍 — 심해·신화 등장 ↑",
        "rain": "🌧️ 비 — 심해어 확률 ↑",
        "fog": "🌫️ 안개 — 전설 등장 ↑",
        "aurora": "🌌 오로라 — 희귀 물고기 ↑",
        "blood_moon": "🌑 블러드문 — 신화·전설 ↑",
    }
    base = hints.get(weather_id, "")
    if is_ghost_fish_hour():
        base = (base + " · " if base else "") + "👻 유령물고기 시간 (KST 0~2시)"
    return base


def apply_weather_rarity_shift(weights: Dict[str, float], weather_id: str) -> Dict[str, float]:
    extra = WEATHER_RARITY_EXTRA.get(weather_id)
    if not extra:
        return weights
    w = dict(weights)
    take = 0.0
    for rarity, boost in extra.items():
        if rarity not in w:
            continue
        steal = clamp(w["common"] * boost * 2.5, 0.0, w["common"] - 0.04)
        take += steal
        w[rarity] = w.get(rarity, 0) + steal
    if take > 0:
        w["common"] = max(0.04, w["common"] - take)
    s = sum(w.values()) or 1.0
    return {k: v / s for k, v in w.items()}


def _fish_by_id(fid: str) -> Optional[Fish]:
    for f in FISH_TABLE:
        if f.id == fid:
            return f
    return None


def choose_context_fish(
    rarity: str,
    map_id: str,
    weather_id: str,
    ghost_hour: bool,
) -> Fish:
    pool: List[Fish] = [f for f in FISH_TABLE if f.rarity == rarity]
    if not pool:
        pool = [f for f in FISH_TABLE if f.rarity == "common"]

    exclusive = list(MAP_EXCLUSIVE.get(map_id, ()))
    if ghost_hour and rarity in ("epic", "legendary", "mythic"):
        for gid in GHOST_FISH_IDS:
            g = _fish_by_id(gid)
            if g and g.rarity == rarity:
                if random.random() < 0.22:
                    return g

    if exclusive and random.random() < 0.38:
        ex_pool = [_fish_by_id(fid) for fid in exclusive]
        ex_pool = [f for f in ex_pool if f and f.rarity == rarity]
        if ex_pool:
            return random.choice(ex_pool)

    if weather_id == "fog" and rarity == "legendary" and random.random() < 0.25:
        leg = [f for f in pool if f.rarity == "legendary"]
        if leg:
            return random.choice(leg)

    return random.choice(pool)


def make_fish_picker(map_id: str, weather_id: str) -> Callable[[str], Fish]:
    ghost = is_ghost_fish_hour()

    def picker(rarity: str) -> Fish:
        return choose_context_fish(rarity, map_id, weather_id, ghost)

    return picker


def roll_fragment_drop(rod_level: int, affix_bonus: float = 0.0) -> int:
    chance = FRAGMENT_DROP_CHANCE + min(0.03, rod_level * 0.001) + affix_bonus
    if random.random() >= chance:
        return 0
    return random.randint(1, 2 if rod_level >= 15 else 1)


def roll_affix() -> dict:
    aid = random.choice(list(AFFIX_TYPES.keys()))
    spec = AFFIX_TYPES[aid]
    val = round(random.uniform(spec["min"], spec["max"]), 4)
    return {"id": aid, "value": val, "locked": False}


def format_affix_line(aff: dict) -> str:
    spec = AFFIX_TYPES.get(aff.get("id", ""), {})
    val = float(aff.get("value", 0))
    unit = spec.get("unit", "")
    if unit == "%":
        return f"{spec.get('name', aff['id'])} +{val*100:.1f}%"
    if unit == "초":
        return f"{spec.get('name', aff['id'])} -{val:.1f}초"
    return f"{spec.get('name', aff['id'])} +{val}"


def affix_cooldown_bonus(affixes: List[dict]) -> float:
    return sum(float(a["value"]) for a in affixes if a.get("id") == "cooldown")


def affix_rarity_bonus(affixes: List[dict]) -> float:
    return sum(float(a["value"]) for a in affixes if a.get("id") == "legendary")


def affix_chest_bonus(affixes: List[dict]) -> float:
    return sum(float(a["value"]) for a in affixes if a.get("id") == "chest")


def affix_boss_bonus(affixes: List[dict]) -> float:
    return sum(float(a["value"]) for a in affixes if a.get("id") == "boss_dmg")


def affix_fragment_bonus(affixes: List[dict]) -> float:
    return sum(float(a["value"]) for a in affixes if a.get("id") == "fragment")


def default_world_boss_state() -> dict:
    return {"active": False, "last_spawn_day": ""}


def world_boss_spawn(max_hp: int, now_ts: int) -> dict:
    info = WORLD_BOSS_INFO
    return {
        "active": True,
        "kind": "world",
        "name": info["name"],
        "hp": max_hp,
        "max_hp": max_hp,
        "spawned_at": now_ts,
        "ends_at": now_ts + int(info["duration_sec"]),
        "contributors": {},
        "last_hit": None,
    }


def default_expedition() -> dict:
    return {}


def default_ship() -> dict:
    return {p: 0 for p in SHIP_PARTS}


def default_aquarium() -> dict:
    return {
        "level": 1,
        "display": [],
        "likes": 0,
        "liked_by": [],
        "last_income_ts": 0,
        "pending_income": 0,
    }


def aquarium_max_slots(level: int) -> int:
    return min(12, 2 + level)


def aquarium_income_per_hour(level: int, display_count: int) -> int:
    return int((500 + level * 200) * max(1, display_count))


def roll_expedition_rewards(ship: dict, hours: int) -> Tuple[List[str], List[tuple]]:
    engine = int(ship.get("engine", 0))
    hold = int(ship.get("hold", 0))
    crew = int(ship.get("crew", 0))
    radar = int(ship.get("radar", 0))
    lines: List[str] = []
    rewards: List[tuple] = []
    rolls = 2 + hold + hours
    for _ in range(rolls):
        r = random.random()
        if r < 0.04 + radar * 0.01:
            lines.append("🗺️ **보물지도** 조각!")
            rewards.append(("fragment", 2))
        elif r < 0.08 + engine * 0.015:
            lines.append("🐟 **희귀 어종** 발견!")
            rewards.append(("fish_rarity", "rare"))
        elif r < 0.12 + crew * 0.02:
            qty = random.randint(5, 15 + hold * 3)
            lines.append(f"🪱 **미끼** x{qty}")
            rewards.append(("item", "bait_worm", qty))
        elif r < 0.15:
            amt = random.randint(3000, 12000 + engine * 2000)
            lines.append(f"💰 **{amt:,}원**")
            rewards.append(("money", amt))
        elif r < 0.18:
            lines.append("⚓ **침몰선** — 파편 +1")
            rewards.append(("fragment", 1))
        elif r < 0.20:
            lines.append("☠️ **저주의 유물** (행운의 주화)")
            rewards.append(("item", "lucky_coin", 1))
        else:
            amt = random.randint(500, 3000)
            lines.append(f"🌊 평범한 항해 (+{amt:,}원)")
            rewards.append(("money", amt))
    return lines, rewards


def expedition_duration_sec(hours: int) -> int:
    h = max(1, min(6, int(hours)))
    return h * EXPEDITION_SEC_PER_HOUR


def ship_upgrade_cost(part: str, level: int) -> int:
    base = {"engine": 25000, "hold": 30000, "crew": 35000, "radar": 40000}
    return int(base.get(part, 30000) * (1.55 ** level))
