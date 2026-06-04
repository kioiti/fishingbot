from __future__ import annotations

import os
import math
import random
from pathlib import Path
from typing import Dict, Tuple

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from fishing_data import (
    FISH_TABLE,
    RODS,
    MAPS,
    ITEMS,
    CHESTS,
    BOSS_ROTATION,
    RARITY_LABEL,
    RARITY_FLAIR,
    boss_spawn,
    choose_fish,
    choose_rarity,
    format_fish_catch,
    format_chest_drop,
    format_rod_name,
    open_chest,
    rod_passive_text,
    roll_fishing_catch,
    spin_slot,
    SLOT_WIN_FEE,
    SLOT_JACKPOT_RATE,
    get_base_cooldown_seconds,
    get_rarity_weights,
    upgrade_cost,
    upgrade_try,
    upgrade_success_rate,
    upgrade_penalty_check,
    ROD_MAX_LEVEL,
)
from utils.jsondb import ensure_dir, get_user_dict, read_json, update_json, utc_ts, write_json
from game_extras import (
    ACHIEVEMENTS,
    TITLES,
    CRAFT_RECIPES,
    DAILY_QUEST_POOL,
    GACHA_COST,
    GACHA_POOL,
    MYSTERY_SHOP_POOL,
    WEATHER_TYPES,
    WEEKLY_QUEST,
    achievement_progress,
    achievement_current_value,
    title_unlock_hint,
    format_title_acquisition_guide,
    chest_chance_bonus,
    generate_mystery_shop,
    market_mult_today,
    pick_daily_quest,
    roll_gacha,
    roll_weather,
    shiny_chance,
    today_key,
    unlocked_titles,
    week_key,
    title_stats,
    format_title_stats,
    apply_title_rarity_shift,
)
from game_events import (
    BOUNTY_SELL_MULT,
    bump_fish_streak,
    bounty_info,
    default_events,
    event_buffs,
    format_events_status,
    force_golden_hour,
    lucky_draw,
    lucky_register,
    payout_lucky_winner,
    roll_daily_bounty,
    try_start_golden_hour,
)
from game_fun import (
    PETS,
    PET_FEED_COST,
    PET_FEED_FISH_COMMON,
    PET_MAX_LEVEL,
    PET_XP_PER_FEED,
    DAILY_WHEEL_POOL,
    TOURNAMENT_PRIZES,
    QUIZ_COOLDOWN_SEC,
    QUIZ_REWARD_MAX,
    QUIZ_REWARD_MIN,
    build_quiz_choices,
    fish_tournament_points,
    is_jackpot_festa,
    is_tournament_active,
    JACKPOT_FESTA_MULT,
    pet_level_progress,
    pet_rarity_bonus,
    pet_shiny_bonus,
    pet_xp_to_level,
    pick_quiz_fish,
    roll_daily_wheel,
    streak_extra_reward,
    tournament_weekend_key,
)
from game_casino_abyss import (
    ABYSS_MAX_BET,
    ABYSS_MIN_BET,
    ABYSS_POT_RATE,
    ABYSS_POT_JACKPOT_CHANCE,
    calc_payout,
    default_abyss_pot,
    odds_table_text,
    roll_abyss,
)
from game_casino_risk import (
    CORRIDOR_MIN_BET,
    TREASURE_DIVE_MIN_BET,
    calc_risk_payout,
    corridor_help_text,
    treasure_dive_help_text,
    roll_corridor,
    roll_treasure_dive,
)
from game_estate import (
    ESTATE_CATALOG,
    SELL_BACK_RATE,
    estate_list_line,
    fmt_estate_price,
    pending_rent,
    resolve_estate,
)
from game_stocks import (
    STOCKS,
    STOCK_TICK_SECONDS,
    STOCK_TICK_CHECK_SECONDS,
    default_market,
    format_change,
    resolve_stock,
    stock_line,
    tick_market,
    should_tick_market,
    seconds_until_next_tick,
    normalize_holding,
    holding_avg_price,
    holding_stats,
    format_holding_detail,
    format_holding_pl,
    format_signed_money,
    roll_stock_news,
    apply_news_shock,
    format_news_broadcast,
    kst_now,
    kst_today_key,
    NEWS_HOURS_KST,
)
from game_world import (
    FRAGMENT_ITEM_ID,
    FRAGMENT_CRAFT_COUNT,
    WORLD_BOSS_INFO,
    apply_weather_rarity_shift,
    make_fish_picker,
    weather_fishing_hint,
    is_ghost_fish_hour,
    kst_hour,
    roll_fragment_drop,
    roll_affix,
    format_affix_line,
    affix_cooldown_bonus,
    affix_rarity_bonus,
    affix_chest_bonus,
    affix_boss_bonus,
    affix_fragment_bonus,
    default_world_boss_state,
    world_boss_spawn,
    default_expedition,
    default_ship,
    default_aquarium,
    aquarium_max_slots,
    aquarium_income_per_hour,
    roll_expedition_rewards,
    expedition_duration_sec,
    ship_upgrade_cost,
    SHIP_PART_NAMES,
    SHIP_PARTS,
    BROADCAST_MYTHIC_CHANCE,
    BROADCAST_LEGENDARY_CHANCE,
)
from game_guild import (
    GUILD_CREATE_COST,
    MAX_GUILD_MEMBERS,
    MAX_OFFICERS,
    INVITE_EXPIRE_SEC,
    DONATE_MIN,
    RAID_DURATION_SEC,
    RAID_COOLDOWN_DAYS,
    default_guild_db,
    default_server_guilds,
    default_clan_raid,
    normalize_guild_name,
    new_clan_id,
    guild_buffs,
    guild_level_from_xp,
    xp_to_next_level,
    weekly_goal_progress,
    find_clan_by_name,
    get_user_clan_id,
    get_clan,
    is_leader,
    is_officer,
    can_manage,
    is_member,
    member_count,
    add_guild_xp,
    reset_weekly_if_needed,
    format_guild_card,
    raid_max_hp,
    week_key,
)


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
ensure_dir(DATA_DIR)

# 서버에 실제 닉네임이 없거나 고정 표기가 필요할 때 사용
USER_MAP = {
    1501525905833594900: "머래",
    261016503963353098: "계삭",
    464655989996519424: "마라콩",
    707895110972473345: "밈콩",
    435351384137662464: "지성콩",
    1004779456696688760: "미희여사",
    706114030061879296: "에빙",
    552137320963244074: "쮼콩",
}

MONEY_PATH = DATA_DIR / "money.json"
INV_PATH = DATA_DIR / "inventory.json"
RODS_PATH = DATA_DIR / "rods.json"
COOLDOWN_PATH = DATA_DIR / "cooldown.json"
STATS_PATH = DATA_DIR / "stats.json"
BOSS_PATH = DATA_DIR / "boss.json"
CASINO_COOLDOWN_PATH = DATA_DIR / "casino_cooldown.json"
CASINO_STATS_PATH = DATA_DIR / "casino_stats.json"
JACKPOT_PATH = DATA_DIR / "jackpot.json"
JACKPOT_HISTORY_PATH = DATA_DIR / "jackpot_history.json"
AUTO_PATH = DATA_DIR / "auto_fish.json"
DAILY_PATH = DATA_DIR / "daily.json"
TREASURE_PATH = DATA_DIR / "treasure.json"
MAP_PATH = DATA_DIR / "map.json"
BAIT_PATH = DATA_DIR / "active_bait.json"
COLLECTION_PATH = DATA_DIR / "collection.json"
PROFILE_PATH = DATA_DIR / "profile.json"
WEATHER_PATH = DATA_DIR / "weather.json"
MERCHANT_PATH = DATA_DIR / "merchant.json"
PET_PATH = DATA_DIR / "pets.json"
FUN_PATH = DATA_DIR / "fun.json"
STOCK_MARKET_PATH = DATA_DIR / "stock_market.json"
STOCK_PORTFOLIO_PATH = DATA_DIR / "stock_portfolio.json"
STOCK_NEWS_PATH = DATA_DIR / "stock_news.json"
ESTATE_PATH = DATA_DIR / "estate.json"
ABYSS_JACKPOT_PATH = DATA_DIR / "abyss_jackpot.json"
DUEL_PATH = DATA_DIR / "duel.json"
DUEL_EXPIRE_SEC = 300
WORLDBOSS_PATH = DATA_DIR / "worldboss.json"
EXPEDITION_PATH = DATA_DIR / "expedition.json"
SHIP_PATH = DATA_DIR / "ship.json"
AQUARIUM_PATH = DATA_DIR / "aquarium.json"
GUILD_PATH = DATA_DIR / "guilds.json"
GUILD_INVITE_PATH = DATA_DIR / "guild_invites.json"
EVENT_PATH = DATA_DIR / "events.json"

QUIZ_PENDING: Dict[int, dict] = {}


def _default_money() -> Dict[str, int]:
    return {}


def _default_inventory() -> Dict[str, dict]:
    return {}


def _default_rods() -> Dict[str, dict]:
    return {}


def _default_cooldown() -> Dict[str, int]:
    return {}


def _default_stats() -> Dict[str, dict]:
    return {}


def _default_boss() -> dict:
    from fishing_data import boss_default_state

    return boss_default_state()


def _default_casino_cooldown() -> Dict[str, int]:
    return {}


def _default_casino_stats() -> Dict[str, dict]:
    return {}


def _default_jackpot() -> dict:
    return {"pot": 0}


def _default_jackpot_history() -> dict:
    return {"hits": []}

def _default_auto() -> dict:
    return {"users": {}}  # user_id(str) -> {enabled: bool, channel_id: int, paid: bool}

def _default_map() -> Dict[str, str]:
    return {}  # user_id(str) -> map_id(str)

def _default_bait() -> Dict[str, str]:
    return {}  # user_id(str) -> bait_id(str)

def _default_collection() -> Dict[str, list]:
    return {}  # user_id(str) -> list of fish_ids


def _default_profile() -> Dict[str, dict]:
    return {}


def _default_weather() -> dict:
    return {"id": "sunny", "until": 0}


def _default_merchant() -> dict:
    return {"until": 0, "items": []}


def _fish_inv_key(fish_id: str, shiny: bool = False) -> str:
    return f"shiny_{fish_id}" if shiny else fish_id


def _inv_item_display(key: str) -> str:
    if key.startswith("shiny_"):
        base = key[6:]
        f = FISH_BY_ID.get(base)
        return f"✨이색 {f.name}" if f else key
    f = FISH_BY_ID.get(key)
    if f:
        return f.name
    if key in ITEMS:
        return ITEMS[key]["name"]
    if key in CHESTS:
        return CHESTS[key]["name"]
    return key


def _fish_sell_price(key: str) -> int:
    if key.startswith("shiny_"):
        base = FISH_BY_ID.get(key[6:])
        return int(base.sell * 3) if base else 0
    f = FISH_BY_ID.get(key)
    return int(f.sell) if f else 0


async def get_user_map(user_id: int) -> str:
    m = await read_json(MAP_PATH, _default_map())
    return str(m.get(str(user_id), "river"))


async def set_user_map(user_id: int, map_id: str) -> None:
    def mut(d):
        d = dict(d or {})
        d[str(user_id)] = str(map_id)
        return d
    await update_json(MAP_PATH, _default_map(), mut)


async def get_user_bait(user_id: int) -> str | None:
    b = await read_json(BAIT_PATH, _default_bait())
    val = b.get(str(user_id))
    return str(val) if val else None


async def set_user_bait(user_id: int, bait_id: str | None) -> None:
    def mut(d):
        d = dict(d or {})
        if bait_id is None or bait_id.lower() == "off":
            d.pop(str(user_id), None)
        else:
            d[str(user_id)] = str(bait_id)
        return d
    await update_json(BAIT_PATH, _default_bait(), mut)


async def get_user_collection(user_id: int) -> list[str]:
    c = await read_json(COLLECTION_PATH, _default_collection())
    return list(c.get(str(user_id)) or [])


async def add_to_collection(user_id: int, fish_id: str) -> bool:
    """물고기를 도감에 추가하고, 새로 추가된 경우 True를 반환합니다."""
    is_new = False
    def mut(d):
        nonlocal is_new
        d = dict(d or {})
        lst = list(d.get(str(user_id)) or [])
        if fish_id not in lst:
            lst.append(fish_id)
            d[str(user_id)] = lst
            is_new = True
        return d
    await update_json(COLLECTION_PATH, _default_collection(), mut)
    return is_new


async def get_collection_completion_status(user_id: int) -> dict:
    col = await get_user_collection(user_id)
    col_set = set(col)
    
    rarities = ["common", "rare", "epic", "legendary", "mythic"]
    status = {}
    for r in rarities:
        fish_in_r = [f.id for f in FISH_TABLE if f.rarity == r]
        total = len(fish_in_r)
        caught = len([fid for fid in fish_in_r if fid in col_set])
        status[r] = {
            "caught": caught,
            "total": total,
            "complete": caught >= total and total > 0
        }
    return status


async def get_collection_buffs(user_id: int) -> dict:
    status = await get_collection_completion_status(user_id)
    return {
        "sell_bonus": 0.05 if status["common"]["complete"] else 0.0,
        "cooldown_reduction": 1 if status["rare"]["complete"] else 0,
        "upgrade_chance_bonus": 0.03 if status["epic"]["complete"] else 0.0,
        "boss_damage_bonus": 0.15 if status["legendary"]["complete"] else 0.0,
        "auto_cooldown_reduction": 1 if status["mythic"]["complete"] else 0
    }


async def get_title_buffs(user_id: int) -> dict:
    p = await get_profile(user_id)
    tid = p.get("title", "title_rookie")
    return title_stats(tid)


async def get_events_state() -> dict:
    st = await read_json(EVENT_PATH, default_events())
    day = today_key()
    b = st.get("bounty") or {}
    if b.get("day") != day or not b.get("fish_id"):
        st["bounty"] = roll_daily_bounty()
        await write_json(EVENT_PATH, st)
    return st


async def get_fishing_buffs(
    user_id: int,
    ctx: commands.Context | None = None,
    discord_server_id: int | None = None,
) -> dict:
    """칭호 + 서버 이벤트 + 길드 낚시 버프 합산."""
    title_b = await get_title_buffs(user_id)
    ev = event_buffs(await get_events_state())
    srv_id = _discord_server_id(ctx, discord_server_id)
    clan_b = await guild_get_buffs(user_id, srv_id)
    out = {"rarity": 0.0, "chest": 0.0, "shiny": 0.0}
    for src in (title_b, ev, clan_b):
        for k in out:
            if k in src:
                out[k] += float(src[k])
    out["_title"] = title_b
    return out


async def get_user_cooldown(user_id: int, rod_type: str, rod_level: int) -> int:
    base = get_base_cooldown_seconds(rod_level)
    passive = (RODS.get(rod_type) or RODS["rookie"])["passive"]
    if passive.get("type") == "cooldown_bonus":
        v = float(passive.get("value", 0.0))
        base = int(math.ceil(base * (1.0 - v)))
    
    # 1. 낚시터 배율 적용
    map_id = await get_user_map(user_id)
    m = MAPS.get(map_id) or MAPS["river"]
    base = int(math.ceil(base * m.get("cooldown_multiplier", 1.0)))
    
    # 2. 미끼 버프 적용 (지렁이 장착 시 15% 감량)
    bait = await get_user_bait(user_id)
    inv = await get_inventory(user_id)
    if bait == "bait_worm" and inv.get("bait_worm", 0) > 0:
        base = int(math.ceil(base * 0.85))
        
    # 3. 도감 완성 버프 (희귀 도감 완성 시 -1초)
    buffs = await get_collection_buffs(user_id)
    base -= buffs.get("cooldown_reduction", 0)

    rec = await get_rod_record(user_id)
    base = max(3, base - int(affix_cooldown_bonus(rec.get("affixes", []))))

    tb = await get_title_buffs(user_id)
    base = max(3, base - int(float(tb.get("cooldown", 0.0))))

    return max(3, base)


async def consume_active_bait(user_id: int) -> dict | None:
    bait_id = await get_user_bait(user_id)
    if not bait_id:
        return None
        
    inv = await get_inventory(user_id)
    qty = int(inv.get(bait_id, 0))
    if qty <= 0:
        # 미끼가 없음 -> 자동으로 장착 해제
        await set_user_bait(user_id, None)
        return None
        
    # 미끼 1개 소모
    def mut(d):
        d = dict(d or {})
        uinv = get_user_dict(d, user_id, {})
        uinv[bait_id] = max(0, int(uinv.get(bait_id, 0)) - 1)
        if uinv[bait_id] <= 0:
            uinv.pop(bait_id, None)
        return d
    await update_json(INV_PATH, _default_inventory(), mut)
    
    # 소모 후 개수 확인
    new_inv = await get_inventory(user_id)
    new_qty = new_inv.get(bait_id, 0)
    
    exhausted = False
    if new_qty <= 0:
        await set_user_bait(user_id, None)
        exhausted = True
        
    return {
        "bait_id": bait_id,
        "item_info": ITEMS[bait_id],
        "exhausted": exhausted,
        "remaining": int(new_qty),
    }


def _format_wait_time(seconds: int) -> str:
    seconds = max(0, int(seconds))
    if seconds >= 60:
        return f"**{seconds // 60}분 {seconds % 60}초**"
    return f"**{seconds}초**"


def _format_bait_status(bait_consumed: dict | None, had_equipped: bool) -> str:
    if bait_consumed:
        name = bait_consumed["item_info"]["name"]
        left = int(bait_consumed.get("remaining", 0))
        if bait_consumed.get("exhausted"):
            return f"\n🪱 **{name}** 1개 소모 → 남은 **0개** (미끼 소진, 장착 해제)"
        return f"\n🪱 **{name}** 1개 소모 → 남은 **{left}개**"
    if had_equipped:
        return "\n⚠️ 장착한 미끼가 없어 효과 없이 낚았어. (자동 장착 해제됨)"
    return ""


FISH_BY_ID = {f.id: f for f in FISH_TABLE}
FISH_BY_NAME = {f.name: f for f in FISH_TABLE}
CHEST_IDS = set(CHESTS.keys())


def _today_key_utc() -> str:
    import time

    return time.strftime("%Y-%m-%d", time.gmtime())


async def get_money(user_id: int) -> int:
    money = await read_json(MONEY_PATH, _default_money())
    return int(money.get(str(user_id), 0))


async def add_money(user_id: int, delta: int) -> int:
    def mut(d):
        d = dict(d or {})
        d[str(user_id)] = int(d.get(str(user_id), 0)) + int(delta)
        if d[str(user_id)] < 0:
            d[str(user_id)] = 0
        return d

    money = await update_json(MONEY_PATH, _default_money(), mut)
    return int(money.get(str(user_id), 0))


async def get_rod_record(user_id: int) -> dict:
    rods = await read_json(RODS_PATH, _default_rods())
    r = rods.get(str(user_id))
    if not isinstance(r, dict):
        return {"type": "rookie", "level": 0, "affixes": []}
    rod_type = r.get("type", "rookie")
    if rod_type not in RODS:
        r["type"] = "rookie"
    r.setdefault("affixes", [])
    if not isinstance(r.get("affixes"), list):
        r["affixes"] = []
    return r


async def get_rod(user_id: int) -> Tuple[str, int]:
    r = await get_rod_record(user_id)
    return r.get("type", "rookie"), max(0, int(r.get("level", 0)))


async def set_rod(user_id: int, rod_type: str, level: int, affixes: list | None = None) -> None:
    def mut(d):
        d = dict(d or {})
        old = d.get(str(user_id)) or {}
        aff = affixes if affixes is not None else old.get("affixes", [])
        d[str(user_id)] = {"type": rod_type, "level": int(level), "affixes": list(aff or [])}
        return d

    await update_json(RODS_PATH, _default_rods(), mut)


async def add_fish(user_id: int, fish_id: str, amount: int = 1) -> None:
    def mut(d):
        d = dict(d or {})
        inv = get_user_dict(d, user_id, {})
        inv[fish_id] = int(inv.get(fish_id, 0)) + int(amount)
        if inv[fish_id] <= 0:
            inv.pop(fish_id, None)
        return d

    await update_json(INV_PATH, _default_inventory(), mut)


def _normalize_inventory_raw(raw) -> Dict[str, int]:
    """구형/깨진 인벤 데이터도 읽을 수 있게 정규화."""
    out: Dict[str, int] = {}
    if raw is None:
        return out
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            k = item.get("id") or item.get("key") or item.get("fish_id")
            if not k:
                continue
            try:
                q = int(item.get("qty", item.get("count", item.get("amount", 1))))
            except Exception:
                continue
            if q > 0:
                out[str(k)] = out.get(str(k), 0) + q
        return {k: v for k, v in out.items() if v > 0}
    if not isinstance(raw, dict):
        return out
    for k, v in raw.items():
        key = str(k)
        try:
            if isinstance(v, dict):
                q = int(v.get("qty", v.get("count", v.get("amount", 0))))
            elif isinstance(v, (list, tuple)):
                continue
            else:
                q = int(float(v))
            if q > 0:
                out[key] = q
        except Exception:
            continue
    return out


async def get_inventory(user_id: int) -> Dict[str, int]:
    inv = await read_json(INV_PATH, _default_inventory())
    uid = str(user_id)
    raw = inv.get(uid)
    if raw is None and user_id in inv:
        raw = inv.get(user_id)
    return _normalize_inventory_raw(raw)


async def _reply_long(ctx: commands.Context, parts: list[str], header: str = "") -> None:
    """디스코드 2000자 제한 대응 분할 전송."""
    limit = 1900
    chunks: list[str] = []
    buf = header
    for part in parts:
        line = part if part.endswith("\n") else part + "\n"
        if len(buf) + len(line) > limit and buf.strip():
            chunks.append(buf.rstrip())
            buf = line
        else:
            buf += line
    if buf.strip():
        chunks.append(buf.rstrip())
    if not chunks:
        chunks = [header or "(내용 없음)"]
    for i, text in enumerate(chunks):
        if i == 0:
            await ctx.reply(text, mention_author=False)
        else:
            await ctx.send(text)


async def get_last_fish_ts(user_id: int) -> int:
    cd = await read_json(COOLDOWN_PATH, _default_cooldown())
    return int(cd.get(str(user_id), 0))


async def set_last_fish_ts(user_id: int, ts: int) -> None:
    def mut(d):
        d = dict(d or {})
        d[str(user_id)] = int(ts)
        return d

    await update_json(COOLDOWN_PATH, _default_cooldown(), mut)


async def bump_stats(user_id: int, rarity: str) -> None:
    def mut(d):
        d = dict(d or {})
        s = get_user_dict(d, user_id, {"fish": 0, "legendary": 0, "mythic": 0})
        s["fish"] = int(s.get("fish", 0)) + 1
        if rarity == "legendary":
            s["legendary"] = int(s.get("legendary", 0)) + 1
        if rarity == "mythic":
            s["mythic"] = int(s.get("mythic", 0)) + 1
        return d

    await update_json(STATS_PATH, _default_stats(), mut)


async def get_last_casino_ts(user_id: int) -> int:
    cd = await read_json(CASINO_COOLDOWN_PATH, _default_casino_cooldown())
    return int(cd.get(str(user_id), 0))


async def set_last_casino_ts(user_id: int, ts: int) -> None:
    def mut(d):
        d = dict(d or {})
        d[str(user_id)] = int(ts)
        return d

    await update_json(CASINO_COOLDOWN_PATH, _default_casino_cooldown(), mut)


async def _casino_bump(user_id: int, bet: int, net: int, game: str) -> dict:
    def mut(d):
        d = dict(d or {})
        s = get_user_dict(
            d,
            user_id,
            {
                "plays": 0,
                "bet": 0,
                "net": 0,
                "win": 0,
                "lose": 0,
                "streak": 0,
                "best_streak": 0,
                "last_game": "",
            },
        )
        s["plays"] = int(s.get("plays", 0)) + 1
        s["bet"] = int(s.get("bet", 0)) + int(bet)
        s["net"] = int(s.get("net", 0)) + int(net)
        if net > 0:
            s["win"] = int(s.get("win", 0)) + 1
            s["streak"] = int(s.get("streak", 0)) + 1
            s["best_streak"] = max(int(s.get("best_streak", 0)), int(s["streak"]))
        else:
            s["lose"] = int(s.get("lose", 0)) + 1
            s["streak"] = 0
        s["last_game"] = str(game)
        return d

    await update_json(CASINO_STATS_PATH, _default_casino_stats(), mut)

    def pm(p):
        p["casino_plays"] = int(p.get("casino_plays", 0)) + 1
        if net > 0:
            p["casino_wins"] = int(p.get("casino_wins", 0)) + 1

    await profile_update(user_id, pm)
    await quest_bump(user_id, "casino_play", 1)
    if net > 0:
        await quest_bump(user_id, "casino_win", 1)

    return {}


def _slot_jackpot_contribution(bet: int) -> int:
    rate = SLOT_JACKPOT_RATE
    if is_jackpot_festa():
        rate *= JACKPOT_FESTA_MULT
    return int(bet * rate)


async def _jackpot_add(delta: int) -> int:
    def mut(d):
        d = dict(d or {})
        d["pot"] = max(0, int(d.get("pot", 0)) + int(delta))
        return d

    j = await update_json(JACKPOT_PATH, _default_jackpot(), mut)
    return int(j.get("pot", 0))


async def _jackpot_take_all() -> int:
    def mut(d):
        d = dict(d or {})
        pot = int(d.get("pot", 0))
        d["pot"] = 0
        d["_taken"] = pot
        return d

    j = await update_json(JACKPOT_PATH, _default_jackpot(), mut)
    return int(j.get("_taken", 0))


async def _jackpot_record_hit(guild_id: int | None, user_id: int, amount: int) -> None:
    hit = {
        "ts": utc_ts(),
        "guild_id": int(guild_id) if guild_id else None,
        "user_id": int(user_id),
        "amount": int(amount),
    }

    def mut(d):
        d = dict(d or {})
        hits = list(d.get("hits") or [])
        hits.append(hit)
        # 최근 200개만 유지
        d["hits"] = hits[-200:]
        return d

    await update_json(JACKPOT_HISTORY_PATH, _default_jackpot_history(), mut)

def _fmt_money(n: int) -> str:
    return f"{int(n):,}원"


def _display_name(ctx: commands.Context, user_id: int) -> str:
    if user_id in USER_MAP:
        return USER_MAP[user_id]
    if ctx.guild:
        m = ctx.guild.get_member(user_id)
        if m:
            return m.display_name
    return f"유저({user_id})"


def _rod_cooldown_seconds(rod_type: str, rod_level: int) -> int:
    base = get_base_cooldown_seconds(rod_level)
    passive = (RODS.get(rod_type) or RODS["rookie"])["passive"]
    ptype = passive.get("type", "none")
    v = 0.0
    if ptype == "cooldown_bonus":
        v = float(passive.get("value", 0.0))
    elif ptype == "combo":
        v = float(passive.get("cooldown", 0.0))
    if v > 0:
        base = int(math.ceil(base * (1.0 - v)))
    return max(3, base)


def _rod_sell_mult(rod_type: str) -> float:
    passive = (RODS.get(rod_type) or RODS["rookie"])["passive"]
    if passive.get("type") == "sell_bonus":
        return 1.0 + float(passive.get("value", 0.0))
    return 1.0


