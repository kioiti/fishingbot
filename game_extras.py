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
    "ach_upgrade_25": {"name": "⚡ 최고 강화", "desc": "낚시대 +25 달성", "check": "rod_level", "target": 25, "reward": 300000},
    "ach_boss_10": {"name": "🐉 보스 헌터", "desc": "보스 공격 10회", "check": "boss_hits", "target": 10, "reward": 60000},
    "ach_casino_win_20": {"name": "🎰 행운아", "desc": "카지노 승리 20회", "check": "casino_wins", "target": 20, "reward": 40000},
    "ach_duel_5": {"name": "⚔️ 결투왕", "desc": "낚시 대결 5승", "check": "duel_wins", "target": 5, "reward": 70000},
    "ach_rich": {"name": "💰 부자", "desc": "보유금 100만원", "check": "money", "target": 1000000, "reward": 50000},
    "ach_gacha_30": {"name": "🎁 뽑기 중독", "desc": "뽑기 30회", "check": "gacha_total", "target": 30, "reward": 80000},
}

# ── 칭호 (업적/조건解鎖) ──────────────────────────
TITLES: Dict[str, dict] = {
    "title_rookie": {"name": "🐣 초보 낚시꾼", "req": None},
    "title_angler": {"name": "🎣 낚시 마스터", "req": "ach_fish_100"},
    "title_legend": {"name": "👑 전설의 낚시왕", "req": "ach_legendary_10"},
    "title_mythic": {"name": "☄️ 신화의 그물", "req": "ach_mythic_3"},
    "title_gambler": {"name": "🎰 카지노의 왕", "req": "ach_casino_win_20"},
    "title_hunter": {"name": "🐉 보스 학살자", "req": "ach_boss_10"},
    "title_shiny": {"name": "✨ 이색의 예술가", "req": "ach_shiny_5"},
    "title_whale": {"name": "🐋 돈 좀 쓰는 사람", "req": "ach_rich"},
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
    weights = [20, 25, 25, 12, 10, 8]
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


def achievement_progress(profile: dict, ach_id: str, rod_level: int, money: int) -> bool:
    if ach_id in profile.get("achievements", []):
        return False
    a = ACHIEVEMENTS.get(ach_id)
    if not a:
        return False
    check = a["check"]
    target = int(a["target"])
    val = 0
    if check == "fish_total":
        val = int(profile.get("fish_total", 0))
    elif check == "chest_total":
        val = int(profile.get("chest_total", 0))
    elif check == "shiny_total":
        val = int(profile.get("shiny_total", 0))
    elif check == "legendary_total":
        val = int(profile.get("legendary_total", 0))
    elif check == "mythic_total":
        val = int(profile.get("mythic_total", 0))
    elif check == "rod_level":
        val = rod_level
    elif check == "boss_hits":
        val = int(profile.get("boss_hits", 0))
    elif check == "casino_wins":
        val = int(profile.get("casino_wins", 0))
    elif check == "duel_wins":
        val = int(profile.get("duel_wins", 0))
    elif check == "money":
        val = money
    elif check == "gacha_total":
        val = int(profile.get("gacha_total", 0))
    return val >= target


def unlocked_titles(profile: dict) -> List[str]:
    ach = set(profile.get("achievements", []))
    out = ["title_rookie"]
    for tid, t in TITLES.items():
        req = t.get("req")
        if req is None or req in ach:
            out.append(tid)
    return out
