"""길드(클랜) 생성 · 가입 · 협동 레이드 · 기부 · 주간 목표"""
from __future__ import annotations

import re
import time
import uuid
from typing import Dict, List, Optional, Tuple

GUILD_CREATE_COST = 100_000
GUILD_JOIN_MIN_LEVEL = 3  # 낚시대 +3 이상 권장 (soft check optional)
MAX_GUILD_MEMBERS = 20
MAX_OFFICERS = 3
INVITE_EXPIRE_SEC = 600
DONATE_MIN = 1_000
RAID_DURATION_SEC = 2 * 3600
RAID_COOLDOWN_DAYS = 2

# 레벨별 협동 버프 (낚시 시 적용)
GUILD_LEVEL_BUFFS: Dict[int, dict] = {
    1: {"rarity": 0.01, "chest": 0.01},
    2: {"rarity": 0.015, "chest": 0.015},
    3: {"rarity": 0.02, "chest": 0.02, "shiny": 0.005},
    4: {"rarity": 0.025, "chest": 0.025, "shiny": 0.008},
    5: {"rarity": 0.03, "chest": 0.03, "shiny": 0.01},
    6: {"rarity": 0.035, "chest": 0.035, "boss": 0.05},
    7: {"rarity": 0.04, "chest": 0.04, "boss": 0.08},
    8: {"rarity": 0.045, "chest": 0.045, "boss": 0.10},
    9: {"rarity": 0.05, "chest": 0.05, "boss": 0.12},
    10: {"rarity": 0.06, "chest": 0.06, "boss": 0.15, "shiny": 0.015},
}

# 길드 XP → 레벨
GUILD_XP_PER_LEVEL = [0, 500, 1500, 3500, 7000, 12000, 20000, 32000, 50000, 80000, 120000]

WEEKLY_FISH_GOALS = [
    (200, 30_000),
    (500, 80_000),
    (1000, 200_000),
    (2000, 500_000),
]


def week_key() -> str:
    return time.strftime("%Y-%W", time.gmtime())


def default_guild_db() -> dict:
    return {}


def default_server_guilds() -> dict:
    return {"clans": {}, "by_user": {}}


def default_clan_raid() -> dict:
    return {
        "active": False,
        "hp": 0,
        "max_hp": 0,
        "ends_at": 0,
        "contributors": {},
        "last_raid_day": "",
    }


def normalize_guild_name(name: str) -> Optional[str]:
    n = (name or "").strip()
    if len(n) < 2 or len(n) > 10:
        return None
    if not re.match(r"^[\w가-힣]+$", n, re.UNICODE):
        return None
    return n


def new_clan_id() -> str:
    return uuid.uuid4().hex[:10]


def guild_level_from_xp(xp: int) -> int:
    lv = 1
    for i, need in enumerate(GUILD_XP_PER_LEVEL):
        if xp >= need:
            lv = i
    return min(10, max(1, lv))


def xp_to_next_level(xp: int) -> Tuple[int, int]:
    lv = guild_level_from_xp(xp)
    if lv >= 10:
        return lv, 0
    nxt = GUILD_XP_PER_LEVEL[lv + 1]
    return lv, max(0, nxt - xp)


def guild_buffs(level: int) -> dict:
    return dict(GUILD_LEVEL_BUFFS.get(min(10, max(1, level)), GUILD_LEVEL_BUFFS[1]))


def raid_max_hp(member_count: int, guild_level: int) -> int:
    base = 80_000 + member_count * 15_000
    return int(base * (1.0 + guild_level * 0.12))


def weekly_goal_progress(weekly_fish: int) -> Tuple[int, int, int]:
    """반환: (목표 낚시 수, 보상금, 다음 단계 인덱)"""
    for target, reward in WEEKLY_FISH_GOALS:
        if weekly_fish < target:
            return target, reward, reward
    return WEEKLY_FISH_GOALS[-1][0], WEEKLY_FISH_GOALS[-1][1], 0


def find_clan_by_name(server_data: dict, name: str) -> Optional[dict]:
    key = normalize_guild_name(name)
    if not key:
        return None
    for c in (server_data.get("clans") or {}).values():
        if (c.get("name") or "").lower() == key.lower():
            return c
    return None


def get_user_clan_id(server_data: dict, user_id: int) -> Optional[str]:
    return (server_data.get("by_user") or {}).get(str(user_id))


def get_clan(server_data: dict, clan_id: str) -> Optional[dict]:
    return (server_data.get("clans") or {}).get(clan_id)


def is_leader(clan: dict, user_id: int) -> bool:
    return int(clan.get("leader", 0)) == int(user_id)


def is_officer(clan: dict, user_id: int) -> bool:
    return str(user_id) in [str(x) for x in (clan.get("officers") or [])]


def can_manage(clan: dict, user_id: int) -> bool:
    return is_leader(clan, user_id) or is_officer(clan, user_id)


def is_member(clan: dict, user_id: int) -> bool:
    return str(user_id) in [str(m) for m in (clan.get("members") or [])]


def member_count(clan: dict) -> int:
    return len(clan.get("members") or [])


def add_guild_xp(clan: dict, amount: int) -> int:
    clan["xp"] = int(clan.get("xp", 0)) + max(0, int(amount))
    clan["level"] = guild_level_from_xp(int(clan["xp"]))
    return int(clan["level"])


def reset_weekly_if_needed(clan: dict) -> None:
    wk = week_key()
    if clan.get("weekly_key") != wk:
        clan["weekly_key"] = wk
        clan["weekly_fish"] = 0
        clan["weekly_claimed"] = []


def format_guild_card(clan: dict) -> List[str]:
    reset_weekly_if_needed(clan)
    lv = int(clan.get("level", 1))
    xp = int(clan.get("xp", 0))
    _, to_next = xp_to_next_level(xp)
    buff = guild_buffs(lv)
    target, reward, _ = weekly_goal_progress(int(clan.get("weekly_fish", 0)))
    wf = int(clan.get("weekly_fish", 0))
    lines = [
        f"**⚔️ 길드 [{clan.get('name', '?')}]** (Lv.{lv})",
        f"- 길드장: <@{clan.get('leader')}>",
        f"- 길드원: **{member_count(clan)}/{MAX_GUILD_MEMBERS}**",
        f"- 길드금고: **{int(clan.get('bank', 0)):,}원**",
        f"- 경험치: **{xp:,}**" + (f" (다음 Lv까지 {to_next:,})" if to_next else " (MAX)"),
        f"- 협동 버프: 희귀+{int(buff.get('rarity',0)*100)}% / 상자+{int(buff.get('chest',0)*100)}%",
        f"- **주간 협동** 낚시 **{wf}/{target}** (달성 시 금고에서 {reward:,}원 분배)",
    ]
    raid = clan.get("raid") or default_clan_raid()
    if raid.get("active") and int(raid.get("hp", 0)) > 0:
        lines.append(
            f"- 🐲 **길드 레이드** HP **{int(raid['hp']):,}/{int(raid.get('max_hp',0)):,}** · `!길드공격`"
        )
    return lines
