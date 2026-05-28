from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple
import random


@dataclass(frozen=True)
class Fish:
    id: str
    name: str
    rarity: str  # common|rare|epic|legendary|mythic
    sell: int


RARITY_ORDER: List[str] = ["common", "rare", "epic", "legendary", "mythic"]
RARITY_LABEL: Dict[str, str] = {
    "common": "일반",
    "rare": "희귀",
    "epic": "영웅",
    "legendary": "전설",
    "mythic": "신화",
}
RARITY_FLAIR: Dict[str, str] = {
    "common": "🐟",
    "rare": "✨",
    "epic": "🗡️",
    "legendary": "👑",
    "mythic": "☄️",
}


FISH_TABLE: List[Fish] = [
    Fish("anchovy", "멸치", "common", 25),
    Fish("mackerel", "고등어", "common", 35),
    Fish("squid", "오징어", "common", 45),
    Fish("carp", "잉어", "common", 60),
    Fish("pollock", "명태", "common", 40),
    Fish("cod", "대구", "common", 55),
    Fish("sea_bream", "도미", "common", 70),
    Fish("flatfish", "광어", "common", 85),
    Fish("octopus", "문어", "common", 95),
    Fish("eel", "장어", "rare", 180),
    Fish("salmon", "연어", "rare", 220),
    Fish("shrimp", "새우", "rare", 160),
    Fish("lobster", "바닷가재", "rare", 320),
    Fish("pufferfish", "복어", "rare", 420),
    Fish("catfish", "메기", "rare", 260),
    Fish("tuna", "참치", "epic", 800),
    Fish("marlin", "청새치", "epic", 1100),
    Fish("anglerfish", "아귀", "epic", 900),
    Fish("swordfish", "황새치", "epic", 1350),
    Fish("giant_grouper", "자이언트 그루퍼", "epic", 1600),
    Fish("bluefin_tuna", "참다랑어", "epic", 1800),
    Fish("golden_koi", "황금잉어", "legendary", 9000),
    Fish("pearl_oyster", "진주 조개", "legendary", 6500),
    Fish("crystal_squid", "수정 오징어", "legendary", 12000),
    Fish("ancient_seahorse", "고대 해마", "legendary", 15000),
    Fish("storm_ray", "폭풍 가오리", "legendary", 17500),
    Fish("leviathan_scale", "레비아탄 비늘", "mythic", 45000),
    Fish("abyssal_heart", "심연의 심장", "mythic", 65000),
    Fish("sea_dragon_fin", "해룡의 지느러미", "mythic", 82000),
    Fish("timeworn_relic", "시간에 닳은 유물", "mythic", 120000),
]


RODS: Dict[str, dict] = {
    "rookie": {
        "name": "초보 낚시대",
        "price": 0,
        "passive": {"type": "none"},
    },
    "flame": {
        "name": "화염 낚시대",
        "price": 25000,
        "passive": {"type": "rarity_bonus", "value": 0.15},
    },
    "thunder": {
        "name": "번개 낚시대",
        "price": 35000,
        "passive": {"type": "cooldown_bonus", "value": 0.15},
    },
    "deepsea": {
        "name": "심해 낚시대",
        "price": 50000,
        "passive": {"type": "boss_bonus", "value": 0.20},
    },
}


def clamp(n: float, a: float, b: float) -> float:
    return max(a, min(b, n))


def get_base_cooldown_seconds(rod_level: int) -> int:
    if rod_level >= 15:
        return 6
    if rod_level >= 10:
        return 9
    if rod_level >= 5:
        return 12
    return 15


def get_legendary_bonus_by_level(rod_level: int) -> float:
    if rod_level >= 15:
        return 0.029
    if rod_level >= 10:
        return 0.009
    return 0.000


def get_rarity_weights(rod_level: int, rod_type: str) -> Dict[str, float]:
    base = {
        "common": 0.78,
        "rare": 0.17,
        "epic": 0.045,
        "legendary": 0.004,
        "mythic": 0.001,
    }

    bonus_leg = get_legendary_bonus_by_level(rod_level)
    if bonus_leg > 0:
        steal_from_common = clamp(bonus_leg * 1.2, 0.0, base["common"] - 0.40)
        base["common"] -= steal_from_common
        base["legendary"] += bonus_leg
        base["epic"] += (steal_from_common - bonus_leg) * 0.55
        base["rare"] += (steal_from_common - bonus_leg) * 0.45

    passive = (RODS.get(rod_type) or RODS["rookie"])["passive"]
    if passive.get("type") == "rarity_bonus":
        boost = float(passive.get("value", 0.0))
        take = clamp(base["common"] * boost, 0.0, base["common"] - 0.35)
        base["common"] -= take
        base["rare"] += take * 0.55
        base["epic"] += take * 0.30
        base["legendary"] += take * 0.13
        base["mythic"] += take * 0.02

    s = sum(base.values())
    for k in list(base.keys()):
        base[k] = base[k] / s
    return base


def choose_rarity(weights: Dict[str, float]) -> str:
    r = random.random()
    acc = 0.0
    for rarity in RARITY_ORDER:
        acc += float(weights.get(rarity, 0.0))
        if r <= acc:
            return rarity
    return "common"


def choose_fish(rarity: str) -> Fish:
    pool = [f for f in FISH_TABLE if f.rarity == rarity]
    if not pool:
        pool = [f for f in FISH_TABLE if f.rarity == "common"]
    return random.choice(pool)


def format_fish_catch(fish: Fish) -> str:
    flair = RARITY_FLAIR.get(fish.rarity, "🐟")
    label = RARITY_LABEL.get(fish.rarity, fish.rarity)
    return f"{flair} {label} 물고기 등장! **{fish.name}** (판매가: {fish.sell}원)"


def format_rod_name(rod_type: str, rod_level: int) -> str:
    rod = RODS.get(rod_type) or RODS["rookie"]
    return f"{rod['name']} +{rod_level}"


def upgrade_cost(rod_level: int) -> int:
    base = 500
    return int(base * (1.65 ** rod_level))


def upgrade_success_rate(rod_level: int) -> float:
    if rod_level < 5:
        return 0.85
    if rod_level < 10:
        return 0.60
    if rod_level < 15:
        return 0.35
    if rod_level < 20:
        return 0.18
    return 0.10


def upgrade_try(rod_level: int) -> Tuple[bool, int]:
    rate = upgrade_success_rate(rod_level)
    ok = random.random() < rate
    return ok, rod_level + 1 if ok else rod_level


def boss_default_state() -> dict:
    return {
        "active": False,
        "hp": 0,
        "max_hp": 0,
        "spawned_at": 0,
        "ends_at": 0,
        "last_spawn_day": "",
        "contributors": {},  # user_id -> damage
        "last_hit": None,  # user_id
        "name": "심해의 거대어",
    }


def boss_spawn(max_hp: int, now_ts: int, duration_seconds: int) -> dict:
    s = boss_default_state()
    s["active"] = True
    s["hp"] = max_hp
    s["max_hp"] = max_hp
    s["spawned_at"] = now_ts
    s["ends_at"] = now_ts + duration_seconds
    s["contributors"] = {}
    s["last_hit"] = None
    return s

