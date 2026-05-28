from __future__ import annotations

import os
import math
import random
from pathlib import Path
from typing import Dict, Tuple

import discord
from discord.ext import commands
from dotenv import load_dotenv

from fishing_data import (
    FISH_TABLE,
    RODS,
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
)
from utils.jsondb import ensure_dir, get_user_dict, read_json, update_json, utc_ts, write_json


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
ensure_dir(DATA_DIR)

MONEY_PATH = DATA_DIR / "money.json"
INV_PATH = DATA_DIR / "inventory.json"
RODS_PATH = DATA_DIR / "rods.json"
COOLDOWN_PATH = DATA_DIR / "cooldown.json"
STATS_PATH = DATA_DIR / "stats.json"
BOSS_PATH = DATA_DIR / "boss.json"


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


def _fmt_money(n: int) -> str:
    return f"{int(n):,}원"


def _rod_cooldown_seconds(rod_type: str, rod_level: int) -> int:
    base = get_base_cooldown_seconds(rod_level)
    passive = (RODS.get(rod_type) or RODS["rookie"])["passive"]
    if passive.get("type") == "cooldown_bonus":
        v = float(passive.get("value", 0.0))
        base = int(math.ceil(base * (1.0 - v)))
    return max(3, base)


def _boss_damage(rod_type: str, rod_level: int) -> int:
    base = random.randint(250, 550) + rod_level * random.randint(30, 55)
    passive = (RODS.get(rod_type) or RODS["rookie"])["passive"]
    if passive.get("type") == "boss_bonus":
        v = float(passive.get("value", 0.0))
        base = int(base * (1.0 + v))
    return max(1, base)


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


@bot.event
async def on_ready():
    ensure_dir(DATA_DIR)
    print(f"Logged in as {bot.user} (id={bot.user.id})")


@bot.command(name="도움말")
async def help_cmd(ctx: commands.Context):
    msg = (
        "**낚시 RPG 봇 명령어**\n"
        "- `!낚시` 낚시하기(쿨타임 있음)\n"
        "- `!인벤` 내 인벤토리 보기\n"
        "- `!판매 <이름|all>` 물고기 판매\n"
        "- `!낚시대` 내 낚시대 정보\n"
        "- `!강화` 낚시대 강화\n"
        "- `!상점` 낚시대 상점 보기\n"
        "- `!구매 <rod_id>` 낚시대 구매 (`rookie|flame|thunder|deepsea`)\n"
        "- `!랭킹` 부자 랭킹 TOP 10\n"
        "- `!보스` 보스 상태/스폰(하루 1회)\n"
        "- `!보스공격` 보스에게 공격\n"
    )
    await ctx.reply(msg, mention_author=False)


@bot.command(name="낚시대")
async def rod_cmd(ctx: commands.Context):
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
    lines = ["**낚시대 상점** (구매: `!구매 <rod_id>`)\n"]
    for rod_id, info in RODS.items():
        price = int(info.get("price", 0))
        lines.append(f"- `{rod_id}`: **{info['name']}** / 가격: **{_fmt_money(price)}**")
    await ctx.reply("\n".join(lines), mention_author=False)


@bot.command(name="구매")
async def buy_cmd(ctx: commands.Context, rod_id: str | None = None):
    if not rod_id:
        await ctx.reply("사용법: `!구매 <rod_id>`  (예: `!구매 flame`)", mention_author=False)
        return
    rod_id = rod_id.strip().lower()
    if rod_id not in RODS:
        await ctx.reply("없는 낚시대입니다. `!상점`에서 확인해줘.", mention_author=False)
        return

    cur_type, cur_level = await get_rod(ctx.author.id)
    if rod_id == cur_type:
        await ctx.reply("이미 같은 낚시대를 사용 중이야.", mention_author=False)
        return

    price = int(RODS[rod_id].get("price", 0))
    money = await get_money(ctx.author.id)
    if money < price:
        await ctx.reply(
            f"돈이 부족해. 필요: **{_fmt_money(price)}**, 보유: **{_fmt_money(money)}**",
            mention_author=False,
        )
        return

    await add_money(ctx.author.id, -price)
    await set_rod(ctx.author.id, rod_id, cur_level)
    await ctx.reply(
        f"구매 완료! 이제 **{format_rod_name(rod_id, cur_level)}** 사용 중이야.",
        mention_author=False,
    )


