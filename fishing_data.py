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
    Fish("neon_tetra", "네온 테트라", "common", 38),
    Fish("rockfish", "우럭", "common", 68),
    Fish("abalone", "전복", "common", 120),
    Fish("horse_mackerel", "전갱이", "common", 48),
    Fish("flounder", "도다리", "common", 90),
    Fish("rainbow_trout", "무지개송어", "rare", 240),
    Fish("king_crab", "킹크랩", "rare", 580),
    Fish("moray_eel", "곰치", "rare", 440),
    Fish("sawshark", "톱상어", "rare", 490),
    Fish("nautilus", "앵무조개", "rare", 350),
    Fish("ghost_shark", "유령상어", "epic", 1900),
    Fish("sunfish", "개복치", "epic", 2300),
    Fish("oarfish", "산갈치", "epic", 2800),
    Fish("vampire_squid", "흡혈오징어", "epic", 2500),
    Fish("emperor_fish", "황제어", "legendary", 24000),
    Fish("kraken_tentacle", "크라켄 촉수", "legendary", 35000),
    Fish("starlight_whale", "별빛 고래", "legendary", 42000),
    Fish("chaos_shark", "혼돈의 상어", "mythic", 180000),
    Fish("eternal_coral", "영원의 산호", "mythic", 220000),
    Fish("genesis_fish", "태초의 물고기", "mythic", 350000),
    Fish("spectral_eel", "유령 장어", "epic", 3400),
    Fish("phantom_koi", "망령 잉어", "legendary", 40000),
    Fish("wraith_shark", "원혼 상어", "mythic", 290000),
]


ROD_PASSIVE_DESC: Dict[str, str] = {
    "none": "기본형",
    "rarity_bonus": "희귀도 ↑",
    "cooldown_bonus": "쿨타임 ↓",
    "boss_bonus": "보스 피해 ↑",
    "crit_bonus": "보스 크리 ↑",
    "sell_bonus": "판매가 ↑",
    "combo": "복합 특성",
}


RODS: Dict[str, dict] = {
    "rookie": {
        "name": "🐟 초보 낚시대",
        "price": 0,
        "req_level": 0,
        "passive": {"type": "none"},
    },
    "bamboo": {
        "name": "🎋 대나무 낚시대",
        "price": 8000,
        "req_level": 0,
        "passive": {"type": "cooldown_bonus", "value": 0.08},
    },
    "flame": {
        "name": "🔥 화염 낚시대",
        "price": 25000,
        "req_level": 3,
        "passive": {"type": "rarity_bonus", "value": 0.15},
    },
    "thunder": {
        "name": "⚡ 번개 낚시대",
        "price": 35000,
        "req_level": 5,
        "passive": {"type": "cooldown_bonus", "value": 0.18},
    },
    "deepsea": {
        "name": "🌊 심해 낚시대",
        "price": 50000,
        "req_level": 7,
        "passive": {"type": "boss_bonus", "value": 0.20},
    },
    "frost": {
        "name": "❄️ 빙하 낚시대",
        "price": 120000,
        "req_level": 10,
        "passive": {"type": "combo", "rarity": 0.10, "cooldown": 0.10},
    },
    "dragon": {
        "name": "🐉 용암 낚시대",
        "price": 200000,
        "req_level": 12,
        "passive": {"type": "combo", "boss": 0.25, "crit": 0.05},
    },
    "phantom": {
        "name": "👻 유령 낚시대",
        "price": 350000,
        "req_level": 15,
        "passive": {"type": "crit_bonus", "value": 0.12},
    },
    "golden": {
        "name": "✨ 황금 낚시대",
        "price": 500000,
        "req_level": 18,
        "passive": {"type": "sell_bonus", "value": 0.25},
    },
    "cosmic_rod": {
        "name": "🌌 코스믹 낚시대",
        "price": 800000,
        "req_level": 20,
        "passive": {"type": "combo", "rarity": 0.18, "boss": 0.15},
    },
    "leviathan": {
        "name": "☄️ 레비아탄 낚시대",
        "price": 1500000,
        "req_level": 22,
        "passive": {"type": "combo", "boss": 0.30, "crit": 0.10, "rarity": 0.12},
    },
    "sovereign": {
        "name": "👑 심연 군주 낚시대",
        "price": 0,
        "req_level": 20,
        "passive": {"type": "combo", "rarity": 0.22, "boss": 0.20, "crit": 0.08},
        "craft_only": True,
    },
}