def _boss_damage(
    rod_type: str, rod_level: int, title_buffs: dict | None = None
) -> tuple[int, bool, float]:
    base = random.randint(250, 550) + rod_level * random.randint(30, 55)
    tb = title_buffs or {}
    passive = (RODS.get(rod_type) or RODS["rookie"])["passive"]
    ptype = passive.get("type", "none")
    if ptype == "boss_bonus":
        base = int(base * (1.0 + float(passive.get("value", 0.0))))
    elif ptype == "combo" and passive.get("boss"):
        base = int(base * (1.0 + float(passive["boss"])))
    elif ptype == "boss_slayer":
        base = int(base * (1.0 + float(passive.get("value", 0.0))))

    crit_rate = min(0.20, 0.07 + (rod_level // 10) * 0.01)
    if ptype == "crit_bonus":
        crit_rate = min(0.25, crit_rate + float(passive.get("value", 0.0)))
    elif ptype == "combo" and passive.get("crit"):
        crit_rate = min(0.25, crit_rate + float(passive["crit"]))
    elif ptype == "boss_slayer":
        crit_rate = min(0.40, crit_rate + float(passive.get("crit", 0.0)))

    if tb.get("boss"):
        base = int(base * (1.0 + float(tb["boss"])))
    crit_rate = min(0.45, crit_rate + float(tb.get("crit", 0.0)))

    crit_mult = 2.0 if ptype == "boss_slayer" else 1.75
    is_crit = random.random() < crit_rate
    dmg = int(base * (crit_mult if is_crit else 1.0))
    return max(1, dmg), is_crit, crit_mult


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


async def _auto_enabled_users() -> dict:
    return await read_json(AUTO_PATH, _default_auto())


async def _set_auto_user(user_id: int, *, enabled: bool, channel_id: int, paid: bool | None = None) -> None:
    def mut(d):
        d = dict(d or {})
        d.setdefault("users", {})
        users = dict(d.get("users") or {})
        cur = dict(users.get(str(user_id)) or {})
        cur["enabled"] = bool(enabled)
        cur["channel_id"] = int(channel_id)
        if paid is not None:
            cur["paid"] = bool(paid)
        users[str(user_id)] = cur
        d["users"] = users
        return d

    await update_json(AUTO_PATH, _default_auto(), mut)


async def _get_auto_user(user_id: int) -> dict:
    d = await read_json(AUTO_PATH, _default_auto())
    users = (d or {}).get("users") or {}
    return dict(users.get(str(user_id)) or {})


def _auto_allowed(rod_level: int, paid: bool) -> bool:
    return rod_level >= 7 or paid


@tasks.loop(seconds=STOCK_TICK_CHECK_SECONDS)
async def stock_market_loop():
    """last_tick 기준 정확히 10분(600초)마다 시세 1회만 변동."""
    try:
        m = await _get_stock_market()
        if should_tick_market(int(m.get("last_tick", 0))):
            await _tick_stock_market()
    except Exception:
        pass


@tasks.loop(minutes=15)
async def stock_news_loop():
    try:
        await _maybe_broadcast_stock_news()
    except Exception:
        pass


@tasks.loop(seconds=300)
async def weather_refresh_loop():
    try:
        wid, until = roll_weather()
        await write_json(WEATHER_PATH, {"id": wid, "until": until})
    except Exception:
        pass


@tasks.loop(seconds=1800)
async def server_events_loop():
    """황금시간 랜덤 발생 · 일일 현상수배 갱신."""
    try:
        st = await get_events_state()
        st, started = try_start_golden_hour(st)
        if started:
            await write_json(EVENT_PATH, st)
            ch_id = _env_int("ANNOUNCE_CHANNEL_ID")
            if ch_id:
                ch = bot.get_channel(ch_id)
                if ch:
                    await ch.send(
                        "✨ **황금의 낚시터**가 열렸다! (15분)\n"
                        "희귀 물고기·상자 대폭 증가 — 지금 `!낚시`!"
                    )
    except Exception:
        pass


@tasks.loop(seconds=5)
async def auto_fish_loop():
    d = await _auto_enabled_users()
    users = (d or {}).get("users") or {}
    if not isinstance(users, dict) or not users:
        return

    now = utc_ts()
    for uid_str, info in list(users.items()):
        try:
            user_id = int(uid_str)
        except Exception:
            continue
        if not isinstance(info, dict) or not info.get("enabled"):
            continue

        channel_id = info.get("channel_id")
        if not channel_id:
            continue
        channel = bot.get_channel(int(channel_id))
        if not channel:
            continue

        rod_type, rod_level = await get_rod(user_id)
        paid = bool(info.get("paid", False))
        if not _auto_allowed(rod_level, paid):
            await _set_auto_user(user_id, enabled=False, channel_id=int(channel_id))
            try:
                await channel.send(f"<@{user_id}> 자동낚시가 꺼졌어. 조건: **+7 이상** 또는 **50,000원 구매**")
            except Exception:
                pass
            continue

        # 1. 쿨타임 조회 (맵, 미끼, 도감 완성 버프가 포함된 쿨타임)
        cd_seconds = await get_user_cooldown(user_id, rod_type, rod_level)
        
        # 신화 도감 버프 (자동 낚시 쿨타임 1초 영구 감소)
        buffs = await get_collection_buffs(user_id)
        if buffs.get("auto_cooldown_reduction", 0) > 0:
            cd_seconds = max(3, cd_seconds - buffs["auto_cooldown_reduction"])

        last = await get_last_fish_ts(user_id)
        if (last + cd_seconds) > now:
            continue

        # 2. 미끼 소모
        map_id = await get_user_map(user_id)
        had_bait_equipped = bool(await get_user_bait(user_id))
        bait_consumed = await consume_active_bait(user_id)
        active_bait_id = bait_consumed["bait_id"] if bait_consumed else None

        await set_last_fish_ts(user_id, now)
        catch_txt, is_new, _, _ = await perform_fishing_catch(
            user_id, rod_type, rod_level, map_id, active_bait_id, None
        )

        bait_txt = _format_bait_status(bait_consumed, had_bait_equipped)
        cd_txt = f"\n⏱️ 다음 낚시까지 {_format_wait_time(cd_seconds)}"

        new_txt = ""
        if is_new:
            new_txt = f"\n🎉 **새로운 물고기 도감 등록!**"

        m_name = MAPS.get(map_id, MAPS["river"])["name"]
        try:
            await channel.send(
                f"🤖🎣 <@{user_id}> 자동낚시 ({m_name}){bait_txt}{cd_txt}\n{catch_txt}{new_txt}"
            )
        except Exception:
            pass


def _parse_bet(s: str | None) -> int | None:
    if not s:
        return None
    s = s.replace(",", "").strip()
    if not s.isdigit():
        return None
    v = int(s)
    return v if v > 0 else None


async def _casino_guard(ctx: commands.Context, bet: int) -> tuple[bool, str | None]:
    if not _channel_allowed(ctx):
        return False, None

    CASINO_CD_SECONDS = 5
    CASINO_MAX_BET = 5_000_000

    if bet <= 0:
        return False, "베팅은 1원 이상만 가능해."
    if bet > CASINO_MAX_BET:
        return False, f"베팅 상한은 **{_fmt_money(CASINO_MAX_BET)}**이야."

    now = utc_ts()
    last = await get_last_casino_ts(ctx.author.id)
    wait = (last + CASINO_CD_SECONDS) - now
    if wait > 0:
        return False, f"카지노 쿨타임이야. **{wait}초** 뒤에 다시!"

    money = await get_money(ctx.author.id)
    if money < bet:
        return False, f"돈이 부족해. 보유: **{_fmt_money(money)}**"

    await set_last_casino_ts(ctx.author.id, now)
    return True, None


async def _get_casino_stats(user_id: int) -> dict:
    all_stats = await read_json(CASINO_STATS_PATH, _default_casino_stats())
    s = (all_stats or {}).get(str(user_id))
    return dict(s or {})


async def _vip_discount_rate(user_id: int) -> float:
    # 연승 + 낚시대 강화로 수수료 할인 (최대 35% 할인)
    s = await _get_casino_stats(user_id)
    streak = int(s.get("streak", 0))
    rod_type, rod_level = await get_rod(user_id)

    streak_part = min(0.15, max(0.0, streak) * 0.01)  # 0~15%
    rod_part = min(0.20, max(0, rod_level) * 0.01)    # 0~20%
    return min(0.35, streak_part + rod_part)


async def _set_lucky_buff(user_id: int, on: bool) -> None:
    def mut(d):
        d = dict(d or {})
        s = get_user_dict(d, user_id, {})
        if on:
            s["lucky_buff"] = 1
        else:
            s.pop("lucky_buff", None)
        return d

    await update_json(CASINO_STATS_PATH, _default_casino_stats(), mut)


async def _consume_lucky_buff(user_id: int) -> bool:
    all_stats = await read_json(CASINO_STATS_PATH, _default_casino_stats())
    s = (all_stats or {}).get(str(user_id)) or {}
    if not s.get("lucky_buff"):
        return False
    await _set_lucky_buff(user_id, False)
    return True


async def _casino_fee(user_id: int, base_fee: float) -> float:
    disc = await _vip_discount_rate(user_id)
    tb = await get_title_buffs(user_id)
    disc += float(tb.get("casino", 0.0))
    disc = min(0.5, disc)
    fee = max(0.0, base_fee * (1.0 - disc))
    all_stats = await read_json(CASINO_STATS_PATH, _default_casino_stats())
    if (all_stats or {}).get(str(user_id), {}).get("lucky_buff"):
        fee *= 0.5
        await _consume_lucky_buff(user_id)
    return fee


async def apply_chest_rewards(user_id: int, rewards: dict) -> str:
    if rewards.get("money", 0) > 0:
        await add_money(user_id, int(rewards["money"]))
    for iid, qty in (rewards.get("items") or {}).items():
        await add_fish(user_id, str(iid), int(qty))
    for fid, qty in (rewards.get("fish") or {}).items():
        await add_fish(user_id, str(fid), int(qty))
        fish = FISH_BY_ID.get(str(fid))
        if fish:
            await bump_stats(user_id, fish.rarity)
            await add_to_collection(user_id, fish.id)
    return "\n".join(rewards.get("lines") or ["(보상 없음)"])


async def get_weather_state() -> dict:
    w = await read_json(WEATHER_PATH, _default_weather())
    now = utc_ts()
    if int(w.get("until", 0)) <= now:
        wid, until = roll_weather()
        w = {"id": wid, "until": until}
        await write_json(WEATHER_PATH, w)
    return w


async def get_profile(user_id: int) -> dict:
    all_p = await read_json(PROFILE_PATH, _default_profile())
    p = dict((all_p or {}).get(str(user_id)) or {})
    ach = p.get("achievements", [])
    if not isinstance(ach, list):
        p["achievements"] = list(ach) if isinstance(ach, (set, tuple)) else []
    p.setdefault("achievements", [])
    p.setdefault("title", "title_rookie")
    p.setdefault("fish_total", 0)
    p.setdefault("chest_total", 0)
    p.setdefault("shiny_total", 0)
    p.setdefault("legendary_total", 0)
    p.setdefault("mythic_total", 0)
    p.setdefault("boss_hits", 0)
    p.setdefault("casino_wins", 0)
    p.setdefault("casino_plays", 0)
    p.setdefault("duel_wins", 0)
    p.setdefault("gacha_total", 0)
    p.setdefault("weekly_fish", 0)
    p.setdefault("weekly_key", "")
    p.setdefault("tourney_key", "")
    p.setdefault("tourney_score", 0)
    return p


async def save_profile(user_id: int, profile: dict) -> None:
    def mut(d):
        d = dict(d or {})
        d[str(user_id)] = profile
        return d

    await update_json(PROFILE_PATH, _default_profile(), mut)


async def profile_update(user_id: int, mutator) -> dict:
    def mut(d):
        d = dict(d or {})
        p = dict((d.get(str(user_id)) or {}))
        mutator(p)
        d[str(user_id)] = p
        return d

    return await update_json(PROFILE_PATH, _default_profile(), mut)


def _default_pets() -> Dict[str, dict]:
    return {}


def _default_fun() -> Dict[str, dict]:
    return {}


def _parse_daily_entry(raw) -> dict:
    if isinstance(raw, dict):
        return {"last": str(raw.get("last", "")), "streak": int(raw.get("streak", 0))}
    if isinstance(raw, str):
        return {"last": raw, "streak": 1}
    return {"last": "", "streak": 0}


async def get_pet_record(user_id: int) -> dict | None:
    pets = await read_json(PET_PATH, _default_pets())
    raw = (pets or {}).get(str(user_id))
    if not isinstance(raw, dict) or not raw.get("pet_id"):
        return None
    return raw


async def save_pet_record(user_id: int, record: dict) -> None:
    def mut(d):
        d = dict(d or {})
        d[str(user_id)] = record
        return d

    await update_json(PET_PATH, _default_pets(), mut)


async def get_pet_bonuses(user_id: int) -> dict:
    p = await get_pet_record(user_id)
    if not p:
        return {"rarity": 0.0, "shiny": 0.0, "level": 0}
    lv = pet_xp_to_level(int(p.get("xp", 0)))
    return {
        "rarity": pet_rarity_bonus(lv),
        "shiny": pet_shiny_bonus(lv),
        "level": lv,
        "pet_id": p["pet_id"],
    }


async def _bump_tournament_score(user_id: int, rarity: str, is_shiny: bool) -> int:
    if not is_tournament_active():
        return 0
    pts = fish_tournament_points(rarity, is_shiny)
    tk = tournament_weekend_key()

    def mut(p):
        if p.get("tourney_key") != tk:
            p["tourney_key"] = tk
            p["tourney_score"] = 0
        p["tourney_score"] = int(p.get("tourney_score", 0)) + pts

    await profile_update(user_id, mut)
    return pts


async def _grant_wheel_reward(user_id: int, roll: dict) -> str:
    t = roll["type"]
    label = roll.get("label", "보상")
    if t == "money":
        amt = random.randint(int(roll["min"]), int(roll["max"]))
        await add_money(user_id, amt)
        return f"{label}: **{_fmt_money(amt)}**"
    if t == "item":
        iid = roll["id"]
        qty = random.randint(int(roll["min"]), int(roll["max"]))
        await add_fish(user_id, iid, qty)
        return f"{label}: **{ITEMS[iid]['name']}** x{qty}"
    if t == "chest":
        cid = roll["id"]
        qty = random.randint(int(roll["min"]), int(roll["max"]))
        await add_fish(user_id, cid, qty)
        return f"{label}: **{CHESTS[cid]['name']}** x{qty}"
    return label


async def check_achievements(user_id: int, rod_level: int, money: int) -> list[str]:
    profile = await get_profile(user_id)
    ach_list = profile.get("achievements", [])
    if not isinstance(ach_list, list):
        ach_list = []
        profile["achievements"] = ach_list
    newly = []
    for ach_id in ACHIEVEMENTS:
        if ach_id in ach_list:
            continue
        if achievement_progress(profile, ach_id, rod_level, money):
            profile.setdefault("achievements", []).append(ach_id)
            newly.append(ach_id)
            await add_money(user_id, int(ACHIEVEMENTS[ach_id]["reward"]))
    if newly:
        await save_profile(user_id, profile)
    return newly


async def quest_bump(user_id: int, qtype: str, amount: int = 1, extra: int = 0) -> None:
    def mut(p):
        day = today_key()
        wk = week_key()
        if p.get("weekly_key") != wk:
            p["weekly_key"] = wk
            p["weekly_fish"] = 0
            p["weekly_quest"] = dict(WEEKLY_QUEST)
            p["weekly_progress"] = 0
            p["weekly_done"] = False

        if p.get("quest_day") != day or not p.get("daily_quest"):
            p["quest_day"] = day
            p["daily_quest"] = pick_daily_quest()
            p["daily_progress"] = 0
            p["daily_done"] = False

        if not p.get("daily_done"):
            dq = p["daily_quest"]
            if dq.get("type") == qtype:
                if qtype == "sell_gold":
                    p["daily_progress"] = int(p.get("daily_progress", 0)) + int(extra)
                else:
                    p["daily_progress"] = int(p.get("daily_progress", 0)) + int(amount)

        if not p.get("weekly_done") and p.get("weekly_quest", {}).get("type") == qtype:
            if qtype != "sell_gold":
                p["weekly_progress"] = int(p.get("weekly_progress", 0)) + int(amount)

    await profile_update(user_id, mut)


async def _announce_epic_catch(
    ctx: commands.Context | None,
    user_id: int,
    fish: Fish,
    is_shiny: bool,
) -> None:
    ch_id = _env_int("ANNOUNCE_CHANNEL_ID")
    if not ch_id:
        return
    if fish.rarity == "mythic":
        if random.random() > BROADCAST_MYTHIC_CHANCE:
            return
    elif fish.rarity == "legendary":
        if random.random() > BROADCAST_LEGENDARY_CHANCE:
            return
    else:
        return
    ch = bot.get_channel(ch_id)
    if not ch:
        return
    name = _display_name(ctx, user_id) if ctx else USER_MAP.get(user_id, f"유저({user_id})")
    flair = "🌌" if fish.rarity == "mythic" else "👑"
    shiny = " ✨이색" if is_shiny else ""
    try:
        await ch.send(
            f"{flair} **[전서버 속보]** **{name}** 님이\n"
            f"**{RARITY_LABEL.get(fish.rarity, fish.rarity)} · {fish.name}**{shiny} 을(를) 낚아올렸다!!!\n"
            f"🌊 심연이 흔들립니다..."
        )
    except Exception:
        pass


def _discord_server_id(ctx: commands.Context | None, explicit: int | None = None) -> int | None:
    if explicit is not None:
        return explicit
    if ctx and ctx.guild:
        return int(ctx.guild.id)
    return None


async def _guild_load_all() -> dict:
    return dict(await read_json(GUILD_PATH, default_guild_db()) or {})


async def _guild_save_all(data: dict) -> None:
    await write_json(GUILD_PATH, data)


async def _guild_get_server(server_id: int) -> tuple[dict, dict, str]:
    all_g = await _guild_load_all()
    sid = str(server_id)
    if sid not in all_g or not isinstance(all_g[sid], dict):
        all_g[sid] = default_server_guilds()
    return all_g[sid], all_g, sid


async def guild_get_buffs(user_id: int, server_id: int | None) -> dict:
    if not server_id:
        return {}
    srv, _, _ = await _guild_get_server(server_id)
    cid = get_user_clan_id(srv, user_id)
    if not cid:
        return {}
    clan = get_clan(srv, cid)
    if not clan:
        return {}
    return guild_buffs(int(clan.get("level", 1)))


async def guild_on_fish_caught(user_id: int, server_id: int | None, count: int = 1) -> None:
    if not server_id or count <= 0:
        return

    def mut(all_g):
        all_g = dict(all_g or {})
        sid = str(server_id)
        srv = dict(all_g.get(sid) or default_server_guilds())
        cid = get_user_clan_id(srv, user_id)
        if not cid:
            return all_g
        clans = dict(srv.get("clans") or {})
        clan = dict(clans.get(cid) or {})
        if not is_member(clan, user_id):
            return all_g
        reset_weekly_if_needed(clan)
        clan["weekly_fish"] = int(clan.get("weekly_fish", 0)) + int(count)
        add_guild_xp(clan, count * 2)
        clans[cid] = clan
        srv["clans"] = clans
        all_g[sid] = srv
        return all_g

    await update_json(GUILD_PATH, default_guild_db(), mut)


async def perform_fishing_catch(
    user_id: int,
    rod_type: str,
    rod_level: int,
    map_id: str,
    active_bait_id: str | None,
    ctx: commands.Context | None = None,
    discord_server_id: int | None = None,
) -> tuple[str, bool, Fish | None, bool]:
    """반환: (메시지, 도감신규, Fish|None, is_shiny)"""
    weather = await get_weather_state()
    wid = weather.get("id", "sunny")
    wbonus_chest = chest_chance_bonus(wid)
    wbonus_rarity = float(WEATHER_TYPES.get(wid, {}).get("rarity_bonus", 0.0))
    pet_b = await get_pet_bonuses(user_id)
    wbonus_rarity += float(pet_b.get("rarity", 0.0))
    rec = await get_rod_record(user_id)
    affixes = rec.get("affixes", [])
    wbonus_chest += affix_chest_bonus(affixes)
    wbonus_rarity += affix_rarity_bonus(affixes)
    fish_buffs = await get_fishing_buffs(user_id, ctx, discord_server_id)
    title_b = fish_buffs.get("_title") or {}
    wbonus_rarity += float(fish_buffs.get("rarity", 0.0))
    wbonus_chest += float(fish_buffs.get("chest", 0.0))
    srv_id = _discord_server_id(ctx, discord_server_id)

    def _weight_adj(w):
        w2 = apply_weather_rarity_shift(w, wid)
        return apply_title_rarity_shift(w2, title_b)

    kind, payload = roll_fishing_catch(
        rod_level,
        rod_type,
        map_id,
        active_bait_id,
        extra_chest_chance=wbonus_chest,
        extra_rarity_boost=wbonus_rarity,
        fish_picker=make_fish_picker(map_id, wid),
        weight_adjuster=_weight_adj,
    )

    def bump_profile(p):
        if kind == "chest":
            p["chest_total"] = int(p.get("chest_total", 0)) + 1
        else:
            p["fish_total"] = int(p.get("fish_total", 0)) + 1
            p["weekly_fish"] = int(p.get("weekly_fish", 0)) + 1

    await profile_update(user_id, bump_profile)

    if kind == "chest":
        chest_id = str(payload)
        await add_fish(user_id, chest_id, 1)
        await quest_bump(user_id, "chest", 1)
        return format_chest_drop(chest_id), False, None, False

    fish = payload
    shiny_rate = shiny_chance(rod_level, wid) + float(pet_b.get("shiny", 0.0))
    shiny_rate += float(fish_buffs.get("shiny", 0.0))
    is_shiny = random.random() < min(0.12, shiny_rate)
    inv_key = _fish_inv_key(fish.id, is_shiny)

    tourney_pts = await _bump_tournament_score(user_id, fish.rarity, is_shiny)
    tourney_txt = ""
    if tourney_pts > 0:
        prof = await get_profile(user_id)
        tourney_txt = (
            f"\n🏆 **토너먼트 +{tourney_pts}점** "
            f"(시즌 합계 **{int(prof.get('tourney_score', 0))}점**)"
        )

    await add_fish(user_id, inv_key, 1)
    await bump_stats(user_id, fish.rarity)

    def bump_rarity(p):
        if is_shiny:
            p["shiny_total"] = int(p.get("shiny_total", 0)) + 1
        if fish.rarity == "legendary":
            p["legendary_total"] = int(p.get("legendary_total", 0)) + 1
        if fish.rarity == "mythic":
            p["mythic_total"] = int(p.get("mythic_total", 0)) + 1

    await profile_update(user_id, bump_rarity)

    is_new = await add_to_collection(user_id, fish.id)
    await quest_bump(user_id, "fish", 1)
    if fish.rarity in ("rare", "epic", "legendary", "mythic"):
        await quest_bump(user_id, "rare_plus", 1)
    await guild_on_fish_caught(user_id, srv_id, 1)

    streak_txt = ""

    def _streak_mut(p):
        nonlocal streak_txt
        p, _streak, streak_txt = bump_fish_streak(p)
        return p

    await profile_update(user_id, _streak_mut)

    frag_txt = ""
    frag_bonus = affix_fragment_bonus(affixes) + float(title_b.get("fragment", 0.0))
    frags = roll_fragment_drop(rod_level, frag_bonus)
    if frags > 0:
        await add_fish(user_id, FRAGMENT_ITEM_ID, frags)
        frag_txt = f"\n🧩 **심연의 파편** +{frags}"

    if is_shiny:
        sell = fish.sell * 3
        msg = (
            f"✨✨ **이색 물고기!** {RARITY_FLAIR.get(fish.rarity,'🐟')} **{fish.name}** "
            f"(이색 판매가: {sell:,}원){tourney_txt}{frag_txt}"
        )
    else:
        msg = format_fish_catch(fish) + tourney_txt + frag_txt

    bty = bounty_info(await get_events_state())
    if bty and fish.id == bty["fish_id"]:
        msg += f"\n🎯 **오늘의 현상수배!** `!판매` 시 **{BOUNTY_SELL_MULT:.0f}배** 보너스!"
    if streak_txt:
        msg += streak_txt

    if fish.rarity in ("legendary", "mythic"):
        await _announce_epic_catch(ctx, user_id, fish, is_shiny)

    return msg, is_new, fish, is_shiny


@bot.command(name="잭팟")
async def jackpot_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    j = await read_json(JACKPOT_PATH, _default_jackpot())
    pot = int((j or {}).get("pot", 0))
    await ctx.reply(f"💰 현재 잭팟: **{_fmt_money(pot)}**", mention_author=False)


@bot.command(name="잭팟랭킹")
async def jackpot_ranking_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    hist = await read_json(JACKPOT_HISTORY_PATH, _default_jackpot_history())
    hits = list((hist or {}).get("hits") or [])
    if ctx.guild:
        hits = [h for h in hits if h.get("guild_id") in (None, ctx.guild.id) or h.get("guild_id") == ctx.guild.id]
        hits = [h for h in hits if h.get("guild_id") == ctx.guild.id]

    if not hits:
        await ctx.reply("아직 잭팟 당첨 기록이 없어.", mention_author=False)
        return

    agg: Dict[int, int] = {}
    for h in hits:
        try:
            uid = int(h.get("user_id"))
            amt = int(h.get("amount", 0))
        except Exception:
            continue
        agg[uid] = agg.get(uid, 0) + max(0, amt)

    top = sorted(agg.items(), key=lambda kv: kv[1], reverse=True)[:10]
    recent = sorted(hits, key=lambda h: int(h.get("ts", 0)), reverse=True)[:5]

    lines = ["**💥 잭팟 랭킹 TOP 10 (누적)**"]
    for i, (uid, total) in enumerate(top, start=1):
        name = _display_name(ctx, uid)
        lines.append(f"{i}. **{name}** — **{_fmt_money(total)}**")

    lines.append("\n**최근 잭팟 5개**")
    for h in recent:
        uid = int(h.get("user_id"))
        amt = int(h.get("amount", 0))
        ts = int(h.get("ts", 0))
        name = _display_name(ctx, uid)
        lines.append(f"- **{name}**: {_fmt_money(amt)} (<t:{ts}:R>)")

    await ctx.reply("\n".join(lines), mention_author=False)


def _env_int(name: str) -> int | None:
    v = os.getenv(name)
    if not v:
        return None
    try:
        return int(v.strip())
    except Exception:
        return None


def _channel_allowed(ctx: commands.Context) -> bool:
    allowed = _env_int("COMMAND_CHANNEL_ID")
    if not allowed:
        return True
    return getattr(ctx.channel, "id", None) == allowed


@bot.event
async def on_command_error(ctx: commands.Context, error: Exception):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.CheckFailure):
        return
    orig = getattr(error, "original", error)
    name = getattr(ctx.command, "name", "?")
    await ctx.reply(
        f"⚠️ `!{name}` 처리 중 오류가 발생했어. 잠시 후 다시 시도해줘.\n"
        f"({type(orig).__name__})",
        mention_author=False,
    )


@bot.event
async def on_ready():
    ensure_dir(DATA_DIR)
    print(f"Logged in as {bot.user} (id={bot.user.id})")
    if not auto_fish_loop.is_running():
        auto_fish_loop.start()
    if not weather_refresh_loop.is_running():
        weather_refresh_loop.start()
    if not stock_market_loop.is_running():
        stock_market_loop.start()
    if not stock_news_loop.is_running():
        stock_news_loop.start()
    if not server_events_loop.is_running():
        server_events_loop.start()
    await _ensure_stock_market()
    await get_events_state()
    ch_id = _env_int("ANNOUNCE_CHANNEL_ID")
    if ch_id:
        ch = bot.get_channel(ch_id)
        if ch:
            try:
                await ch.send("낚시 RPG 봇 온라인!")
            except Exception:
                pass


HELP_TOPICS: Dict[str, list[str]] = {
    "낚시": [
        "**🎣 낚시 · 성장**",
        "`!낚시` `!인벤` `!판매` `!판매 all` `!판매 아이템all` `!판매 전체`",
        "`!도감` `!낚시대` `!강화` (최대 +30강)",
        "`!상점` `!아이템상점` `!구매` `!미끼장착` `!낚시터` `!이동`",
        "`!랭킹` `!낚시대랭킹` `!보스` `!보스공격` `!자동낚시`",
        "`!상자` `!상자깨기` `!상자정보` `!보물상자`(30분 쿨)",
    ],
    "시작": [
        "**📖 처음 오셨나요?**",
        "1️⃣ `!낚시` — 돈·물고기 획득 (가장 기본)",
        "2️⃣ `!판매` / `!판매 all` — 물고기 판매로 돈 벌기",
        "3️⃣ `!강화` — 낚시대 +1~+30 (최대 **+30강**)",
        "4️⃣ `!상점` → `!구매` — 더 좋은 낚시대",
        "5️⃣ `!낚시터` → `!이동 ocean` — 지역 이동",
        "6️⃣ `!보스` → `!보스공격` — 요일 보스 · `!월드보스` 크라켄",
        "7️⃣ `!길드생성` / `!길드가입` — 친구들과 협동",
        "💡 자세히: `!가이드` · 카테고리: `!도움말 낚시`",
    ],
    "카지노": [
        "**🎲 도박** (베팅  50만)",
        "`!슬롯` `!슬롯10` `!잭팟` `!잭팟랭킹` `!주화`",
        "`!로켓 <베팅> <배율2~10>` — 로켓 (쉬움)",
        "`!심연 <베팅>` — 극악확률 초고배당 (`!심연확률`)",
        "`!보물탐사 <베팅> <문1~3>` — 3문 중 선택 (`!보물탐사도움`)",
        "`!복도 <베팅> <구간1~5>` — 구간 돌파 (`!복도도움`)",
    ],
    "성장": [
        "**🌟 성장 · 이벤트**",
        "`!일일` `!행운판` `!프로필` `!퀘스트` `!업적` `!칭호`",
        "`!날씨` `!시세` `!뽑기` `!수수권` `!제작`",
        "`!대결` `!대결수락` `!대결거절` `!대결취소` `!낚시랭킹`",
        "`!펫` `!펫데려오기` `!펫밥` `!펫이름` `!토너먼트` `!토너랭킹`",
        "`!물고기퀴즈` `!퀴즈정답`",
        "`!칭호` — 장착 시 **능력치 실제 적용** (희귀·보스·판매 등)",
    ],
    "이벤트": [
        "**🎪 서버 이벤트 · 미니게임**",
        "`!이벤트` — 황금시간·현상수배·연속기록·복권 현황",
        "✨ **황금의 낚시터** — 30분마다 랜덤 15분 / `!황금시간`(하루 1회 강제)",
        "🎯 **현상수배** — 오늘 지정 물고기 `!판매` 시 **3배**",
        "🔥 **연속 낚시** — 하루 연속 30회 → 업적·칭호 `title_streak`",
        "🎟️ `!행운번호 77` → `!행운번호추첨` (1~100, 하루 1회 참여)",
    ],
    "투자": [
        "**📈 주식 · 부동산**",
        "`!주식목록` `!주식매수` `!주식매도` `!주식매도 전체` `!주식보유` `!주식시세`",
        "`!부동산` `!부동산구매` `!부동산보유` `!월세수령` `!부동산매도`",
        "`!대출` `!상환`",
    ],
    "길드": [
        "**⚔️ 길드 · 협동**",
        "`!길드생성 <이름>` `!길드가입 <이름>` `!길드초대` `!길드수락` `!길드거절`",
        "`!길드` `!길드원` `!길드탈퇴` `!길드기부` `!길드출금`(길드장)",
        "`!길드레이드` `!길드공격` `!길드주간보상` `!길드랭킹`",
        "`!길드추방` `!길드임명` `!길드해산`(길드장)",
    ],
    "월드": [
        "**🗺️ 월드 · 탐험 · 수집**",
        "`!낚시터` `!이동` — volcano glacier lab 등 지역별 희귀어",
        "`!날씨` — 폭풍/안개 등 시세·등장률 · KST 0~2시 유령물고기",
        "`!월드보스` `!보스공격` — 크라켄 서버 레이드",
        "`!파편제작` — 심연의 파편 100개 → 신화 낚시대",
        "`!탐험` `!탐험수령` `!탐험선` `!탐험업그레이드`",
        "`!섬` `!섬전시` `!섬수령` `!섬방문` `!섬좋아요`",
        "`!옵션` `!재련` `!옵션잠금` — 낚시대 랜덤 옵션",
    ],
}


def _help_all_parts() -> list[str]:
    parts = [
        "**🎣 낚시 RPG — 전체 명령어**",
        "카테고리: `!도움말 시작` `!도움말 낚시` `!도움말 카지노` `!도움말 성장` `!도움말 이벤트` `!도움말 투자` `!도움말 길드` `!도움말 월드`",
    ]
    for lines in HELP_TOPICS.values():
        parts.extend(lines)
        parts.append("")
    return parts


@bot.command(name="가이드", aliases=["시작가이드", "튜토리얼"])
async def guide_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    parts = HELP_TOPICS["시작"] + [
        "",
        "**⚔️ 최종 목표 낚시대**",
        "- **⚔️ 세계관수** — 보스 딜 최강 (상점 판매 ❌)",
        "- 획득: 🦴 **관수의 척추** (월드보스·요일보스 딜1등 극소확률)",
        "- `!각성` — 척추 **5개** + 파편 **80개** + 낚시대 **+24강** 이상",
        "",
        "**🛒 추천 성장 루트**",
        "초보 → `!구매 bamboo` → `!강화` → `!이동 ocean` → `!구매 deepsea`",
        "중반 → 길드 가입 · `!탐험 3` · `!파편제작`(파편100)",
        "",
        "**🎖️ 칭호 · 🎪 이벤트**",
        "- `!업적` 달성 → 칭호 해금 · `!칭호 <ID>` 장착 시 **능력치 적용**",
        "- `!이벤트` — 황금시간 / 현상수배 3배판매 / 연속낚시 / 행운복권",
        "",
        "명령어 전체: `!도움말` / 분류: `!도움말 이벤트`",
    ]
    await _reply_long(ctx, parts, header="**📖 낚시 RPG 가이드**")


@bot.command(name="도움말")
async def help_cmd(ctx: commands.Context, topic: str | None = None):
    if not _channel_allowed(ctx):
        return
    try:
        key = (topic or "").strip().lower()
        if key and key not in HELP_TOPICS and key not in ("전체", "all"):
            await ctx.reply(
                "없는 카테고리야.\n"
                "`!도움말` `!도움말 시작` `!도움말 낚시` `!도움말 카지노` `!도움말 성장` `!도움말 투자` `!도움말 길드` `!도움말 월드`",
                mention_author=False,
            )
            return
        parts = HELP_TOPICS[key] if key in HELP_TOPICS else _help_all_parts()
        header = f"**도움말 — {key}**" if key in HELP_TOPICS else ""
        await _reply_long(ctx, parts, header=header)
    except discord.HTTPException:
        await ctx.reply(
            "도움말이 길어서 나눠 보낼게.\n"
            "`!도움말 시작` / `!도움말 낚시` / `!도움말 카지노` / `!도움말 성장` / `!도움말 투자` / `!도움말 길드` / `!도움말 월드`",
            mention_author=False,
        )


WORLDENDER_SPINE = "worldender_spine"
WORLDENDER_SPINE_NEED = 5
WORLDENDER_FRAGMENT_NEED = 80


async def _maybe_drop_spine(uid: int, chance: float) -> bool:
    if random.random() < chance:
        await add_fish(uid, WORLDENDER_SPINE, 1)
        return True
    return False


@bot.command(name="낚시대")
async def rod_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    rod_type, level = await get_rod(ctx.author.id)
    cd = _rod_cooldown_seconds(rod_type, level)
    rec = await get_rod_record(ctx.author.id)
    aff = rec.get("affixes", [])
    aff_txt = ""
    if aff:
        aff_txt = "\n옵션: " + ", ".join(format_affix_line(a) for a in aff[:3])
    await ctx.reply(
        f"**{ctx.author.display_name}**의 낚시대: **{format_rod_name(rod_type, level)}** (최대 +{ROD_MAX_LEVEL}){aff_txt}\n"
        f"- 기본 쿨타임: **{cd}초**\n"
        f"- 보유금: **{_fmt_money(await get_money(ctx.author.id))}**",
        mention_author=False,
    )


@bot.command(name="상점")
async def shop_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    lines = [
        f"**🎣 낚시대 상점** (구매: `!구매 <ID>`) · 강화 최대 **+{ROD_MAX_LEVEL}**\n",
        "특수: `sovereign` 파편제작 · `worldender` 각성 (`!가이드`)\n",
    ]
    for rod_id, info in RODS.items():
        if info.get("craft_only") or info.get("drop_only"):
            tag = "🔒각성/제작"
            lines.append(
                f"- `{rod_id}`: **{info['name']}** — {rod_passive_text(rod_id)} ({tag})"
            )
            continue
        price = int(info.get("price", 0))
        req = int(info.get("req_level", 0))
        req_txt = f" (요구 **+{req}강**)" if req > 0 else ""
        desc = rod_passive_text(rod_id)
        lines.append(f"- `{rod_id}`: **{info['name']}** — {desc}{req_txt}\n  가격: **{_fmt_money(price)}**")
    await _reply_long(ctx, lines[1:], header=lines[0])


@bot.command(name="구매")
async def buy_cmd(ctx: commands.Context, item_id: str | None = None, amount_raw: str | None = None):
    if not _channel_allowed(ctx):
        return
    if not item_id:
        await ctx.reply("사용법: `!구매 <아이디|낚시대ID> [수량]`  (예: `!구매 flame` 또는 `!구매 bait_worm 10`)", mention_author=False)
        return
    
    item_id = item_id.strip().lower()
    
    # 1. 낚시대 구매인 경우
    if item_id in RODS:
        rod_info = RODS[item_id]
        if rod_info.get("craft_only") or rod_info.get("drop_only"):
            await ctx.reply(
                f"**{rod_info['name']}** 는 상점에서 살 수 없어.\n"
                f"{rod_info.get('desc', '특수 제작·각성·보스 드랍으로 획득')}",
                mention_author=False,
            )
            return
        cur_type, cur_level = await get_rod(ctx.author.id)
        if item_id == cur_type:
            await ctx.reply("이미 같은 낚시대를 사용 중이야.", mention_author=False)
            return

        req = int(RODS[item_id].get("req_level", 0))
        if cur_level < req:
            await ctx.reply(
                f"구매 조건 미달! **{RODS[item_id]['name']}**는 낚시대 **+{req}강** 이상 필요.\n"
                f"현재: **{format_rod_name(cur_type, cur_level)}**",
                mention_author=False,
            )
            return

        price = int(RODS[item_id].get("price", 0))
        money = await get_money(ctx.author.id)
        if money < price:
            await ctx.reply(
                f"돈이 부족해. 필요: **{_fmt_money(price)}**, 보유: **{_fmt_money(money)}**",
                mention_author=False,
            )
            return

        await add_money(ctx.author.id, -price)
        await set_rod(ctx.author.id, item_id, cur_level)
        await ctx.reply(
            f"구매 완료! 이제 **{format_rod_name(item_id, cur_level)}** 사용 중이야.",
            mention_author=False,
        )
        return
    
    # 2. 소모성 아이템 구매인 경우
    elif item_id in ITEMS:
        amount = 1
        if amount_raw:
            amount_raw = amount_raw.replace(",", "").strip()
            if amount_raw.isdigit():
                amount = int(amount_raw)
        if amount <= 0:
            await ctx.reply("구매 수량은 1개 이상이어야 해.", mention_author=False)
            return

        info = ITEMS[item_id]
        price_unit = int(info["price"])
        merchant = await read_json(MERCHANT_PATH, _default_merchant())
        m_offer = None
        if int(merchant.get("until", 0)) > utc_ts():
            for it in merchant.get("items", []):
                if it.get("id") == item_id and int(it.get("stock_left", 0)) > 0:
                    m_offer = it
                    price_unit = int(price_unit * float(it.get("discount", 1.0)))
                    break
        total_price = price_unit * amount
        
        money = await get_money(ctx.author.id)
        if money < total_price:
            await ctx.reply(
                f"돈이 부족해. 필요: **{_fmt_money(total_price)}**, 보유: **{_fmt_money(money)}**",
                mention_author=False,
            )
            return
            
        await add_money(ctx.author.id, -total_price)
        await add_fish(ctx.author.id, item_id, amount)

        if m_offer:
            stock = int(m_offer.get("stock_left", 0))
            if amount > stock:
                await ctx.reply(f"수수권 재고 부족! 남은 수량: **{stock}**", mention_author=False)
                return

            def mut_m(d):
                d = dict(d or {})
                for it in d.get("items", []):
                    if it.get("id") == item_id:
                        it["stock_left"] = max(0, int(it.get("stock_left", 0)) - amount)
                return d

            await update_json(MERCHANT_PATH, _default_merchant(), mut_m)
            disc_txt = f" (🧙 수수권 할인가)"
        else:
            disc_txt = ""

        await ctx.reply(
            f"🛒 구매 완료! **{info['name']} x{amount}**{disc_txt} (소모: {_fmt_money(total_price)})",
            mention_author=False,
        )
        return
        
    else:
        await ctx.reply("존재하지 않는 낚시대 또는 아이템 ID입니다. `!상점` 또는 `!아이템상점`을 확인해줘.", mention_author=False)


@bot.command(name="아이템상점")
async def item_shop_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    lines = ["**🛒 소모성 아이템 상점** (구매: `!구매 <아이템ID> [수량]`)\n"]
    for item_id, info in ITEMS.items():
        price = int(info.get("price", 0))
        lines.append(f"- `{item_id}`: **{info['name']}** / 가격: **{_fmt_money(price)}**")
        lines.append(f"  *설명: {info['desc']}*")
    await ctx.reply("\n".join(lines), mention_author=False)


@bot.command(name="낚시터")
async def maps_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    user_id = ctx.author.id
    cur_map = await get_user_map(user_id)
    
    w = await get_weather_state()
    wh = weather_fishing_hint(w.get("id", "sunny"))
    lines = [
        "**🗺️ 낚시터 목록** (이동: `!이동 <낚시터ID>`)\n",
        f"📡 날씨: {WEATHER_TYPES.get(w.get('id','sunny'),{}).get('name','?')}" + (f" — {wh}" if wh else "") + "\n",
    ]
    for m_id, info in MAPS.items():
        prefix = "📌 " if m_id == cur_map else "- "
        req = f"(요구 강화: **+{info['req_level']}강**)" if info['req_level'] > 0 else "(제한 없음)"
        fee = f"/ 이동 비용: **{_fmt_money(info['fee'])}**" if info['fee'] > 0 else ""
        lines.append(f"{prefix}`{m_id}`: **{info['name']}** {req} {fee}")
        
        mult = f"(쿨타임 배율 x{info['cooldown_multiplier']})"
        lines.append(f"  *배율: {mult}*")
    
    await ctx.reply("\n".join(lines), mention_author=False)


@bot.command(name="이동")
async def move_cmd(ctx: commands.Context, map_id: str | None = None):
    if not _channel_allowed(ctx):
        return
    if not map_id:
        await ctx.reply("사용법: `!이동 <낚시터ID>`  (예: `!이동 ocean`)", mention_author=False)
        return
        
    map_id = map_id.strip().lower()
    if map_id not in MAPS:
        await ctx.reply("존재하지 않는 낚시터입니다. `!낚시터`를 확인해줘.", mention_author=False)
        return
        
    user_id = ctx.author.id
    cur_map = await get_user_map(user_id)
    if map_id == cur_map:
        await ctx.reply("이미 그 낚시터에 위치해 있습니다.", mention_author=False)
        return
        
    rod_type, rod_level = await get_rod(user_id)
    info = MAPS[map_id]
    
    # 레벨 조건 체크
    if rod_level < info["req_level"]:
        await ctx.reply(
            f"🚫 입장 조건 미달! **{info['name']}**에 가려면 낚시대가 최소 **+{info['req_level']}강**이어야 합니다.\n"
            f"현재 낚시대: **{format_rod_name(rod_type, rod_level)}**",
            mention_author=False,
        )
        return
        
    # 이동 비용 차감
    fee = int(info["fee"])
    money = await get_money(user_id)
    if money < fee:
        await ctx.reply(
            f"🚫 이동 비용 부족! 필요: **{_fmt_money(fee)}**, 보유: **{_fmt_money(money)}**",
            mention_author=False,
        )
        return
        
    await add_money(user_id, -fee)
    await set_user_map(user_id, map_id)
    await ctx.reply(
        f"⛵ 슝! **{_fmt_money(fee)}**을(를) 지불하고 **{info['name']}**(으)로 성공적으로 이동했습니다!",
        mention_author=False,
    )


@bot.command(name="미끼장착")
async def bait_equip_cmd(ctx: commands.Context, bait_id: str | None = None):
    if not _channel_allowed(ctx):
        return
    if not bait_id:
        await ctx.reply("사용법: `!미끼장착 <미끼ID|off>`  (예: `!미끼장착 bait_worm` 또는 `!미끼장착 off`)", mention_author=False)
        return
        
    bait_id = bait_id.strip().lower()
    user_id = ctx.author.id
    
    if bait_id == "off" or bait_id == "해제":
        await set_user_bait(user_id, None)
        await ctx.reply("미끼 장착을 해제했습니다.", mention_author=False)
        return
        
    if bait_id not in ITEMS or ITEMS[bait_id]["type"] != "bait":
        await ctx.reply("올바른 미끼 ID가 아닙니다. `!아이템상점`에서 미끼 ID를 확인해줘.", mention_author=False)
        return
        
    inv = await get_inventory(user_id)
    qty = int(inv.get(bait_id, 0))
    if qty <= 0:
        await ctx.reply(f"해당 미끼(**{ITEMS[bait_id]['name']}**)를 보유하고 있지 않습니다. `!구매`로 구매해줘.", mention_author=False)
        return
        
    await set_user_bait(user_id, bait_id)
    await ctx.reply(f"🎣 **{ITEMS[bait_id]['name']}**을(를) 장착했습니다! (남은 수량: {qty}개)\n낚시 시 자동으로 소모 및 효과가 적용됩니다.", mention_author=False)


@bot.command(name="도감")
async def collection_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    user_id = ctx.author.id
    status = await get_collection_completion_status(user_id)
    buffs = await get_collection_buffs(user_id)
    
    lines = [f"**🏆 {ctx.author.display_name}**의 물고기 도감 달성도\n"]
    
    rarities = [
        ("common", "일반", "🐟"),
        ("rare", "희귀", "✨"),
        ("epic", "영웅", "🗡️"),
        ("legendary", "전설", "👑"),
        ("mythic", "신화", "☄️"),
    ]
    
    for r_key, r_name, flair in rarities:
        st = status[r_key]
        complete_flair = "✅ 완료! (버프 활성)" if st["complete"] else "⏳ 진행 중"
        lines.append(f"{flair} **{r_name}**: `{st['caught']}/{st['total']}` 개 수집 ({complete_flair})")
        
    lines.append("\n**✨ 현재 활성화된 영구 도감 버프**")
    
    if buffs["sell_bonus"] > 0:
        lines.append(f"- 물고기 판매가 **+{int(buffs['sell_bonus']*100)}%** 보너스 (일반 완료)")
    else:
        lines.append("- *물고기 판매가 +5%* (일반 도감 100% 필요)")
        
    if buffs["cooldown_reduction"] > 0:
        lines.append(f"- 낚시 기본 쿨타임 **-{buffs['cooldown_reduction']}초** 단축 (희귀 완료)")
    else:
        lines.append("- *낚시 쿨타임 -1초* (희귀 도감 100% 필요)")
        
    if buffs["upgrade_chance_bonus"] > 0:
        lines.append(f"- 낚시대 강화 확률 **+{int(buffs['upgrade_chance_bonus']*100)}%** 절대값 합산 (영웅 완료)")
    else:
        lines.append("- *강화 성공률 +3%* (영웅 도감 100% 필요)")
        
    if buffs["boss_damage_bonus"] > 0:
        lines.append(f"- 보스 레이드 데미지 **+{int(buffs['boss_damage_bonus']*100)}%** 버프 (전설 완료)")
    else:
        lines.append("- *보스 레이드 데미지 +15%* (전설 도감 100% 필요)")
        
    if buffs["auto_cooldown_reduction"] > 0:
        lines.append(f"- 자동 낚시 쿨타임 **-{buffs['auto_cooldown_reduction']}초** 추가 단축 (신화 완료)")
    else:
        lines.append("- *자동 낚시 쿨타임 -1초* (신화 도감 100% 필요)")
        
    await ctx.reply("\n".join(lines), mention_author=False)


@bot.command(name="낚시")
async def fish_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    user_id = ctx.author.id
    rod_type, rod_level = await get_rod(user_id)
    
    # 1. 쿨타임 계산
    cd_seconds = await get_user_cooldown(user_id, rod_type, rod_level)

    now = utc_ts()
    last = await get_last_fish_ts(user_id)
    wait = (last + cd_seconds) - now
    if wait > 0:
        bait_line = ""
        bait_id = await get_user_bait(user_id)
        if bait_id and bait_id in ITEMS:
            inv = await get_inventory(user_id)
            bait_line = (
                f"\n🪱 장착 미끼: **{ITEMS[bait_id]['name']}** "
                f"(보유 **{int(inv.get(bait_id, 0))}개**)"
            )
        await ctx.reply(
            f"⏱️ 낚시 쿨타임! {_format_wait_time(wait)} 뒤에 다시 가능해.{bait_line}",
            mention_author=False,
        )
        return

    # 2. 맵 정보 및 미끼 소모
    map_id = await get_user_map(user_id)
    had_bait_equipped = bool(await get_user_bait(user_id))
    bait_consumed = await consume_active_bait(user_id)
    active_bait_id = bait_consumed["bait_id"] if bait_consumed else None

    await set_last_fish_ts(user_id, now)
    catch_txt, is_new, _, _ = await perform_fishing_catch(
        user_id, rod_type, rod_level, map_id, active_bait_id, ctx
    )

    bait_txt = _format_bait_status(bait_consumed, had_bait_equipped)
    cd_txt = f"\n⏱️ 다음 낚시까지 {_format_wait_time(cd_seconds)}"

    new_txt = ""
    if is_new:
        new_txt = f"\n🎉 **새로운 물고기 도감 등록!**"

    m_name = MAPS.get(map_id, MAPS["river"])["name"]
    w = await get_weather_state()
    wid = w.get("id", "sunny")
    wtxt = WEATHER_TYPES.get(wid, {}).get("name", "")
    whint = weather_fishing_hint(wid)
    hint_txt = f"\n📡 {whint}" if whint else ""
    rod_lv = (await get_rod(user_id))[1]
    ach_new = await check_achievements(user_id, rod_lv, await get_money(user_id))
    ach_txt = ""
    if ach_new:
        lines = [f"🏆 업적 달성: **{ACHIEVEMENTS[a]['name']}** (+{_fmt_money(ACHIEVEMENTS[a]['reward'])})" for a in ach_new[:3]]
        ach_txt = "\n" + "\n".join(lines)

    pet_txt = ""
    pet_rec = await get_pet_record(user_id)
    if pet_rec:
        pe = PETS.get(pet_rec["pet_id"], {})
        pet_txt = f"\n{pe.get('emoji', '🐾')} **{pet_rec.get('name') or pe.get('name', '펫')}**가 함께했어!"

    await ctx.reply(
        f"**{ctx.author.display_name}** 낚시 성공! ({m_name}) {wtxt}{hint_txt}{bait_txt}{cd_txt}{pet_txt}\n"
        f"{catch_txt}{new_txt}{ach_txt}",
        mention_author=False,
    )


@bot.command(name="자동낚시")
async def auto_fish_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return

    user_id = ctx.author.id
    st = await _get_auto_user(user_id)
    enabled = bool(st.get("enabled", False))
    paid = bool(st.get("paid", False))
    rod_type, rod_level = await get_rod(user_id)

    if enabled:
        await _set_auto_user(user_id, enabled=False, channel_id=ctx.channel.id)
        await ctx.reply("자동낚시 OFF", mention_author=False)
        return

    if not _auto_allowed(rod_level, paid):
        price = 50_000
        money = await get_money(user_id)
        if money >= price:
            await add_money(user_id, -price)
            paid = True
            await _set_auto_user(user_id, enabled=True, channel_id=ctx.channel.id, paid=True)
            await ctx.reply(
                f"자동낚시 ON (구매 완료: **{_fmt_money(price)}**)\n"
                f"- 조건: +7 미만이면 50,000원 구매 필요\n"
                f"- 현재 낚시대: **{format_rod_name(rod_type, rod_level)}**",
                mention_author=False,
            )
            return

        await ctx.reply(
            "자동낚시는 조건이 있어.\n"
            f"- 조건: **낚시대 +7 이상** 또는 **{_fmt_money(price)}** 구매\n"
            f"- 현재 낚시대: **{format_rod_name(rod_type, rod_level)}**\n"
            f"- 보유금: **{_fmt_money(money)}**",
            mention_author=False,
        )
        return

    await _set_auto_user(user_id, enabled=True, channel_id=ctx.channel.id)
    await ctx.reply(
        f"자동낚시 ON\n- 채널: <#{ctx.channel.id}>\n- 낚시대: **{format_rod_name(rod_type, rod_level)}**",
        mention_author=False,
    )


@bot.command(name="인벤")
async def inv_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    try:
        inv = await get_inventory(ctx.author.id)
        if not inv:
            await ctx.reply("인벤토리가 비었어. `!낚시`로 시작해봐.", mention_author=False)
            return

        fish_lines = []
        item_lines = []
        unknown_lines = []

        total_items = 0
        total_value = 0

        mkt = market_mult_today()
        for item_key, cnt in sorted(inv.items(), key=lambda kv: (-int(kv[1]), str(kv[0]))):
            try:
                cnt = int(cnt)
            except Exception:
                continue
            if cnt <= 0:
                continue
            if item_key in FISH_BY_ID or (
                isinstance(item_key, str) and item_key.startswith("shiny_")
            ):
                sp = _fish_sell_price(item_key)
                total_items += cnt
                total_value += int(sp * mkt * cnt)
                fish_lines.append(
                    f"- {_inv_item_display(item_key)} x{cnt} (개당 {int(sp * mkt):,}원)"
                )
            elif item_key in CHESTS:
                info = CHESTS[item_key]
                item_lines.append(f"- {info['name']} x{cnt} (`!상자깨기 {item_key}`)")
            elif item_key in ITEMS:
                info = ITEMS[item_key]
                price = int(info.get("price", 0))
                sell_hint = f" / 판매 {price:,}원" if price > 0 else ""
                item_lines.append(f"- {info['name']} x{cnt}{sell_hint}")
            else:
                unknown_lines.append(f"- `{item_key}` x{cnt}")

        parts = [f"**🎒 {ctx.author.display_name}**의 인벤토리"]

        if fish_lines:
            parts.append("**🐟 물고기**")
            parts.extend(fish_lines)
            parts.append(
                f"합계: **{total_items}개** / 예상 판매가: **{_fmt_money(total_value)}**"
            )
        else:
            parts.append("🐟 *물고기 보관함이 비어있습니다.*")

        chest_lines = [l for l in item_lines if "상자깨기" in l]
        other_items = [l for l in item_lines if "상자깨기" not in l]
        if chest_lines:
            parts.append("**📦 보물상자**")
            parts.extend(chest_lines)
        if other_items:
            parts.append("**🎒 소모품·재료**")
            parts.extend(other_items)
        if unknown_lines:
            parts.append("**❓ 기타**")
            parts.extend(unknown_lines[:30])
            if len(unknown_lines) > 30:
                parts.append(f"... 외 {len(unknown_lines) - 30}종")

        bait = await get_user_bait(ctx.author.id)
        if bait and bait in ITEMS:
            qty = int(inv.get(bait, 0))
            parts.append(
                f"🎣 **장착 미끼**: {ITEMS[bait]['name']} (보유 **{qty}개**)"
            )

        map_id = await get_user_map(ctx.author.id)
        parts.append(f"📍 **낚시터**: {MAPS.get(map_id, MAPS['river'])['name']}")

        await _reply_long(ctx, parts)
    except Exception:
        await ctx.reply(
            "인벤을 불러오는 중 오류가 났어. 잠시 후 다시 시도해줘.\n"
            "(아이템이 너무 많으면 관리자에게 문의)",
            mention_author=False,
        )


def _sell_mult_for_user(
    buffs: dict, rod_type: str, title_buffs: dict | None = None
) -> float:
    tb = title_buffs or {}
    return (
        (1.0 + buffs.get("sell_bonus", 0.0))
        * (1.0 + float(tb.get("sell", 0.0)))
        * _rod_sell_mult(rod_type)
        * market_mult_today()
    )


def _bounty_sell_mult_for_key(fish_key: str, bounty: dict | None) -> float:
    if not bounty:
        return 1.0
    fid = fish_key[6:] if fish_key.startswith("shiny_") else fish_key
    if fid == bounty.get("fish_id"):
        return BOUNTY_SELL_MULT
    return 1.0


async def _sell_all_fish(user_id: int, sell_mult: float) -> int:
    inv = await get_inventory(user_id)
    bounty = bounty_info(await get_events_state())
    total = 0
    for fish_id, cnt in inv.items():
        if fish_id in FISH_BY_ID or fish_id.startswith("shiny_"):
            bm = _bounty_sell_mult_for_key(fish_id, bounty)
            total += int(math.floor(_fish_sell_price(fish_id) * cnt * sell_mult * bm))

    if total <= 0:
        return 0

    def mut(d):
        d = dict(d or {})
        uinv = get_user_dict(d, user_id, {})
        for key in list(uinv.keys()):
            if key in FISH_BY_ID or key.startswith("shiny_"):
                uinv.pop(key, None)
        if not uinv:
            d.pop(str(user_id), None)
        return d

    await update_json(INV_PATH, _default_inventory(), mut)
    return total


async def _sell_all_items(user_id: int) -> tuple[int, list[str]]:
    """소모품·재료(상점 판매가 있는 ITEMS) 일괄 판매. 상자·물고기 제외."""
    inv = await get_inventory(user_id)
    total = 0
    lines: list[str] = []
    for iid, cnt in list(inv.items()):
        if iid in CHESTS or iid in FISH_BY_ID or str(iid).startswith("shiny_"):
            continue
        if iid not in ITEMS:
            continue
        price = int(ITEMS[iid].get("price", 0))
        if price <= 0 or cnt <= 0:
            continue
        value = price * int(cnt)
        total += value
        await add_fish(user_id, iid, -int(cnt))
        lines.append(f"- {ITEMS[iid]['name']} x{cnt} ({value:,}원)")
    return total, lines


async def _stock_sell_all(ctx: commands.Context) -> None:
    port = await _get_user_portfolio(ctx.author.id)
    if not port:
        await ctx.reply("보유 주식이 없어.", mention_author=False)
        return

    market = await _get_stock_market()
    total_payout = 0
    total_cost = 0
    details: list[str] = []

    for sid in list(port.keys()):
        if sid not in STOCKS:
            continue
        pos = port.get(sid)
        qty = int(normalize_holding(pos).get("qty", 0))
        if qty <= 0:
            continue
        price, _ = _stock_price(market, sid)
        payout = price * qty
        _, cost_sold = _portfolio_remove_sell(port, sid, qty)
        realized = payout - cost_sold
        total_payout += payout
        total_cost += cost_sold
        s = STOCKS[sid]
        pl_icon = "🟢" if realized > 0 else ("🔴" if realized < 0 else "⚪")
        details.append(
            f"- **{s['company']}** {qty}주 @ {price:,}원 → {_fmt_money(payout)} "
            f"({pl_icon} {format_signed_money(realized)})"
        )

    if total_payout <= 0:
        await ctx.reply("매도할 주식이 없어.", mention_author=False)
        return

    await _set_user_portfolio(ctx.author.id, port)
    bal = await add_money(ctx.author.id, total_payout)
    total_realized = total_payout - total_cost
    pct = (total_realized / total_cost * 100) if total_cost > 0 else 0
    summary_pl = ""
    if total_cost > 0:
        icon = "🟢" if total_realized > 0 else ("🔴" if total_realized < 0 else "⚪")
        summary_pl = (
            f"\n{icon} **총 실현손익: {format_signed_money(total_realized)}** ({pct:+.2f}%)"
        )

    body = "\n".join(details[:20])
    if len(details) > 20:
        body += f"\n... 외 {len(details) - 20}종목"
    await ctx.reply(
        f"✅ **주식 전량 매도** ({len(details)}종목)\n"
        f"{body}\n"
        f"\n💰 매도 합계: **{_fmt_money(total_payout)}**{summary_pl}\n"
        f"잔액: **{_fmt_money(bal)}**",
        mention_author=False,
    )


async def _stock_buy_all(ctx: commands.Context) -> None:
    market = await _get_stock_market()
    money = await get_money(ctx.author.id)
    if money <= 0:
        await ctx.reply("매수할 돈이 없어.", mention_author=False)
        return

    ids = [sid for sid in STOCKS.keys() if sid in (market.get("prices") or {})]
    if not ids:
        await ctx.reply("매수 가능한 종목이 없어. 잠시 후 다시 시도해줘.", mention_author=False)
        return

    per_budget = money // len(ids)
    if per_budget <= 0:
        await ctx.reply("잔액이 너무 적어서 전체 분산 매수가 불가능해.", mention_author=False)
        return

    plan: list[tuple[str, int, int, int]] = []  # sid, price, qty, spend
    spent = 0
    for sid in ids:
        price, _ = _stock_price(market, sid)
        qty = int(per_budget // max(1, price))
        if qty <= 0:
            continue
        spend = qty * price
        plan.append((sid, price, qty, spend))
        spent += spend

    if not plan or spent <= 0:
        await ctx.reply(
            "현재 시세 기준으로는 잔액이 부족해 전체 분산 매수가 안 돼.",
            mention_author=False,
        )
        return

    await add_money(ctx.author.id, -spent)
    port = await _get_user_portfolio(ctx.author.id)
    lines = []
    for sid, price, qty, spend in plan:
        _portfolio_add_buy(port, sid, qty, price)
        s = STOCKS[sid]
        lines.append(f"- **{s['company']}** {qty}주 @ {price:,}원 = {_fmt_money(spend)}")
    await _set_user_portfolio(ctx.author.id, port)

    bal = await get_money(ctx.author.id)
    body = "\n".join(lines[:18])
    if len(lines) > 18:
        body += f"\n... 외 {len(lines) - 18}종목"
    await ctx.reply(
        f"✅ **전체 종목 분산 매수 완료** ({len(plan)}종목)\n"
        f"{body}\n"
        f"\n💸 사용 금액: **{_fmt_money(spent)}** / 잔액: **{_fmt_money(bal)}**",
        mention_author=False,
    )


@bot.command(name="판매")
async def sell_cmd(ctx: commands.Context, *, target: str | None = None):
    if not _channel_allowed(ctx):
        return
    if not target:
        await ctx.reply(
            "사용법:\n"
            "- `!판매 <물고기이름>` / `!판매 all` 물고기 전부\n"
            "- `!판매 아이템all` 소모품·재료 전부 (미끼·주문서 등)\n"
            "- `!판매 전체` 물고기 + 소모품 한 번에",
            mention_author=False,
        )
        return

    target = target.strip()
    inv = await get_inventory(ctx.author.id)
    if not inv:
        await ctx.reply("팔 게 없어. `!낚시`부터!", mention_author=False)
        return

    buffs = await get_collection_buffs(ctx.author.id)
    rod_type, _ = await get_rod(ctx.author.id)
    tb = await get_title_buffs(ctx.author.id)
    sell_mult = _sell_mult_for_user(buffs, rod_type, tb)
    bounty = bounty_info(await get_events_state())
    bonus_parts = []
    if buffs.get("sell_bonus", 0.0) > 0:
        bonus_parts.append("도감 +5%")
    if tb.get("sell"):
        bonus_parts.append(f"칭호 +{int(float(tb['sell']) * 100)}%")
    if _rod_sell_mult(rod_type) > 1.0:
        bonus_parts.append("낚시대 판매보너스")
    if bounty:
        bonus_parts.append(f"현상수배 {bounty['name']} x{BOUNTY_SELL_MULT:.0f}")
    bonus_txt = f" ({', '.join(bonus_parts)} 적용)" if bonus_parts else ""

    tlower = target.lower().replace(" ", "")

    if tlower in ("아이템all", "소모품all", "재료all", "소모품전부", "아이템전부"):
        item_total, item_lines = await _sell_all_items(ctx.author.id)
        if item_total <= 0:
            await ctx.reply(
                "판매할 소모품·재료가 없어. (상점 판매가 있는 아이템만 해당, 상자 제외)",
                mention_author=False,
            )
            return
        bal = await add_money(ctx.author.id, item_total)
        body = "\n".join(item_lines[:25])
        if len(item_lines) > 25:
            body += f"\n... 외 {len(item_lines) - 25}종"
        await ctx.reply(
            f"🛒 **소모품·재료 일괄 판매** ({len(item_lines)}종)\n"
            f"{body}\n\n"
            f"획득: **{_fmt_money(item_total)}** / 잔액: **{_fmt_money(bal)}**",
            mention_author=False,
        )
        return

    if tlower in ("전체", "풀팔기", "다팔기", "all전체"):
        fish_total = await _sell_all_fish(ctx.author.id, sell_mult)
        item_total, item_lines = await _sell_all_items(ctx.author.id)
        grand = fish_total + item_total
        if grand <= 0:
            await ctx.reply("판매할 물고기·소모품이 없어.", mention_author=False)
            return
        if fish_total > 0:
            await quest_bump(ctx.author.id, "sell_gold", 0, extra=fish_total)
        bal = await add_money(ctx.author.id, grand)
        parts = [f"💰 **일괄 판매 완료**{bonus_txt}"]
        if fish_total > 0:
            parts.append(f"- 🐟 물고기: **{_fmt_money(fish_total)}**")
        if item_total > 0:
            parts.append(f"- 🎒 소모품·재료: **{_fmt_money(item_total)}** ({len(item_lines)}종)")
        parts.append(f"- 합계: **{_fmt_money(grand)}** / 잔액: **{_fmt_money(bal)}**")
        await ctx.reply("\n".join(parts), mention_author=False)
        return

    if tlower == "all":
        total = await _sell_all_fish(ctx.author.id, sell_mult)
        if total <= 0:
            await ctx.reply("인벤토리에 판매 가능한 물고기가 없어.", mention_author=False)
            return

        bal = await add_money(ctx.author.id, total)
        await quest_bump(ctx.author.id, "sell_gold", 0, extra=total)
        await ctx.reply(
            f"🐟 **물고기 전부 판매!**{bonus_txt}\n"
            f"획득: **{_fmt_money(total)}** / 잔액: **{_fmt_money(bal)}**\n"
            f"(소모품은 `!판매 아이템all` · 한꺼번에 `!판매 전체`)",
            mention_author=False,
        )
        return

    fish = FISH_BY_NAME.get(target)
    if not fish:
        for iid, info in ITEMS.items():
            if info.get("name") == target or iid == target:
                price = int(info.get("price", 0))
                if price <= 0:
                    break
                cnt = int(inv.get(iid, 0))
                if cnt <= 0:
                    await ctx.reply("그 아이템은 인벤에 없어.", mention_author=False)
                    return
                value = price * cnt
                await add_fish(ctx.author.id, iid, -cnt)
                bal = await add_money(ctx.author.id, value)
                await ctx.reply(
                    f"**{info['name']} x{cnt}** 판매 완료! 획득: **{_fmt_money(value)}** / 잔액: **{_fmt_money(bal)}**",
                    mention_author=False,
                )
                return
        await ctx.reply("그 물고기/아이템은 몰라. 정확한 이름으로 다시 입력해줘.", mention_author=False)
        return

    key = fish.id
    if target.startswith("이색") or "이색" in target:
        key = f"shiny_{fish.id}"
    cnt = int(inv.get(key, 0))
    if cnt <= 0:
        await ctx.reply("그 물고기는 인벤에 없어.", mention_author=False)
        return

    bm = _bounty_sell_mult_for_key(key, bounty)
    value = int(math.floor(_fish_sell_price(key) * cnt * sell_mult * bm))
    await add_fish(ctx.author.id, key, -cnt)
    bal = await add_money(ctx.author.id, value)
    await quest_bump(ctx.author.id, "sell_gold", 0, extra=value)
    await ctx.reply(
        f"**{_inv_item_display(key)} x{cnt}** 판매 완료!{bonus_txt} 획득: **{_fmt_money(value)}** / 잔액: **{_fmt_money(bal)}**",
        mention_author=False,
    )


async def consume_protection_scroll(user_id: int) -> bool:
    inv = await get_inventory(user_id)
    qty = inv.get("scroll_protect", 0)
    if qty <= 0:
        return False
        
    def mut(d):
        d = dict(d or {})
        uinv = get_user_dict(d, user_id, {})
        uinv["scroll_protect"] = max(0, int(uinv.get("scroll_protect", 0)) - 1)
        if uinv["scroll_protect"] <= 0:
            uinv.pop("scroll_protect", None)
        return d
    await update_json(INV_PATH, _default_inventory(), mut)
    return True


@bot.command(name="강화")
async def upgrade_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    rod_type, level = await get_rod(ctx.author.id)
    
    if level >= ROD_MAX_LEVEL:
        await ctx.reply(
            f"이미 최고 강화 레벨(+{ROD_MAX_LEVEL})에 도달했어!",
            mention_author=False,
        )
        return

    cost = upgrade_cost(level)
    
    # 도감 완성 버프 (영웅 도감 완성 시 강화 성공 확률 +3% 절대값 추가)
    buffs = await get_collection_buffs(ctx.author.id)
    chance_bonus = buffs.get("upgrade_chance_bonus", 0.0)
    tb = await get_title_buffs(ctx.author.id)
    title_up = float(tb.get("upgrade_chance", 0.0))

    rate = upgrade_success_rate(level)
    final_rate = min(1.0, rate + chance_bonus + title_up)
    bonus_parts = []
    if chance_bonus > 0:
        bonus_parts.append("도감 +3%")
    if title_up > 0:
        bonus_parts.append(f"칭호 +{int(title_up * 100)}%")
    bonus_txt = f" ({', '.join(bonus_parts)} 적용)" if bonus_parts else ""

    money = await get_money(ctx.author.id)
    if money < cost:
        await ctx.reply(
            f"강화 비용이 부족해. 필요: **{_fmt_money(cost)}** / 보유: **{_fmt_money(money)}**",
            mention_author=False,
        )
        return

    await add_money(ctx.author.id, -cost)
    
    ok = random.random() < final_rate
    
    if ok:
        new_level = level + 1
        rec = await get_rod_record(ctx.author.id)
        affixes = list(rec.get("affixes", []))
        affix_txt = ""
        if new_level in (5, 10, 15, 20) and len(affixes) < 3:
            affixes.append(roll_affix())
            affix_txt = f"\n✨ **옵션 부여!** {format_affix_line(affixes[-1])}"
        await set_rod(ctx.author.id, rod_type, new_level, affixes)
        await ctx.reply(
            f"🎉 강화 성공!{bonus_txt} **{format_rod_name(rod_type, new_level)}**\n"
            f"- 다음 강화 비용: **{_fmt_money(upgrade_cost(new_level))}**{affix_txt}",
            mention_author=False,
        )
    else:
        # 실패 시 등급 하락 체크 (+10강 이상부터 적용)
        is_downgrade = upgrade_penalty_check(level)
        if is_downgrade:
            # 보호권 소모 시도
            protected = await consume_protection_scroll(ctx.author.id)
            if protected:
                await ctx.reply(
                    f"강화 실패...{bonus_txt} (성공확률 {int(final_rate*100)}%)\n"
                    f"⚠️ **레벨 하락 위기!** 하지만 **📜 강화 보호 주문서**를 소모하여 등급 하락을 방지했습니다!\n"
                    f"현재 낚시대: **{format_rod_name(rod_type, level)}**",
                    mention_author=False,
                )
            else:
                new_level = max(0, level - 1)
                await set_rod(ctx.author.id, rod_type, new_level)
                await ctx.reply(
                    f"강화 실패...{bonus_txt} (성공확률 {int(final_rate*100)}%)\n"
                    f"💥 콰아아앙! 강화 단계가 1단계 하락했습니다...\n"
                    f"현재 낚시대: **{format_rod_name(rod_type, new_level)}**",
                    mention_author=False,
                )
        else:
            await ctx.reply(
                f"강화 실패...{bonus_txt} (성공확률 {int(final_rate*100)}%)\n"
                f"현재 낚시대: **{format_rod_name(rod_type, level)}**",
                mention_author=False,
            )


@bot.command(name="랭킹")
async def ranking_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    money = await read_json(MONEY_PATH, _default_money())
    items = []
    for uid, m in (money or {}).items():
        try:
            items.append((int(uid), int(m)))
        except Exception:
            continue
    items.sort(key=lambda x: x[1], reverse=True)
    top = items[:10]
    if not top:
        await ctx.reply("아직 랭킹 데이터가 없어.", mention_author=False)
        return

    lines = ["**부자 랭킹 TOP 10**"]
    for i, (uid, m) in enumerate(top, start=1):
        name = _display_name(ctx, uid)
        lines.append(f"{i}. **{name}** — {_fmt_money(m)}")
    await ctx.reply("\n".join(lines), mention_author=False)


@bot.command(name="낚시대랭킹")
async def rod_ranking_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return

    rods = await read_json(RODS_PATH, _default_rods())
    items = []
    for uid_str, r in (rods or {}).items():
        if not isinstance(r, dict):
            continue
        try:
            uid = int(uid_str)
        except Exception:
            continue
        rod_type = r.get("type", "rookie")
        if rod_type not in RODS:
            rod_type = "rookie"
        try:
            level = int(r.get("level", 0))
        except Exception:
            level = 0
        level = max(0, level)
        items.append((uid, level, rod_type))

    if not items:
        await ctx.reply("아직 낚시대 랭킹 데이터가 없어. `!강화`부터 ㄱㄱ", mention_author=False)
        return

    # 강화 레벨 desc, 그 다음 낚시대 가격 desc(대충), 마지막 uid
    def rod_price(rt: str) -> int:
        try:
            return int((RODS.get(rt) or RODS["rookie"]).get("price", 0))
        except Exception:
            return 0

    items.sort(key=lambda x: (x[1], rod_price(x[2])), reverse=True)
    top = items[:10]

    lines = ["**🎣 낚시대 랭킹 TOP 10** (강화 기준)"]
    for i, (uid, level, rod_type) in enumerate(top, start=1):
        name = _display_name(ctx, uid)
        lines.append(f"{i}. **{name}** — **{format_rod_name(rod_type, level)}**")

    await ctx.reply("\n".join(lines), mention_author=False)


async def _slot_calc(user_id: int, bet: int, guild_id: int | None) -> tuple[int, str]:
    """반환: (지급액 win, 메시지). 베팅 차감은 호출자가 처리."""
    a, b, c, payout_mult, jackpot_hit, label = spin_slot()
    fee = await _casino_fee(user_id, SLOT_WIN_FEE) if payout_mult > 0 else 0.0
    win = int(bet * payout_mult * (1.0 - fee)) if payout_mult > 0 else 0

    jackpot_take = 0
    if jackpot_hit:
        jackpot_take = await _jackpot_take_all()
        win += jackpot_take
        if jackpot_take > 0:
            await _jackpot_record_hit(guild_id, user_id, jackpot_take)

    net = win - bet
    if payout_mult <= 0:
        body = f"🎰 [{a} | {b} | {c}] 꽝!"
    else:
        extra = f"\n💥 **잭팟 +{_fmt_money(jackpot_take)}**" if jackpot_take else ""
        body = f"🎰 [{a} | {b} | {c}] **{label}** (x{payout_mult:g}) → **{_fmt_money(net)}**{extra}"
    return win, body


@bot.command(name="슬롯")
async def slot_cmd(ctx: commands.Context, bet_raw: str | None = None):
    bet = _parse_bet(bet_raw)
    if bet is None:
        await ctx.reply("사용법: `!슬롯 <베팅>` (예: `!슬롯 1000`)", mention_author=False)
        return

    ok, err = await _casino_guard(ctx, bet)
    if not ok:
        if err:
            await ctx.reply(err, mention_author=False)
        return

    await add_money(ctx.author.id, -bet)
    pot_after_add = await _jackpot_add(_slot_jackpot_contribution(bet))

    win, body = await _slot_calc(ctx.author.id, bet, ctx.guild.id if ctx.guild else None)
    await add_money(ctx.author.id, win)
    net = win - bet
    await _casino_bump(ctx.author.id, bet, net, "슬롯")
    bal = await get_money(ctx.author.id)
    festa = " 🎉**잭팟페스타**(적립2배)" if is_jackpot_festa() else ""
    await ctx.reply(
        f"{body}\n잭팟: **{_fmt_money(pot_after_add)}**{festa} / 잔액: **{_fmt_money(bal)}**",
        mention_author=False,
    )


@bot.command(name="슬롯10")
async def slot10_cmd(ctx: commands.Context, bet_raw: str | None = None):
    bet = _parse_bet(bet_raw)
    if bet is None:
        await ctx.reply("사용법: `!슬롯10 <베팅>` (예: `!슬롯10 1000`)", mention_author=False)
        return

    ok, err = await _casino_guard(ctx, bet)
    if not ok:
        if err:
            await ctx.reply(err, mention_author=False)
        return

    spins = 10
    needed = bet * spins
    money = await get_money(ctx.author.id)
    if money < needed:
        await ctx.reply(
            f"10연속은 선결제가 필요해.\n필요: **{_fmt_money(needed)}** / 보유: **{_fmt_money(money)}**",
            mention_author=False,
        )
        return

    await add_money(ctx.author.id, -needed)
    pot_after_add = await _jackpot_add(_slot_jackpot_contribution(needed))

    total_net = 0
    hits = 0
    jackpots = 0
    best_body = ""
    best_net = -bet

    total_win = 0
    for _ in range(spins):
        win, body = await _slot_calc(
            ctx.author.id, bet, ctx.guild.id if ctx.guild else None
        )
        total_win += win
        spin_net = win - bet
        total_net += spin_net  # 회차별 순이익 합 = 총 획득 - 총 베팅(선결제는 별도)
        if spin_net > 0:
            hits += 1
        if "잭팟" in body:
            jackpots += 1
        if spin_net > best_net:
            best_net = spin_net
            best_body = body

    await add_money(ctx.author.id, total_win)
    await _casino_bump(ctx.author.id, needed, total_net, "슬롯10")
    bal = await get_money(ctx.author.id)

    net_sign = "+" if total_net >= 0 else ""
    extra = f"\n💥 잭팟 {jackpots}회!" if jackpots else ""
    await ctx.reply(
        f"🎰 **슬롯 10연속 결과**\n"
        f"- 적중: **{hits}/10**\n"
        f"- 베스트: {best_body or '(없음)'}\n"
        f"- 총 베팅: **{_fmt_money(needed)}** / 총 획득: **{_fmt_money(total_win)}**\n"
        f"- 순수익: **{net_sign}{_fmt_money(total_net)}** (잔액 변동과 동일)\n"
        f"- 잭팟 적립: **{_fmt_money(pot_after_add)}** / 잔액: **{_fmt_money(bal)}**{extra}",
        mention_author=False,
    )


def _default_daily() -> Dict[str, dict]:
    return {}


def _yesterday_key() -> str:
    import datetime

    y = datetime.datetime.utcnow() - datetime.timedelta(days=1)
    return y.strftime("%Y-%m-%d")


@bot.command(name="일일")
async def daily_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    today = _today_key_utc()
    uid = str(ctx.author.id)
    d = await read_json(DAILY_PATH, _default_daily())
    entry = _parse_daily_entry(d.get(uid))
    if entry.get("last") == today:
        await ctx.reply(
            f"오늘은 이미 출석했어! 🔥 연속 **{entry.get('streak', 1)}일**\n"
            f"내일도 오면 연속 보상이 커져.",
            mention_author=False,
        )
        return

    streak = 1
    if entry.get("last") == _yesterday_key():
        streak = int(entry.get("streak", 0)) + 1
    else:
        streak = 1

    def mut(x):
        x = dict(x or {})
        x[uid] = {"last": today, "streak": streak}
        return x

    await update_json(DAILY_PATH, _default_daily(), mut)
    reward = random.randint(8000, 45000)
    streak_bonus = streak_extra_reward(streak) + random.randint(0, 8000)
    total = reward + streak_bonus
    bal = await add_money(ctx.author.id, total)
    milestone = ""
    if streak in (3, 7, 14, 30):
        milestone = f"\n🎁 **{streak}일 연속 달성 보너스** 포함!"
    await ctx.reply(
        f"📅 **일일 출석 완료!** 🔥 **{streak}일 연속**\n"
        f"- 기본: **{_fmt_money(reward)}** + 연속보너스: **{_fmt_money(streak_bonus)}**\n"
        f"- 합계: **{_fmt_money(total)}** / 잔액: **{_fmt_money(bal)}**{milestone}",
        mention_author=False,
    )


def _default_treasure() -> Dict[str, int]:
    return {}


@bot.command(name="상자")
async def chest_list_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    inv = await get_inventory(ctx.author.id)
    lines = ["**📦 보유 보물상자**"]
    found = False
    for cid in CHESTS:
        cnt = int(inv.get(cid, 0))
        if cnt > 0:
            found = True
            lines.append(f"- `{cid}`: **{CHESTS[cid]['name']}** x{cnt}")
    if not found:
        lines.append("보유 상자 없음. `!낚시`로 낚아보자!")
    lines.append("\n개봉: `!상자깨기 <ID>` / `!상자깨기 all`")
    await ctx.reply("\n".join(lines), mention_author=False)


@bot.command(name="상자정보")
async def chest_info_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    lines = ["**📦 보물상자 종류** (낚시 시 **약 16%** 확률로 획득)\n"]
    for cid, c in CHESTS.items():
        rare = max(e.get("chance", 0) for e in c["rewards"])
        lines.append(f"- `{cid}`: **{c['name']}** — 최고 보상 확률 ~{int(rare*100)}%")
    await ctx.reply("\n".join(lines), mention_author=False)


@bot.command(name="상자깨기")
async def chest_open_cmd(ctx: commands.Context, *, target: str | None = None):
    if not _channel_allowed(ctx):
        return
    if not target:
        await ctx.reply("사용법: `!상자깨기 <상자ID|all>` (예: `!상자깨기 chest_gold`)", mention_author=False)
        return

    inv = await get_inventory(ctx.author.id)
    target = target.strip().lower()

    if target == "all":
        opened = 0
        all_lines = []
        for cid in list(CHESTS.keys()):
            cnt = int(inv.get(cid, 0))
            for _ in range(cnt):
                rewards = open_chest(cid)
                txt = await apply_chest_rewards(ctx.author.id, rewards)
                all_lines.append(f"**{CHESTS[cid]['name']}** → {txt}")
                opened += 1
            if cnt > 0:
                await add_fish(ctx.author.id, cid, -cnt)
        if opened == 0:
            await ctx.reply("깰 상자가 없어.", mention_author=False)
            return
        preview = all_lines[:8]
        extra = f"\n... 외 {opened - 8}개" if opened > 8 else ""
        bal = await get_money(ctx.author.id)
        await ctx.reply(
            f"📦 **{opened}개 상자 개봉 완료!**\n" + "\n".join(preview) + extra + f"\n잔액: **{_fmt_money(bal)}**",
            mention_author=False,
        )
        return

    if target not in CHESTS:
        await ctx.reply(f"없는 상자 ID. `!상자`로 확인해줘.", mention_author=False)
        return

    cnt = int(inv.get(target, 0))
    if cnt <= 0:
        await ctx.reply("그 상자는 인벤에 없어.", mention_author=False)
        return

    await add_fish(ctx.author.id, target, -1)
    rewards = open_chest(target)
    txt = await apply_chest_rewards(ctx.author.id, rewards)
    bal = await get_money(ctx.author.id)
    await ctx.reply(
        f"📦 **{CHESTS[target]['name']}** 개봉!\n{txt}\n잔액: **{_fmt_money(bal)}**",
        mention_author=False,
    )


@bot.command(name="주화")
async def lucky_coin_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    inv = await get_inventory(ctx.author.id)
    if int(inv.get("lucky_coin", 0)) <= 0:
        await ctx.reply("행운의 주화가 없어. 상자에서 얻을 수 있어!", mention_author=False)
        return
    await add_fish(ctx.author.id, "lucky_coin", -1)
    await _set_lucky_buff(ctx.author.id, True)
    await ctx.reply(
        "🪙 **행운의 주화** 사용!\n다음 `!슬롯`·`!로켓`·`!심연`·`!보물탐사`·`!복도` 1회 **수수료 50% 추가 감소**",
        mention_author=False,
    )


async def _abyss_pot_read() -> int:
    j = await read_json(ABYSS_JACKPOT_PATH, default_abyss_pot())
    return int((j or {}).get("pot", 0))


async def _abyss_pot_add(delta: int) -> int:
    def mut(d):
        d = dict(d or {})
        d["pot"] = max(0, int(d.get("pot", 0)) + int(delta))
        return d

    j = await update_json(ABYSS_JACKPOT_PATH, default_abyss_pot(), mut)
    return int(j.get("pot", 0))


async def _abyss_pot_take_all() -> int:
    def mut(d):
        d = dict(d or {})
        pot = int(d.get("pot", 0))
        d["pot"] = 0
        d["_taken"] = pot
        return d

    j = await update_json(ABYSS_JACKPOT_PATH, default_abyss_pot(), mut)
    return int(j.get("_taken", 0))


async def _abyss_announce_big_win(ctx: commands.Context, payout: int, tier: str) -> None:
    ch_id = _env_int("ANNOUNCE_CHANNEL_ID")
    if not ch_id or payout < 500_000:
        return
    ch = bot.get_channel(ch_id)
    if not ch:
        return
    try:
        await ch.send(
            f"☄️☄️ **[전서버 속보]** {ctx.author.mention} 님이 **운명의 심연**에서\n"
            f"**{tier}** → **{_fmt_money(payout)}** 획득!!!"
        )
    except Exception:
        pass


@bot.command(name="심연확률")
async def abyss_odds_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    pot = await _abyss_pot_read()
    await ctx.reply(
        f"{odds_table_text()}\n\n🎰 현재 **심연 잭팟 풀**: **{_fmt_money(pot)}**",
        mention_author=False,
    )


@bot.command(name="심연잭팟")
async def abyss_pot_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    pot = await _abyss_pot_read()
    await ctx.reply(
        f"🕳️ **심연 잭팟 풀**: **{_fmt_money(pot)}**\n"
        f"- 베팅의 **{int(ABYSS_POT_RATE*100)}%** 적립\n"
        f"- **{ABYSS_POT_JACKPOT_CHANCE*100:.3f}%**** 확률로 풀 **전액** + 배당 동시 획득\n"
        f"- `!심연 <베팅>` 으로 도전 (최소 {_fmt_money(ABYSS_MIN_BET)})",
        mention_author=False,
    )


@bot.command(name="심연", aliases=["미친도박", "대박복권", "운명의심연"])
async def abyss_cmd(ctx: commands.Context, bet_raw: str | None = None):
    if not _channel_allowed(ctx):
        return
    bet = _parse_bet(bet_raw)
    if bet is None:
        await ctx.reply(
            "☄️ **운명의 심연** — 극악의 확률, 광기의 배당\n"
            "사용법: `!심연 <베팅>` (예: `!심연 50000`)\n"
            f"- 최소 **{_fmt_money(ABYSS_MIN_BET)}** / 상한 **{_fmt_money(ABYSS_MAX_BET)}**\n"
            "- `!심연확률` 확률표 · `!심연잭팟` 잭팟 풀",
            mention_author=False,
        )
        return
    if bet < ABYSS_MIN_BET:
        await ctx.reply(
            f"심연은 최소 **{_fmt_money(ABYSS_MIN_BET)}** 이상만 받아.\n"
            f"(일반 카지노보다 하이리스크!)",
            mention_author=False,
        )
        return

    ok, err = await _casino_guard(ctx, bet)
    if not ok:
        if err:
            await ctx.reply(err, mention_author=False)
        return

    await add_money(ctx.author.id, -bet)
    pot_after = await _abyss_pot_add(int(bet * ABYSS_POT_RATE))

    roll = roll_abyss(bet)
    pot_take = 0
    if roll["pot_hit"]:
        pot_take = await _abyss_pot_take_all()

    gross = calc_payout(bet, roll["mult"], pot_take, roll["pot_hit"])
    fee = await _casino_fee(ctx.author.id, 0.01) if gross > 0 else 0.0
    payout = int(gross * (1.0 - fee)) if gross > 0 else 0
    if payout > 0:
        await add_money(ctx.author.id, payout)

    net = payout - bet
    await _casino_bump(ctx.author.id, bet, net, "심연")
    bal = await get_money(ctx.author.id)

    tier = roll["tier"]
    mult = roll["mult"]
    lines = [
        "━━━━━━━━━━━━━━━━━━",
        "☄️ **운명의 심연** 에 빠져든다...",
        "🌀🌀🌀 ... ... ...",
        f"✨ 결과: **{tier}**",
        "━━━━━━━━━━━━━━━━━━",
    ]
    if mult <= 0:
        lines.append(f"💀 **전멸** — 베팅 **{_fmt_money(bet)}** 소멸")
    elif net < 0:
        lines.append(
            f"📉 배율 **x{mult:g}** — 회수 **{_fmt_money(payout)}** "
            f"(순손실 **{_fmt_money(-net)}**)"
        )
    else:
        lines.append(
            f"🎉 배율 **x{mult:g}** — 획득 **{_fmt_money(payout)}** "
            f"(순수익 **+{_fmt_money(net)}**)"
        )
    if roll["pot_hit"] and pot_take > 0:
        lines.append(f"🎰 **심연 잭팟 풀 전액** +{_fmt_money(pot_take)} 포함!!!")
    lines.append(f"\n🕳️ 심연 잭팟 적립: **{_fmt_money(pot_after)}** / 잔액: **{_fmt_money(bal)}**")

    await ctx.reply("\n".join(lines), mention_author=False)

    if mult >= 50 or roll["pot_hit"]:
        await _abyss_announce_big_win(ctx, payout, tier)


@bot.command(name="보물상자")
async def treasure_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    now = utc_ts()
    cd = 30 * 60
    t = await read_json(TREASURE_PATH, _default_treasure())
    last = int(t.get(str(ctx.author.id), 0))
    wait = (last + cd) - now
    if wait > 0:
        await ctx.reply(f"보물상자 쿨타임! **{wait // 60}분 {wait % 60}초** 후", mention_author=False)
        return

    def mut(x):
        x = dict(x or {})
        x[str(ctx.author.id)] = now
        return x

    await update_json(TREASURE_PATH, _default_treasure(), mut)

    roll = random.random()
    if roll < 0.05:
        amt = random.randint(80000, 200000)
        txt = "💎 **대박 보물상자!**"
    elif roll < 0.25:
        amt = random.randint(20000, 60000)
        txt = "✨ **희귀 보물!**"
    elif roll < 0.55:
        amt = random.randint(5000, 20000)
        txt = "📦 **일반 보물**"
    else:
        item_roll = random.choice(list(ITEMS.keys()))
        qty = random.randint(1, 3)
        await add_fish(ctx.author.id, item_roll, qty)
        await ctx.reply(
            f"{txt}\n**{ITEMS[item_roll]['name']}** x{qty} 획득!",
            mention_author=False,
        )
        return

    bal = await add_money(ctx.author.id, amt)
    await ctx.reply(f"{txt}\n**{_fmt_money(amt)}** 획득! / 잔액: **{_fmt_money(bal)}**", mention_author=False)


async def get_max_server_rod_level() -> int:
    rods = await read_json(RODS_PATH, _default_rods())
    max_lvl = 0
    for r in rods.values():
        if isinstance(r, dict):
            try:
                max_lvl = max(max_lvl, int(r.get("level", 0)))
            except Exception:
                pass
    return max_lvl


def get_today_weekday_korean_and_index() -> tuple[str, int]:
    import datetime
    weekday_idx = datetime.datetime.now().weekday()
    weekday_korean = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"][weekday_idx]
    return weekday_korean, weekday_idx


async def _get_boss_state() -> dict:
    return await read_json(BOSS_PATH, _default_boss())


async def _set_boss_state(state: dict) -> None:
    await write_json(BOSS_PATH, state)


def _boss_alive(state: dict, now: int) -> bool:
    return bool(state.get("active")) and int(state.get("hp", 0)) > 0 and int(state.get("ends_at", 0)) > now


@bot.command(name="보스")
async def boss_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    now = utc_ts()
    state = await _get_boss_state()

    if _boss_alive(state, now):
        hp = int(state["hp"])
        mx = int(state["max_hp"])
        await ctx.reply(
            f"⚔️ **보스 레이드 진행 중!**\n"
            f"- 보스: **{state.get('name','보스')}**\n"
            f"- HP: **{hp:,}/{mx:,}**\n"
            f"- 제한시간: <t:{int(state['ends_at'])}:R>\n"
            f"공격: `!보스공격`",
            mention_author=False,
        )
        return

    today = _today_key_utc()
    if state.get("last_spawn_day") == today:
        await ctx.reply("보스는 **하루 1회** 소환 가능해. 내일 다시 와!", mention_author=False)
        return

    # 가변 보스 체력 설정: 서버 내 최고 강화 레벨 비례
    max_rod = await get_max_server_rod_level()
    base_hp = 100_000 + 30_000 * max_rod
    
    # 요일 보스 로테이션 적용
    weekday_korean, weekday_idx = get_today_weekday_korean_and_index()
    boss_info = BOSS_ROTATION[weekday_idx]
    
    max_hp = int(base_hp * boss_info["hp_mult"])
    duration = 60 * 60
    
    new_state = boss_spawn(max_hp=max_hp, now_ts=now, duration_seconds=duration, name=boss_info["name"])
    new_state["last_spawn_day"] = today
    new_state["weekday_idx"] = weekday_idx
    await _set_boss_state(new_state)

    await ctx.reply(
        f"💥 **요일 보스 소환 완료! ({weekday_korean})**\n"
        f"- 이름: **{boss_info['name']}**\n"
        f"- HP: **{max_hp:,}** (서버 최고 강화도 +{max_rod} 적용)\n"
        f"- 특징: *{boss_info['desc']}*\n"
        f"- 제한시간: 1시간\n"
        f"참여: `!보스공격`",
        mention_author=False,
    )


async def _boss_payout(ctx: commands.Context, state: dict) -> None:
    contributors: Dict[str, int] = dict(state.get("contributors") or {})
    if not contributors:
        await ctx.send("보스가 쓰러졌지만, 참여자가 없어 보상이 지급되지 않았어.")
        return

    total_damage = sum(int(v) for v in contributors.values() if int(v) > 0)
    if total_damage <= 0:
        await ctx.send("보스가 쓰러졌지만, 유효 피해가 없어 보상이 지급되지 않았어.")
        return

    # 요일 보스별 보상 조회
    import datetime
    weekday_idx = state.get("weekday_idx", datetime.datetime.now().weekday())
    boss_info = BOSS_ROTATION.get(weekday_idx, BOSS_ROTATION[0])
    
    base_reward = boss_info["base_reward"]
    last_hit_bonus = int(base_reward * 0.125) # 12.5% 막타 보너스
    top_bonus = int(base_reward * 0.165)      # 16.5% 1등 보너스

    last_hit = state.get("last_hit")
    top_uid = max(contributors.items(), key=lambda kv: int(kv[1]))[0]

    drop_item = boss_info["drop_item"]
    drop_rate = boss_info["drop_rate"]
    drop_info = ITEMS[drop_item]

    reward_lines = [f"**🏆 요일 보스 [{boss_info['name']}] 토벌 성공!**\n"]
    
    for uid_str, dmg in contributors.items():
        uid = int(uid_str)
        dmg = int(dmg)
        if dmg <= 0:
            continue
            
        share = int(base_reward * (dmg / total_damage))
        bonus = 0
        bonus_txts = []
        
        # 1등 및 막타 확인
        if uid_str == str(last_hit):
            bonus += last_hit_bonus
            bonus_txts.append("막타 🎯")
        if uid_str == str(top_uid):
            bonus += top_bonus
            bonus_txts.append("딜1등 👑")
            
        total = share + bonus
        await add_money(uid, total)
        
        # 전리품 아이템 드롭 연산
        items_dropped = 0
        if uid_str == str(top_uid):
            # 딜 1등은 확정 지급 (일요일 포세이돈은 2개)
            items_dropped = 2 if weekday_idx == 6 and drop_item == "scroll_protect" else 1
        elif uid_str == str(last_hit):
            # 막타는 원래 확률
            if random.random() < drop_rate:
                items_dropped = 1
        else:
            # 일반 기여자는 드롭 확률의 절반 적용
            if random.random() < (drop_rate * 0.5):
                items_dropped = 1
                
        drop_msg = ""
        if items_dropped > 0:
            await add_fish(uid, drop_item, items_dropped)
            drop_msg = f" (+{drop_info['name']} x{items_dropped})"

        tag = f" [{', '.join(bonus_txts)}]" if bonus_txts else ""
        name = _display_name(ctx, uid)
        spine_txt = ""
        if uid_str == str(top_uid) and await _maybe_drop_spine(uid, 0.025):
            spine_txt = " 🦴**관수의 척추!**"
        reward_lines.append(f"- **{name}**: 딜 {dmg:,} ({int(dmg/total_damage*100)}%) ➡️ **{_fmt_money(total)}**{tag}{drop_msg}{spine_txt}")

    reward_lines.append(f"\n- 총 딜량: **{total_damage:,}**")
    reward_lines.append(f"- 토벌 기본금: **{_fmt_money(base_reward)}** (딜량 비례 배분)")
    reward_lines.append(f"- 딜 1등 보너스: **{_fmt_money(top_bonus)}**")
    reward_lines.append(f"- 막타 보너스: **{_fmt_money(last_hit_bonus)}**")
    await ctx.send("\n".join(reward_lines))


async def _get_worldboss_state() -> dict:
    return await read_json(WORLDBOSS_PATH, default_world_boss_state())


def _worldboss_alive(state: dict, now: int) -> bool:
    return bool(state.get("active")) and int(state.get("hp", 0)) > 0 and int(state.get("ends_at", 0)) > now


async def _worldboss_payout(ctx: commands.Context, state: dict) -> None:
    info = WORLD_BOSS_INFO
    contributors: Dict[str, int] = dict(state.get("contributors") or {})
    if not contributors:
        await ctx.send("크라켄이 쓰러졌지만 참여자가 없어 보상이 없어.")
        return
    total_damage = sum(int(v) for v in contributors.values() if int(v) > 0)
    if total_damage <= 0:
        return
    base_reward = int(info["base_reward"])
    last_hit_bonus = int(base_reward * 0.15)
    top_bonus = int(base_reward * 0.20)
    last_hit = state.get("last_hit")
    top_uid = max(contributors.items(), key=lambda kv: int(kv[1]))[0]
    drop_item = info["drop_item"]
    lines = [f"**🐙 {info['name']} 토벌!** (서버 협동 레이드)\n"]
    for uid_str, dmg in contributors.items():
        dmg = int(dmg)
        if dmg <= 0:
            continue
        share = int(base_reward * (dmg / total_damage))
        bonus = 0
        tags = []
        if uid_str == str(last_hit):
            bonus += last_hit_bonus
            tags.append("막타 🎯")
        if uid_str == str(top_uid):
            bonus += top_bonus
            tags.append("딜1등 👑")
        uid = int(uid_str)
        await add_money(uid, share + bonus)
        frags = random.randint(int(info["fragment_min"]), int(info["fragment_max"]))
        if uid_str == str(top_uid) or random.random() < float(info["drop_rate"]):
            await add_fish(uid, FRAGMENT_ITEM_ID, frags)
        if uid_str == str(top_uid) or uid_str == str(last_hit):
            await add_fish(uid, drop_item, 1)
        name = _display_name(ctx, uid)
        tag = f" [{', '.join(tags)}]" if tags else ""
        spine_txt = ""
        if uid_str == str(top_uid) and await _maybe_drop_spine(uid, 0.04):
            spine_txt = " 🦴**관수의 척추!**"
        lines.append(f"- **{name}**: 딜 {dmg:,} → **{_fmt_money(share + bonus)}** +파편{frags}{tag}{spine_txt}")
    await ctx.send("\n".join(lines))
    ch_id = _env_int("ANNOUNCE_CHANNEL_ID")
    if ch_id:
        ch = bot.get_channel(ch_id)
        if ch:
            try:
                await ch.send(f"🐙 **크라켄 토벌 완료!** 서버 영웅들에게 감사합니다!")
            except Exception:
                pass


@bot.command(name="월드보스", aliases=["크라켄"])
async def worldboss_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    now = utc_ts()
    state = await _get_worldboss_state()
    if _worldboss_alive(state, now):
        hp, mx = int(state["hp"]), int(state["max_hp"])
        await ctx.reply(
            f"🐙 **월드 레이드 진행 중!**\n"
            f"- {state.get('name', WORLD_BOSS_INFO['name'])}\n"
            f"- HP: **{hp:,}/{mx:,}** (서버 공유)\n"
            f"- 종료: <t:{int(state['ends_at'])}:R>\n"
            f"공격: `!보스공격`",
            mention_author=False,
        )
        return
    import datetime
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    last = state.get("last_spawn_day", "")
    if last:
        try:
            d0 = datetime.datetime.strptime(last, "%Y-%m-%d")
            d1 = datetime.datetime.strptime(today, "%Y-%m-%d")
            if (d1 - d0).days < int(WORLD_BOSS_INFO["cooldown_days"]):
                await ctx.reply(
                    f"월드보스는 **{WORLD_BOSS_INFO['cooldown_days']}일**에 한 번 소환 가능해.",
                    mention_author=False,
                )
                return
        except Exception:
            pass
    max_rod = await get_max_server_rod_level()
    max_hp = int((200_000 + 50_000 * max_rod) * float(WORLD_BOSS_INFO["hp_mult"]))
    new_state = world_boss_spawn(max_hp, now)
    new_state["last_spawn_day"] = today
    await write_json(WORLDBOSS_PATH, new_state)
    ch_id = _env_int("ANNOUNCE_CHANNEL_ID")
    if ch_id:
        ch = bot.get_channel(ch_id)
        if ch:
            try:
                await ch.send(
                    f"🐙🐙 **[전서버 속보]** **{WORLD_BOSS_INFO['name']}** 출현!!!\n"
                    f"HP **{max_hp:,}** · 모두 `!보스공격`으로 참여하세요!"
                )
            except Exception:
                pass
    await ctx.reply(
        f"🐙 **월드보스 소환!** {WORLD_BOSS_INFO['name']}\n"
        f"- HP: **{max_hp:,}** (3시간 · 서버 전체 공유)\n"
        f"- 보상: 파편·전설미끼·딜/막타 보너스\n"
        f"`!보스공격`으로 참여!",
        mention_author=False,
    )


@bot.command(name="보스공격")
async def boss_attack_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    now = utc_ts()
    wb = await _get_worldboss_state()
    world_mode = _worldboss_alive(wb, now)
    if world_mode:
        state = wb
        boss_path = WORLDBOSS_PATH
        boss_default = default_world_boss_state
    else:
        state = await _get_boss_state()
        if not _boss_alive(state, now):
            await ctx.reply(
                "지금은 활성 보스가 없어. `!보스` (요일보스) · `!월드보스` (크라켄)",
                mention_author=False,
            )
            return
        boss_path = BOSS_PATH
        boss_default = _default_boss

    rod_type, rod_level = await get_rod(ctx.author.id)
    tb = await get_title_buffs(ctx.author.id)
    dmg, is_crit, crit_mult = _boss_damage(rod_type, rod_level, tb)
    rec = await get_rod_record(ctx.author.id)
    affix_boss = affix_boss_bonus(rec.get("affixes", []))
    if affix_boss > 0:
        dmg = int(dmg * (1.0 + affix_boss))

    def pm(p):
        p["boss_hits"] = int(p.get("boss_hits", 0)) + 1

    await profile_update(ctx.author.id, pm)
    await quest_bump(ctx.author.id, "boss_hit", 1)

    # 도감 완성 버프 (전설 도감 완성 시 보스 레이드 데미지 +15% 버프)
    buffs = await get_collection_buffs(ctx.author.id)
    bonus_damage_multiplier = 1.0 + buffs.get("boss_damage_bonus", 0.0)
    if buffs.get("boss_damage_bonus", 0.0) > 0:
        dmg = int(dmg * bonus_damage_multiplier)
        
    crit_txt = ""
    if is_crit:
        crit_txt = f" 💥크리티컬! (x{crit_mult:g})"
    if buffs.get("boss_damage_bonus", 0.0) > 0:
        crit_txt += " 👑(전설 도감 +15% 적용)"

    def mut(s):
        s = dict(s or {})
        hp = int(s.get("hp", 0))
        hp = max(0, hp - dmg)
        s["hp"] = hp
        s["contributors"] = dict(s.get("contributors") or {})
        uid = str(ctx.author.id)
        s["contributors"][uid] = int(s["contributors"].get(uid, 0)) + dmg
        s["last_hit"] = ctx.author.id
        if hp <= 0:
            s["active"] = False
            s["ends_at"] = now
        return s

    state = await update_json(boss_path, boss_default(), mut)
    hp = int(state.get("hp", 0))
    mx = int(state.get("max_hp", 0))
    boss_label = "🐙 크라켄" if world_mode else state.get("name", "보스")

    if hp > 0:
        await ctx.reply(
            f"**{ctx.author.display_name}** → **{boss_label}** 피해 **{dmg:,}**{crit_txt}\n"
            f"- HP: **{hp:,}/{mx:,}**",
            mention_author=False,
        )
        return

    await ctx.send(f"**{ctx.author.display_name}**의 막타! **{boss_label}** 격파! (피해 {dmg:,}){crit_txt}")
    if world_mode:
        await _worldboss_payout(ctx, state)
    else:
        await _boss_payout(ctx, state)


@bot.command(name="프로필")
async def profile_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    p = await get_profile(ctx.author.id)
    rod_type, rod_lv = await get_rod(ctx.author.id)
    tid = p.get("title", "title_rookie")
    title = TITLES.get(tid, TITLES["title_rookie"])["name"]
    t_eff = format_title_stats(title_stats(tid))
    ach_cnt = len(p.get("achievements", []))
    streak = int(p.get("fish_streak_today", 0)) if p.get("streak_day") == today_key() else 0
    await ctx.reply(
        f"**👤 {ctx.author.display_name}** 프로필\n"
        f"- 칭호: **{title}** — 효과: {t_eff}\n"
        f"- 오늘 연속 낚시: **{streak}회** (`!이벤트`)\n"
        f"- 낚시대: **{format_rod_name(rod_type, rod_lv)}**\n"
        f"- 총 낚시: **{p.get('fish_total', 0)}** / 상자: **{p.get('chest_total', 0)}**\n"
        f"- 이색: **{p.get('shiny_total', 0)}** / 전설: **{p.get('legendary_total', 0)}** / 신화: **{p.get('mythic_total', 0)}**\n"
        f"- 업적: **{ach_cnt}/{len(ACHIEVEMENTS)}** / 대결승: **{p.get('duel_wins', 0)}**\n"
        f"- 보유금: **{_fmt_money(await get_money(ctx.author.id))}**",
        mention_author=False,
    )


@bot.command(name="퀘스트")
async def quest_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    p = await get_profile(ctx.author.id)
    day = today_key()
    if p.get("quest_day") != day or not p.get("daily_quest"):
        p["quest_day"] = day
        p["daily_quest"] = pick_daily_quest()
        p["daily_progress"] = 0
        p["daily_done"] = False
        await save_profile(ctx.author.id, p)

    dq = p.get("daily_quest", {})
    wq = p.get("weekly_quest", WEEKLY_QUEST)
    lines = [
        f"**📋 {ctx.author.display_name}** 퀘스트",
        f"\n**일일** — {dq.get('name', '?')} ({p.get('daily_progress', 0)}/{dq.get('target', 0)})",
        f"보상: **{_fmt_money(dq.get('reward', 0))}** {'✅완료' if p.get('daily_done') else ''}",
        f"\n**주간** — {wq.get('name')} ({p.get('weekly_progress', 0)}/{wq.get('target', 0)})",
        f"보상: **{_fmt_money(wq.get('reward', 0))}** {'✅완료' if p.get('weekly_done') else ''}",
    ]
    await ctx.reply("\n".join(lines), mention_author=False)

    if not p.get("daily_done") and int(p.get("daily_progress", 0)) >= int(dq.get("target", 0)):
        bal = await add_money(ctx.author.id, int(dq.get("reward", 0)))
        p["daily_done"] = True
        await save_profile(ctx.author.id, p)
        await ctx.send(f"🎉 일일 퀘스트 완료! **{_fmt_money(dq.get('reward', 0))}** / 잔액 **{_fmt_money(bal)}**")

    if not p.get("weekly_done") and int(p.get("weekly_progress", 0)) >= int(wq.get("target", 0)):
        bal = await add_money(ctx.author.id, int(wq.get("reward", 0)))
        p["weekly_done"] = True
        await save_profile(ctx.author.id, p)
        await ctx.send(f"🎉 주간 퀘스트 완료! **{_fmt_money(wq.get('reward', 0))}** / 잔액 **{_fmt_money(bal)}**")


@bot.command(name="업적")
async def achievements_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    rod_rt, rod_lv = await get_rod(ctx.author.id)
    money = await get_money(ctx.author.id)
    newly = await check_achievements(ctx.author.id, rod_lv, money)
    p = await get_profile(ctx.author.id)
    done = set(p.get("achievements", []))
    lines = [
        f"**🏆 업적** ({len(done)}/{len(ACHIEVEMENTS)})",
        "달성 시 보상 + 칭호 자동 해금. 획득·장착 방법은 `!칭호` 참고",
    ]
    if newly:
        names = ", ".join(f"**{ACHIEVEMENTS[a]['name']}**" for a in newly[:5])
        lines.append(f"🎉 **방금 달성:** {names}")
    for aid, a in ACHIEVEMENTS.items():
        if aid in done:
            lines.append(f"✅ **{a['name']}** — {a['desc']} · 보상 {_fmt_money(a['reward'])}")
        else:
            cur = achievement_current_value(p, aid, rod_lv, money)
            tgt = int(a["target"])
            lines.append(
                f"⬜ **{a['name']}** — {a['desc']} · 진행 **{cur}/{tgt}** · 보상 {_fmt_money(a['reward'])}"
            )
    await _reply_long(ctx, lines[1:], header=lines[0])


@bot.command(name="칭호")
async def title_cmd(ctx: commands.Context, title_id: str | None = None):
    if not _channel_allowed(ctx):
        return
    p = await get_profile(ctx.author.id)
    unlocked_set = set(unlocked_titles(p))
    if not title_id:
        cur_tid = p.get("title", "title_rookie")
        guide = format_title_acquisition_guide()
        lines = guide + [
            "",
            f"**현재 장착:** `{cur_tid}` — **{TITLES.get(cur_tid, {}).get('name', '?')}**",
            "**내 칭호 상태**",
        ]
        for tid, t in TITLES.items():
            if tid in unlocked_set:
                mark = "✅"
                cur = " **← 장착**" if tid == cur_tid else ""
            else:
                mark = "🔒"
                cur = ""
            eff = format_title_stats(t.get("stats") or {})
            lines.append(f"{mark} `{tid}` **{t['name']}**{cur}")
            lines.append(f"   └ {title_unlock_hint(tid)}")
            lines.append(f"   └ **효과:** {eff}")
        await _reply_long(ctx, lines, header="**🎖️ 칭호**")
        return
    title_id = title_id.strip().lower()
    if title_id not in TITLES:
        await ctx.reply(f"없는 칭호 ID야. `!칭호`로 목록을 확인해줘.", mention_author=False)
        return
    if title_id not in unlocked_set:
        await ctx.reply(
            f"아직 해금되지 않았어.\n└ {title_unlock_hint(title_id)}",
            mention_author=False,
        )
        return
    p["title"] = title_id
    await save_profile(ctx.author.id, p)
    eff = format_title_stats(TITLES[title_id].get("stats") or {})
    await ctx.reply(
        f"칭호 장착: **{TITLES[title_id]['name']}** (`{title_id}`)\n"
        f"**적용 효과:** {eff}",
        mention_author=False,
    )


@bot.command(name="이벤트", aliases=["서버이벤트"])
async def events_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    st = await get_events_state()
    p = await get_profile(ctx.author.id)
    streak = int(p.get("fish_streak_today", 0)) if p.get("streak_day") == today_key() else 0
    lines = format_events_status(st, streak)
    lines.append("")
    lines.append("**📣 정기 이벤트**")
    if is_tournament_active():
        lines.append("🏆 **주말 낚시 토너먼트** — `!토너먼트`")
    else:
        lines.append("🏆 토너먼트: 금·토·일")
    if is_jackpot_festa():
        lines.append("🎰 **잭팟 페스타** — 슬롯 잭팟 2배!")
    else:
        lines.append("🎰 잭팟 페스타: 금·토·일")
    lines.append("🎡 `!행운판` · 📅 `!일일` · ❓ `!물고기퀴즈`")
    await _reply_long(ctx, lines[1:], header=lines[0])


@bot.command(name="행운번호")
async def lucky_number_cmd(ctx: commands.Context, number: int | None = None):
    if not _channel_allowed(ctx):
        return
    if number is None:
        await ctx.reply("사용법: `!행운번호 42` (1~100, 하루 1회)", mention_author=False)
        return
    st = await get_events_state()
    ok, msg = lucky_register(st, ctx.author.id, number)
    if ok:
        await write_json(EVENT_PATH, st)
    await ctx.reply(msg, mention_author=False)


@bot.command(name="행운번호추첨", aliases=["복권추첨"])
async def lucky_draw_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    st = await get_events_state()
    st, msg = lucky_draw(st)
    if "당첨 번호" in msg and st.get("lucky", {}).get("winner"):
        winner = int(st["lucky"]["winner"])
        entries = st["lucky"].get("entries") or {}
        winning = int(st["lucky"].get("winning", 0))
        payout = payout_lucky_winner(entries, winning, winner)
        await add_money(winner, payout)
        msg += f"\n💰 <@{winner}> **{_fmt_money(payout)}** 지급!"
    await write_json(EVENT_PATH, st)
    await ctx.reply(msg, mention_author=False)


@bot.command(name="황금시간", aliases=["골든아워"])
async def golden_hour_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    p = await get_profile(ctx.author.id)
    st = await get_events_state()
    st, ok, msg = force_golden_hour(st, p.get("golden_force_day", ""))
    if ok:
        p["golden_force_day"] = today_key()
        await save_profile(ctx.author.id, p)
        await write_json(EVENT_PATH, st)
        ch_id = _env_int("ANNOUNCE_CHANNEL_ID")
        if ch_id:
            ch = bot.get_channel(ch_id)
            if ch:
                try:
                    await ch.send(
                        f"✨ **황금의 낚시터** — {ctx.author.display_name}님이 열었다! (15분)"
                    )
                except Exception:
                    pass
    await ctx.reply(msg + ("\n지금 `!낚시`!" if ok else ""), mention_author=False)


@bot.command(name="날씨")
async def weather_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    w = await get_weather_state()
    wid = w.get("id", "sunny")
    info = WEATHER_TYPES.get(wid, {})
    remain = max(0, int(w.get("until", 0)) - utc_ts())
    hint = weather_fishing_hint(wid)
    ghost = "👻 **유령물고기 시간** (KST 0~2시)" if is_ghost_fish_hour() else ""
    await ctx.reply(
        f"**🌍 서버 날씨** (KST {kst_hour()}시)\n"
        f"- 현재: **{info.get('name', '?')}**\n"
        f"- 남은 시간: **{remain // 60}분**\n"
        f"- 효과: 상자+{int(info.get('chest_bonus',0)*100)}% / 희귀+{int(info.get('rarity_bonus',0)*100)}% / 이색+{int(info.get('shiny_bonus',0)*100)}%\n"
        f"- 낚시: {hint or '평범한 날씨'}\n{ghost}",
        mention_author=False,
    )


@bot.command(name="시세")
async def market_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    m = market_mult_today()
    import datetime
    days = ["월", "화", "수", "목", "금", "토", "일"]
    d = days[datetime.datetime.now().weekday()]
    emoji = "📈" if m >= 1.1 else ("📉" if m < 1.0 else "➡️")
    await ctx.reply(
        f"{emoji} **오늘({d}) 물고기 시세**: **x{m:.2f}**\n"
        f"`!판매` 시 적용됩니다. 금요일·토요일이 장터일이야!",
        mention_author=False,
    )


@bot.command(name="뽑기")
async def gacha_cmd(ctx: commands.Context, count_raw: str | None = None):
    if not _channel_allowed(ctx):
        return
    count = 1
    if count_raw and count_raw.isdigit():
        count = min(10, max(1, int(count_raw)))
    cost = GACHA_COST * count
    money = await get_money(ctx.author.id)
    if money < cost:
        await ctx.reply(f"돈 부족! 필요 **{_fmt_money(cost)}**", mention_author=False)
        return
    await add_money(ctx.author.id, -cost)

    lines = [f"**🎁 뽑기 {count}회** (비용 {_fmt_money(cost)})"]
    for _ in range(count):
        roll = roll_gacha()
        t = roll["type"]
        if t == "money":
            amt = random.randint(int(roll["min"]), int(roll["max"]))
            await add_money(ctx.author.id, amt)
            lines.append(f"- 💰 {amt:,}원")
        elif t == "item":
            iid = roll["id"]
            qty = random.randint(int(roll["min"]), int(roll["max"]))
            await add_fish(ctx.author.id, iid, qty)
            lines.append(f"- {ITEMS.get(iid, {}).get('name', iid)} x{qty}")
        elif t == "chest":
            cid = roll["id"]
            qty = random.randint(int(roll["min"]), int(roll["max"]))
            await add_fish(ctx.author.id, cid, qty)
            lines.append(f"- {CHESTS[cid]['name']} x{qty}")

    def pm(p):
        p["gacha_total"] = int(p.get("gacha_total", 0)) + count

    await profile_update(ctx.author.id, pm)
    await quest_bump(ctx.author.id, "gacha", count)
    bal = await get_money(ctx.author.id)
    await ctx.reply("\n".join(lines[:12]) + (f"\n...외 {count-12}줄" if count > 12 else "") + f"\n잔액 **{_fmt_money(bal)}**", mention_author=False)


@bot.command(name="수수권")
async def merchant_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    now = utc_ts()
    m = await read_json(MERCHANT_PATH, _default_merchant())
    if int(m.get("until", 0)) <= now:
        items = generate_mystery_shop()
        m = {"until": now + 3600, "items": items}
        await write_json(MERCHANT_PATH, m)
    lines = ["**🧙 신비한 상인** (1시간마다 갱신)\n구매: `!구매 <아이템ID>`"]
    for it in m.get("items", []):
        iid = it["id"]
        disc = float(it["discount"])
        price = int(ITEMS[iid]["price"] * disc)
        lines.append(f"- `{iid}`: {ITEMS[iid]['name']} **{_fmt_money(price)}** (재고 {it.get('stock_left', 0)})")
    await ctx.reply("\n".join(lines), mention_author=False)


@bot.command(name="제작")
async def craft_cmd(ctx: commands.Context, recipe_id: str | None = None):
    if not _channel_allowed(ctx):
        return
    if not recipe_id or recipe_id not in CRAFT_RECIPES:
        lines = ["**🔨 제작 레시피** (`!제작 <ID>`)"]
        for rid, r in CRAFT_RECIPES.items():
            cost_txt = ", ".join(f"{k} {v}마리" for k, v in r["cost"].items())
            lines.append(f"- `{rid}`: {r['name']} — {cost_txt} → x{r['yield']}")
        await ctx.reply("\n".join(lines), mention_author=False)
        return
    recipe = CRAFT_RECIPES[recipe_id]
    inv = await get_inventory(ctx.author.id)
    for rarity, need in recipe["cost"].items():
        have = sum(
            cnt for fid, cnt in inv.items()
            if (fid in FISH_BY_ID and FISH_BY_ID[fid].rarity == rarity)
            or (fid.startswith("shiny_") and FISH_BY_ID.get(fid[6:], None) and FISH_BY_ID[fid[6:]].rarity == rarity)
        )
        if have < need:
            await ctx.reply(f"재료 부족! {rarity} 등급 물고기 {need}마리 필요 (보유 환산 {have})", mention_author=False)
            return
    left = dict(recipe["cost"])
    for fid in list(inv.keys()):
        if left.get("common", 0) <= 0 and left.get("rare", 0) <= 0 and left.get("epic", 0) <= 0 and left.get("legendary", 0) <= 0:
            break
        r = None
        if fid in FISH_BY_ID:
            r = FISH_BY_ID[fid].rarity
        elif fid.startswith("shiny_"):
            f = FISH_BY_ID.get(fid[6:])
            r = f.rarity if f else None
        if r and left.get(r, 0) > 0:
            await add_fish(ctx.author.id, fid, -1)
            left[r] -= 1
    await add_fish(ctx.author.id, recipe_id, int(recipe["yield"]))
    await ctx.reply(f"제작 완료! **{recipe['name']}** x{recipe['yield']}", mention_author=False)


async def _duel_read_all() -> dict:
    return dict(await read_json(DUEL_PATH, {}) or {})


async def _duel_set_pending(opponent_id: int, data: dict) -> None:
    def mut(d):
        d = dict(d or {})
        d[str(opponent_id)] = data
        return d

    await update_json(DUEL_PATH, {}, mut)


async def _duel_clear_pending(opponent_id: int) -> None:
    def mut(d):
        d = dict(d or {})
        d.pop(str(opponent_id), None)
        return d

    await update_json(DUEL_PATH, {}, mut)


async def _duel_get_valid_pending(opponent_id: int) -> dict | None:
    all_d = await _duel_read_all()
    p = all_d.get(str(opponent_id))
    if not p:
        return None
    if utc_ts() > int(p.get("expires", 0)):
        challenger = int(p.get("challenger", 0))
        bet = int(p.get("bet", 0))
        if challenger and bet > 0:
            await add_money(challenger, bet)
        await _duel_clear_pending(opponent_id)
        return None
    return p


async def _duel_fish_score(uid: int) -> int:
    rarity_score = {"common": 1, "rare": 2, "epic": 4, "legendary": 8, "mythic": 15}
    rt, lv = await get_rod(uid)
    w = get_rarity_weights(lv, rt, await get_user_map(uid))
    r = choose_rarity(w)
    return rarity_score.get(r, 1) + random.randint(0, lv)


async def _run_duel_fight(
    ctx: commands.Context, challenger_id: int, opponent_id: int, bet: int
) -> None:
    s1 = await _duel_fish_score(challenger_id)
    s2 = await _duel_fish_score(opponent_id)
    name1 = _display_name(ctx, challenger_id)
    name2 = _display_name(ctx, opponent_id)

    if s1 > s2:
        payout = int(bet * 1.9)
        await add_money(challenger_id, payout)

        def pm(p):
            p["duel_wins"] = int(p.get("duel_wins", 0)) + 1

        await profile_update(challenger_id, pm)
        rod_rt, rod_lv = await get_rod(challenger_id)
        await check_achievements(challenger_id, rod_lv, await get_money(challenger_id))
        winner_txt = f"**{name1}** 승리! (+{_fmt_money(payout - bet)})"
    elif s2 > s1:
        payout = int(bet * 1.9)
        await add_money(opponent_id, payout)

        def pm(p):
            p["duel_wins"] = int(p.get("duel_wins", 0)) + 1

        await profile_update(opponent_id, pm)
        rod_rt, rod_lv = await get_rod(opponent_id)
        await check_achievements(opponent_id, rod_lv, await get_money(opponent_id))
        winner_txt = f"**{name2}** 승리!"
    else:
        await add_money(challenger_id, bet)
        await add_money(opponent_id, bet)
        winner_txt = "**무승부!** 베팅 환급"

    await ctx.reply(
        f"⚔️ **{name1}** {s1} vs **{name2}** {s2}\n{winner_txt}",
        mention_author=False,
    )


@bot.command(name="대결")
async def duel_cmd(ctx: commands.Context, opponent: discord.Member | None = None, bet_raw: str | None = None):
    if not _channel_allowed(ctx):
        return
    if not opponent or not bet_raw:
        await ctx.reply(
            "**⚔️ 대결 (상대 승인제)**\n"
            "- 신청: `!대결 @유저 <베팅>` (신청자 베팅금 선차감)\n"
            "- 수락: 상대가 `!대결수락`\n"
            "- 거절: 상대가 `!대결거절` / 취소: 신청자 `!대결취소`\n"
            f"- **{DUEL_EXPIRE_SEC // 60}분** 내 미응답 시 자동 환급",
            mention_author=False,
        )
        return
    bet = _parse_bet(bet_raw)
    if bet is None:
        return
    if opponent.bot or opponent.id == ctx.author.id:
        await ctx.reply("유효한 상대를 멘션해줘.", mention_author=False)
        return
    if await get_money(ctx.author.id) < bet:
        await ctx.reply("돈 부족!", mention_author=False)
        return
    if await get_money(opponent.id) < bet:
        await ctx.reply("상대가 돈이 부족해.", mention_author=False)
        return

    all_d = await _duel_read_all()
    for opp_id, p in all_d.items():
        if int(p.get("challenger", 0)) == ctx.author.id:
            await ctx.reply(
                "이미 보낸 대결 신청이 있어. `!대결취소`로 취소하거나 상대 응답을 기다려줘.",
                mention_author=False,
            )
            return
    if await _duel_get_valid_pending(opponent.id):
        await ctx.reply("상대에게 이미 다른 대결 신청이 있어.", mention_author=False)
        return

    await add_money(ctx.author.id, -bet)
    await _duel_set_pending(
        opponent.id,
        {
            "challenger": ctx.author.id,
            "bet": bet,
            "expires": utc_ts() + DUEL_EXPIRE_SEC,
            "channel_id": getattr(ctx.channel, "id", 0),
        },
    )
    opp_name = _display_name(ctx, opponent.id)
    await ctx.reply(
        f"⚔️ **{_display_name(ctx, ctx.author.id)}** → **{opp_name}** 에게 대결 신청!\n"
        f"- 베팅: **{_fmt_money(bet)}** (신청자 선차감)\n"
        f"- {opponent.mention} 님이 `!대결수락` 또는 `!대결거절` ({DUEL_EXPIRE_SEC // 60}분)",
        mention_author=False,
    )


@bot.command(name="대결수락")
async def duel_accept_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    pending = await _duel_get_valid_pending(ctx.author.id)
    if not pending:
        await ctx.reply("받은 대결 신청이 없어.", mention_author=False)
        return
    challenger_id = int(pending["challenger"])
    bet = int(pending["bet"])
    if await get_money(ctx.author.id) < bet:
        await ctx.reply("베팅금이 부족해서 수락할 수 없어.", mention_author=False)
        return
    await _duel_clear_pending(ctx.author.id)
    await add_money(ctx.author.id, -bet)
    await _run_duel_fight(ctx, challenger_id, ctx.author.id, bet)


@bot.command(name="대결거절")
async def duel_decline_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    pending = await _duel_get_valid_pending(ctx.author.id)
    if not pending:
        await ctx.reply("거절할 대결 신청이 없어.", mention_author=False)
        return
    challenger_id = int(pending["challenger"])
    bet = int(pending["bet"])
    await _duel_clear_pending(ctx.author.id)
    await add_money(challenger_id, bet)
    await ctx.reply(
        f"⚔️ **{_display_name(ctx, ctx.author.id)}** 님이 대결을 거절했어. "
        f"**{_display_name(ctx, challenger_id)}** 베팅 **{_fmt_money(bet)}** 환급.",
        mention_author=False,
    )


@bot.command(name="대결취소")
async def duel_cancel_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    all_d = await _duel_read_all()
    found_opp = None
    found = None
    for opp_id, p in all_d.items():
        if int(p.get("challenger", 0)) == ctx.author.id:
            found_opp = int(opp_id)
            found = p
            break
    if not found:
        await ctx.reply("취소할 대결 신청이 없어.", mention_author=False)
        return
    bet = int(found.get("bet", 0))
    await _duel_clear_pending(found_opp)
    await add_money(ctx.author.id, bet)
    await ctx.reply(f"대결 신청 취소. **{_fmt_money(bet)}** 환급했어.", mention_author=False)


@bot.command(name="낚시랭킹")
async def fish_rank_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    all_p = await read_json(PROFILE_PATH, _default_profile())
    wk = week_key()
    items = []
    for uid, p in (all_p or {}).items():
        if (p or {}).get("weekly_key") == wk:
            try:
                items.append((int(uid), int(p.get("weekly_fish", 0))))
            except Exception:
                pass
    items.sort(key=lambda x: x[1], reverse=True)
    top = items[:10]
    lines = [f"**🎣 주간 낚시 랭킹** ({wk})"]
    for i, (uid, cnt) in enumerate(top, 1):
        name = _display_name(ctx, uid)
        lines.append(f"{i}. **{name}** — {cnt}회")
    await ctx.reply("\n".join(lines) if top else "아직 데이터 없음", mention_author=False)

def generate_rocket_crash():
    r = random.random()

    # 60% -> 1.5 ~ 3배
    if r < 0.60:
        return round(random.uniform(1.5, 3.0), 2)

    # 25% -> 3 ~ 10배
    elif r < 0.85:
        return round(random.uniform(3.0, 10.0), 2)

    # 10% -> 10 ~ 25배
    elif r < 0.95:
        return round(random.uniform(10.0, 25.0), 2)

    # 4% -> 25 ~ 50배
    elif r < 0.99:
        return round(random.uniform(25.0, 50.0), 2)

    # 1% -> 50 ~ 100배
    else:
        return round(random.uniform(50.0, 100.0), 2)


@bot.command(name="로켓")
async def rocket_cmd(ctx: commands.Context, bet_raw: str | None = None, target_raw: str | None = None):
    if not _channel_allowed(ctx):
        return

    bet = _parse_bet(bet_raw)

    if bet is None or not target_raw:
        await ctx.reply(
            "사용법: `!로켓 <베팅> <목표배율 2~100>` — 터지기 전에 맞추면 성공",
            mention_author=False
        )
        return

    try:
        target = float(target_raw)
    except Exception:
        await ctx.reply("배율은 2~100 사이 숫자", mention_author=False)
        return

    if target < 2 or target > 100:
        await ctx.reply("배율은 2~100", mention_author=False)
        return

    ok, err = await _casino_guard(ctx, bet)

    if not ok:
        if err:
            await ctx.reply(err, mention_author=False)
        return

    await add_money(ctx.author.id, -bet)

    # 가중치 적용된 로켓 배율
    crash = generate_rocket_crash()

    fee = await _casino_fee(ctx.author.id, 0.01)

    if target <= crash:
        payout = int(bet * target * (1 - fee))
        await add_money(ctx.author.id, payout)

        net = payout - bet

        await _casino_bump(ctx.author.id, bet, net, "로켓")

        msg = (
            f"🚀 로켓 **{crash}x**에서 수익 인출!\n"
            f"🎯 목표: {target}x\n"
            f"💰 수익: **+{_fmt_money(net)}**"
        )

        # 고배율 성공 특별 메시지
        if target >= 50:
            msg += "\n🔥 전설적인 대박!"
        elif target >= 25:
            msg += "\n⚡ 초고배율 성공!"
        elif target >= 10:
            msg += "\n✨ 고배율 성공!"

        await ctx.reply(msg, mention_author=False)

    else:
        await _casino_bump(ctx.author.id, bet, -bet, "로켓")

        await ctx.reply(
            f"💥 로켓 **{crash}x**에서 터짐!\n"
            f"🎯 목표: {target}x 실패",
            mention_author=False
        )

async def _risk_game_settle(
    ctx: commands.Context, bet: int, roll: dict, game_name: str, intro_lines: list[str] | None = None
) -> None:
    mult = float(roll.get("mult", 0))
    gross = calc_risk_payout(bet, mult)
    fee = await _casino_fee(ctx.author.id, 0.01) if gross > 0 else 0.0
    payout = int(gross * (1.0 - fee)) if gross > 0 else 0
    if payout > 0:
        await add_money(ctx.author.id, payout)
    net = payout - bet
    await _casino_bump(ctx.author.id, bet, net, game_name)
    bal = await get_money(ctx.author.id)
    lines = list(intro_lines or [])
    lines.append(f"✨ **{roll.get('tier', '?')}**")
    if mult <= 0:
        lines.append(f"💀 **전멸** — **-{_fmt_money(bet)}**")
    elif net >= 0:
        lines.append(
            f"배율 **x{mult:g}** → **+{_fmt_money(net)}** / 잔액 **{_fmt_money(bal)}**"
        )
    else:
        lines.append(
            f"배율 **x{mult:g}** → **{_fmt_money(net)}** / 잔액 **{_fmt_money(bal)}**"
        )
    await ctx.reply("\n".join(lines), mention_author=False)


@bot.command(name="보물탐사도움")
async def treasure_dive_help_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    await ctx.reply(treasure_dive_help_text(), mention_author=False)


@bot.command(name="보물탐사", aliases=["보물찾기"])
async def treasure_dive_cmd(ctx: commands.Context, bet_raw: str | None = None, door_raw: str | None = None):
    if not _channel_allowed(ctx):
        return
    bet = _parse_bet(bet_raw)
    if bet is None or not door_raw or not door_raw.isdigit():
        await ctx.reply(treasure_dive_help_text(), mention_author=False)
        return
    door = int(door_raw)
    if door < 1 or door > 3:
        await ctx.reply("문 번호는 **1, 2, 3** 중 하나", mention_author=False)
        return
    if bet < TREASURE_DIVE_MIN_BET:
        await ctx.reply(f"최소 **{_fmt_money(TREASURE_DIVE_MIN_BET)}**", mention_author=False)
        return
    ok, err = await _casino_guard(ctx, bet)
    if not ok:
        if err:
            await ctx.reply(err, mention_author=False)
        return
    await add_money(ctx.author.id, -bet)
    roll = roll_treasure_dive(door)
    hit_txt = "✅ **정답 문!**" if roll["hit"] else f"❌ 정답은 **{roll['winning_door']}번** 문"
    await _risk_game_settle(
        ctx,
        bet,
        roll,
        "보물탐사",
        [f"🗺️ **보물탐사** — 네가 고른 **{door}번** 문", hit_txt],
    )


@bot.command(name="복도도움")
async def corridor_help_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    await ctx.reply(corridor_help_text(), mention_author=False)


@bot.command(name="복도", aliases=["어둠의복도"])
async def corridor_cmd(ctx: commands.Context, bet_raw: str | None = None, steps_raw: str | None = None):
    if not _channel_allowed(ctx):
        return
    bet = _parse_bet(bet_raw)
    if bet is None or not steps_raw or not steps_raw.isdigit():
        await ctx.reply(
            corridor_help_text() + "\n예: `!복도 20000 3`",
            mention_author=False,
        )
        return
    steps = int(steps_raw)
    if steps < 1 or steps > 5:
        await ctx.reply("구간은 **1~5**만 선택 가능해.", mention_author=False)
        return
    if bet < CORRIDOR_MIN_BET:
        await ctx.reply(f"최소 베팅 **{_fmt_money(CORRIDOR_MIN_BET)}**", mention_author=False)
        return
    ok, err = await _casino_guard(ctx, bet)
    if not ok:
        if err:
            await ctx.reply(err, mention_author=False)
        return
    await add_money(ctx.author.id, -bet)
    roll = roll_corridor(steps)
    log_txt = "\n".join(f"- {x}" for x in roll.get("log", [])[:5])
    intro = [f"🚪 **어둠의 복도** — **{steps}구간** 도전!", log_txt]
    await _risk_game_settle(ctx, bet, roll, "복도", intro)


def _guild_need_server(ctx: commands.Context) -> int | None:
    if not ctx.guild:
        return None
    return int(ctx.guild.id)


async def _guild_invites() -> dict:
    return dict(await read_json(GUILD_INVITE_PATH, {}) or {})


async def _guild_set_invite(user_id: int, data: dict | None) -> None:
    def mut(d):
        d = dict(d or {})
        key = str(user_id)
        if data is None:
            d.pop(key, None)
        else:
            d[key] = data
        return d

    await update_json(GUILD_INVITE_PATH, {}, mut)


@bot.command(name="길드생성")
async def guild_create_cmd(ctx: commands.Context, name: str | None = None):
    if not _channel_allowed(ctx):
        return
    sid = _guild_need_server(ctx)
    if sid is None:
        await ctx.reply("디스코드 **서버 채널**에서만 길드를 만들 수 있어.", mention_author=False)
        return
    norm = normalize_guild_name(name)
    if not norm:
        await ctx.reply("길드 이름은 **2~10자** (한글·영문·숫자). 예: `!길드생성 콩방패`", mention_author=False)
        return
    srv, all_g, sk = await _guild_get_server(sid)
    if get_user_clan_id(srv, ctx.author.id):
        await ctx.reply("이미 길드에 소속되어 있어. `!길드탈퇴` 후 다시 시도해줘.", mention_author=False)
        return
    if find_clan_by_name(srv, norm):
        await ctx.reply("같은 이름의 길드가 이미 있어.", mention_author=False)
        return
    if await get_money(ctx.author.id) < GUILD_CREATE_COST:
        await ctx.reply(f"생성 비용 **{_fmt_money(GUILD_CREATE_COST)}** 부족", mention_author=False)
        return
    await add_money(ctx.author.id, -GUILD_CREATE_COST)
    cid = new_clan_id()
    clan = {
        "id": cid,
        "name": norm,
        "leader": ctx.author.id,
        "officers": [],
        "members": [ctx.author.id],
        "bank": 0,
        "xp": 0,
        "level": 1,
        "weekly_fish": 0,
        "weekly_key": week_key(),
        "weekly_claimed_goal": 0,
        "created": utc_ts(),
        "raid": default_clan_raid(),
    }
    srv["clans"][cid] = clan
    srv["by_user"][str(ctx.author.id)] = cid
    all_g[sk] = srv
    await _guild_save_all(all_g)
    await ctx.reply(
        f"⚔️ **길드 [{norm}]** 생성 완료!\n"
        f"- 비용: **{_fmt_money(GUILD_CREATE_COST)}**\n"
        f"- `!길드초대 @유저` · `!길드` 로 확인",
        mention_author=False,
    )


@bot.command(name="길드가입")
async def guild_join_cmd(ctx: commands.Context, name: str | None = None):
    if not _channel_allowed(ctx):
        return
    sid = _guild_need_server(ctx)
    if sid is None:
        await ctx.reply("서버 채널에서만 가능해.", mention_author=False)
        return
    if not name:
        await ctx.reply("사용법: `!길드가입 <길드이름>`", mention_author=False)
        return
    srv, all_g, sk = await _guild_get_server(sid)
    if get_user_clan_id(srv, ctx.author.id):
        await ctx.reply("이미 길드 소속이야.", mention_author=False)
        return
    clan = find_clan_by_name(srv, name)
    if not clan:
        await ctx.reply("길드를 찾을 수 없어. `!길드랭킹` 확인", mention_author=False)
        return
    if member_count(clan) >= MAX_GUILD_MEMBERS:
        await ctx.reply("정원이 가득 찼어.", mention_author=False)
        return
    cid = clan["id"]
    clan = dict(get_clan(srv, cid) or clan)
    clan.setdefault("members", []).append(ctx.author.id)
    srv["clans"][cid] = clan
    srv["by_user"][str(ctx.author.id)] = cid
    all_g[sk] = srv
    await _guild_save_all(all_g)
    await ctx.reply(f"⚔️ **[{clan['name']}]** 길드에 가입했어!", mention_author=False)


@bot.command(name="길드초대")
async def guild_invite_cmd(ctx: commands.Context, member: discord.Member | None = None):
    if not _channel_allowed(ctx):
        return
    sid = _guild_need_server(ctx)
    if sid is None or not member or member.bot:
        await ctx.reply("사용법: `!길드초대 @유저` (길드장·부길드장)", mention_author=False)
        return
    srv, _, _ = await _guild_get_server(sid)
    cid = get_user_clan_id(srv, ctx.author.id)
    clan = get_clan(srv, cid) if cid else None
    if not clan or not can_manage(clan, ctx.author.id):
        await ctx.reply("길드 관리 권한이 없어.", mention_author=False)
        return
    if get_user_clan_id(srv, member.id):
        await ctx.reply("상대는 이미 다른 길드 소속이야.", mention_author=False)
        return
    if member_count(clan) >= MAX_GUILD_MEMBERS:
        await ctx.reply("정원 초과", mention_author=False)
        return
    await _guild_set_invite(
        member.id,
        {
            "clan_id": cid,
            "server_id": sid,
            "from": ctx.author.id,
            "expires": utc_ts() + INVITE_EXPIRE_SEC,
        },
    )
    await ctx.reply(
        f"📨 **{member.display_name}** 님에게 초대를 보냈어!\n"
        f"수락: `!길드수락` (10분 유효)",
        mention_author=False,
    )


@bot.command(name="길드수락")
async def guild_accept_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    inv_all = await _guild_invites()
    inv = inv_all.get(str(ctx.author.id))
    if not inv or int(inv.get("expires", 0)) < utc_ts():
        await _guild_set_invite(ctx.author.id, None)
        await ctx.reply("받은 초대가 없거나 만료됐어.", mention_author=False)
        return
    sid = int(inv["server_id"])
    cid = inv["clan_id"]
    srv, all_g, sk = await _guild_get_server(sid)
    if get_user_clan_id(srv, ctx.author.id):
        await _guild_set_invite(ctx.author.id, None)
        await ctx.reply("이미 길드 소속", mention_author=False)
        return
    clan = get_clan(srv, cid)
    if not clan or member_count(clan) >= MAX_GUILD_MEMBERS:
        await ctx.reply("가입할 수 없는 길드야.", mention_author=False)
        return
    clan = dict(clan)
    clan.setdefault("members", []).append(ctx.author.id)
    srv["clans"][cid] = clan
    srv["by_user"][str(ctx.author.id)] = cid
    all_g[sk] = srv
    await _guild_save_all(all_g)
    await _guild_set_invite(ctx.author.id, None)
    await ctx.reply(f"⚔️ **[{clan['name']}]** 길드 가입 완료!", mention_author=False)


@bot.command(name="길드거절")
async def guild_decline_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    await _guild_set_invite(ctx.author.id, None)
    await ctx.reply("길드 초대를 거절했어.", mention_author=False)


@bot.command(name="길드", aliases=["길드정보"])
async def guild_info_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    sid = _guild_need_server(ctx)
    if sid is None:
        await ctx.reply("서버에서만 사용 가능", mention_author=False)
        return
    srv, _, _ = await _guild_get_server(sid)
    cid = get_user_clan_id(srv, ctx.author.id)
    if not cid:
        await ctx.reply(
            "소속 길드가 없어.\n`!길드생성 <이름>` · `!길드가입 <이름>` · `!길드랭킹`",
            mention_author=False,
        )
        return
    clan = get_clan(srv, cid)
    if not clan:
        await ctx.reply("길드 데이터 오류. 관리자에게 문의해줘.", mention_author=False)
        return
    await ctx.reply("\n".join(format_guild_card(clan)), mention_author=False)


@bot.command(name="길드원")
async def guild_members_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    sid = _guild_need_server(ctx)
    if sid is None:
        return
    srv, _, _ = await _guild_get_server(sid)
    cid = get_user_clan_id(srv, ctx.author.id)
    clan = get_clan(srv, cid) if cid else None
    if not clan:
        await ctx.reply("길드 미가입", mention_author=False)
        return
    lines = [f"**👥 [{clan['name']}] 길드원**"]
    for uid in clan.get("members", []):
        uid = int(uid)
        role = "길드장" if is_leader(clan, uid) else ("부길드장" if is_officer(clan, uid) else "길드원")
        lines.append(f"- {role}: **{_display_name(ctx, uid)}**")
    await ctx.reply("\n".join(lines), mention_author=False)


@bot.command(name="길드탈퇴")
async def guild_leave_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    sid = _guild_need_server(ctx)
    if sid is None:
        return
    srv, all_g, sk = await _guild_get_server(sid)
    cid = get_user_clan_id(srv, ctx.author.id)
    if not cid:
        await ctx.reply("소속 길드 없음", mention_author=False)
        return
    clan = dict(get_clan(srv, cid) or {})
    if is_leader(clan, ctx.author.id):
        await ctx.reply("길드장은 `!길드해산` 또는 길드장 위임 후 탈퇴해줘.", mention_author=False)
        return
    members = [m for m in clan.get("members", []) if int(m) != ctx.author.id]
    clan["members"] = members
    officers = [o for o in clan.get("officers", []) if int(o) != ctx.author.id]
    clan["officers"] = officers
    srv["clans"][cid] = clan
    srv["by_user"].pop(str(ctx.author.id), None)
    all_g[sk] = srv
    await _guild_save_all(all_g)
    await ctx.reply(f"**[{clan['name']}]** 길드에서 탈퇴했어.", mention_author=False)


@bot.command(name="길드해산")
async def guild_disband_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    sid = _guild_need_server(ctx)
    if sid is None:
        return
    srv, all_g, sk = await _guild_get_server(sid)
    cid = get_user_clan_id(srv, ctx.author.id)
    clan = get_clan(srv, cid) if cid else None
    if not clan or not is_leader(clan, ctx.author.id):
        await ctx.reply("길드장만 해산할 수 있어.", mention_author=False)
        return
    name = clan["name"]
    for m in clan.get("members", []):
        srv["by_user"].pop(str(m), None)
    srv["clans"].pop(cid, None)
    all_g[sk] = srv
    await _guild_save_all(all_g)
    await ctx.reply(f"⚔️ 길드 **[{name}]** 가 해산되었어.", mention_author=False)


@bot.command(name="길드추방")
async def guild_kick_cmd(ctx: commands.Context, member: discord.Member | None = None):
    if not _channel_allowed(ctx):
        return
    sid = _guild_need_server(ctx)
    if not sid or not member:
        await ctx.reply("사용법: `!길드추방 @유저`", mention_author=False)
        return
    srv, all_g, sk = await _guild_get_server(sid)
    cid = get_user_clan_id(srv, ctx.author.id)
    clan = dict(get_clan(srv, cid) or {}) if cid else {}
    if not can_manage(clan, ctx.author.id):
        await ctx.reply("권한 없음", mention_author=False)
        return
    if not is_member(clan, member.id):
        await ctx.reply("같은 길드가 아니야.", mention_author=False)
        return
    if is_leader(clan, member.id):
        await ctx.reply("길드장은 추방할 수 없어.", mention_author=False)
        return
    clan["members"] = [m for m in clan.get("members", []) if int(m) != member.id]
    clan["officers"] = [o for o in clan.get("officers", []) if int(o) != member.id]
    srv["clans"][cid] = clan
    srv["by_user"].pop(str(member.id), None)
    all_g[sk] = srv
    await _guild_save_all(all_g)
    await ctx.reply(f"**{_display_name(ctx, member.id)}** 님을 추방했어.", mention_author=False)


@bot.command(name="길드임명")
async def guild_promote_cmd(ctx: commands.Context, member: discord.Member | None = None):
    if not _channel_allowed(ctx):
        return
    sid = _guild_need_server(ctx)
    if not sid or not member:
        await ctx.reply("사용법: `!길드임명 @유저` (부길드장 임명)", mention_author=False)
        return
    srv, all_g, sk = await _guild_get_server(sid)
    cid = get_user_clan_id(srv, ctx.author.id)
    clan = dict(get_clan(srv, cid) or {}) if cid else {}
    if not is_leader(clan, ctx.author.id):
        await ctx.reply("길드장만 임명할 수 있어.", mention_author=False)
        return
    if not is_member(clan, member.id):
        await ctx.reply("길드원만 임명 가능", mention_author=False)
        return
    officers = [str(o) for o in clan.get("officers", [])]
    mid = str(member.id)
    if mid in officers:
        officers.remove(mid)
        clan["officers"] = [int(x) for x in officers]
        msg = "부길드장 해제"
    else:
        if len(officers) >= MAX_OFFICERS:
            await ctx.reply(f"부길드장은 최대 {MAX_OFFICERS}명", mention_author=False)
            return
        officers.append(mid)
        clan["officers"] = [int(x) for x in officers]
        msg = "부길드장 임명"
    srv["clans"][cid] = clan
    all_g[sk] = srv
    await _guild_save_all(all_g)
    await ctx.reply(f"**{_display_name(ctx, member.id)}** — {msg}", mention_author=False)


@bot.command(name="길드기부")
async def guild_donate_cmd(ctx: commands.Context, amount_raw: str | None = None):
    if not _channel_allowed(ctx):
        return
    sid = _guild_need_server(ctx)
    if sid is None:
        return
    if not amount_raw or not amount_raw.isdigit():
        await ctx.reply(f"사용법: `!길드기부 <금액>` (최소 {_fmt_money(DONATE_MIN)})", mention_author=False)
        return
    amt = int(amount_raw)
    if amt < DONATE_MIN:
        await ctx.reply(f"최소 **{_fmt_money(DONATE_MIN)}**", mention_author=False)
        return
    if await get_money(ctx.author.id) < amt:
        await ctx.reply("보유금 부족", mention_author=False)
        return
    srv, all_g, sk = await _guild_get_server(sid)
    cid = get_user_clan_id(srv, ctx.author.id)
    clan = dict(get_clan(srv, cid) or {}) if cid else None
    if not clan:
        await ctx.reply("길드 미가입", mention_author=False)
        return
    await add_money(ctx.author.id, -amt)
    clan["bank"] = int(clan.get("bank", 0)) + amt
    add_guild_xp(clan, amt // 100)
    srv["clans"][cid] = clan
    all_g[sk] = srv
    await _guild_save_all(all_g)
    await ctx.reply(
        f"💰 **{_fmt_money(amt)}** 기부! 금고 **{clan['bank']:,}원** (길드 Lv.{clan['level']})",
        mention_author=False,
    )


@bot.command(name="길드출금")
async def guild_withdraw_cmd(ctx: commands.Context, amount_raw: str | None = None):
    if not _channel_allowed(ctx):
        return
    sid = _guild_need_server(ctx)
    if sid is None or not amount_raw or not amount_raw.isdigit():
        await ctx.reply("사용법: `!길드출금 <금액>` (길드장)", mention_author=False)
        return
    amt = int(amount_raw)
    srv, all_g, sk = await _guild_get_server(sid)
    cid = get_user_clan_id(srv, ctx.author.id)
    clan = dict(get_clan(srv, cid) or {}) if cid else None
    if not clan or not is_leader(clan, ctx.author.id):
        await ctx.reply("길드장만 출금 가능", mention_author=False)
        return
    if int(clan.get("bank", 0)) < amt:
        await ctx.reply("길드 금고 부족", mention_author=False)
        return
    clan["bank"] = int(clan["bank"]) - amt
    srv["clans"][cid] = clan
    all_g[sk] = srv
    await _guild_save_all(all_g)
    await add_money(ctx.author.id, amt)
    await ctx.reply(f"길드 금고에서 **{_fmt_money(amt)}** 출금", mention_author=False)


@bot.command(name="길드주간보상")
async def guild_weekly_claim_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    sid = _guild_need_server(ctx)
    if sid is None:
        return
    srv, all_g, sk = await _guild_get_server(sid)
    cid = get_user_clan_id(srv, ctx.author.id)
    clan = dict(get_clan(srv, cid) or {}) if cid else None
    if not clan or not can_manage(clan, ctx.author.id):
        await ctx.reply("길드장·부길드장만 주간 보상을 받을 수 있어.", mention_author=False)
        return
    reset_weekly_if_needed(clan)
    wf = int(clan.get("weekly_fish", 0))
    target, reward, _ = weekly_goal_progress(wf)
    claimed = int(clan.get("weekly_claimed_goal", 0))
    if wf < target:
        await ctx.reply(f"주간 낚시 **{wf}/{target}** — 아직 목표 미달성", mention_author=False)
        return
    if claimed >= target:
        await ctx.reply("이번 주 목표 보상은 이미 받았어.", mention_author=False)
        return
    members = clan.get("members") or []
    if not members:
        return
    per = max(1, reward // len(members))
    for m in members:
        await add_money(int(m), per)
    clan["weekly_claimed_goal"] = target
    srv["clans"][cid] = clan
    all_g[sk] = srv
    await _guild_save_all(all_g)
    await ctx.reply(
        f"🎉 **주간 협동 보상!** 길드원 **{len(members)}명**에게 각 **{_fmt_money(per)}** 지급\n"
        f"(목표 낚시 {target}회 달성)",
        mention_author=False,
    )


@bot.command(name="길드레이드")
async def guild_raid_start_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    sid = _guild_need_server(ctx)
    if sid is None:
        return
    srv, all_g, sk = await _guild_get_server(sid)
    cid = get_user_clan_id(srv, ctx.author.id)
    clan = dict(get_clan(srv, cid) or {}) if cid else None
    if not clan or not can_manage(clan, ctx.author.id):
        await ctx.reply("길드장·부길드장만 레이드 시작 가능", mention_author=False)
        return
    raid = dict(clan.get("raid") or default_clan_raid())
    now = utc_ts()
    if raid.get("active") and int(raid.get("hp", 0)) > 0:
        await ctx.reply("이미 레이드 진행 중! `!길드공격`", mention_author=False)
        return
    import datetime
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    last = raid.get("last_raid_day", "")
    if last:
        try:
            d0 = datetime.datetime.strptime(last, "%Y-%m-%d")
            d1 = datetime.datetime.strptime(today, "%Y-%m-%d")
            if (d1 - d0).days < RAID_COOLDOWN_DAYS:
                await ctx.reply(f"길드 레이드는 **{RAID_COOLDOWN_DAYS}일**마다 1회", mention_author=False)
                return
        except Exception:
            pass
    mc = member_count(clan)
    if mc < 2:
        await ctx.reply("레이드는 길드원 **2명 이상** 필요", mention_author=False)
        return
    mx = raid_max_hp(mc, int(clan.get("level", 1)))
    raid = {
        "active": True,
        "hp": mx,
        "max_hp": mx,
        "ends_at": now + RAID_DURATION_SEC,
        "contributors": {},
        "last_raid_day": today,
    }
    clan["raid"] = raid
    srv["clans"][cid] = clan
    all_g[sk] = srv
    await _guild_save_all(all_g)
    await ctx.reply(
        f"🐲 **길드 레이드 시작!** [{clan['name']}]\n"
        f"- HP: **{mx:,}** (2시간 · 길드원 협동)\n"
        f"- `!길드공격` 으로 참여!",
        mention_author=False,
    )


async def _guild_raid_payout(ctx: commands.Context, clan: dict, cid: str, srv: dict, all_g: dict, sk: str) -> None:
    raid = clan.get("raid") or {}
    contributors = dict(raid.get("contributors") or {})
    total = sum(int(v) for v in contributors.values())
    bank_bonus = min(int(clan.get("bank", 0)), 200_000)
    base = 50_000 + int(clan.get("level", 1)) * 20_000
    lines = [f"**🐲 [{clan['name']}] 길드 레이드 토벌!**\n"]
    if total <= 0:
        await ctx.send("참여자가 없어 보상이 없어.")
        return
    top_uid = max(contributors.items(), key=lambda kv: int(kv[1]))[0]
    for uid_str, dmg in contributors.items():
        dmg = int(dmg)
        if dmg <= 0:
            continue
        share = int((base + bank_bonus) * (dmg / total))
        bonus = int(base * 0.15) if uid_str == top_uid else 0
        await add_money(int(uid_str), share + bonus)
        await add_fish(int(uid_str), FRAGMENT_ITEM_ID, random.randint(1, 3))
        tag = " 👑딜1등" if uid_str == top_uid else ""
        spine_txt = ""
        if uid_str == str(top_uid) and await _maybe_drop_spine(int(uid_str), 0.03):
            spine_txt = " 🦴**관수의 척추!**"
        lines.append(f"- **{_display_name(ctx, int(uid_str))}**: {dmg:,} 딜 → **{_fmt_money(share + bonus)}**{tag}{spine_txt}")
    clan["bank"] = max(0, int(clan.get("bank", 0)) - bank_bonus)
    clan["raid"] = default_clan_raid()
    add_guild_xp(clan, 500)
    srv["clans"][cid] = clan
    all_g[sk] = srv
    await _guild_save_all(all_g)
    await ctx.send("\n".join(lines))


@bot.command(name="길드공격")
async def guild_raid_attack_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    sid = _guild_need_server(ctx)
    if sid is None:
        return
    srv, all_g, sk = await _guild_get_server(sid)
    cid = get_user_clan_id(srv, ctx.author.id)
    clan = dict(get_clan(srv, cid) or {}) if cid else None
    if not clan:
        await ctx.reply("길드 미가입", mention_author=False)
        return
    raid = dict(clan.get("raid") or default_clan_raid())
    now = utc_ts()
    if not raid.get("active") or int(raid.get("hp", 0)) <= 0 or int(raid.get("ends_at", 0)) < now:
        await ctx.reply("활성 길드 레이드가 없어. `!길드레이드`", mention_author=False)
        return
    rod_type, rod_level = await get_rod(ctx.author.id)
    tb = await get_title_buffs(ctx.author.id)
    dmg, is_crit, crit_mult = _boss_damage(rod_type, rod_level, tb)
    clan_b = await guild_get_buffs(ctx.author.id, sid)
    if clan_b.get("boss", 0) > 0:
        dmg = int(dmg * (1.0 + float(clan_b["boss"])))
    if is_crit:
        dmg = int(dmg * crit_mult)
    hp = max(0, int(raid.get("hp", 0)) - dmg)
    raid["hp"] = hp
    uid = str(ctx.author.id)
    raid["contributors"] = dict(raid.get("contributors") or {})
    raid["contributors"][uid] = int(raid["contributors"].get(uid, 0)) + dmg
    clan["raid"] = raid
    srv["clans"][cid] = clan
    all_g[sk] = srv
    await _guild_save_all(all_g)
    mx = int(raid.get("max_hp", 0))
    crit_txt = " 💥크리!" if is_crit else ""
    if hp > 0:
        await ctx.reply(
            f"🐲 **{ctx.author.display_name}** 공격 **{dmg:,}**{crit_txt}\nHP **{hp:,}/{mx:,}**",
            mention_author=False,
        )
        return
    await ctx.send(f"🐲 **{ctx.author.display_name}** 막타! 길드 레이드 격파!{crit_txt}")
    await _guild_raid_payout(ctx, clan, cid, srv, all_g, sk)


@bot.command(name="길드랭킹")
async def guild_ranking_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    sid = _guild_need_server(ctx)
    if sid is None:
        return
    srv, _, _ = await _guild_get_server(sid)
    clans = list((srv.get("clans") or {}).values())
    if not clans:
        await ctx.reply("이 서버에 길드가 없어.", mention_author=False)
        return
    clans.sort(key=lambda c: (int(c.get("level", 1)), int(c.get("xp", 0))), reverse=True)
    lines = ["**⚔️ 서버 길드 랭킹**"]
    for i, c in enumerate(clans[:10], 1):
        lines.append(
            f"{i}. **[{c.get('name')}]** Lv.{c.get('level')} · "
            f"원 {member_count(c)} · XP {int(c.get('xp',0)):,}"
        )
    await ctx.reply("\n".join(lines), mention_author=False)


@bot.command(name="각성", aliases=["세계관수"])
async def worldender_awaken_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    inv = await get_inventory(ctx.author.id)
    spines = int(inv.get(WORLDENDER_SPINE, 0))
    frags = int(inv.get(FRAGMENT_ITEM_ID, 0))
    _, level = await get_rod(ctx.author.id)
    if level < 24:
        await ctx.reply(
            f"각성은 낚시대 **+24강** 이상 필요 (현재 +{level})",
            mention_author=False,
        )
        return
    if spines < WORLDENDER_SPINE_NEED:
        await ctx.reply(
            f"🦴 **관수의 척추** **{spines}/{WORLDENDER_SPINE_NEED}**개 부족.\n"
            "월드보스·요일보스 **딜 1등** 극소확률 드랍",
            mention_author=False,
        )
        return
    if frags < WORLDENDER_FRAGMENT_NEED:
        await ctx.reply(
            f"🧩 파편 **{frags}/{WORLDENDER_FRAGMENT_NEED}**개 부족",
            mention_author=False,
        )
        return
    await add_fish(ctx.author.id, WORLDENDER_SPINE, -WORLDENDER_SPINE_NEED)
    await add_fish(ctx.author.id, FRAGMENT_ITEM_ID, -WORLDENDER_FRAGMENT_NEED)
    rec = await get_rod_record(ctx.author.id)
    await set_rod(ctx.author.id, "worldender", max(level, 24), rec.get("affixes", []))
    ch_id = _env_int("ANNOUNCE_CHANNEL_ID")
    if ch_id:
        ch = bot.get_channel(ch_id)
        if ch:
            try:
                await ch.send(
                    f"⚔️⚔️ **[전서버 속보]** {ctx.author.mention} 님이\n"
                    f"전설의 **⚔️ 세계관수 낚시대** 를 각성했다!!!\n"
                    f"🌊 보스를 학살할 자격을 얻었다..."
                )
            except Exception:
                pass
    await ctx.reply(
        f"⚔️ **세계관수 낚시대 각성!**\n"
        f"- 척소 {WORLDENDER_SPINE_NEED}개 · 파편 {WORLDENDER_FRAGMENT_NEED}개 소모\n"
        f"- **{format_rod_name('worldender', max(level, 24))}**\n"
        f"- 보스 피해 **+125%** · 크리티컬 강화 (낚시 희귀도는 거의 없음)\n"
        f"`!보스공격` `!길드공격` 에서 진가 발휘!",
        mention_author=False,
    )


@bot.command(name="파편제작")
async def fragment_craft_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    inv = await get_inventory(ctx.author.id)
    have = int(inv.get(FRAGMENT_ITEM_ID, 0))
    if have < FRAGMENT_CRAFT_COUNT:
        await ctx.reply(
            f"🧩 **심연의 파편** **{have}/{FRAGMENT_CRAFT_COUNT}**개 부족.\n"
            f"낚시·월드보스·탐험에서 모을 수 있어.",
            mention_author=False,
        )
        return
    await add_fish(ctx.author.id, FRAGMENT_ITEM_ID, -FRAGMENT_CRAFT_COUNT)
    rod_type, level = await get_rod(ctx.author.id)
    new_level = max(level, 20)
    await set_rod(ctx.author.id, "sovereign", new_level)
    await ctx.reply(
        f"👑 **심연 군주 낚시대** 제작 완료!\n"
        f"- **{format_rod_name('sovereign', new_level)}**\n"
        f"- 파편 {FRAGMENT_CRAFT_COUNT}개 소모",
        mention_author=False,
    )


@bot.command(name="탐험")
async def expedition_start_cmd(ctx: commands.Context, hours_raw: str | None = None):
    if not _channel_allowed(ctx):
        return
    hours = 3
    if hours_raw and hours_raw.isdigit():
        hours = max(1, min(6, int(hours_raw)))
    uid = str(ctx.author.id)
    all_e = await read_json(EXPEDITION_PATH, default_expedition())
    if uid in all_e and int(all_e[uid].get("ends_at", 0)) > utc_ts():
        remain = int(all_e[uid]["ends_at"]) - utc_ts()
        await ctx.reply(
            f"이미 탐험 중! **{remain // 3600}시간 {(remain % 3600) // 60}분** 후 `!탐험수령`",
            mention_author=False,
        )
        return
    cost = 15000 * hours
    if await get_money(ctx.author.id) < cost:
        await ctx.reply(f"출항 비용 **{_fmt_money(cost)}** 필요", mention_author=False)
        return
    await add_money(ctx.author.id, -cost)
    ends = utc_ts() + expedition_duration_sec(hours)

    def mut(d):
        d = dict(d or {})
        d[uid] = {"ends_at": ends, "hours": hours, "started": utc_ts()}
        return d

    await update_json(EXPEDITION_PATH, default_expedition(), mut)
    await ctx.reply(
        f"⛵ **탐험 출항!** ({hours}시간)\n"
        f"- 비용: **{_fmt_money(cost)}**\n"
        f"- 귀항: <t:{ends}:R> 후 `!탐험수령`\n"
        f"- `!탐험선` 으로 배 업그레이드 가능",
        mention_author=False,
    )


@bot.command(name="탐험수령")
async def expedition_claim_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    uid = str(ctx.author.id)
    all_e = await read_json(EXPEDITION_PATH, default_expedition())
    trip = all_e.get(uid)
    if not trip:
        await ctx.reply("`!탐험 3` 으로 먼저 출항해줘.", mention_author=False)
        return
    if int(trip.get("ends_at", 0)) > utc_ts():
        remain = int(trip["ends_at"]) - utc_ts()
        await ctx.reply(f"아직 항해 중... **{remain // 60}분** 남음", mention_author=False)
        return
    ships = await read_json(SHIP_PATH, {})
    ship = ships.get(uid) or default_ship()
    hours = int(trip.get("hours", 3))
    log_lines, rewards = roll_expedition_rewards(ship, hours)
    for rw in rewards:
        if rw[0] == "money":
            await add_money(ctx.author.id, int(rw[1]))
        elif rw[0] == "fragment":
            await add_fish(ctx.author.id, FRAGMENT_ITEM_ID, int(rw[1]))
        elif rw[0] == "item":
            await add_fish(ctx.author.id, rw[1], int(rw[2]))
        elif rw[0] == "fish_rarity":
            pool = [f for f in FISH_TABLE if f.rarity == rw[1]]
            if pool:
                f = random.choice(pool)
                await add_fish(ctx.author.id, f.id, 1)
                log_lines.append(f"→ **{f.name}** 획득!")

    def mut(d):
        d = dict(d or {})
        d.pop(uid, None)
        return d

    await update_json(EXPEDITION_PATH, default_expedition(), mut)
    bal = await get_money(ctx.author.id)
    await ctx.reply(
        f"⚓ **탐험 귀항!**\n" + "\n".join(log_lines[:14]) + f"\n\n잔액 **{_fmt_money(bal)}**",
        mention_author=False,
    )


@bot.command(name="탐험선")
async def ship_status_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    ships = await read_json(SHIP_PATH, {})
    ship = ships.get(str(ctx.author.id)) or default_ship()
    lines = ["**⛵ 탐험선** (`!탐험업그레이드 <엔진|저장고|선원|레이더>`)"]
    key_map = {"engine": "engine", "hold": "hold", "crew": "crew", "radar": "radar"}
    for part in SHIP_PARTS:
        lv = int(ship.get(part, 0))
        cost = ship_upgrade_cost(part, lv)
        lines.append(f"- {SHIP_PART_NAMES[part]} Lv**{lv}** → 다음 **{_fmt_money(cost)}**")
    await ctx.reply("\n".join(lines), mention_author=False)


@bot.command(name="탐험업그레이드")
async def ship_upgrade_cmd(ctx: commands.Context, part_raw: str | None = None):
    if not _channel_allowed(ctx):
        return
    if not part_raw:
        await ctx.reply("예: `!탐험업그레이드 engine` / hold / crew / radar", mention_author=False)
        return
    aliases = {
        "엔진": "engine", "engine": "engine",
        "저장고": "hold", "hold": "hold",
        "선원": "crew", "crew": "crew",
        "레이더": "radar", "radar": "radar",
    }
    part = aliases.get(part_raw.strip().lower())
    if not part:
        await ctx.reply("engine · hold · crew · radar", mention_author=False)
        return
    uid = str(ctx.author.id)
    ships = await read_json(SHIP_PATH, {})
    ship = dict(ships.get(uid) or default_ship())
    lv = int(ship.get(part, 0))
    if lv >= 5:
        await ctx.reply("최대 레벨 5", mention_author=False)
        return
    cost = ship_upgrade_cost(part, lv)
    if await get_money(ctx.author.id) < cost:
        await ctx.reply(f"비용 **{_fmt_money(cost)}** 부족", mention_author=False)
        return
    await add_money(ctx.author.id, -cost)
    ship[part] = lv + 1

    def mut(d):
        d = dict(d or {})
        d[uid] = ship
        return d

    await update_json(SHIP_PATH, {}, mut)
    await ctx.reply(f"{SHIP_PART_NAMES[part]} → **Lv{lv + 1}**!", mention_author=False)


async def _get_aquarium(user_id: int) -> dict:
    all_a = await read_json(AQUARIUM_PATH, {})
    uid = str(user_id)
    a = dict(all_a.get(uid) or default_aquarium())
    return a


async def _save_aquarium(user_id: int, data: dict) -> None:
    def mut(d):
        d = dict(d or {})
        d[str(user_id)] = data
        return d

    await update_json(AQUARIUM_PATH, {}, mut)


@bot.command(name="섬", aliases=["수족관"])
async def island_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    a = await _get_aquarium(ctx.author.id)
    slots = aquarium_max_slots(int(a.get("level", 1)))
    disp = a.get("display") or []
    lines = [
        f"**🏝️ {ctx.author.display_name}의 섬** (Lv{a.get('level', 1)})",
        f"- 전시 **{len(disp)}/{slots}** · ❤️ **{int(a.get('likes', 0))}**",
        f"- 미수령 수익: **{_fmt_money(int(a.get('pending_income', 0)))}** (`!섬수령`)",
        "`!섬전시 <물고기ID>` · `!섬방문 @유저` · `!섬좋아요 @유저`",
    ]
    for fid in disp[:slots]:
        f = FISH_BY_ID.get(fid)
        lines.append(f"  🐟 {f.name if f else fid}")
    await ctx.reply("\n".join(lines), mention_author=False)


@bot.command(name="섬전시")
async def island_display_cmd(ctx: commands.Context, fish_id: str | None = None):
    if not _channel_allowed(ctx):
        return
    if not fish_id or fish_id not in FISH_BY_ID:
        await ctx.reply("도감 ID로 전시 (`!도감` 참고)", mention_author=False)
        return
    inv = await get_inventory(ctx.author.id)
    if int(inv.get(fish_id, 0)) + int(inv.get(f"shiny_{fish_id}", 0)) <= 0:
        await ctx.reply("인벤에 없는 물고기야.", mention_author=False)
        return
    a = await _get_aquarium(ctx.author.id)
    slots = aquarium_max_slots(int(a.get("level", 1)))
    disp = list(a.get("display") or [])
    if fish_id in disp:
        await ctx.reply("이미 전시 중", mention_author=False)
        return
    if len(disp) >= slots:
        await ctx.reply(f"슬롯 가득 ({slots}). 다른 물고기를 빼고 전시해줘.", mention_author=False)
        return
    disp.append(fish_id)
    a["display"] = disp
    await _save_aquarium(ctx.author.id, a)
    await ctx.reply(f"🏝️ **{FISH_BY_ID[fish_id].name}** 전시 완료!", mention_author=False)


@bot.command(name="섬수령")
async def island_income_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    a = await _get_aquarium(ctx.author.id)
    now = utc_ts()
    last = int(a.get("last_income_ts", now))
    hours = max(0, (now - last) // 3600)
    disp = a.get("display") or []
    earned = int(a.get("pending_income", 0))
    if hours > 0 and disp:
        earned += aquarium_income_per_hour(int(a.get("level", 1)), len(disp)) * hours
    if earned <= 0:
        await ctx.reply("수령할 수익이 없어. 희귀 물고기를 전시해봐!", mention_author=False)
        return
    await add_money(ctx.author.id, earned)
    a["pending_income"] = 0
    a["last_income_ts"] = now
    await _save_aquarium(ctx.author.id, a)
    await ctx.reply(f"🏝️ 섬 수익 **{_fmt_money(earned)}** 수령!", mention_author=False)


@bot.command(name="섬방문")
async def island_visit_cmd(ctx: commands.Context, member: discord.Member | None = None):
    if not _channel_allowed(ctx):
        return
    if not member:
        await ctx.reply("`!섬방문 @유저`", mention_author=False)
        return
    a = await _get_aquarium(member.id)
    disp = a.get("display") or []
    lines = [
        f"**🏝️ {_display_name(ctx, member.id)}의 섬** (Lv{a.get('level', 1)}) · ❤️ {int(a.get('likes', 0))}",
    ]
    for fid in disp[:12]:
        f = FISH_BY_ID.get(fid)
        lines.append(f"  🐟 {f.name if f else fid}")
    if not disp:
        lines.append("  (비어 있음)")
    await ctx.reply("\n".join(lines), mention_author=False)


@bot.command(name="섬좋아요")
async def island_like_cmd(ctx: commands.Context, member: discord.Member | None = None):
    if not _channel_allowed(ctx):
        return
    if not member or member.bot:
        await ctx.reply("`!섬좋아요 @유저`", mention_author=False)
        return
    a = await _get_aquarium(member.id)
    liked = list(a.get("liked_by") or [])
    if str(ctx.author.id) in liked:
        await ctx.reply("오늘은 이미 좋아요 했어.", mention_author=False)
        return
    liked.append(str(ctx.author.id))
    a["liked_by"] = liked[-500:]
    a["likes"] = int(a.get("likes", 0)) + 1
    if int(a.get("likes", 0)) % 5 == 0:
        a["level"] = min(20, int(a.get("level", 1)) + 1)
    await _save_aquarium(member.id, a)
    await ctx.reply(f"❤️ **{_display_name(ctx, member.id)}** 섬에 좋아요!", mention_author=False)


@bot.command(name="옵션")
async def rod_option_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    rec = await get_rod_record(ctx.author.id)
    affixes = rec.get("affixes", [])
    if not affixes:
        await ctx.reply(
            "낚시대 옵션이 없어. **+5 / +10 / +15 / +20** 강화 성공 시 랜덤 옵션 부여.\n"
            "`!재련` `!옵션잠금 <번호>`",
            mention_author=False,
        )
        return
    lines = ["**⚙️ 낚시대 옵션**"]
    for i, a in enumerate(affixes, 1):
        lock = " 🔒" if a.get("locked") else ""
        lines.append(f"{i}. {format_affix_line(a)}{lock}")
    lines.append("\n`!재련` (5만원) · `!옵션잠금 1`")
    await ctx.reply("\n".join(lines), mention_author=False)


@bot.command(name="재련")
async def reroll_option_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    cost = 50_000
    if await get_money(ctx.author.id) < cost:
        await ctx.reply(f"재련 비용 **{_fmt_money(cost)}**", mention_author=False)
        return
    rec = await get_rod_record(ctx.author.id)
    affixes = list(rec.get("affixes", []))
    if not affixes:
        await ctx.reply("옵션이 없어.", mention_author=False)
        return
    unlocked = [i for i, a in enumerate(affixes) if not a.get("locked")]
    if not unlocked:
        await ctx.reply("잠금 해제 후 재련해줘.", mention_author=False)
        return
    await add_money(ctx.author.id, -cost)
    idx = random.choice(unlocked)
    affixes[idx] = roll_affix()
    if affixes[idx].get("locked"):
        affixes[idx]["locked"] = False
    rod_type, lv = await get_rod(ctx.author.id)
    await set_rod(ctx.author.id, rod_type, lv, affixes)
    await ctx.reply(f"🔨 슬롯 **{idx + 1}** 재련 → {format_affix_line(affixes[idx])}", mention_author=False)


@bot.command(name="옵션잠금")
async def lock_option_cmd(ctx: commands.Context, slot_raw: str | None = None):
    if not _channel_allowed(ctx):
        return
    if not slot_raw or not slot_raw.isdigit():
        await ctx.reply("예: `!옵션잠금 1`", mention_author=False)
        return
    idx = int(slot_raw) - 1
    rec = await get_rod_record(ctx.author.id)
    affixes = list(rec.get("affixes", []))
    if idx < 0 or idx >= len(affixes):
        await ctx.reply("잘못된 번호", mention_author=False)
        return
    affixes[idx]["locked"] = not bool(affixes[idx].get("locked"))
    rod_type, lv = await get_rod(ctx.author.id)
    await set_rod(ctx.author.id, rod_type, lv, affixes)
    state = "잠금" if affixes[idx]["locked"] else "해제"
    await ctx.reply(f"슬롯 {idx + 1} **{state}**", mention_author=False)


LOAN_PATH = DATA_DIR / "loan.json"


def _default_loan() -> Dict[str, int]:
    return {}


@bot.command(name="대출")
async def loan_cmd(ctx: commands.Context, amount_raw: str | None = None):
    if not _channel_allowed(ctx):
        return
    if not amount_raw or not amount_raw.isdigit():
        await ctx.reply("사용법: `!대출 <금액>` (최대 50만)", mention_author=False)
        return
    amt = min(500_000, int(amount_raw))
    loans = await read_json(LOAN_PATH, _default_loan())
    if int(loans.get(str(ctx.author.id), 0)) > 0:
        await ctx.reply("이미 대출 중! `!상환` 먼저", mention_author=False)
        return
    def mut(d):
        d = dict(d or {})
        d[str(ctx.author.id)] = amt
        return d
    await update_json(LOAN_PATH, _default_loan(), mut)
    bal = await add_money(ctx.author.id, amt)
    await ctx.reply(f"🏦 대출 **{_fmt_money(amt)}** (상환액 **{_fmt_money(int(amt*1.1))}**) / 잔액 **{_fmt_money(bal)}**", mention_author=False)


@bot.command(name="상환")
async def repay_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    loans = await read_json(LOAN_PATH, _default_loan())
    owed = int(loans.get(str(ctx.author.id), 0))
    if owed <= 0:
        await ctx.reply("대출 없음", mention_author=False)
        return
    repay = int(owed * 1.1)
    money = await get_money(ctx.author.id)
    if money < repay:
        await ctx.reply(f"상환 부족! 필요 **{_fmt_money(repay)}**", mention_author=False)
        return
    await add_money(ctx.author.id, -repay)
    def mut(d):
        d = dict(d or {})
        d.pop(str(ctx.author.id), None)
        return d
    await update_json(LOAN_PATH, _default_loan(), mut)
    await ctx.reply(f"✅ 대출 상환 완료! **{_fmt_money(repay)}**", mention_author=False)


async def _consume_common_fish(user_id: int, count: int) -> bool:
    inv = await get_inventory(user_id)
    keys = [k for k, v in inv.items() if k in FISH_BY_ID and FISH_BY_ID[k].rarity == "common" and v > 0]
    total = sum(inv.get(k, 0) for k in keys)
    if total < count:
        return False
    left = count
    for k in keys:
        if left <= 0:
            break
        take = min(left, int(inv.get(k, 0)))
        await add_fish(user_id, k, -take)
        left -= take
    return left <= 0


@bot.command(name="행운판")
async def daily_wheel_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    today = _today_key_utc()
    uid = str(ctx.author.id)
    fun = await read_json(FUN_PATH, _default_fun())
    u = dict((fun or {}).get(uid) or {})
    if u.get("wheel_day") == today:
        await ctx.reply("오늘은 이미 행운판을 돌렸어! 내일 다시 와.", mention_author=False)
        return

    roll = roll_daily_wheel()
    reward_txt = await _grant_wheel_reward(ctx.author.id, roll)

    def mut(d):
        d = dict(d or {})
        u2 = dict(d.get(uid) or {})
        u2["wheel_day"] = today
        d[uid] = u2
        return d

    await update_json(FUN_PATH, _default_fun(), mut)
    bal = await get_money(ctx.author.id)
    await ctx.reply(
        f"🎡 **무료 행운판** 결과!\n- {reward_txt}\n- 잔액: **{_fmt_money(bal)}**",
        mention_author=False,
    )


@bot.command(name="펫")
async def pet_info_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    rec = await get_pet_record(ctx.author.id)
    if not rec:
        lines = ["**🐾 펫 시스템**\n아직 펫이 없어! `!펫데려오기`로 입양해줘.\n"]
        for pid, info in PETS.items():
            lines.append(f"- `{pid}`: {info['name']} — {info['desc']}")
        await ctx.reply("\n".join(lines), mention_author=False)
        return
    pid = rec["pet_id"]
    info = PETS.get(pid, {"name": "펫", "emoji": "🐾"})
    xp = int(rec.get("xp", 0))
    lv, cur, need = pet_level_progress(xp)
    bonuses = await get_pet_bonuses(ctx.author.id)
    nick = rec.get("name") or info["name"]
    await ctx.reply(
        f"{info.get('emoji', '🐾')} **{nick}** (Lv.**{lv}** / MAX {PET_MAX_LEVEL})\n"
        f"- 경험치: **{cur}/{need if need else 'MAX'}**\n"
        f"- 효과: 희귀↑ **+{int(bonuses['rarity']*100)}%** / 이색↑ **+{int(bonuses['shiny']*100)}%p**\n"
        f"- `!펫밥` 으로 성장 (`!펫이름 <이름>` 변경)",
        mention_author=False,
    )


@bot.command(name="펫데려오기")
async def pet_adopt_cmd(ctx: commands.Context, pet_id: str | None = None):
    if not _channel_allowed(ctx):
        return
    if await get_pet_record(ctx.author.id):
        await ctx.reply("이미 펫이 있어! `!펫`으로 확인해줘.", mention_author=False)
        return
    if pet_id:
        pet_id = pet_id.strip().lower()
        if pet_id not in PETS:
            await ctx.reply(
                f"없는 펫 ID야. 목록: {', '.join(f'`{k}`' for k in PETS)}",
                mention_author=False,
            )
            return
    else:
        pet_id = random.choice(list(PETS.keys()))
    info = PETS[pet_id]
    await save_pet_record(
        ctx.author.id,
        {"pet_id": pet_id, "xp": 0, "name": info["name"]},
    )
    await ctx.reply(
        f"🎉 **{info['name']}** 입양 완료!\n{info['desc']}\n낚시할 때 옆에서 도와줄 거야.",
        mention_author=False,
    )


@bot.command(name="펫밥")
async def pet_feed_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    rec = await get_pet_record(ctx.author.id)
    if not rec:
        await ctx.reply("펫이 없어! `!펫데려오기` 먼저.", mention_author=False)
        return
    xp = int(rec.get("xp", 0))
    lv = pet_xp_to_level(xp)
    if lv >= PET_MAX_LEVEL:
        await ctx.reply("이미 최대 레벨이야!", mention_author=False)
        return

    fed = False
    if await _consume_common_fish(ctx.author.id, PET_FEED_FISH_COMMON):
        fed = True
    else:
        money = await get_money(ctx.author.id)
        if money >= PET_FEED_COST:
            await add_money(ctx.author.id, -PET_FEED_COST)
            fed = True
        else:
            await ctx.reply(
                f"밥 재료 부족!\n- 일반 물고기 **{PET_FEED_FISH_COMMON}마리** 또는\n"
                f"- **{_fmt_money(PET_FEED_COST)}** 필요",
                mention_author=False,
            )
            return

    rec["xp"] = xp + PET_XP_PER_FEED
    await save_pet_record(ctx.author.id, rec)
    new_lv = pet_xp_to_level(int(rec["xp"]))
    lvup = " 🎊 **레벨 업!**" if new_lv > lv else ""
    await ctx.reply(
        f"🍽️ 맛있게 먹었어! (+{PET_XP_PER_FEED} XP){lvup}\n`!펫`으로 성장 확인",
        mention_author=False,
    )


@bot.command(name="펫이름")
async def pet_name_cmd(ctx: commands.Context, *, nickname: str | None = None):
    if not _channel_allowed(ctx):
        return
    rec = await get_pet_record(ctx.author.id)
    if not rec:
        await ctx.reply("펫이 없어!", mention_author=False)
        return
    if not nickname or len(nickname.strip()) < 1:
        await ctx.reply("사용법: `!펫이름 바다친구`", mention_author=False)
        return
    nickname = nickname.strip()[:12]
    rec["name"] = nickname
    await save_pet_record(ctx.author.id, rec)
    await ctx.reply(f"이제부터 **{nickname}**(이)라고 불러줄게!", mention_author=False)


@bot.command(name="토너먼트")
async def tournament_info_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    active = is_tournament_active()
    prof = await get_profile(ctx.author.id)
    tk = tournament_weekend_key()
    score = int(prof.get("tourney_score", 0)) if prof.get("tourney_key") == tk else 0
    status = "🔥 **진행 중!**" if active else "⏸️ 지금은 휴식 (금~일 오픈)"
    prize_lines = "\n".join(f"  {rank}위: {_fmt_money(amt)}" for rank, amt in TOURNAMENT_PRIZES)
    await ctx.reply(
        f"🏆 **주말 낚시 토너먼트** ({tk})\n"
        f"- 상태: {status}\n"
        f"- 내 점수: **{score}점**\n"
        f"- 점수: 일반5 / 희귀15 / 영웅40 / 전설120 / 신화350 (이색 x1.5)\n"
        f"- 시상 (참고): \n{prize_lines}\n"
        f"- `!토너랭킹` 순위 확인",
        mention_author=False,
    )


@bot.command(name="토너랭킹")
async def tournament_rank_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    tk = tournament_weekend_key()
    all_p = await read_json(PROFILE_PATH, _default_profile())
    items = []
    for uid, p in (all_p or {}).items():
        if (p or {}).get("tourney_key") == tk:
            try:
                items.append((int(uid), int(p.get("tourney_score", 0))))
            except Exception:
                pass
    items.sort(key=lambda x: x[1], reverse=True)
    lines = [f"**🏆 토너먼트 랭킹** ({tk})"]
    for i, (uid, sc) in enumerate(items[:10], 1):
        lines.append(f"{i}. **{_display_name(ctx, uid)}** — **{sc}점**")
    if len(items) <= 10:
        pass
    else:
        lines.append(f"... 외 {len(items)-10}명")
    await ctx.reply("\n".join(lines) if items else "아직 점수 없음! 금~일에 `!낚시`로 점수를 모아봐.", mention_author=False)


@bot.command(name="물고기퀴즈")
async def fish_quiz_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    uid = ctx.author.id
    now = utc_ts()
    if uid in QUIZ_PENDING and int(QUIZ_PENDING[uid].get("until", 0)) > now:
        await ctx.reply("`!퀴즈정답 <번호>` 로 답해줘!", mention_author=False)
        return

    fun = await read_json(FUN_PATH, _default_fun())
    u = dict((fun or {}).get(str(uid)) or {})
    last_q = int(u.get("quiz_last", 0))
    if now - last_q < QUIZ_COOLDOWN_SEC:
        wait = QUIZ_COOLDOWN_SEC - (now - last_q)
        await ctx.reply(f"퀴즈 쿨타임! **{wait}초** 후 다시.", mention_author=False)
        return

    correct = pick_quiz_fish(FISH_TABLE)
    choices = build_quiz_choices(correct, FISH_TABLE, 4)
    answer_idx = next(i for i, c in enumerate(choices) if c["id"] == correct["id"]) + 1

    QUIZ_PENDING[uid] = {
        "until": now + 90,
        "answer": answer_idx,
        "choices": [c["name"] for c in choices],
    }

    lines = [
        f"❓ **물고기 퀴즈!** (힌트: **{RARITY_LABEL.get(correct['rarity'], correct['rarity'])}** 등급)",
        "이름을 맞춰봐!",
    ]
    for i, c in enumerate(choices, 1):
        lines.append(f"**{i}.** {c['name']}")
    lines.append("\n`!퀴즈정답 <번호>` (90초)")
    await ctx.reply("\n".join(lines), mention_author=False)


@bot.command(name="퀴즈정답")
async def fish_quiz_answer_cmd(ctx: commands.Context, num_raw: str | None = None):
    if not _channel_allowed(ctx):
        return
    uid = ctx.author.id
    pending = QUIZ_PENDING.get(uid)
    if not pending or utc_ts() > int(pending.get("until", 0)):
        QUIZ_PENDING.pop(uid, None)
        await ctx.reply("진행 중인 퀴즈가 없어. `!물고기퀴즈`로 시작!", mention_author=False)
        return
    if not num_raw or not num_raw.strip().isdigit():
        await ctx.reply("사용법: `!퀴즈정답 <번호>`", mention_author=False)
        return
    pick = int(num_raw.strip())
    correct = int(pending["answer"])
    QUIZ_PENDING.pop(uid, None)

    def mut_fun(d):
        d = dict(d or {})
        u = dict(d.get(str(uid)) or {})
        u["quiz_last"] = utc_ts()
        d[str(uid)] = u
        return d

    await update_json(FUN_PATH, _default_fun(), mut_fun)

    if pick == correct:
        reward = random.randint(QUIZ_REWARD_MIN, QUIZ_REWARD_MAX)
        bal = await add_money(uid, reward)
        await ctx.reply(
            f"✅ **정답!** ({pending['choices'][correct-1]})\n"
            f"보상 **{_fmt_money(reward)}** / 잔액 **{_fmt_money(bal)}**",
            mention_author=False,
        )
    else:
        await ctx.reply(
            f"❌ 틀렸어! 정답은 **{correct}번** {pending['choices'][correct-1]}",
            mention_author=False,
        )


def _default_stock_portfolio() -> Dict[str, dict]:
    return {}


async def _ensure_stock_market() -> dict:
    m = await read_json(STOCK_MARKET_PATH, default_market())
    if not m.get("prices") or len(m.get("prices", {})) < len(STOCKS):
        m = default_market()
        m["last_tick"] = utc_ts()
        await write_json(STOCK_MARKET_PATH, m)
    return m


async def _get_stock_market() -> dict:
    return await _ensure_stock_market()


async def _tick_stock_market() -> None:
    m = await _get_stock_market()
    prices = dict(m.get("prices") or {})
    prev = dict(m.get("prev") or prices)
    new_prices, new_prev = tick_market(prices, prev)
    await write_json(
        STOCK_MARKET_PATH,
        {
            "prices": new_prices,
            "prev": new_prev,
            "last_tick": utc_ts(),
        },
    )


def _default_stock_news() -> dict:
    return {"by_day": {}, "last_news": None}


async def _apply_stock_news(news: dict) -> tuple[int, int]:
    m = await _get_stock_market()
    prices = dict(m.get("prices") or {})
    prev = dict(m.get("prev") or prices)
    sid = news["stock_id"]
    new_prices, new_prev, old_p, new_p = apply_news_shock(
        prices, prev, sid, float(news["change"])
    )
    await write_json(
        STOCK_MARKET_PATH,
        {
            "prices": new_prices,
            "prev": new_prev,
            "last_tick": utc_ts(),
        },
    )
    return old_p, new_p


async def _broadcast_stock_news() -> str:
    news = roll_stock_news()
    old_p, new_p = await _apply_stock_news(news)
    msg = format_news_broadcast(news, old_p, new_p)

    def mut(state):
        state = dict(state or {})
        day = kst_today_key()
        by_day = dict(state.get("by_day") or {})
        fired = list(by_day.get(day) or [])
        news_record = {**news, "old_price": old_p, "new_price": new_p}
        state["last_news"] = news_record
        state["history"] = ([news_record] + list(state.get("history") or []))[:20]
        return state

    await update_json(STOCK_NEWS_PATH, _default_stock_news(), mut)

    ch_id = _env_int("ANNOUNCE_CHANNEL_ID")
    if ch_id:
        ch = bot.get_channel(ch_id)
        if ch:
            try:
                await ch.send(msg)
            except Exception:
                pass
    return msg


async def _maybe_broadcast_stock_news() -> None:
    now = kst_now()
    day = kst_today_key()
    hour = now.hour

    slot = None
    for nh in NEWS_HOURS_KST:
        if hour == nh:
            slot = nh
            break
    if slot is None:
        return

    state = await read_json(STOCK_NEWS_PATH, _default_stock_news())
    by_day = dict(state.get("by_day") or {})
    fired = list(by_day.get(day) or [])
    if slot in fired:
        return

    await _broadcast_stock_news()

    def mut(s):
        s = dict(s or {})
        bd = dict(s.get("by_day") or {})
        lst = list(bd.get(day) or [])
        if slot not in lst:
            lst.append(slot)
        bd[day] = lst
        s["by_day"] = bd
        return s

    await update_json(STOCK_NEWS_PATH, _default_stock_news(), mut)


async def _get_user_portfolio(user_id: int) -> Dict[str, dict]:
    all_p = await read_json(STOCK_PORTFOLIO_PATH, _default_stock_portfolio())
    raw = dict((all_p or {}).get(str(user_id)) or {})
    out: Dict[str, dict] = {}
    for k, v in raw.items():
        h = normalize_holding(v)
        if h["qty"] > 0:
            out[str(k)] = h
    return out


async def _set_user_portfolio(user_id: int, holdings: Dict[str, dict]) -> None:
    def mut(d):
        d = dict(d or {})
        cleaned = {}
        for k, v in holdings.items():
            h = normalize_holding(v)
            if h["qty"] > 0:
                cleaned[k] = h
        if cleaned:
            d[str(user_id)] = cleaned
        else:
            d.pop(str(user_id), None)
        return d

    await update_json(STOCK_PORTFOLIO_PATH, _default_stock_portfolio(), mut)


def _portfolio_add_buy(port: Dict[str, dict], stock_id: str, qty: int, price: int) -> dict:
    h = normalize_holding(port.get(stock_id))
    h["qty"] += int(qty)
    h["cost_total"] += int(price) * int(qty)
    port[stock_id] = h
    return h


def _portfolio_remove_sell(port: Dict[str, dict], stock_id: str, qty: int) -> tuple[dict, int]:
    """반환: (남은 포지션, 매도분 매입원가)"""
    h = normalize_holding(port.get(stock_id))
    if h["qty"] <= 0:
        return h, 0
    avg = holding_avg_price(h) or 0
    if avg > 0:
        cost_sold = int(avg * qty)
    elif h["cost_total"] > 0:
        cost_sold = int(h["cost_total"] * qty / h["qty"])
    else:
        cost_sold = 0
    h["qty"] -= qty
    h["cost_total"] = max(0, h["cost_total"] - cost_sold)
    if h["qty"] <= 0:
        port.pop(stock_id, None)
        return {"qty": 0, "cost_total": 0}, cost_sold
    port[stock_id] = h
    return h, cost_sold


def _stock_price(market: dict, stock_id: str) -> tuple[int, int]:
    prices = market.get("prices") or {}
    prev = market.get("prev") or {}
    cur = int(prices.get(stock_id, STOCKS[stock_id]["base_price"]))
    old = int(prev.get(stock_id, cur))
    return cur, old


@bot.command(name="주식속보")
async def stock_news_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    state = await read_json(STOCK_NEWS_PATH, _default_stock_news())
    last = state.get("last_news")
    if not last:
        await ctx.reply(
            f"아직 속보가 없어. **KST {NEWS_HOURS_KST[0]}시·{NEWS_HOURS_KST[1]}시**에 "
            f"[속보]가 공지 채널에 올라와!",
            mention_author=False,
        )
        return
    old_p = int(last.get("old_price", 0))
    new_p = int(last.get("new_price", 0))
    await ctx.reply(format_news_broadcast(last, old_p, new_p), mention_author=False)


@bot.command(name="주식목록", aliases=["주식"])
async def stock_list_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    market = await _get_stock_market()
    state = await read_json(STOCK_NEWS_PATH, _default_stock_news())
    last = state.get("last_news")
    last_tick = int(market.get("last_tick", 0))
    wait = seconds_until_next_tick(last_tick)
    wait_txt = "곧 변동" if wait <= 0 else f"다음 변동 **{wait // 60}분 {wait % 60}초** 후"
    lines = [
        f"**📈 콩 주식거래소** — 시세는 **정확히 {STOCK_TICK_SECONDS // 60}분마다 1회** 변동 ({wait_txt})\n"
    ]
    if last:
        tag = last.get("tag", "")
        comp = last.get("company", "")
        lines.append(f"📰 최근 속보: **{tag}** — **{comp}** (`!주식속보`)\n")
    for sid in STOCKS:
        cur, prev = _stock_price(market, sid)
        lines.append(stock_line(sid, cur, prev))
    lines.append(
        "\n💡 `!주식매수 머래 5` · `!주식매도 MRRX all` · `!주식매도 전체`"
    )
    await ctx.reply("\n".join(lines), mention_author=False)


@bot.command(name="주식시세")
async def stock_quote_cmd(ctx: commands.Context, *, query: str | None = None):
    if not _channel_allowed(ctx):
        return
    if not query:
        await ctx.reply(
            "사용법: `!주식시세 <종목>` (예: `!주식시세 머래제약` · `!주식시세 EVNG`)",
            mention_author=False,
        )
        return
    sid = resolve_stock(query.split()[0] if query else "")
    if not sid:
        await ctx.reply("종목을 찾을 수 없어. `!주식목록`을 확인해줘.", mention_author=False)
        return
    market = await _get_stock_market()
    cur, prev = _stock_price(market, sid)
    s = STOCKS[sid]
    holdings = await _get_user_portfolio(ctx.author.id)
    pos = holdings.get(sid)
    stats = holding_stats(cur, pos) if pos else None
    my_block = "보유 없음"
    if stats:
        my_block = format_holding_detail(stats, cur)
    await ctx.reply(
        f"**{s['company']}** (`{s['ticker']}`)\n"
        f"- 대표 브랜드: **{s['nick']}**\n"
        f"- 현재가: **{cur:,}원**/주 {format_change(cur, prev)}\n"
        f"- 직전가: **{prev:,}원**\n"
        f"- 기준가(참고): **{int(s['base_price']):,}원**\n"
        f"\n**📌 내 포지션**\n{my_block}",
        mention_author=False,
    )


@bot.command(name="주식매수")
async def stock_buy_cmd(ctx: commands.Context, query: str | None = None, qty_raw: str | None = None):
    if not _channel_allowed(ctx):
        return
    if query and query.strip().lower() in ("all", "전체", "전부", "일괄", "풀매수"):
        await _stock_buy_all(ctx)
        return
    if not query or not qty_raw:
        await ctx.reply(
            "사용법: `!주식매수 <종목> <수량>`\n"
            "예: `!주식매수 머래제약 10` · `!주식매수 밈콩 3` · `!주식매수 all`",
            mention_author=False,
        )
        return
    sid = resolve_stock(query)
    if not sid:
        await ctx.reply("종목을 찾을 수 없어. `!주식목록` 참고!", mention_author=False)
        return
    if not qty_raw.isdigit():
        await ctx.reply("수량은 숫자로 입력해줘.", mention_author=False)
        return
    qty = int(qty_raw)
    if qty <= 0:
        await ctx.reply("수량은 1주 이상으로 입력해줘.", mention_author=False)
        return

    market = await _get_stock_market()
    price, _ = _stock_price(market, sid)
    total = price * qty
    money = await get_money(ctx.author.id)
    if money < total:
        await ctx.reply(
            f"돈이 부족해!\n"
            f"- 필요: **{_fmt_money(total)}** ({price:,}원 x {qty}주)\n"
            f"- 보유: **{_fmt_money(money)}**",
            mention_author=False,
        )
        return

    await add_money(ctx.author.id, -total)
    port = await _get_user_portfolio(ctx.author.id)
    h = _portfolio_add_buy(port, sid, qty, price)
    await _set_user_portfolio(ctx.author.id, port)
    bal = await get_money(ctx.author.id)
    s = STOCKS[sid]
    avg = holding_avg_price(h)
    st = holding_stats(price, h)
    pl_hint = f"\n- **평균 매수가 {avg:,}원/주** (매입 총 **{h['cost_total']:,}원**)"
    if st and st.get("pl") is not None and st["pl"] != 0:
        pl_hint += f"\n- 현재가 기준: {format_holding_pl(st)}"
    await ctx.reply(
        f"✅ **매수 체결**\n"
        f"- 종목: **{s['company']}** (`{s['ticker']}`)\n"
        f"- 이번 체결가: **{price:,}원** x **{qty}주** = **{_fmt_money(total)}**\n"
        f"- 보유: **{h['qty']}주**{pl_hint}\n"
        f"- 잔액: **{_fmt_money(bal)}**",
        mention_author=False,
    )


@bot.command(name="주식매도", aliases=["주식일괄매도"])
async def stock_sell_cmd(ctx: commands.Context, query: str | None = None, qty_raw: str | None = None):
    if not _channel_allowed(ctx):
        return
    if not query:
        await ctx.reply(
            "사용법:\n"
            "- `!주식매도 <종목> <수량>` (수량 `all` 가능)\n"
            "- `!주식매도 전체` / `!주식매도 all` 보유 주식 **전량 매도**",
            mention_author=False,
        )
        return

    qnorm = query.strip().lower().replace(" ", "")
    if qnorm in ("전체", "all", "일괄", "전량", "풀매도") and (
        not qty_raw or qty_raw.strip().lower() in ("", "all", "전체")
    ):
        await _stock_sell_all(ctx)
        return

    if not qty_raw:
        await ctx.reply(
            "수량을 입력해줘.\n"
            "예: `!주식매도 MRRX 5` · `!주식매도 머래제약 all` · `!주식매도 전체`",
            mention_author=False,
        )
        return

    sid = resolve_stock(query)
    if not sid:
        await ctx.reply("종목을 찾을 수 없어.", mention_author=False)
        return

    port = await _get_user_portfolio(ctx.author.id)
    have = int(normalize_holding(port.get(sid)).get("qty", 0))
    if have <= 0:
        await ctx.reply("그 주식은 보유하고 있지 않아.", mention_author=False)
        return

    if qty_raw.strip().lower() == "all":
        qty = have
    elif qty_raw.isdigit():
        qty = int(qty_raw)
    else:
        await ctx.reply("수량은 숫자 또는 `all`", mention_author=False)
        return

    if qty <= 0:
        await ctx.reply(f"수량은 1주 이상으로 입력해줘. (보유 {have}주)", mention_author=False)
        return
    if qty > have:
        await ctx.reply(f"보유 주식이 부족해! (보유 **{have}주**)", mention_author=False)
        return

    market = await _get_stock_market()
    price, _ = _stock_price(market, sid)
    total = price * qty
    _, cost_sold = _portfolio_remove_sell(port, sid, qty)
    realized = total - cost_sold
    await add_money(ctx.author.id, total)
    await _set_user_portfolio(ctx.author.id, port)
    bal = await get_money(ctx.author.id)
    s = STOCKS[sid]
    left = int(normalize_holding(port.get(sid, {})).get("qty", 0))
    pl_line = ""
    if cost_sold > 0:
        pct = realized / cost_sold * 100 if cost_sold else 0
        icon = "🟢" if realized > 0 else ("🔴" if realized < 0 else "⚪")
        pl_line = (
            f"\n- 실현 손익: {icon} **{format_signed_money(realized)}** ({pct:+.2f}%)\n"
            f"  (매입원가 **{cost_sold:,}원** → 매도 **{total:,}원**)"
        )
    await ctx.reply(
        f"✅ **매도 체결**\n"
        f"- 종목: **{s['company']}** (`{s['ticker']}`)\n"
        f"- 체결가: **{price:,}원** x **{qty}주** = **{_fmt_money(total)}**{pl_line}\n"
        f"- 남은 보유: **{left}주** / 잔액: **{_fmt_money(bal)}**",
        mention_author=False,
    )


@bot.command(name="주식보유", aliases=["내주식"])
async def stock_portfolio_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    port = await _get_user_portfolio(ctx.author.id)
    if not port:
        await ctx.reply(
            "보유 주식이 없어. `!주식목록` 보고 `!주식매수`로 사봐!",
            mention_author=False,
        )
        return
    market = await _get_stock_market()
    lines = [f"**💼 {ctx.author.display_name}** 주식 포트폴리오\n"]
    total_val = 0
    total_cost = 0
    total_pl = 0
    has_cost = False
    rows = []
    for sid, pos in port.items():
        if sid not in STOCKS:
            continue
        cur, prev = _stock_price(market, sid)
        stats = holding_stats(cur, pos)
        if not stats:
            continue
        rows.append((stats["value"], sid, pos, cur, prev, stats))
    rows.sort(key=lambda r: r[0], reverse=True)

    for _val, sid, pos, cur, prev, stats in rows:
        total_val += stats["value"]
        s = STOCKS[sid]
        lines.append(
            f"**{s['company']}** `{s['ticker']}` · 시세 {cur:,}원 {format_change(cur, prev)}"
        )
        lines.append(format_holding_detail(stats, cur))
        lines.append("")
        if stats.get("pl") is not None:
            has_cost = True
            total_cost += stats["cost_total"]
            total_pl += stats["pl"]
    cash = await get_money(ctx.author.id)
    lines.append(f"📊 **주식 평가 합계: {_fmt_money(total_val)}**")
    if has_cost:
        total_pct = (total_pl / total_cost * 100) if total_cost > 0 else 0
        icon = "🟢" if total_pl > 0 else ("🔴" if total_pl < 0 else "⚪")
        lines.append(
            f"{icon} **총 평가손익: {format_signed_money(total_pl)}** ({total_pct:+.2f}%)\n"
            f"   (매입 **{total_cost:,}원** → 평가 **{total_val:,}원**)"
        )
    else:
        lines.append("📋 평균 매수가 미기록 종목 있음 → 추가 매수 후 손익 표시")
    lines.append(f"💰 현금 **{_fmt_money(cash)}** · 총자산 **{_fmt_money(total_val + cash)}**")
    await ctx.reply("\n".join(lines), mention_author=False)


def _default_estate() -> Dict[str, dict]:
    return {}


async def _get_user_estates(user_id: int) -> Dict[str, dict]:
    all_e = await read_json(ESTATE_PATH, _default_estate())
    raw = dict((all_e or {}).get(str(user_id)) or {})
    out: Dict[str, dict] = {}
    for eid, rec in raw.items():
        if eid in ESTATE_CATALOG and isinstance(rec, dict):
            out[eid] = rec
    return out


async def _save_user_estates(user_id: int, owned: Dict[str, dict]) -> None:
    def mut(d):
        d = dict(d or {})
        if owned:
            d[str(user_id)] = owned
        else:
            d.pop(str(user_id), None)
        return d

    await update_json(ESTATE_PATH, _default_estate(), mut)


@bot.command(name="부동산")
async def estate_list_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    lines = [
        "**🏘️ 한국 지역 부동산 매물** (가격 1억 ~ 20억)\n"
        "구매 후 **1시간마다** 월세가 쌓여요. `!월세수령`으로 받기\n",
    ]
    for eid in ESTATE_CATALOG:
        lines.append(estate_list_line(eid))
    await _reply_long(ctx, lines)


@bot.command(name="부동산구매")
async def estate_buy_cmd(ctx: commands.Context, *, query: str | None = None):
    if not _channel_allowed(ctx):
        return
    if not query:
        await ctx.reply("사용법: `!부동산구매 <매물ID|이름>` (예: `!부동산구매 est_jeju_pension`)", mention_author=False)
        return
    eid = resolve_estate(query.strip().split()[0])
    if not eid:
        await ctx.reply("매물을 찾을 수 없어. `!부동산` 목록 확인!", mention_author=False)
        return
    estate = ESTATE_CATALOG[eid]
    owned = await _get_user_estates(ctx.author.id)
    if eid in owned:
        await ctx.reply("이미 보유 중인 매물이야.", mention_author=False)
        return
    price = int(estate["price"])
    money = await get_money(ctx.author.id)
    if money < price:
        await ctx.reply(
            f"돈이 부족해!\n필요: **{fmt_estate_price(price)}** / 보유: **{_fmt_money(money)}**",
            mention_author=False,
        )
        return
    now = utc_ts()
    await add_money(ctx.author.id, -price)
    owned[eid] = {"bought_at": now, "last_rent": now}
    await _save_user_estates(ctx.author.id, owned)
    bal = await get_money(ctx.author.id)
    await ctx.reply(
        f"🎉 **{estate['emoji']} {estate['name']}** 매입 완료!\n"
        f"- 지역: **{estate['region']}**\n"
        f"- 가격: **{fmt_estate_price(price)}**\n"
        f"- 시간당 월세: **{int(estate['rent_amount']):,}원** (`!월세수령`)\n"
        f"- 잔액: **{_fmt_money(bal)}**",
        mention_author=False,
    )


@bot.command(name="부동산보유", aliases=["내부동산"])
async def estate_owned_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    owned = await _get_user_estates(ctx.author.id)
    if not owned:
        await ctx.reply("보유 부동산이 없어. `!부동산`에서 매물을 확인해줘.", mention_author=False)
        return
    now = utc_ts()
    lines = [f"**🏘️ {ctx.author.display_name}** 보유 부동산\n"]
    total_pending = 0
    for eid, rec in owned.items():
        e = ESTATE_CATALOG[eid]
        amt, ticks, wait = pending_rent(rec, e, now)
        total_pending += amt
        tick_txt = f"수령 가능 **{_fmt_money(amt)}** ({ticks}회분)" if ticks > 0 else f"다음 월세 **{wait // 60}분 {wait % 60}초** 후"
        lines.append(
            f"{e['emoji']} **{e['name']}** ({e['region']})\n"
            f"  └ 매입 **{fmt_estate_price(e['price'])}** · 시세 월세 **{e['rent_amount']:,}원/h**\n"
            f"  └ {tick_txt}"
        )
    lines.append(f"\n💰 미수령 월세 합계: **{_fmt_money(total_pending)}** → `!월세수령`")
    await _reply_long(ctx, lines)


@bot.command(name="월세수령")
async def estate_collect_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    owned = await _get_user_estates(ctx.author.id)
    if not owned:
        await ctx.reply("보유 부동산이 없어.", mention_author=False)
        return
    now = utc_ts()
    total = 0
    details = []
    for eid, rec in list(owned.items()):
        e = ESTATE_CATALOG[eid]
        amt, ticks, _ = pending_rent(rec, e, now)
        if ticks <= 0:
            continue
        cycle = int(e["rent_cycle_sec"])
        rec["last_rent"] = int(rec.get("last_rent", rec.get("bought_at", now))) + ticks * cycle
        owned[eid] = rec
        total += amt
        details.append(f"- {e['name']}: **{_fmt_money(amt)}** ({ticks}시간분)")

    if total <= 0:
        await ctx.reply(
            "아직 수령할 월세가 없어.\n`!부동산보유`로 다음 지급 시간을 확인해줘.",
            mention_author=False,
        )
        return

    await _save_user_estates(ctx.author.id, owned)
    bal = await add_money(ctx.author.id, total)
    await ctx.reply(
        f"💵 **월세 수령 완료!** 합계 **{_fmt_money(total)}**\n"
        + "\n".join(details[:15])
        + (f"\n...외 {len(details)-15}건" if len(details) > 15 else "")
        + f"\n잔액: **{_fmt_money(bal)}**",
        mention_author=False,
    )


@bot.command(name="부동산매도")
async def estate_sell_cmd(ctx: commands.Context, *, query: str | None = None):
    if not _channel_allowed(ctx):
        return
    if not query:
        await ctx.reply("사용법: `!부동산매도 <매물ID>`", mention_author=False)
        return
    eid = resolve_estate(query.strip().split()[0])
    if not eid:
        await ctx.reply("매물을 찾을 수 없어.", mention_author=False)
        return
    owned = await _get_user_estates(ctx.author.id)
    if eid not in owned:
        await ctx.reply("그 매물을 보유하고 있지 않아.", mention_author=False)
        return
    estate = ESTATE_CATALOG[eid]
    rec = owned[eid]
    now = utc_ts()
    rent, ticks, _ = pending_rent(rec, estate, now)
    if ticks > 0:
        cycle = int(estate["rent_cycle_sec"])
        rec["last_rent"] = int(rec.get("last_rent", now)) + ticks * cycle
        await add_money(ctx.author.id, rent)

    payout = int(int(estate["price"]) * SELL_BACK_RATE)
    del owned[eid]
    await _save_user_estates(ctx.author.id, owned)
    bal = await add_money(ctx.author.id, payout)
    extra = f"\n- 미수령 월세 **{_fmt_money(rent)}** 포함" if rent > 0 else ""
    await ctx.reply(
        f"🏷️ **{estate['name']}** 매도 완료\n"
        f"- 환급 (**{int(SELL_BACK_RATE*100)}%**): **{_fmt_money(payout)}**{extra}\n"
        f"- 잔액: **{_fmt_money(bal)}**",
        mention_author=False,
    )


def main() -> None:
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise SystemExit("DISCORD_TOKEN이 없습니다. .env 파일에 DISCORD_TOKEN=... 을 넣어주세요.")
    bot.run(token)


if __name__ == "__main__":
    main()
