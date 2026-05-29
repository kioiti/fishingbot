"""닉네임 기반 주식 시장 (랜덤 시세 변동)"""
from __future__ import annotations

import random
import time
from typing import Dict, List, Optional, Tuple

# id -> 종목 정보
STOCKS: Dict[str, dict] = {
    "eving": {
        "id": "eving",
        "ticker": "EVNG",
        "company": "에빙전자",
        "nick": "에빙",
        "base_price": 14_200,
        "aliases": ["에빙", "에빙전자", "evng", "eving"],
    },
    "memkong": {
        "id": "memkong",
        "ticker": "MEMK",
        "company": "밈콩엔터",
        "nick": "밈콩",
        "base_price": 9_800,
        "aliases": ["밈콩", "밈콩엔터", "memk", "memkong"],
    },
    "marakong": {
        "id": "marakong",
        "ticker": "MARA",
        "company": "마라콩식품",
        "nick": "마라콩",
        "base_price": 11_500,
        "aliases": ["마라콩", "마라콩식품", "mara", "marakong"],
    },
    "mrrx": {
        "id": "mrrx",
        "ticker": "MRRX",
        "company": "머래제약",
        "nick": "머래",
        "base_price": 22_400,
        "aliases": ["머래", "머래제약", "mrrx"],
    },
    "mihee": {
        "id": "mihee",
        "ticker": "MHYS",
        "company": "미희여사패션",
        "nick": "미희여사",
        "base_price": 16_700,
        "aliases": ["미희여사", "미희여사패션", "mhys", "mihee"],
    },
    "jisung": {
        "id": "jisung",
        "ticker": "JSKO",
        "company": "지성콩바이오",
        "nick": "지성콩",
        "base_price": 18_900,
        "aliases": ["지성콩", "지성콩바이오", "jsko", "jisung"],
    },
    "zzunkong": {
        "id": "zzunkong",
        "ticker": "ZZMK",
        "company": "쮼콩게임즈",
        "nick": "쮼콩",
        "base_price": 12_300,
        "aliases": ["쮼콩", "쮼콩게임즈", "zzmk", "zzunkong"],
    },
    "gyesak": {
        "id": "gyesak",
        "ticker": "GSSC",
        "company": "계삭증권",
        "nick": "계삭",
        "base_price": 20_100,
        "aliases": ["계삭", "계삭증권", "gssc", "gyesak"],
    },
}

STOCK_TICK_SECONDS = 120
MAX_TRADE_QTY = 5_000
NEWS_HOURS_KST = (11, 20)  # 하루 2회 (KST 11시, 20시)

# 속보에 등장하는 가상 파트너/기관
NEWS_PARTNERS: List[str] = [
    "글로벌헬스케어",
    "스타트업벤처스",
    "메가푸드그룹",
    "AI테크홀딩스",
    "블루오션캐피탈",
    "동아시아물산",
    "네오바이오랩",
    "콩테크유니온",
    "퍼시픽리테일",
    "한빛전자",
]

GOOD_NEWS_TEMPLATES: List[str] = [
    "**{company}**, **{partner}**와 전략적 파트너십 체결!",
    "**{company}**, **{partner}**와 대규모 공급 계약 체결",
    "**{company}** 분기 실적, 시장 예상 크게 상회(서프라이즈)",
    "**{company}**, 신규 사업 진출에 **{partner}** 투자 유치",
    "**{company}** 대표 {nick}, 업계 혁신상 수상",
    "**{company}**, 해외 진출 MOU 체결 — **{partner}**",
    "**{company}** 주력 신제품, 출시 첫 주 완판 돌풍",
]

BAD_NEWS_TEMPLATES: List[str] = [
    "**{company}**, **{partner}**와의 계약 결렬설 보도",
    "**{company}** 분기 실적 부진, 목표가 하향",
    "**{company}**, 제품 품질 이슈로 자진 리콜",
    "**{company}** 대표 {nick}, 내부 회계 조사 착수",
    "**{company}**, 주요 고객사 이탈 — 매출 타격 우려",
    "**{company}** 신작 부진, 개발비 손실 확대 전망",
    "**{company}**, 규제 당국 현장 조사 착수",
]