def rod_passive_text(rod_id: str) -> str:
    rod = RODS.get(rod_id) or RODS["rookie"]
    p = rod.get("passive", {})
    t = p.get("type", "none")
    if t == "none":
        return ROD_PASSIVE_DESC["none"]
    if t == "combo":
        parts = []
        if "rarity" in p:
            parts.append(f"희귀+{int(p['rarity']*100)}%")
        if "cooldown" in p:
            parts.append(f"쿨-{int(p['cooldown']*100)}%")
        if "boss" in p:
            parts.append(f"보스+{int(p['boss']*100)}%")
        if "crit" in p:
            parts.append(f"크리+{int(p['crit']*100)}%p")
        return " / ".join(parts) if parts else "복합"
    v = p.get("value", 0)
    return f"{ROD_PASSIVE_DESC.get(t, t)} {int(v*100)}%"


def spin_slot() -> Tuple[str, str, str, float, bool, str]:
    """슬롯 1회. 반환: (a,b,c, 배당배수, 잭팟여부, 결과라벨)"""
    symbols = ["🍒", "🍋", "🍇", "🔔", "⭐", "7️⃣"]
    weights = [20, 18, 17, 16, 15, 14]
    a, b, c = random.choices(symbols, weights=weights, k=3)

    payout_mult = 0.0
    label = "꽝"
    jackpot_hit = False

    if a == b == c == "7️⃣":
        payout_mult = 18.0
        jackpot_hit = True
        label = "💥 잭팟 7"
    elif a == b == c == "⭐":
        payout_mult = 7.0
        label = "⭐ 3연속"
    elif a == b == c == "🔔":
        payout_mult = 5.0
        label = "🔔 3연속"
    elif a == b == c:
        payout_mult = 3.0
        label = f"{a} 3연속"
    elif (a == b == "7️⃣") or (a == c == "7️⃣") or (b == c == "7️⃣"):
        payout_mult = 3.5
        label = "7️⃣ 더블"
    elif len({a, b, c}) == 2:
        payout_mult = 1.85
        label = "2매칭"
    elif "🍒" in (a, b, c):
        payout_mult = 0.85
        label = "🍒 체리 터치"
    elif "⭐" in (a, b, c):
        payout_mult = 0.45
        label = "⭐ 스타 터치"

    return a, b, c, payout_mult, jackpot_hit, label


SLOT_WIN_FEE = 0.005
SLOT_JACKPOT_RATE = 0.015


