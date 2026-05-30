"""서버 이벤트 · 연속 낚시 · 행운 복권 — 흥미 컨텐츠"""
from __future__ import annotations

import datetime
import random
import time
from typing import Dict, List, Optional, Tuple

from fishing_data import FISH_TABLE

GOLDEN_HOUR_DURATION = 15 * 60
GOLDEN_HOUR_RARITY = 0.22
GOLDEN_HOUR_CHANCE_PER_TICK = 0.06  # 30분마다 체크 시

BOUNTY_SELL_MULT = 3.0
LUCKY_MAX = 100
LUCKY_JACKPOT = 500_000
LUCKY_PARTICIPATE = 15_000


def today_key() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def kst_hour() -> int:
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).hour


def default_events() -> dict:
    return {
        "golden_hour": {"until": 0},
        "bounty": {"day": "", "fish_id": ""},
        "lucky": {"day": "", "entries": {}, "drawn": False, "winning": 0, "winner": None},
    }


def roll_daily_bounty() -> dict:
    f = random.choice(FISH_TABLE)
    return {"day": today_key(), "fish_id": f.id, "fish_name": f.name}


def event_buffs(state: dict) -> dict:
    """서버 전역 낚시 버프 (칭호와 합산)."""
    out = {"rarity": 0.0, "chest": 0.0, "shiny": 0.0}
    now = int(time.time())
    gh = state.get("golden_hour") or {}
    if int(gh.get("until", 0)) > now:
        out["rarity"] += GOLDEN_HOUR_RARITY
        out["chest"] += 0.05
        out["shiny"] += 0.01
    return out


def bounty_info(state: dict) -> Optional[dict]:
    b = state.get("bounty") or {}
    if b.get("day") != today_key() or not b.get("fish_id"):
        return None
    fid = b["fish_id"]
    f = next((x for x in FISH_TABLE if x.id == fid), None)
    return {
        "fish_id": fid,
        "name": b.get("fish_name") or (f.name if f else fid),
        "mult": BOUNTY_SELL_MULT,
    }


def format_events_status(state: dict, streak: int = 0) -> List[str]:
    now = int(time.time())
    lines = ["**🎪 서버 이벤트**"]
    gh = state.get("golden_hour") or {}
    if int(gh.get("until", 0)) > now:
        remain = int(gh["until"]) - now
        lines.append(
            f"✨ **황금의 낚시터** 진행 중! ({remain // 60}분 {remain % 60}초 남음)\n"
            f"   └ 희귀 물고기 대폭 증가 · `!낚시` GO!"
        )
    else:
        lines.append("✨ 황금의 낚시터: 대기 중 (랜덤 발생)")
    b = bounty_info(state)
    if b:
        lines.append(
            f"🎯 **오늘의 현상수배**: **{b['name']}** (`{b['fish_id']}`)\n"
            f"   └ 잡아 `!판매` 시 **{BOUNTY_SELL_MULT:.0f}배** 보너스!"
        )
    lucky = state.get("lucky") or {}
    ent = len(lucky.get("entries") or {})
    if lucky.get("day") == today_key():
        if lucky.get("drawn"):
            win = lucky.get("winning", "?")
            lines.append(f"🎟️ 행운 복권: 추첨 완료 (당첨 번호 **{win}**)")
        else:
            lines.append(f"🎟️ 행운 복권: **{ent}명** 참여 · `!행운번호 <1~100>` · `!행운번호추첨`")
    else:
        lines.append("🎟️ 행운 복권: `!행운번호 77` 로 오늘 번호 등록")
    if streak > 0:
        lines.append(f"🔥 오늘 연속 낚시: **{streak}회** (30회 달성 시 업적·칭호)")
    lines.append("\n`!황금시간` — 황금시간 강제 시작 (관리자급, 하루 1회)")
    return lines