def _alias_index() -> Dict[str, str]:
    out: Dict[str, str] = {}
    for sid, s in STOCKS.items():
        out[sid.lower()] = sid
        out[s["ticker"].lower()] = sid
        out[s["company"].lower()] = sid
        out[s["nick"].lower()] = sid
        for a in s.get("aliases", []):
            out[str(a).lower()] = sid
    return out


_ALIAS_INDEX = _alias_index()


def resolve_stock(query: str) -> Optional[str]:
    q = (query or "").strip().lower().replace(" ", "")
    if not q:
        return None
    return _ALIAS_INDEX.get(q)


def default_market() -> dict:
    prices = {sid: int(s["base_price"]) for sid, s in STOCKS.items()}
    return {
        "prices": prices,
        "prev": dict(prices),
        "last_tick": 0,
    }


def price_bounds(stock_id: str, price: int) -> int:
    base = int(STOCKS[stock_id]["base_price"])
    lo = max(100, int(base * 0.25))
    hi = int(base * 5.0)
    return max(lo, min(hi, int(price)))


def tick_market(prices: dict, prev: dict) -> Tuple[dict, dict]:
    """한 틱 시세 변동. 반환: (new_prices, new_prev)"""
    new_prices = dict(prices)
    new_prev = dict(prices)
    for sid in STOCKS:
        cur = int(new_prices.get(sid, STOCKS[sid]["base_price"]))
        if random.random() < 0.06:
            change = random.choice([-1, 1]) * random.uniform(0.10, 0.22)
        else:
            change = random.uniform(-0.09, 0.09)
        nxt = int(cur * (1.0 + change))
        nxt = price_bounds(sid, nxt)
        new_prev[sid] = cur
        new_prices[sid] = nxt
    return new_prices, new_prev


def change_pct(cur: int, prev: int) -> float:
    if prev <= 0:
        return 0.0
    return (cur - prev) / prev * 100.0


def format_change(cur: int, prev: int) -> str:
    pct = change_pct(cur, prev)
    if pct > 0.01:
        return f"📈 +{pct:.2f}%"
    if pct < -0.01:
        return f"📉 {pct:.2f}%"
    return "➡️ 0.00%"


def stock_line(stock_id: str, cur: int, prev: int) -> str:
    s = STOCKS[stock_id]
    ch = format_change(cur, prev)
    return (
        f"**{s['company']}** (`{s['ticker']}`) — **{cur:,}원**/주 {ch}\n"
        f"  └ 대표: {s['nick']} · 매수/매도: `!주식매수 {s['nick']} <수량>`"
    )


def normalize_holding(raw) -> dict:
    """보유 포지션: qty, cost_total(총 매입금액)"""
    if isinstance(raw, dict):
        qty = max(0, int(raw.get("qty", 0)))
        cost = max(0, int(raw.get("cost_total", 0)))
        return {"qty": qty, "cost_total": cost}
    if isinstance(raw, int):
        q = max(0, int(raw))
        return {"qty": q, "cost_total": 0}
    return {"qty": 0, "cost_total": 0}