# ── 낚시 보물 상자 ──────────────────────────────────────────
CHESTS: Dict[str, dict] = {
    "chest_wood": {
        "name": "🪵 나무 보물상자",
        "desc": "초보가 자주 낚는 상자",
        "rewards": [
            {"chance": 0.35, "type": "money", "min": 800, "max": 4000},
            {"chance": 0.30, "type": "item", "id": "bait_worm", "min": 1, "max": 4},
            {"chance": 0.25, "type": "fish_rarity", "rarity": "common", "min": 1, "max": 3},
            {"chance": 0.08, "type": "item", "id": "bait_shrimp", "min": 1, "max": 1},
            {"chance": 0.02, "type": "item", "id": "treasure_pearl", "min": 1, "max": 1},
        ],
    },
    "chest_silver": {
        "name": "🥈 은 보물상자",
        "desc": "괜찮은 전리품",
        "rewards": [
            {"chance": 0.28, "type": "money", "min": 4000, "max": 15000},
            {"chance": 0.22, "type": "item", "id": "bait_shrimp", "min": 1, "max": 3},
            {"chance": 0.20, "type": "fish_rarity", "rarity": "rare", "min": 1, "max": 2},
            {"chance": 0.15, "type": "item", "id": "bait_gold", "min": 1, "max": 1},
            {"chance": 0.10, "type": "money", "min": 20000, "max": 35000},
            {"chance": 0.03, "type": "item", "id": "scroll_protect", "min": 1, "max": 1},
            {"chance": 0.02, "type": "item", "id": "lucky_coin", "min": 1, "max": 1},
        ],
    },
    "chest_gold": {
        "name": "🥇 금 보물상자",
        "desc": "빛나는 보물",
        "rewards": [
            {"chance": 0.22, "type": "money", "min": 15000, "max": 50000},
            {"chance": 0.20, "type": "item", "id": "bait_gold", "min": 1, "max": 2},
            {"chance": 0.18, "type": "fish_rarity", "rarity": "epic", "min": 1, "max": 1},
            {"chance": 0.15, "type": "fish_rarity", "rarity": "legendary", "min": 1, "max": 1},
            {"chance": 0.12, "type": "money", "min": 50000, "max": 90000},
            {"chance": 0.08, "type": "item", "id": "scroll_protect", "min": 1, "max": 1},
            {"chance": 0.03, "type": "item", "id": "mystic_shard", "min": 1, "max": 1},
            {"chance": 0.02, "type": "chest", "id": "chest_abyss", "min": 1, "max": 1},
        ],
    },
    "chest_abyss": {
        "name": "🌑 심연 보물상자",
        "desc": "심해에서 떠오른 상자",
        "rewards": [
            {"chance": 0.20, "type": "money", "min": 40000, "max": 120000},
            {"chance": 0.18, "type": "fish_rarity", "rarity": "legendary", "min": 1, "max": 2},
            {"chance": 0.15, "type": "item", "id": "scroll_protect", "min": 1, "max": 2},
            {"chance": 0.15, "type": "item", "id": "bait_gold", "min": 2, "max": 4},
            {"chance": 0.12, "type": "fish_rarity", "rarity": "mythic", "min": 1, "max": 1},
            {"chance": 0.10, "type": "money", "min": 100000, "max": 200000},
            {"chance": 0.05, "type": "item", "id": "mystic_shard", "min": 1, "max": 2},
            {"chance": 0.03, "type": "item", "id": "ancient_relic", "min": 1, "max": 1},
            {"chance": 0.02, "type": "chest", "id": "chest_cosmic", "min": 1, "max": 1},
        ],
    },
    "chest_cosmic": {
        "name": "🌌 코스믹 보물상자",
        "desc": "우주의 기운이 느껴진다",
        "rewards": [
            {"chance": 0.18, "type": "money", "min": 80000, "max": 250000},
            {"chance": 0.17, "type": "fish_rarity", "rarity": "mythic", "min": 1, "max": 2},
            {"chance": 0.15, "type": "item", "id": "scroll_protect", "min": 2, "max": 3},
            {"chance": 0.14, "type": "fish_rarity", "rarity": "legendary", "min": 2, "max": 3},
            {"chance": 0.12, "type": "money", "min": 200000, "max": 400000},
            {"chance": 0.10, "type": "item", "id": "mystic_shard", "min": 1, "max": 3},
            {"chance": 0.08, "type": "item", "id": "ancient_relic", "min": 1, "max": 1},
            {"chance": 0.03, "type": "item", "id": "divine_scale", "min": 1, "max": 1},
            {"chance": 0.03, "type": "chest", "id": "chest_divine", "min": 1, "max": 1},
        ],
    },
    "chest_divine": {
        "name": "👑 신성 보물상자",
        "desc": "전설급 보물만 담긴 상자",
        "rewards": [
            {"chance": 0.20, "type": "money", "min": 150000, "max": 500000},
            {"chance": 0.18, "type": "fish_rarity", "rarity": "mythic", "min": 1, "max": 3},
            {"chance": 0.15, "type": "item", "id": "scroll_protect", "min": 2, "max": 5},
            {"chance": 0.12, "type": "money", "min": 500000, "max": 1000000},
            {"chance": 0.10, "type": "item", "id": "divine_scale", "min": 1, "max": 1},
            {"chance": 0.10, "type": "item", "id": "ancient_relic", "min": 1, "max": 2},
            {"chance": 0.08, "type": "item", "id": "mystic_shard", "min": 2, "max": 5},
            {"chance": 0.05, "type": "item", "id": "lucky_coin", "min": 3, "max": 5},
            {"chance": 0.02, "type": "money", "min": 1000000, "max": 2000000},
        ],
    },
}