def lucky_register(state: dict, user_id: int, number: int) -> Tuple[bool, str]:
    number = max(1, min(LUCKY_MAX, int(number)))
    lucky = dict(state.get("lucky") or {})
    if lucky.get("day") != today_key():
        lucky = {"day": today_key(), "entries": {}, "drawn": False, "winning": 0, "winner": None}
    if lucky.get("drawn"):
        return False, "오늘은 이미 추첨이 끝났어."
    uid = str(user_id)
    if uid in lucky.get("entries", {}):
        return False, f"이미 **{lucky['entries'][uid]}번**으로 참여했어."
    lucky.setdefault("entries", {})[uid] = number
    state["lucky"] = lucky
    return True, f"🎟️ 행운 복권 등록: **{number}번** (1~{LUCKY_MAX})"


def lucky_draw(state: dict) -> Tuple[dict, Optional[str]]:
    lucky = dict(state.get("lucky") or {})
    if lucky.get("day") != today_key():
        return state, "오늘 참여자가 없어."
    if lucky.get("drawn"):
        return state, f"이미 추첨됨. 당첨 번호 **{lucky.get('winning')}**"
    entries = lucky.get("entries") or {}
    if not entries:
        return state, "참여자가 없어."
    winning = random.randint(1, LUCKY_MAX)
    lucky["winning"] = winning
    lucky["drawn"] = True
    # 가장 가까운 번호
    best_uid = min(entries.keys(), key=lambda u: abs(int(entries[u]) - winning))
    lucky["winner"] = int(best_uid)
    state["lucky"] = lucky
    diff = abs(int(entries[best_uid]) - winning)
    msg = (
        f"🎟️ **행운 복권 추첨!** 당첨 번호 **{winning}**\n"
        f"- 1등: <@{best_uid}> (**{entries[best_uid]}번**, 차이 {diff})"
    )
    if diff == 0:
        msg += f"\n🎊 **완전 일치 잭팟!** {_fmt_hint_jackpot()}"
    return state, msg


def _fmt_hint_jackpot() -> str:
    return f"**{LUCKY_JACKPOT:,}원**"


def payout_lucky_winner(entries: dict, winning: int, winner_uid: int) -> int:
    diff = abs(int(entries.get(str(winner_uid), 0)) - winning)
    if diff == 0:
        return LUCKY_JACKPOT
    if diff <= 3:
        return 200_000
    if diff <= 10:
        return 80_000
    return LUCKY_PARTICIPATE


def bump_fish_streak(profile: dict) -> Tuple[dict, int, str]:
    """프로필 갱신, 연속 횟수, 보너스 메시지."""
    day = today_key()
    if profile.get("streak_day") != day:
        profile["streak_day"] = day
        profile["fish_streak_today"] = 0
    profile["fish_streak_today"] = int(profile.get("fish_streak_today", 0)) + 1
    streak = int(profile["fish_streak_today"])
    profile["max_streak_today"] = max(int(profile.get("max_streak_today", 0)), streak)
    bonus_msg = ""
    if streak in (10, 20, 30, 50, 100):
        bonus_msg = f"\n🔥 **연속 {streak}회 달성!** "
        if streak == 30:
            bonus_msg += "(업적·칭호 해금 조건 충족! `!업적`)"
        elif streak == 100:
            bonus_msg += "🎊 **전설의 낚시광!**"
    return profile, streak, bonus_msg


def try_start_golden_hour(state: dict) -> Tuple[dict, bool]:
    now = int(time.time())
    gh = state.get("golden_hour") or {}
    if int(gh.get("until", 0)) > now:
        return state, False
    if random.random() > GOLDEN_HOUR_CHANCE_PER_TICK:
        return state, False
    state["golden_hour"] = {"until": now + GOLDEN_HOUR_DURATION}
    return state, True


def force_golden_hour(state: dict, last_force_day: str) -> Tuple[dict, bool, str]:
    if last_force_day == today_key():
        return state, False, "오늘은 이미 황금시간을 열었어."
    now = int(time.time())
    state["golden_hour"] = {"until": now + GOLDEN_HOUR_DURATION}
    return state, True, "황금시간 시작!"
