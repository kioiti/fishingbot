"""게임 확장 컨텐츠: 업적, 퀘스트, 칭호, 날씨, 뽑기, 수수권 등"""
from __future__ import annotations

import random
import time
from typing import Dict, List, Optional, Tuple

# ── 업적 ──────────────────────────────────────────
ACHIEVEMENTS: Dict[str, dict] = {
    "ach_first_fish": {"name": "🎣 첫 낚시", "desc": "첫 물고기를 낚다", "check": "fish_total", "target": 1, "reward": 3000},
    "ach_fish_100": {"name": "🐟 낚시꾼", "desc": "물고기 100마리", "check": "fish_total", "target": 100, "reward": 25000},
    "ach_fish_500": {"name": "🌊 바다의 지배자", "desc": "물고기 500마리", "check": "fish_total", "target": 500, "reward": 100000},
    "ach_chest_20": {"name": "📦 보물 사냥꾼", "desc": "상자 20개 획득", "check": "chest_total", "target": 20, "reward": 30000},
    "ach_shiny_5": {"name": "✨ 이색 수집가", "desc": "이색 물고기 5마리", "check": "shiny_total", "target": 5, "reward": 50000},
    "ach_legendary_10": {"name": "👑 전설의 손", "desc": "전설 물고기 10마리", "check": "legendary_total", "target": 10, "reward": 80000},
    "ach_mythic_3": {"name": "☄️ 신화를 낚다", "desc": "신화 물고기 3마리", "check": "mythic_total", "target": 3, "reward": 150000},
    "ach_upgrade_15": {"name": "🔨 강화 장인", "desc": "낚시대 +15 달성", "check": "rod_level", "target": 15, "reward": 100000},
    "ach_upgrade_25": {"name": "⚡ 강화 마스터", "desc": "낚시대 +25 달성", "check": "rod_level", "target": 25, "reward": 300000},
    "ach_upgrade_30": {"name": "🌟 신의 손길", "desc": "낚시대 +30 달성", "check": "rod_level", "target": 30, "reward": 500000},
    "ach_boss_10": {"name": "🐉 보스 헌터", "desc": "보스 공격 10회", "check": "boss_hits", "target": 10, "reward": 60000},
    "ach_casino_win_20": {"name": "🎰 행운아", "desc": "카지노 승리 20회", "check": "casino_wins", "target": 20, "reward": 40000},
    "ach_duel_5": {"name": "⚔️ 결투왕", "desc": "낚시 대결 5승", "check": "duel_wins", "target": 5, "reward": 70000},
    "ach_rich": {"name": "💰 부자", "desc": "보유금 100만원", "check": "money", "target": 1000000, "reward": 50000},
    "ach_gacha_30": {"name": "🎁 뽑기 중독", "desc": "뽑기 30회", "check": "gacha_total", "target": 30, "reward": 80000},
    "ach_streak_30": {
        "name": "🔥 불꽃 낚시광",
        "desc": "하루에 연속 낚시 30회 달성",
        "check": "max_streak_today",
        "target": 30,
        "reward": 120000,
    },
}

# 칭호 장착 시 능력치 (낚시·보스·판매·강화·카지노에 반영)
# rarity/chest/shiny: 확률 가산 | rare~mythic: 해당 등급 가중치 | boss/crit/sell/cooldown/fragment/upgrade_chance/casino
TITLES: Dict[str, dict] = {
    "title_rookie": {"name": "🐣 초보 낚시꾼", "req": None, "stats": {"rarity": 0.01}},
    "title_angler": {
        "name": "🎣 낚시 마스터",
        "req": "ach_fish_100",
        "stats": {"rarity": 0.025, "cooldown": 0.5},
    },
    "title_deep": {
        "name": "🌊 바다의 지배자",
        "req": "ach_fish_500",
        "stats": {"rarity": 0.03, "chest": 0.03, "sell": 0.05},
    },
    "title_chest": {
        "name": "📦 보물 사냥꾼",
        "req": "ach_chest_20",
        "stats": {"chest": 0.06, "rarity": 0.015},
    },
    "title_legend": {
        "name": "👑 전설의 낚시왕",
        "req": "ach_legendary_10",
        "stats": {"legendary": 0.07, "rarity": 0.02},
    },
    "title_mythic": {
        "name": "☄️ 신화의 그물",
        "req": "ach_mythic_3",
        "stats": {"mythic": 0.05, "legendary": 0.04, "shiny": 0.012},
    },
    "title_gambler": {
        "name": "🎰 카지노의 왕",
        "req": "ach_casino_win_20",
        "stats": {"casino": 0.015, "chest": 0.02},
    },
    "title_hunter": {
        "name": "🐉 보스 학살자",
        "req": "ach_boss_10",
        "stats": {"boss": 0.12, "crit": 0.04},
    },
    "title_shiny": {
        "name": "✨ 이색의 예술가",
        "req": "ach_shiny_5",
        "stats": {"shiny": 0.025, "rarity": 0.015},
    },
    "title_whale": {
        "name": "🐋 돈 좀 쓰는 사람",
        "req": "ach_rich",
        "stats": {"sell": 0.10, "fragment": 0.02},
    },
    "title_artisan": {
        "name": "🔨 강화 장인",
        "req": "ach_upgrade_30",
        "stats": {"upgrade_chance": 0.025, "cooldown": 0.5},
    },
    "title_duelist": {
        "name": "⚔️ 결투왕",
        "req": "ach_duel_5",
        "stats": {"boss": 0.08, "crit": 0.03},
    },
    "title_streak": {
        "name": "🔥 연소의 낚시광",
        "req": "ach_streak_30",
        "stats": {"rarity": 0.04, "shiny": 0.02, "chest": 0.03},
    },
}

