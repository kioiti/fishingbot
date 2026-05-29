"""닉네임 기반 주식 시장 (랜덤 시세 변동)"""
from __future__ import annotations

import random
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