def _roll_chest_tier(rod_level: int, map_id: str) -> str:
    map_bonus = {
        "river": 0, "ocean": 1, "abyss": 2, "cosmic": 3,
        "volcano": 2, "glacier": 1, "lab": 2,
    }.get(map_id, 0)
    tiers: List[Tuple[str, int]] = [
        ("chest_wood", 42),
        ("chest_silver", 30),
        ("chest_gold", 16),
        ("chest_abyss", 8),
        ("chest_cosmic", 3),
        ("chest_divine", 1),
    ]
    if rod_level < 5:
        tiers = tiers[:2]
    elif rod_level < 10:
        tiers = tiers[:3]
    elif rod_level < 15:
        tiers = tiers[:4]
    elif rod_level < 20:
        tiers = tiers[:5]

    if map_bonus >= 2:
        tiers = [(k, w + (3 if "abyss" in k or "cosmic" in k else 0)) for k, w in tiers]
    if map_bonus >= 3:
        tiers = [(k, w + (5 if k == "chest_divine" else 0)) for k, w in tiers]

    ids, weights = zip(*tiers)
    return random.choices(list(ids), weights=list(weights), k=1)[0]


def roll_fishing_catch(
    rod_level: int,
    rod_type: str,
    map_id: str = "river",
    active_bait: str | None = None,
    extra_chest_chance: float = 0.0,
    extra_rarity_boost: float = 0.0,
    fish_picker=None,
    weight_adjuster=None,
) -> Tuple[str, object]:
    """반환: ('fish', Fish) 또는 ('chest', chest_id)"""
    map_bonus = {
        "river": 0.0, "ocean": 0.02, "abyss": 0.05, "cosmic": 0.08,
        "volcano": 0.04, "glacier": 0.03, "lab": 0.06,
    }.get(map_id, 0.0)
    chest_chance = 0.16 + min(0.12, rod_level * 0.004) + map_bonus + float(extra_chest_chance)

    if random.random() < chest_chance:
        return "chest", _roll_chest_tier(rod_level, map_id)

    weights = get_rarity_weights(rod_level, rod_type, map_id, active_bait)
    if weight_adjuster:
        weights = weight_adjuster(weights)
    if extra_rarity_boost > 0:
        take = clamp(weights["common"] * extra_rarity_boost, 0.0, weights["common"] - 0.05)
        weights = dict(weights)
        weights["common"] -= take
        weights["rare"] += take * 0.4
        weights["epic"] += take * 0.35
        weights["legendary"] += take * 0.2
        weights["mythic"] += take * 0.05
        s = sum(weights.values())
        for k in weights:
            weights[k] /= s
    rarity = choose_rarity(weights)
    if fish_picker:
        return "fish", fish_picker(rarity)
    return "fish", choose_fish(rarity)


def _pick_chest_reward(chest_id: str) -> dict:
    """상자 1개 개봉 보상 1종 + 30% 확률로 보너스 소액"""
    chest = CHESTS[chest_id]
    pool = chest["rewards"]
    roll = random.random()
    acc = 0.0
    chosen = pool[-1]
    for entry in pool:
        acc += float(entry["chance"])
        if roll <= acc:
            chosen = entry
            break

    result: dict = {"money": 0, "items": {}, "fish": {}, "lines": []}

    def _apply(entry: dict) -> None:
        t = entry["type"]
        if t == "money":
            amt = random.randint(int(entry["min"]), int(entry["max"]))
            result["money"] += amt
            result["lines"].append(f"💰 **{amt:,}원**")
        elif t == "item":
            iid = entry["id"]
            qty = random.randint(int(entry["min"]), int(entry["max"]))
            result["items"][iid] = result["items"].get(iid, 0) + qty
            iname = ITEMS.get(iid, {}).get("name", iid)
            result["lines"].append(f"📦 {iname} x{qty}")
        elif t == "fish_rarity":
            rarity = entry["rarity"]
            pool_f = [f for f in FISH_TABLE if f.rarity == rarity]
            if pool_f:
                f = random.choice(pool_f)
                qty = random.randint(int(entry["min"]), int(entry["max"]))
                result["fish"][f.id] = result["fish"].get(f.id, 0) + qty
                result["lines"].append(f"🐟 **{f.name}** x{qty}")
        elif t == "chest":
            cid = entry["id"]
            qty = random.randint(int(entry["min"]), int(entry["max"]))
            result["items"][cid] = result["items"].get(cid, 0) + qty
            cname = CHESTS.get(cid, {}).get("name", cid)
            result["lines"].append(f"📦 **{cname}** x{qty} (중첩 획득!)")

    _apply(chosen)
    if random.random() < 0.30:
        bonus = random.randint(500, 3000)
        result["money"] += bonus
        result["lines"].append(f"✨ 보너스 **{bonus:,}원**")
    return result