STAT_LABELS: Dict[str, str] = {
    "rarity": "희귀",
    "chest": "상자",
    "shiny": "이색",
    "rare": "레어 가중",
    "epic": "에픽 가중",
    "legendary": "전설 가중",
    "mythic": "신화 가중",
    "boss": "보스 피해",
    "crit": "치명타",
    "sell": "판매가",
    "cooldown": "쿨감(초)",
    "fragment": "파편",
    "upgrade_chance": "강화 성공",
    "casino": "카지노 수수료↓",
}

# ── 일일 퀘스트 풀 ────────────────────────────────
DAILY_QUEST_POOL: List[dict] = [
    {"id": "q_fish_15", "name": "낚시 15회", "type": "fish", "target": 15, "reward": 12000},
    {"id": "q_fish_30", "name": "낚시 30회", "type": "fish", "target": 30, "reward": 28000},
    {"id": "q_chest_3", "name": "상자 3개 획득", "type": "chest", "target": 3, "reward": 15000},
    {"id": "q_sell_50000", "name": "물고기 5만원 판매", "type": "sell_gold", "target": 50000, "reward": 10000},
    {"id": "q_rare_3", "name": "희귀 이상 3마리", "type": "rare_plus", "target": 3, "reward": 20000},
    {"id": "q_casino_5", "name": "카지노 5회 플레이", "type": "casino_play", "target": 5, "reward": 8000},
    {"id": "q_boss_3", "name": "보스 공격 3회", "type": "boss_hit", "target": 3, "reward": 18000},
    {"id": "q_gacha_2", "name": "뽑기 2회", "type": "gacha", "target": 2, "reward": 5000},
]

WEEKLY_QUEST = {
    "id": "wq_fish_200",
    "name": "주간: 낚시 200회",
    "type": "fish",
    "target": 200,
    "reward": 250000,
}

# ── 날씨 ──────────────────────────────────────────
WEATHER_TYPES: Dict[str, dict] = {
    "sunny": {"name": "☀️ 맑음", "chest_bonus": 0.0, "rarity_bonus": 0.0, "shiny_bonus": 0.005},
    "cloudy": {"name": "☁️ 흐림", "chest_bonus": 0.02, "rarity_bonus": 0.03, "shiny_bonus": 0.0},
    "rain": {"name": "🌧️ 비", "chest_bonus": 0.05, "rarity_bonus": 0.05, "shiny_bonus": 0.01},
    "storm": {"name": "⛈️ 폭풍", "chest_bonus": 0.08, "rarity_bonus": 0.08, "shiny_bonus": 0.015},
    "aurora": {"name": "🌌 오로라", "chest_bonus": 0.03, "rarity_bonus": 0.12, "shiny_bonus": 0.025},
    "blood_moon": {"name": "🌑 블러드문", "chest_bonus": 0.10, "rarity_bonus": 0.15, "shiny_bonus": 0.02},
    "fog": {"name": "🌫️ 안개", "chest_bonus": 0.01, "rarity_bonus": 0.02, "shiny_bonus": 0.008},
}