@bot.command(name="낚시")
async def fish_cmd(ctx: commands.Context):
    user_id = ctx.author.id
    rod_type, rod_level = await get_rod(user_id)
    cd_seconds = _rod_cooldown_seconds(rod_type, rod_level)

    now = utc_ts()
    last = await get_last_fish_ts(user_id)
    wait = (last + cd_seconds) - now
    if wait > 0:
        await ctx.reply(f"쿨타임이야. **{wait}초** 뒤에 다시 낚시 가능!", mention_author=False)
        return

    weights = get_rarity_weights(rod_level, rod_type)
    rarity = choose_rarity(weights)
    fish = choose_fish(rarity)

    await set_last_fish_ts(user_id, now)
    await add_fish(user_id, fish.id, 1)
    await bump_stats(user_id, fish.rarity)

    await ctx.reply(
        f"**{ctx.author.display_name}** 낚시 성공!\n{format_fish_catch(fish)}",
        mention_author=False,
    )


@bot.command(name="인벤")
async def inv_cmd(ctx: commands.Context):
    inv = await get_inventory(ctx.author.id)
    if not inv:
        await ctx.reply("인벤토리가 비었어. `!낚시`로 시작해봐.", mention_author=False)
        return

    lines = [f"**{ctx.author.display_name}** 인벤토리"]
    total_items = 0
    total_value = 0
    for fish_id, cnt in sorted(inv.items(), key=lambda kv: (-kv[1], kv[0])):
        fish = FISH_BY_ID.get(fish_id)
        if not fish:
            continue
        total_items += cnt
        total_value += fish.sell * cnt
        lines.append(f"- {fish.name} x{cnt} (개당 {fish.sell}원)")

    lines.append(f"\n합계: **{total_items}개**, 전부 팔면: **{_fmt_money(total_value)}**")
    await ctx.reply("\n".join(lines), mention_author=False)


