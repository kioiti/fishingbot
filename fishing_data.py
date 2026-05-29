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
    Fish("sardine", "정어리", "common", 30),
    Fish("herring", "청어", "common", 42),
    Fish("barracuda", "바라쿠다", "common", 110),
    Fish("sea_urchin", "성게", "common", 75),
    Fish("clam", "바지락", "common", 28),
    Fish("eel", "장어", "rare", 180),
    Fish("salmon", "연어", "rare", 220),
    Fish("shrimp", "새우", "rare", 160),
    Fish("lobster", "바닷가재", "rare", 320),
    Fish("pufferfish", "복어", "rare", 420),
    Fish("catfish", "메기", "rare", 260),
    Fish("red_snapper", "붉은도미", "rare", 310),
    Fish("sea_cucumber", "해삼", "rare", 380),
    Fish("giant_crab", "대게", "rare", 520),
    Fish("stingray", "가오리", "rare", 460),
    Fish("tuna", "참치", "epic", 800),
    Fish("marlin", "청새치", "epic", 1100),
    Fish("anglerfish", "아귀", "epic", 900),
    Fish("swordfish", "황새치", "epic", 1350),
    Fish("giant_grouper", "자이언트 그루퍼", "epic", 1600),
    Fish("bluefin_tuna", "참다랑어", "epic", 1800),
    Fish("megalodon_tooth", "메갈로돈 이빨", "epic", 2600),
    Fish("glacier_eel", "빙하 장어", "epic", 2400),
    Fish("lava_piranha", "용암 피라냐", "epic", 2200),
    Fish("moon_jelly", "달빛 해파리", "epic", 2100),
    Fish("golden_koi", "황금잉어", "legendary", 9000),
    Fish("pearl_oyster", "진주 조개", "legendary", 6500),
    Fish("crystal_squid", "수정 오징어", "legendary", 12000),
    Fish("ancient_seahorse", "고대 해마", "legendary", 15000),
    Fish("storm_ray", "폭풍 가오리", "legendary", 17500),
    Fish("sunken_crown", "가라앉은 왕관", "legendary", 22000),
    Fish("phoenix_koi", "불사조 잉어", "legendary", 28000),
    Fish("void_pearl", "공허의 진주", "legendary", 32000),
    Fish("sirens_lute", "세이렌의 류트", "legendary", 26000),
    Fish("leviathan_scale", "레비아탄 비늘", "mythic", 45000),
    Fish("abyssal_heart", "심연의 심장", "mythic", 65000),
    Fish("sea_dragon_fin", "해룡의 지느러미", "mythic", 82000),
    Fish("timeworn_relic", "시간에 닳은 유물", "mythic", 120000),
    Fish("cosmic_anchor", "우주의 닻", "mythic", 160000),
    Fish("ocean_god_eye", "바다신의 눈", "mythic", 200000),
    Fish("black_tide_core", "검은 조류의 핵", "mythic", 260000),
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


MAPS: Dict[str, dict] = {
    "river": {
        "name": "🌳 초보의 강",
        "req_level": 0,
        "fee": 0,
        "cooldown_multiplier": 1.0,
        "rarity_weights": {
            "common": 0.82,
            "rare": 0.14,
            "epic": 0.04,
            "legendary": 0.00,
            "mythic": 0.00,
        }
    },
    "ocean": {
        "name": "🌊 깊은 바다",
        "req_level": 5,
        "fee": 10000,
        "cooldown_multiplier": 1.0,
        "rarity_weights": {
            "common": 0.60,
            "rare": 0.28,
            "epic": 0.10,
            "legendary": 0.017,
            "mythic": 0.003,
        }
    },
    "abyss": {
        "name": "🌋 심해의 구렁",
        "req_level": 10,
        "fee": 30000,
        "cooldown_multiplier": 1.2,
        "rarity_weights": {
            "common": 0.35,
            "rare": 0.38,
            "epic": 0.20,
            "legendary": 0.05,
            "mythic": 0.02,
        }
    },
    "cosmic": {
        "name": "🌌 코스믹 오션",
        "req_level": 15,
        "fee": 100000,
        "cooldown_multiplier": 1.5,
        "rarity_weights": {
            "common": 0.10,
            "rare": 0.25,
            "epic": 0.38,
            "legendary": 0.19,
            "mythic": 0.08,
        }
    }
}


ITEMS: Dict[str, dict] = {
    "bait_worm": {
        "name": "🐛 일반 지렁이",
        "price": 500,
        "desc": "쿨타임을 15% 단축시켜 줍니다. (낚시 1회당 1개 소모)",
        "type": "bait",
        "effect_type": "cooldown",
        "effect_value": 0.15
    },
    "bait_shrimp": {
        "name": "🦐 크릴새우",
        "price": 2000,
        "desc": "영웅 이상 물고기 확률을 보정해 줍니다. (낚시 1회당 1개 소모)",
        "type": "bait",
        "effect_type": "rarity_mid",
        "effect_value": 0.25
    },
    "bait_gold": {
        "name": "🌟 황금 미끼",
        "price": 10000,
        "desc": "전설/신화 물고기 확률을 보정해 줍니다. (낚시 1회당 1개 소모)",
        "type": "bait",
        "effect_type": "rarity_high",
        "effect_value": 0.50
    },
    "scroll_protect": {
        "name": "📜 강화 보호 주문서",
        "price": 100000,
        "desc": "+10강 이상에서 강화 실패 시 레벨 하락을 100% 방어해 줍니다. (자동 소모)",
        "type": "scroll",
        "effect_type": "protect",
        "effect_value": 0.0
    }
}