# ── 뽑기 (가챠) ──────────────────────────────────
GACHA_COST = 15000
GACHA_POOL: List[dict] = [
    {"weight": 30, "type": "money", "min": 1000, "max": 8000},
    {"weight": 22, "type": "item", "id": "bait_worm", "min": 2, "max": 8},
    {"weight": 15, "type": "item", "id": "bait_shrimp", "min": 1, "max": 3},
    {"weight": 10, "type": "item", "id": "bait_gold", "min": 1, "max": 2},
    {"weight": 8, "type": "chest", "id": "chest_wood", "min": 1, "max": 2},
    {"weight": 5, "type": "chest", "id": "chest_silver", "min": 1, "max": 1},
    {"weight": 4, "type": "money", "min": 20000, "max": 50000},
    {"weight": 3, "type": "item", "id": "lucky_coin", "min": 1, "max": 1},
    {"weight": 1.5, "type": "item", "id": "scroll_protect", "min": 1, "max": 1},
    {"weight": 1, "type": "chest", "id": "chest_gold", "min": 1, "max": 1},
    {"weight": 0.5, "type": "item", "id": "mystic_shard", "min": 1, "max": 1},
    {"weight": 0.3, "type": "chest", "id": "chest_cosmic", "min": 1, "max": 1},
    {"weight": 0.2, "type": "item", "id": "divine_scale", "min": 1, "max": 1},
]

# ── 수수권 (랜덤 상인) ────────────────────────────
MYSTERY_SHOP_POOL: List[dict] = [
    {"id": "bait_gold", "discount": 0.5, "stock": 3},
    {"id": "scroll_protect", "discount": 0.7, "stock": 1},
    {"id": "bait_shrimp", "discount": 0.4, "stock": 10},
    {"id": "lucky_coin", "discount": 0.6, "stock": 2},
    {"id": "mystic_shard", "discount": 0.8, "stock": 1},
    {"id": "treasure_pearl", "discount": 0.5, "stock": 2},
]

# ── 제작 레시피 (물고기 → 아이템) ─────────────────
CRAFT_RECIPES: Dict[str, dict] = {
    "bait_worm": {"name": "🐛 지렁이", "cost": {"common": 5}, "yield": 3},
    "bait_shrimp": {"name": "🦐 크릴새우", "cost": {"rare": 3}, "yield": 2},
    "bait_gold": {"name": "🌟 황금미끼", "cost": {"epic": 2, "legendary": 1}, "yield": 1},
}

# ── 시세 (요일별 판매 배율) ───────────────────────
MARKET_DAY_MULT: Dict[int, float] = {
    0: 1.05,  # 월
    1: 0.95,
    2: 1.10,
    3: 1.00,
    4: 1.15,  # 금요일 장터
    5: 1.20,  # 토요일
    6: 0.90,
}


def today_key() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def week_key() -> str:
    return time.strftime("%Y-%W", time.gmtime())


def roll_weather() -> Tuple[str, int]:
    ids = list(WEATHER_TYPES.keys())
    weights = [18, 22, 24, 12, 9, 7, 8]
    wid = random.choices(ids, weights=weights, k=1)[0]
    until = int(time.time()) + 3600
    return wid, until


def pick_daily_quest() -> dict:
    return dict(random.choice(DAILY_QUEST_POOL))


def roll_gacha() -> dict:
    weights = [float(x["weight"]) for x in GACHA_POOL]
    return dict(random.choices(GACHA_POOL, weights=weights, k=1)[0])


def generate_mystery_shop() -> List[dict]:
    picks = random.sample(MYSTERY_SHOP_POOL, k=min(4, len(MYSTERY_SHOP_POOL)))
    out = []
    for p in picks:
        out.append({**p, "stock_left": p["stock"]})
    return out


def shiny_chance(rod_level: int, weather_id: str) -> float:
    base = 0.02 + min(0.03, rod_level * 0.001)
    w = WEATHER_TYPES.get(weather_id, WEATHER_TYPES["sunny"])
    return min(0.08, base + float(w.get("shiny_bonus", 0.0)))


def chest_chance_bonus(weather_id: str) -> float:
    return float(WEATHER_TYPES.get(weather_id, {}).get("chest_bonus", 0.0))


def market_mult_today() -> float:
    import datetime
    wd = datetime.datetime.now().weekday()
    return MARKET_DAY_MULT.get(wd, 1.0)