def open_chest(chest_id: str) -> dict:
    if chest_id not in CHESTS:
        return {"money": 0, "items": {}, "fish": {}, "lines": ["알 수 없는 상자"]}
    return _pick_chest_reward(chest_id)


def format_chest_drop(chest_id: str) -> str:
    c = CHESTS.get(chest_id)
    if not c:
        return f"📦 보물상자 ({chest_id})"
    return f"📦 **보물상자 등장!** {c['name']}\n`!상자깨기 {chest_id}` 또는 `!상자깨기 all`"


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
    },
    "volcano": {
        "name": "🌋 화산 지대",
        "req_level": 8,
        "fee": 25000,
        "cooldown_multiplier": 1.15,
        "rarity_weights": {
            "common": 0.45,
            "rare": 0.32,
            "epic": 0.17,
            "legendary": 0.05,
            "mythic": 0.01,
        },
    },
    "glacier": {
        "name": "❄️ 빙하 호수",
        "req_level": 7,
        "fee": 20000,
        "cooldown_multiplier": 1.1,
        "rarity_weights": {
            "common": 0.50,
            "rare": 0.30,
            "epic": 0.15,
            "legendary": 0.04,
            "mythic": 0.01,
        },
    },
    "lab": {
        "name": "🧪 버려진 연구소",
        "req_level": 12,
        "fee": 50000,
        "cooldown_multiplier": 1.25,
        "rarity_weights": {
            "common": 0.30,
            "rare": 0.35,
            "epic": 0.22,
            "legendary": 0.10,
            "mythic": 0.03,
        },
    },
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
    },
    "treasure_pearl": {
        "name": "💠 보물 진주",
        "price": 80000,
        "desc": "상자에서 나온 희귀 진주. 판매하거나 보관.",
        "type": "treasure",
    },
    "lucky_coin": {
        "name": "🪙 행운의 주화",
        "price": 50000,
        "desc": "카지노 수수료 50% 감소 (다음 1회, `!주화`로 활성화)",
        "type": "treasure",
    },
    "mystic_shard": {
        "name": "🔮 신비의 파편",
        "price": 150000,
        "desc": "고대 마력이 깃든 파편. 매우 비싸게 판매 가능.",
        "type": "treasure",
    },
    "ancient_relic": {
        "name": "🏺 고대 유물",
        "price": 300000,
        "desc": "심해 유적에서 발굴된 전설급 유물.",
        "type": "treasure",
    },
    "divine_scale": {
        "name": "🐲 신룡의 비늘",
        "price": 800000,
        "desc": "신화급 재료. 획득 확률 1~3%.",
        "type": "treasure",
    },
    "abyss_fragment": {
        "name": "🧩 심연의 파편",
        "price": 0,
        "desc": "100개 모으면 `!파편제작`으로 신화 낚시대 제작",
        "type": "material",
    },
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
    ptype = passive.get("type", "none")

    def _apply_rarity_boost(boost: float) -> None:
        nonlocal base
        take = clamp(base["common"] * boost, 0.0, base["common"] - 0.05)
        base["common"] -= take
        base["rare"] += take * 0.55
        base["epic"] += take * 0.30
        base["legendary"] += take * 0.13
        base["mythic"] += take * 0.02

    if ptype == "rarity_bonus":
        _apply_rarity_boost(float(passive.get("value", 0.0)))
    elif ptype == "combo" and passive.get("rarity"):
        _apply_rarity_boost(float(passive["rarity"]))

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