@bot.command(name="판매")
async def sell_cmd(ctx: commands.Context, *, target: str | None = None):
    if not target:
        await ctx.reply("사용법: `!판매 <물고기이름|all>`", mention_author=False)
        return

    target = target.strip()
    inv = await get_inventory(ctx.author.id)
    if not inv:
        await ctx.reply("팔 게 없어. `!낚시`부터!", mention_author=False)
        return

    if target.lower() == "all":
        total = 0
        for fish_id, cnt in inv.items():
            fish = FISH_BY_ID.get(fish_id)
            if fish:
                total += fish.sell * cnt
        def mut(d):
            d = dict(d or {})
            d.pop(str(ctx.author.id), None)
            return d

        await update_json(INV_PATH, _default_inventory(), mut)
        bal = await add_money(ctx.author.id, total)
        await ctx.reply(
            f"전부 판매 완료! 획득: **{_fmt_money(total)}** / 현재 잔액: **{_fmt_money(bal)}**",
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

    value = fish.sell * cnt
    await add_fish(ctx.author.id, fish.id, -cnt)
    bal = await add_money(ctx.author.id, value)
    await ctx.reply(
        f"**{fish.name} x{cnt}** 판매 완료! 획득: **{_fmt_money(value)}** / 잔액: **{_fmt_money(bal)}**",
        mention_author=False,
    )


@bot.command(name="강화")
async def upgrade_cmd(ctx: commands.Context):
    rod_type, level = await get_rod(ctx.author.id)
    cost = upgrade_cost(level)
    rate = upgrade_success_rate(level)
    money = await get_money(ctx.author.id)
    if money < cost:
        await ctx.reply(
            f"강화 비용이 부족해. 필요: **{_fmt_money(cost)}** / 보유: **{_fmt_money(money)}**",
            mention_author=False,
        )
        return

    await add_money(ctx.author.id, -cost)
    ok, new_level = upgrade_try(level)
    await set_rod(ctx.author.id, rod_type, new_level)

    if ok:
        await ctx.reply(
            f"강화 성공! **{format_rod_name(rod_type, new_level)}**\n"
            f"- 다음 강화 비용: **{_fmt_money(upgrade_cost(new_level))}**",
            mention_author=False,
        )
    else:
        await ctx.reply(
            f"강화 실패... (성공확률 {int(rate*100)}%)\n"
            f"현재 낚시대: **{format_rod_name(rod_type, level)}**",
            mention_author=False,
        )


@bot.command(name="랭킹")
async def ranking_cmd(ctx: commands.Context):
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
        user = ctx.guild.get_member(uid) if ctx.guild else None
        name = user.display_name if user else f"유저({uid})"
        lines.append(f"{i}. **{name}** — {_fmt_money(m)}")
    await ctx.reply("\n".join(lines), mention_author=False)


async def _get_boss_state() -> dict:
    return await read_json(BOSS_PATH, _default_boss())


async def _set_boss_state(state: dict) -> None:
    await write_json(BOSS_PATH, state)


def _boss_alive(state: dict, now: int) -> bool:
    return bool(state.get("active")) and int(state.get("hp", 0)) > 0 and int(state.get("ends_at", 0)) > now


@bot.command(name="보스")
async def boss_cmd(ctx: commands.Context):
    now = utc_ts()
    state = await _get_boss_state()

    if _boss_alive(state, now):
        hp = int(state["hp"])
        mx = int(state["max_hp"])
        await ctx.reply(
            f"**보스 레이드 진행 중!**\n- 보스: **{state.get('name','보스')}**\n- HP: **{hp:,}/{mx:,}**\n"
            f"- 제한시간: <t:{int(state['ends_at'])}:R>\n"
            f"공격: `!보스공격`",
            mention_author=False,
        )
        return

    today = _today_key_utc()
    if state.get("last_spawn_day") == today:
        await ctx.reply("보스는 **하루 1회**야. 내일 다시 와!", mention_author=False)
        return

    max_hp = 100_000
    duration = 60 * 60
    new_state = boss_spawn(max_hp=max_hp, now_ts=now, duration_seconds=duration)
    new_state["last_spawn_day"] = today
    await _set_boss_state(new_state)

    await ctx.reply(
        f"**보스 출현!** **{new_state.get('name','보스')}**\n- HP: **{max_hp:,}**\n"
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

    base_reward = 120_000
    last_hit_bonus = 15_000
    top_bonus = 20_000

    last_hit = state.get("last_hit")
    top_uid = max(contributors.items(), key=lambda kv: int(kv[1]))[0]

    reward_lines = ["**보스 토벌 성공! 보상 지급**"]
    for uid_str, dmg in contributors.items():
        dmg = int(dmg)
        if dmg <= 0:
            continue
        share = int(base_reward * (dmg / total_damage))
        bonus = 0
        if uid_str == str(last_hit):
            bonus += last_hit_bonus
        if uid_str == str(top_uid):
            bonus += top_bonus
        total = share + bonus
        await add_money(int(uid_str), total)

    last_member = ctx.guild.get_member(int(last_hit)) if ctx.guild and last_hit else None
    top_member = ctx.guild.get_member(int(top_uid)) if ctx.guild else None
    reward_lines.append(f"- 총 보상 풀: **{_fmt_money(base_reward)}** (피해 비례)")
    reward_lines.append(f"- 딜 1등 보너스: **{_fmt_money(top_bonus)}** — {top_member.display_name if top_member else top_uid}")
    reward_lines.append(f"- 막타 보너스: **{_fmt_money(last_hit_bonus)}** — {last_member.display_name if last_member else last_hit}")
    await ctx.send("\n".join(reward_lines))


@bot.command(name="보스공격")
async def boss_attack_cmd(ctx: commands.Context):
    now = utc_ts()
    state = await _get_boss_state()
    if not _boss_alive(state, now):
        await ctx.reply("지금은 활성 보스가 없어. `!보스`로 확인해봐.", mention_author=False)
        return

    rod_type, rod_level = await get_rod(ctx.author.id)
    dmg = _boss_damage(rod_type, rod_level)

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
            f"**{ctx.author.display_name}**의 공격! 피해 **{dmg:,}**\n- 보스 HP: **{hp:,}/{mx:,}**",
            mention_author=False,
        )
        return

    await ctx.send(f"**{ctx.author.display_name}**의 막타로 보스가 쓰러졌다! (피해 {dmg:,})")
    await _boss_payout(ctx, state)


def main() -> None:
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise SystemExit("DISCORD_TOKEN이 없습니다. .env 파일에 DISCORD_TOKEN=... 을 넣어주세요.")
    bot.run(token)


if __name__ == "__main__":
    main()