def holding_avg_price(holding: dict) -> int:
    q = int(holding.get("qty", 0))
    c = int(holding.get("cost_total", 0))
    if q <= 0 or c <= 0:
        return 0
    return int(c // q)


def holding_stats(cur_price: int, holding: dict) -> Optional[dict]:
    h = normalize_holding(holding)
    qty = h["qty"]
    if qty <= 0:
        return None
    cost_total = h["cost_total"]
    avg = holding_avg_price(h)
    value = int(cur_price) * qty
    if cost_total <= 0:
        return {
            "qty": qty,
            "avg": 0,
            "cost_total": 0,
            "value": value,
            "pl": None,
            "pct": None,
        }
    pl = value - cost_total
    pct = pl / cost_total * 100.0
    return {
        "qty": qty,
        "avg": avg,
        "cost_total": cost_total,
        "value": value,
        "pl": int(pl),
        "pct": float(pct),
    }


def format_signed_money(amount: int) -> str:
    if amount > 0:
        return f"+{amount:,}원"
    if amount < 0:
        return f"{amount:,}원"
    return "±0원"


def format_holding_pl(stats: dict) -> str:
    if stats.get("pl") is None:
        return "📋 평균 매수가 **미기록** (추가 매수 시부터 계산)"
    pl = int(stats["pl"])
    pct = float(stats["pct"])
    icon = "🟢" if pl > 0 else ("🔴" if pl < 0 else "⚪")
    return f"{icon} 평가손익 **{format_signed_money(pl)}** ({pct:+.2f}%)"


def kst_now():
    import datetime

    return datetime.datetime.utcnow() + datetime.timedelta(hours=9)


def kst_today_key() -> str:
    return kst_now().strftime("%Y-%m-%d")


def roll_stock_news() -> dict:
    """속보 1건 생성. change는 비율(호재 +, 악재 -)."""
    stock_id = random.choice(list(STOCKS.keys()))
    s = STOCKS[stock_id]
    partner = random.choice(NEWS_PARTNERS)
    is_good = random.random() < 0.52

    if is_good:
        headline = random.choice(GOOD_NEWS_TEMPLATES).format(
            company=s["company"],
            partner=partner,
            nick=s["nick"],
        )
        change = random.uniform(0.20, 0.42)
        tag = "호재"
        flair = "🚀"
    else:
        headline = random.choice(BAD_NEWS_TEMPLATES).format(
            company=s["company"],
            partner=partner,
            nick=s["nick"],
        )
        change = -random.uniform(0.20, 0.42)
        tag = "악재"
        flair = "💥"

    return {
        "stock_id": stock_id,
        "ticker": s["ticker"],
        "company": s["company"],
        "is_good": is_good,
        "tag": tag,
        "flair": flair,
        "headline": headline,
        "change": float(change),
        "partner": partner,
        "ts": int(time.time()),
    }


def apply_news_shock(
    prices: dict, prev: dict, stock_id: str, change_ratio: float
) -> Tuple[dict, dict, int, int]:
    cur = int(prices.get(stock_id, STOCKS[stock_id]["base_price"]))
    new_prices = dict(prices)
    new_prev = dict(prev)
    new_prev[stock_id] = cur
    nxt = price_bounds(stock_id, int(cur * (1.0 + change_ratio)))
    new_prices[stock_id] = nxt
    return new_prices, new_prev, cur, nxt


def format_news_broadcast(news: dict, old_price: int, new_price: int) -> str:
    pct = change_pct(new_price, old_price)
    sign = f"+{pct:.1f}%" if pct > 0 else f"{pct:.1f}%"
    move = "급등" if news["is_good"] else "급락"
    return (
        f"📰 **[속보]** {news['flair']} **{news['tag']}**\n"
        f"{news['headline']}\n\n"
        f"📊 **{news['company']}** (`{news['ticker']}`) 시세 **{move}**\n"
        f"- **{old_price:,}원** → **{new_price:,}원** ({sign})\n"
        f"- `!주식시세 {news['company']}` · `!주식목록`"
    )


def format_holding_detail(stats: dict, cur_price: int) -> str:
    if stats.get("avg", 0) <= 0:
        return (
            f"보유 **{stats['qty']}주** · 평가 **{stats['value']:,}원**\n"
            f"  └ 평균 매수가: **미기록** (이번부터 매수 내역 저장)"
        )
    per_share_pl = cur_price - stats["avg"]
    return (
        f"보유 **{stats['qty']}주**\n"
        f"  └ 평균 매수가: **{stats['avg']:,}원**/주\n"
        f"  └ 매입 총액: **{stats['cost_total']:,}원** → 평가 **{stats['value']:,}원**\n"
        f"  └ 1주당 손익: **{format_signed_money(per_share_pl)}** · {format_holding_pl(stats)}"
    )