BOSS_ROTATION: Dict[int, dict] = {
    0: {
        "name": "🐙 대왕 크라켄",
        "hp_mult": 1.2,
        "base_reward": 150000,
        "drop_item": "scroll_protect",
        "drop_rate": 0.25,
        "desc": "거대한 다리로 배를 습격하는 심해의 군주입니다."
    },
    1: {
        "name": "👻 유령 더블룬선",
        "hp_mult": 1.0,
        "base_reward": 120000,
        "drop_item": "bait_gold",
        "drop_rate": 0.40,
        "desc": "바다 밑을 표류하는 고대 황금 해적선입니다."
    },
    2: {
        "name": "🌋 고대 용암 게",
        "hp_mult": 1.5,
        "base_reward": 180000,
        "drop_item": "scroll_protect",
        "drop_rate": 0.35,
        "desc": "심해 화산지대에서 서식하는 거대한 등껍질의 갑각류입니다."
    },
    3: {
        "name": "⚡ 전기 해파리 퀸",
        "hp_mult": 1.1,
        "base_reward": 130000,
        "drop_item": "bait_gold",
        "drop_rate": 0.30,
        "desc": "수만 볼트의 전류를 내뿜는 심해의 발광 생명체입니다."
    },
    4: {
        "name": "🐉 심해룡 레비아탄",
        "hp_mult": 2.0,
        "base_reward": 250000,
        "drop_item": "scroll_protect",
        "drop_rate": 0.60,
        "desc": "바다 전체를 뒤흔드는 고대 신화 속의 거대 용입니다."
    },
    5: {
        "name": "🌌 코스믹 가디언",
        "hp_mult": 2.5,
        "base_reward": 300000,
        "drop_item": "scroll_protect",
        "drop_rate": 0.80,
        "desc": "우주의 기운을 머금고 심해 속 차원문을 지키는 차원의 수호자입니다."
    },
    6: {
        "name": "👑 바다신 포세이돈의 환영",
        "hp_mult": 3.0,
        "base_reward": 400000,
        "drop_item": "scroll_protect",
        "drop_rate": 1.0,
        "desc": "바다신의 신성한 영혼이 실체화된 분노의 환영입니다."
    }
}


def clamp(n: float, a: float, b: float) -> float:
    return max(a, min(b, n))


def get_base_cooldown_seconds(rod_level: int) -> int:
    if rod_level >= 25:
        return 3
    if rod_level >= 20:
        return 4
    if rod_level >= 15:
        return 6
    if rod_level >= 10:
        return 9
    if rod_level >= 5:
        return 12
    return 15


def get_legendary_bonus_by_level(rod_level: int) -> float:
    if rod_level >= 25:
        return 0.089
    if rod_level >= 20:
        return 0.059
    if rod_level >= 15:
        return 0.029
    if rod_level >= 10:
        return 0.009
    return 0.000


def get_rarity_weights(rod_level: int, rod_type: str, map_id: str = "river", active_bait: str | None = None) -> Dict[str, float]:
    m = MAPS.get(map_id) or MAPS["river"]
    base = dict(m["rarity_weights"])

    bonus_leg = get_legendary_bonus_by_level(rod_level)
    if bonus_leg > 0:
        steal_from_common = clamp(bonus_leg * 1.2, 0.0, base["common"] - 0.05)
        base["common"] -= steal_from_common
        base["legendary"] += bonus_leg
        base["epic"] += (steal_from_common - bonus_leg) * 0.55
        base["rare"] += (steal_from_common - bonus_leg) * 0.45

    passive = (RODS.get(rod_type) or RODS["rookie"])["passive"]
    if passive.get("type") == "rarity_bonus":
        boost = float(passive.get("value", 0.0))
        take = clamp(base["common"] * boost, 0.0, base["common"] - 0.05)
        base["common"] -= take
        base["rare"] += take * 0.55
        base["epic"] += take * 0.30
        base["legendary"] += take * 0.13
        base["mythic"] += take * 0.02

    if active_bait:
        if active_bait == "bait_shrimp":
            boost = 0.25
            take = clamp(base["common"] * boost, 0.0, base["common"] - 0.05)
            base["common"] -= take
            base["rare"] += take * 0.60
            base["epic"] += take * 0.40
        elif active_bait == "bait_gold":
            boost = 0.50
            take = clamp(base["common"] * boost, 0.0, base["common"] - 0.05)
            base["common"] -= take
            base["legendary"] += take * 0.70
            base["mythic"] += take * 0.30

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
    if rod_level < 25:
        return 0.08
    return 0.03


def upgrade_penalty_check(rod_level: int) -> bool:
    """강화 실패 시 등급이 하락할지 여부를 판환합니다. (+10강 이상)"""
    if rod_level >= 15:
        return random.random() < 0.45
    if rod_level >= 10:
        return random.random() < 0.25
    return False


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


def boss_spawn(max_hp: int, now_ts: int, duration_seconds: int, name: str = "심해의 거대어") -> dict:
    s = boss_default_state()
    s["active"] = True
    s["hp"] = max_hp
    s["max_hp"] = max_hp
    s["spawned_at"] = now_ts
    s["ends_at"] = now_ts + duration_seconds
    s["contributors"] = {}
    s["last_hit"] = None
    s["name"] = name
    return s

