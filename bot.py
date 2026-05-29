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
    BOSS_ROTATION,
    RARITY_LABEL,
    boss_spawn,
    choose_fish,
    choose_rarity,
    format_fish_catch,
    format_rod_name,
    get_base_cooldown_seconds,
    get_rarity_weights,
    upgrade_cost,
    upgrade_try,
    upgrade_success_rate,
    upgrade_penalty_check,
)
from utils.jsondb import ensure_dir, get_user_dict, read_json, update_json, utc_ts, write_json


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
MAP_PATH = DATA_DIR / "map.json"
BAIT_PATH = DATA_DIR / "active_bait.json"
COLLECTION_PATH = DATA_DIR / "collection.json"


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
        "exhausted": exhausted
    }


FISH_BY_ID = {f.id: f for f in FISH_TABLE}
FISH_BY_NAME = {f.name: f for f in FISH_TABLE}


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


async def get_rod(user_id: int) -> Tuple[str, int]:
    rods = await read_json(RODS_PATH, _default_rods())
    r = rods.get(str(user_id))
    if not isinstance(r, dict):
        return "rookie", 0
    rod_type = r.get("type", "rookie")
    level = int(r.get("level", 0))
    if rod_type not in RODS:
        rod_type = "rookie"
    return rod_type, max(0, level)


async def set_rod(user_id: int, rod_type: str, level: int) -> None:
    def mut(d):
        d = dict(d or {})
        d[str(user_id)] = {"type": rod_type, "level": int(level)}
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


async def get_inventory(user_id: int) -> Dict[str, int]:
    inv = await read_json(INV_PATH, _default_inventory())
    raw = inv.get(str(user_id), {})
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, int] = {}
    for k, v in raw.items():
        try:
            out[str(k)] = max(0, int(v))
        except Exception:
            continue
    return {k: v for k, v in out.items() if v > 0}


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

    return await update_json(CASINO_STATS_PATH, _default_casino_stats(), mut)


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
    if passive.get("type") == "cooldown_bonus":
        v = float(passive.get("value", 0.0))
        base = int(math.ceil(base * (1.0 - v)))
    return max(3, base)