def achievement_current_value(profile: dict, ach_id: str, rod_level: int, money: int) -> int:
    a = ACHIEVEMENTS.get(ach_id)
    if not a:
        return 0
    check = a["check"]
    if check == "fish_total":
        return int(profile.get("fish_total", 0))
    if check == "chest_total":
        return int(profile.get("chest_total", 0))
    if check == "shiny_total":
        return int(profile.get("shiny_total", 0))
    if check == "legendary_total":
        return int(profile.get("legendary_total", 0))
    if check == "mythic_total":
        return int(profile.get("mythic_total", 0))
    if check == "rod_level":
        return rod_level
    if check == "boss_hits":
        return int(profile.get("boss_hits", 0))
    if check == "casino_wins":
        return int(profile.get("casino_wins", 0))
    if check == "duel_wins":
        return int(profile.get("duel_wins", 0))
    if check == "money":
        return money
    if check == "gacha_total":
        return int(profile.get("gacha_total", 0))
    if check == "max_streak_today":
        return int(profile.get("max_streak_today", 0))
    return 0


def achievement_progress(profile: dict, ach_id: str, rod_level: int, money: int) -> bool:
    ach_list = profile.get("achievements", [])
    if not isinstance(ach_list, list):
        ach_list = []
    if ach_id in ach_list:
        return False
    a = ACHIEVEMENTS.get(ach_id)
    if not a:
        return False
    return achievement_current_value(profile, ach_id, rod_level, money) >= int(a["target"])


def title_stats(title_id: str) -> dict:
    t = TITLES.get(title_id, {})
    return dict(t.get("stats") or {})


def format_title_stats(stats: dict) -> str:
    if not stats:
        return "특수 효과 없음"
    parts: List[str] = []
    pct_keys = {
        "rarity",
        "chest",
        "shiny",
        "rare",
        "epic",
        "legendary",
        "mythic",
        "boss",
        "crit",
        "sell",
        "fragment",
        "upgrade_chance",
        "casino",
    }
    for k, v in stats.items():
        label = STAT_LABELS.get(k, k)
        if k in pct_keys:
            parts.append(f"{label}+{int(float(v) * 100)}%")
        elif k == "cooldown":
            parts.append(f"{label}-{float(v):g}")
        else:
            parts.append(f"{label}+{v}")
    return " · ".join(parts)


def apply_title_rarity_shift(weights: Dict[str, float], stats: dict) -> Dict[str, float]:
    """칭호의 rare~mythic 가중치를 희귀도 테이블에 반영."""
    extra = {k: float(stats[k]) for k in ("rare", "epic", "legendary", "mythic") if stats.get(k)}
    if not extra:
        return weights
    w = dict(weights)
    take = 0.0
    for rarity, boost in extra.items():
        if rarity not in w:
            continue
        steal = min(w.get("common", 0.5) * boost * 2.5, max(0.0, w.get("common", 0.5) - 0.04))
        take += steal
        w[rarity] = w.get(rarity, 0) + steal
    if take > 0:
        w["common"] = max(0.04, w.get("common", 0.5) - take)
    s = sum(w.values()) or 1.0
    return {k: v / s for k, v in w.items()}


def title_unlock_hint(title_id: str) -> str:
    t = TITLES.get(title_id, {})
    req = t.get("req")
    if not req:
        return "처음부터 사용 · `!칭호 title_rookie`"
    a = ACHIEVEMENTS.get(req)
    if not a:
        return f"`!업적`에서 업적 `{req}` 달성"
    return (
        f"`!업적` **{a['name']}** 달성 시 해금 — {a['desc']} "
        f"(업적 보상 {int(a['reward']):,}원)"
    )


def format_title_acquisition_guide() -> List[str]:
    """칭호 획득 경로 안내 (상점 없음, 업적 연동)."""
    lines = [
        "**칭호는 어디서 얻나요?**",
        "1. **`!업적`** 에서 각 목표(낚시 횟수, 보스 공격 등)를 달성",
        "2. 업적 달성 시 **보상금 + 칭호 자동 해금** (별도 구매·상점 없음)",
        "3. **`!칭호 <ID>`** 로 원하는 칭호 장착 — **장착 시 능력치가 실제로 적용**됨",
        "4. **`!이벤트`** — 황금시간·현상수배·행운복권 등 서버 이벤트",
        "",
        "**칭호 ↔ 업적 · 능력치**",
    ]
    for tid, t in TITLES.items():
        eff = format_title_stats(t.get("stats") or {})
        req = t.get("req")
        if not req:
            lines.append(f"- `{tid}` **{t['name']}** — 기본 · 효과: {eff}")
        else:
            a = ACHIEVEMENTS.get(req, {})
            lines.append(
                f"- `{tid}` **{t['name']}** ← **{a.get('name', req)}** · 효과: {eff}"
            )
    return lines


def unlocked_titles(profile: dict) -> List[str]:
    ach = set(profile.get("achievements", []))
    out = ["title_rookie"]
    for tid, t in TITLES.items():
        req = t.get("req")
        if req is None or req in ach:
            out.append(tid)
    return out