def _boss_damage(rod_type: str, rod_level: int) -> tuple[int, bool, float]:
    base = random.randint(250, 550) + rod_level * random.randint(30, 55)
    passive = (RODS.get(rod_type) or RODS["rookie"])["passive"]
    if passive.get("type") == "boss_bonus":
        v = float(passive.get("value", 0.0))
        base = int(base * (1.0 + v))

    # 크리: 기본 7%, 강화레벨 10당 +1% (최대 15%)
    crit_rate = min(0.15, 0.07 + (rod_level // 10) * 0.01)
    crit_mult = 1.75
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
        bait_consumed = await consume_active_bait(user_id)
        active_bait_id = bait_consumed["bait_id"] if bait_consumed else None

        # 3. 희귀도 및 물고기 결정
        weights = get_rarity_weights(rod_level, rod_type, map_id, active_bait_id)
        rarity = choose_rarity(weights)
        fish = choose_fish(rarity)

        # 4. 저장 및 통계 갱신
        await set_last_fish_ts(user_id, now)
        await add_fish(user_id, fish.id, 1)
        await bump_stats(user_id, fish.rarity)
        
        # 도감 등록
        is_new = await add_to_collection(user_id, fish.id)

        # 5. 출력 포맷
        bait_txt = ""
        if bait_consumed:
            bait_name = bait_consumed["item_info"]["name"]
            if bait_consumed["exhausted"]:
                bait_txt = f"\n(소모: {bait_name} - ⚠️ **미끼를 모두 소모하여 장착 해제되었습니다!**)"
            else:
                bait_txt = f"\n(소모: {bait_name})"
                
        new_txt = ""
        if is_new:
            new_txt = f"\n🎉 **새로운 물고기 도감 등록!**"

        m_name = MAPS.get(map_id, MAPS["river"])["name"]
        try:
            await channel.send(f"🤖🎣 <@{user_id}> 자동낚시 ({m_name}){bait_txt}\n{format_fish_catch(fish)}{new_txt}")
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
    CASINO_MAX_BET = 250_000

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


async def _casino_fee(user_id: int, base_fee: float) -> float:
    disc = await _vip_discount_rate(user_id)
    return max(0.0, base_fee * (1.0 - disc))


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
        m = ctx.guild.get_member(uid) if ctx.guild else None
        name = m.display_name if m else f"유저({uid})"
        lines.append(f"{i}. **{name}** — **{_fmt_money(total)}**")

    lines.append("\n**최근 잭팟 5개**")
    for h in recent:
        uid = int(h.get("user_id"))
        amt = int(h.get("amount", 0))
        ts = int(h.get("ts", 0))
        m = ctx.guild.get_member(uid) if ctx.guild else None
        name = m.display_name if m else f"유저({uid})"
        lines.append(f"- **{name}**: {_fmt_money(amt)} (<t:{ts}:R>)")

    await ctx.reply("\n".join(lines), mention_author=False)


@bot.command(name="카지노")
async def casino_stats_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    all_stats = await read_json(CASINO_STATS_PATH, _default_casino_stats())
    s = (all_stats or {}).get(str(ctx.author.id)) or {}
    plays = int(s.get("plays", 0))
    bet = int(s.get("bet", 0))
    net = int(s.get("net", 0))
    win = int(s.get("win", 0))
    lose = int(s.get("lose", 0))
    streak = int(s.get("streak", 0))
    best = int(s.get("best_streak", 0))
    last_game = s.get("last_game", "-")
    await ctx.reply(
        f"🎲 **{ctx.author.display_name}** 카지노 기록\n"
        f"- 플레이: **{plays}회** (승 {win} / 패 {lose})\n"
        f"- 총 베팅: **{_fmt_money(bet)}**\n"
        f"- 누적 수익: **{_fmt_money(net)}**\n"
        f"- 연승: **{streak}** (최고 {best})\n"
        f"- 마지막 게임: **{last_game}**",
        mention_author=False,
    )


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
async def on_ready():
    ensure_dir(DATA_DIR)
    print(f"Logged in as {bot.user} (id={bot.user.id})")
    if not auto_fish_loop.is_running():
        auto_fish_loop.start()
    ch_id = _env_int("ANNOUNCE_CHANNEL_ID")
    if ch_id:
        ch = bot.get_channel(ch_id)
        if ch:
            try:
                await ch.send("낚시 RPG 봇 온라인!")
            except Exception:
                pass


@bot.command(name="도움말")
async def help_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    msg = (
        "**🎣 낚시 RPG 봇 명령어**\n"
        "- `!낚시` 낚시하기 (위치한 낚시터 및 장착 미끼 적용)\n"
        "- `!인벤` 내 인벤토리 보기 (물고기 / 소모품 / 위치 / 장착 미끼)\n"
        "- `!판매 <이름|all>` 물고기 판매 (도감 판매 보너스 적용)\n"
        "- `!도감` 물고기 도감 달성률 및 영구 도감 버프 보기\n"
        "- `!낚시대` 내 낚시대 정보 및 보유금 조회\n"
        "- `!강화` 낚시대 강화 (최대 +25강 / 등급 하락 페널티 및 보호 주문서 적용)\n"
        "- `!상점` 낚시대 상점 보기\n"
        "- `!아이템상점` 미끼 및 주문서 상점 보기\n"
        "- `!구매 <낚시대ID|아이템ID> [수량]` 낚시대 또는 아이템 구매\n"
        "- `!미끼장착 <미끼ID|off>` 미끼 장착 또는 장착 해제\n"
        "- `!낚시터` 이동 가능한 낚시터 목록 보기\n"
        "- `!이동 <낚시터ID>` 낚시터로 이동 (이동 비용 및 최소 강화 필요)\n"
        "- `!랭킹` 보유금 TOP 10 랭킹\n"
        "- `!낚시대랭킹` 낚시대 강화 TOP 10 랭킹\n"
        "- `!보스` 오늘의 요일 보스 상태 확인 및 스폰\n"
        "- `!보스공격` 보스에게 공격 가하기\n"
        "- `!자동낚시` 자동낚시 ON/OFF\n"
        "\n"
        "**🎲 카지노 명령어**\n"
        "- `!슬롯 <베팅>` 슬롯머신 돌리기\n"
        "- `!슬롯10 <베팅>` 슬롯 10회 연속 돌리기\n"
        "- `!주사위 <베팅>` 1~6 주사위 던지기\n"
        "- `!동전 <베팅> <앞|뒤>` 동전 뒤집기 베팅\n"
        "- `!잭팟` 현재 잭팟 누적 금액 확인\n"
        "- `!잭팟랭킹` 잭팟 명예의 전당 랭킹\n"
        "- `!카지노` 본인의 카지노 상세 기록\n"
    )
    await ctx.reply(msg, mention_author=False)


@bot.command(name="낚시대")
async def rod_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    rod_type, level = await get_rod(ctx.author.id)
    cd = _rod_cooldown_seconds(rod_type, level)
    await ctx.reply(
        f"**{ctx.author.display_name}**의 낚시대: **{format_rod_name(rod_type, level)}**\n"
        f"- 기본 쿨타임: **{cd}초**\n"
        f"- 보유금: **{_fmt_money(await get_money(ctx.author.id))}**",
        mention_author=False,
    )


@bot.command(name="상점")
async def shop_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    lines = ["**🎣 낚시대 상점** (구매: `!구매 <낚시대ID>`)\n"]
    for rod_id, info in RODS.items():
        price = int(info.get("price", 0))
        lines.append(f"- `{rod_id}`: **{info['name']}** / 가격: **{_fmt_money(price)}**")
    await ctx.reply("\n".join(lines), mention_author=False)


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
        cur_type, cur_level = await get_rod(ctx.author.id)
        if item_id == cur_type:
            await ctx.reply("이미 같은 낚시대를 사용 중이야.", mention_author=False)
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
        
        await ctx.reply(
            f"🛒 구매 완료! **{info['name']} x{amount}**을(를) 구매하여 인벤토리에 추가했습니다. (소모: {_fmt_money(total_price)})",
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
    
    lines = ["**🗺️ 낚시터 목록** (이동: `!이동 <낚시터ID>`)\n"]
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
        await ctx.reply(f"쿨타임이야. **{wait}초** 뒤에 다시 낚시 가능!", mention_author=False)
        return

    # 2. 맵 정보 및 미끼 소모
    map_id = await get_user_map(user_id)
    bait_consumed = await consume_active_bait(user_id)
    active_bait_id = bait_consumed["bait_id"] if bait_consumed else None

    # 3. 낚시 결과 결정
    weights = get_rarity_weights(rod_level, rod_type, map_id, active_bait_id)
    rarity = choose_rarity(weights)
    fish = choose_fish(rarity)

    # 4. 데이터 저장
    await set_last_fish_ts(user_id, now)
    await add_fish(user_id, fish.id, 1)
    await bump_stats(user_id, fish.rarity)
    
    # 도감 등록
    is_new = await add_to_collection(user_id, fish.id)

    # 5. 출력 메시지 포맷팅
    bait_txt = ""
    if bait_consumed:
        bait_name = bait_consumed["item_info"]["name"]
        if bait_consumed["exhausted"]:
            bait_txt = f"\n(소모: {bait_name} - ⚠️ **미끼를 모두 소모하여 장착 해제되었습니다!**)"
        else:
            bait_txt = f"\n(소모: {bait_name})"
            
    new_txt = ""
    if is_new:
        new_txt = f"\n🎉 **새로운 물고기 도감 등록!**"

    m_name = MAPS.get(map_id, MAPS["river"])["name"]
    await ctx.reply(
        f"**{ctx.author.display_name}** 낚시 성공! ({m_name}){bait_txt}\n"
        f"{format_fish_catch(fish)}{new_txt}",
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
    inv = await get_inventory(ctx.author.id)
    if not inv:
        await ctx.reply("인벤토리가 비었어. `!낚시`로 시작해봐.", mention_author=False)
        return

    fish_lines = []
    item_lines = []
    
    total_items = 0
    total_value = 0
    
    for item_key, cnt in sorted(inv.items(), key=lambda kv: (-kv[1], kv[0])):
        if item_key in FISH_BY_ID:
            fish = FISH_BY_ID[item_key]
            total_items += cnt
            total_value += fish.sell * cnt
            fish_lines.append(f"- {fish.name} x{cnt} (개당 {fish.sell}원)")
        elif item_key in ITEMS:
            info = ITEMS[item_key]
            item_lines.append(f"- {info['name']} x{cnt}")

    lines = [f"**🎒 {ctx.author.display_name}**의 인벤토리\n"]
    
    if fish_lines:
        lines.append("**🐟 물고기**")
        lines.extend(fish_lines)
        lines.append(f"합계: **{total_items}개** / 예상 판매가: **{_fmt_money(total_value)}**")
    else:
        lines.append("🐟 *물고기 보관함이 비어있습니다.*")
        
    if item_lines:
        lines.append("\n**📦 소모품**")
        lines.extend(item_lines)
        
    # 현재 장착 중인 미끼 표시
    bait = await get_user_bait(ctx.author.id)
    if bait:
        lines.append(f"\n🎣 **현재 장착 미끼**: {ITEMS[bait]['name']}")
        
    # 현재 위치한 낚시터 표시
    map_id = await get_user_map(ctx.author.id)
    lines.append(f"📍 **현재 위치**: {MAPS.get(map_id, MAPS['river'])['name']}")

    await ctx.reply("\n".join(lines), mention_author=False)


@bot.command(name="판매")
async def sell_cmd(ctx: commands.Context, *, target: str | None = None):
    if not _channel_allowed(ctx):
        return
    if not target:
        await ctx.reply("사용법: `!판매 <물고기이름|all>`", mention_author=False)
        return

    target = target.strip()
    inv = await get_inventory(ctx.author.id)
    if not inv:
        await ctx.reply("팔 게 없어. `!낚시`부터!", mention_author=False)
        return

    # 도감 완성 버프 (일반 도감 완성 시 판매가 5% 보너스)
    buffs = await get_collection_buffs(ctx.author.id)
    sell_mult = 1.0 + buffs.get("sell_bonus", 0.0)
    bonus_txt = " (도감 버프 +5% 적용)" if buffs.get("sell_bonus", 0.0) > 0 else ""

    if target.lower() == "all":
        total = 0
        for fish_id, cnt in inv.items():
            fish = FISH_BY_ID.get(fish_id)
            if fish:
                total += int(math.floor(fish.sell * cnt * sell_mult))
                
        if total <= 0:
            await ctx.reply("인벤토리에 판매 가능한 물고기가 없어.", mention_author=False)
            return

        def mut(d):
            d = dict(d or {})
            uinv = get_user_dict(d, ctx.author.id, {})
            # 일반 물고기 아이템만 삭제하고 소모품(미끼, 주문서 등)은 보존
            for key in list(uinv.keys()):
                if key in FISH_BY_ID:
                    uinv.pop(key, None)
            if not uinv:
                d.pop(str(ctx.author.id), None)
            return d

        await update_json(INV_PATH, _default_inventory(), mut)
        bal = await add_money(ctx.author.id, total)
        await ctx.reply(
            f"전부 판매 완료!{bonus_txt} 획득: **{_fmt_money(total)}** / 현재 잔액: **{_fmt_money(bal)}**",
            mention_author=False,
        )
        return

    fish = FISH_BY_NAME.get(target)
    if not fish:
        await ctx.reply("그 물고기는 몰라. 정확한 이름으로 다시 입력해줘.", mention_author=False)
        return

    cnt = int(inv.get(fish.id, 0))
    if cnt <= 0:
        await ctx.reply("그 물고기는 인벤에 없어.", mention_author=False)
        return

    value = int(math.floor(fish.sell * cnt * sell_mult))
    await add_fish(ctx.author.id, fish.id, -cnt)
    bal = await add_money(ctx.author.id, value)
    await ctx.reply(
        f"**{fish.name} x{cnt}** 판매 완료!{bonus_txt} 획득: **{_fmt_money(value)}** / 잔액: **{_fmt_money(bal)}**",
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
    
    if level >= 25:
        await ctx.reply("이미 최고 강화 레벨(+25)에 도달하여 더 이상 강화할 수 없습니다!", mention_author=False)
        return

    cost = upgrade_cost(level)
    
    # 도감 완성 버프 (영웅 도감 완성 시 강화 성공 확률 +3% 절대값 추가)
    buffs = await get_collection_buffs(ctx.author.id)
    chance_bonus = buffs.get("upgrade_chance_bonus", 0.0)
    
    rate = upgrade_success_rate(level)
    final_rate = min(1.0, rate + chance_bonus)
    bonus_txt = " (+3% 도감 버프 적용)" if chance_bonus > 0 else ""

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
        await set_rod(ctx.author.id, rod_type, new_level)
        await ctx.reply(
            f"🎉 강화 성공!{bonus_txt} **{format_rod_name(rod_type, new_level)}**\n"
            f"- 다음 강화 비용: **{_fmt_money(upgrade_cost(new_level))}**",
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

    # 선차감 + 잭팟 적립(베팅의 5%)
    await add_money(ctx.author.id, -bet)
    pot_after_add = await _jackpot_add(int(bet * 0.05))

    symbols = ["🍒", "🍋", "🍇", "🔔", "⭐", "7️⃣"]
    weights = [35, 28, 18, 10, 7, 2]  # 7은 매우 낮게
    a, b, c = random.choices(symbols, weights=weights, k=3)

    payout_mult = 0.0
    jackpot_hit = False
    if a == b == c == "7️⃣":
        payout_mult = 12.0
        jackpot_hit = True
    elif a == b == c == "⭐":
        payout_mult = 8.0
    elif a == b == c == "🔔":
        payout_mult = 5.0
    elif a == b == c:
        payout_mult = 3.0
    elif len({a, b, c}) == 2:
        payout_mult = 1.2

    # 하우스 엣지: 승리 시에도 수수료 (VIP 할인 적용)
    fee = await _casino_fee(ctx.author.id, 0.03)
    win = int(bet * payout_mult * (1.0 - fee))

    bonus_spin = 0
    if a == b == c == "🍒" and random.random() < 0.35:
        bonus_spin = 1
    if a == b == c == "⭐" and random.random() < 0.20:
        bonus_spin = 1

    jackpot_take = 0
    if jackpot_hit:
        jackpot_take = await _jackpot_take_all()
        win += jackpot_take
        await _jackpot_record_hit(ctx.guild.id if ctx.guild else None, ctx.author.id, jackpot_take)

    await add_money(ctx.author.id, win)
    net = win - bet
    await _casino_bump(ctx.author.id, bet, net, "슬롯")
    bal = await get_money(ctx.author.id)

    if payout_mult == 0.0:
        await ctx.reply(
            f"🎰 [{a} | {b} | {c}] 꽝! **-{_fmt_money(bet)}**\n"
            f"잭팟: **{_fmt_money(pot_after_add)}** / 잔액: **{_fmt_money(bal)}**",
            mention_author=False,
        )
    else:
        extra = ""
        if jackpot_hit:
            extra = f"\n💥 **잭팟 당첨!** 잭팟: **{_fmt_money(jackpot_take)}**"
        if bonus_spin:
            extra += "\n🎁 **보너스 스핀 1회!** (같은 베팅으로 한 번 더 돌려봐)"
        await ctx.reply(
            f"🎰 [{a} | {b} | {c}] 적중! 배당 x{payout_mult:g}\n"
            f"결과: **{_fmt_money(net)}** / 잭팟: **{_fmt_money(pot_after_add)}** / 잔액: **{_fmt_money(bal)}**{extra}",
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

    # 선결제 + 잭팟 적립(슬롯은 5%)
    await add_money(ctx.author.id, -needed)
    pot_after_add = await _jackpot_add(int(needed * 0.05))

    symbols = ["🍒", "🍋", "🍇", "🔔", "⭐", "7️⃣"]
    weights = [35, 28, 18, 10, 7, 2]
    fee = await _casino_fee(ctx.author.id, 0.03)

    total_win = 0
    total_net = -needed
    hits = 0
    jackpots = 0
    best_line = None
    best_mult = 0.0
    jackpot_take_total = 0

    for _ in range(spins):
        a, b, c = random.choices(symbols, weights=weights, k=3)
        payout_mult = 0.0
        jackpot_hit = False
        if a == b == c == "7️⃣":
            payout_mult = 12.0
            jackpot_hit = True
        elif a == b == c == "⭐":
            payout_mult = 8.0
        elif a == b == c == "🔔":
            payout_mult = 5.0
        elif a == b == c:
            payout_mult = 3.0
        elif len({a, b, c}) == 2:
            payout_mult = 1.2

        win = int(bet * payout_mult * (1.0 - fee))
        if jackpot_hit:
            take = await _jackpot_take_all()
            if take > 0:
                await _jackpot_record_hit(ctx.guild.id if ctx.guild else None, ctx.author.id, take)
            win += take
            jackpot_take_total += take
            jackpots += 1

        total_win += win
        if payout_mult > 0:
            hits += 1
        if payout_mult > best_mult:
            best_mult = payout_mult
            best_line = (a, b, c)

    await add_money(ctx.author.id, total_win)
    total_net += total_win
    await _casino_bump(ctx.author.id, needed, total_net, "슬롯10")
    bal = await get_money(ctx.author.id)

    line_txt = f"[{best_line[0]} | {best_line[1]} | {best_line[2]}]" if best_line else "(베스트 없음)"
    extra = ""
    if jackpots:
        extra = f"\n💥 잭팟 {jackpots}회 (회수: **{_fmt_money(jackpot_take_total)}**)"
    await ctx.reply(
        f"🎰 **슬롯 10연속 결과**\n"
        f"- 적중: **{hits}/10**\n"
        f"- 베스트: {line_txt} (x{best_mult:g})\n"
        f"- 순수익: **{_fmt_money(total_net)}**\n"
        f"- 잭팟: **{_fmt_money(pot_after_add)}** / 잔액: **{_fmt_money(bal)}**{extra}",
        mention_author=False,
    )


@bot.command(name="주사위")
async def dice_cmd(ctx: commands.Context, bet_raw: str | None = None):
    bet = _parse_bet(bet_raw)
    if bet is None:
        await ctx.reply("사용법: `!주사위 <베팅>` (예: `!주사위 2000`)", mention_author=False)
        return

    ok, err = await _casino_guard(ctx, bet)
    if not ok:
        if err:
            await ctx.reply(err, mention_author=False)
        return

    await add_money(ctx.author.id, -bet)
    await _jackpot_add(int(bet * 0.02))

    roll = random.randint(1, 6)
    win = roll >= 4
    mult = 1.8  # 약한 하우스 엣지
    fee = await _casino_fee(ctx.author.id, 0.02)

    if win:
        gross = int(bet * mult)
        payout = int(gross * (1.0 - fee))
        await add_money(ctx.author.id, payout)
        net = payout - bet
        await _casino_bump(ctx.author.id, bet, net, "주사위")
        bal = await get_money(ctx.author.id)
        await ctx.reply(
            f"🎲 주사위: **{roll}** (승!)\n결과: **+{_fmt_money(net)}** / 잔액: **{_fmt_money(bal)}**",
            mention_author=False,
        )
    else:
        await _casino_bump(ctx.author.id, bet, -bet, "주사위")
        bal = await get_money(ctx.author.id)
        await ctx.reply(
            f"🎲 주사위: **{roll}** (패)\n결과: **-{_fmt_money(bet)}** / 잔액: **{_fmt_money(bal)}**",
            mention_author=False,
        )


@bot.command(name="동전")
async def coin_cmd(ctx: commands.Context, bet_raw: str | None = None, choice_raw: str | None = None):
    bet = _parse_bet(bet_raw)
    if bet is None or not choice_raw:
        await ctx.reply("사용법: `!동전 <베팅> <앞|뒤>` (예: `!동전 1500 앞`)", mention_author=False)
        return

    ok, err = await _casino_guard(ctx, bet)
    if not ok:
        if err:
            await ctx.reply(err, mention_author=False)
        return

    await add_money(ctx.author.id, -bet)
    await _jackpot_add(int(bet * 0.02))

    choice = choice_raw.strip()
    if choice not in ("앞", "뒤"):
        await ctx.reply("선택은 `앞` 또는 `뒤`만 가능해.", mention_author=False)
        return

    result = random.choice(["앞", "뒤"])
    win = (choice == result)

    mult = 1.9
    fee = await _casino_fee(ctx.author.id, 0.03)

    if win:
        gross = int(bet * mult)
        payout = int(gross * (1.0 - fee))
        await add_money(ctx.author.id, payout)
        net = payout - bet
        await _casino_bump(ctx.author.id, bet, net, "동전")
        bal = await get_money(ctx.author.id)
        await ctx.reply(
            f"🪙 결과: **{result}** (승!)\n결과: **+{_fmt_money(net)}** / 잔액: **{_fmt_money(bal)}**",
            mention_author=False,
        )
    else:
        await _casino_bump(ctx.author.id, bet, -bet, "동전")
        bal = await get_money(ctx.author.id)
        await ctx.reply(
            f"🪙 결과: **{result}** (패)\n결과: **-{_fmt_money(bet)}** / 잔액: **{_fmt_money(bal)}**",
            mention_author=False,
        )


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
        m = ctx.guild.get_member(uid) if ctx.guild else None
        name = m.display_name if m else f"유저({uid})"
        
        reward_lines.append(f"- **{name}**: 딜 {dmg:,} ({int(dmg/total_damage*100)}%) ➡️ **{_fmt_money(total)}**{tag}{drop_msg}")

    reward_lines.append(f"\n- 총 딜량: **{total_damage:,}**")
    reward_lines.append(f"- 토벌 기본금: **{_fmt_money(base_reward)}** (딜량 비례 배분)")
    reward_lines.append(f"- 딜 1등 보너스: **{_fmt_money(top_bonus)}**")
    reward_lines.append(f"- 막타 보너스: **{_fmt_money(last_hit_bonus)}**")
    await ctx.send("\n".join(reward_lines))


@bot.command(name="보스공격")
async def boss_attack_cmd(ctx: commands.Context):
    if not _channel_allowed(ctx):
        return
    now = utc_ts()
    state = await _get_boss_state()
    if not _boss_alive(state, now):
        await ctx.reply("지금은 활성 보스가 없어. `!보스`로 확인해봐.", mention_author=False)
        return

    rod_type, rod_level = await get_rod(ctx.author.id)
    dmg, is_crit, crit_mult = _boss_damage(rod_type, rod_level)
    
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

    state = await update_json(BOSS_PATH, _default_boss(), mut)
    hp = int(state.get("hp", 0))
    mx = int(state.get("max_hp", 0))

    if hp > 0:
        await ctx.reply(
            f"**{ctx.author.display_name}**의 공격! 피해 **{dmg:,}**{crit_txt}\n- 보스 HP: **{hp:,}/{mx:,}**",
            mention_author=False,
        )
        return

    await ctx.send(f"**{ctx.author.display_name}**의 막타로 보스가 쓰러졌다! (피해 {dmg:,}){crit_txt}")
    await _boss_payout(ctx, state)


def main() -> None:
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise SystemExit("DISCORD_TOKEN이 없습니다. .env 파일에 DISCORD_TOKEN=... 을 넣어주세요.")
    bot.run(token)


if __name__ == "__main__":
    main()
