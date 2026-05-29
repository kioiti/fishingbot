"""부동산: 한국 지역 테마, 구매 후 주기적 월세(게임 내)"""
from __future__ import annotations

from typing import Dict, List, Optional

# 가격 1억 ~ 20억 (일부 프리미엄 라인은 그 이상 확장 가능 — 요청은 20억까지)
ESTATE_CATALOG: Dict[str, dict] = {
    "est_busan_room": {
        "id": "est_busan_room",
        "name": "부산 서면 원룸",
        "region": "부산",
        "emoji": "🏠",
        "price": 100_000_000,
        "rent_cycle_sec": 3600,
        "rent_amount": 350_000,
        "aliases": ["부산", "서면", "est_busan_room"],
    },
    "est_daegu_shop": {
        "id": "est_daegu_shop",
        "name": "대구 동성로 상가",
        "region": "대구",
        "emoji": "🏪",
        "price": 150_000_000,
        "rent_cycle_sec": 3600,
        "rent_amount": 520_000,
        "aliases": ["대구", "동성로", "est_daegu_shop"],
    },
    "est_incheon_apt": {
        "id": "est_incheon_apt",
        "name": "인천 송도 아파트",
        "region": "인천",
        "emoji": "🏢",
        "price": 250_000_000,
        "rent_cycle_sec": 3600,
        "rent_amount": 850_000,
        "aliases": ["인천", "송도", "est_incheon_apt"],
    },
    "est_daejeon_office": {
        "id": "est_daejeon_office",
        "name": "대전 둔산 오피스텔",
        "region": "대전",
        "emoji": "🏬",
        "price": 400_000_000,
        "rent_cycle_sec": 3600,
        "rent_amount": 1_350_000,
        "aliases": ["대전", "둔산", "est_daejeon_office"],
    },
    "est_gwangju_villa": {
        "id": "est_gwangju_villa",
        "name": "광주 상무지구 빌라",
        "region": "광주",
        "emoji": "🏡",
        "price": 600_000_000,
        "rent_cycle_sec": 3600,
        "rent_amount": 2_000_000,
        "aliases": ["광주", "상무", "est_gwangju_villa"],
    },
    "est_jeonju_hanok": {
        "id": "est_jeonju_hanok",
        "name": "전주 한옥 인근 게스트하우스",
        "region": "전북",
        "emoji": "🏯",
        "price": 800_000_000,
        "rent_cycle_sec": 3600,
        "rent_amount": 2_650_000,
        "aliases": ["전주", "한옥", "est_jeonju_hanok"],
    },
    "est_jeju_pension": {
        "id": "est_jeju_pension",
        "name": "제주 연동 펜션",
        "region": "제주",
        "emoji": "🌴",
        "price": 1_000_000_000,
        "rent_cycle_sec": 3600,
        "rent_amount": 3_300_000,
        "aliases": ["제주", "펜션", "est_jeju_pension"],
    },
    "est_suwon_apt": {
        "id": "est_suwon_apt",
        "name": "수원 영통 아파트",
        "region": "경기",
        "emoji": "🏢",
        "price": 1_200_000_000,
        "rent_cycle_sec": 3600,
        "rent_amount": 4_000_000,
        "aliases": ["수원", "영통", "est_suwon_apt"],
    },
    "est_gangnam_studio": {
        "id": "est_gangnam_studio",
        "name": "서울 강남 역세권 오피스텔",
        "region": "서울",
        "emoji": "🌆",
        "price": 1_500_000_000,
        "rent_cycle_sec": 3600,
        "rent_amount": 5_000_000,
        "aliases": ["강남", "역세권", "est_gangnam_studio"],
    },
    "est_haeundae_view": {
        "id": "est_haeundae_view",
        "name": "부산 해운대 뷰아파트",
        "region": "부산",
        "emoji": "🌊",
        "price": 2_000_000_000,
        "rent_cycle_sec": 3600,
        "rent_amount": 6_600_000,
        "aliases": ["해운대", "est_haeundae_view"],
    },
    "est_mapo_office": {
        "id": "est_mapo_office",
        "name": "서울 마포 오피스텔",
        "region": "서울",
        "emoji": "🎸",
        "price": 3_500_000_000,
        "rent_cycle_sec": 3600,
        "rent_amount": 11_500_000,
        "aliases": ["마포", "est_mapo_office"],
    },
    "est_songpa_apt": {
        "id": "est_songpa_apt",
        "name": "서울 송파 헬리오시티 인근",
        "region": "서울",
        "emoji": "🏙️",
        "price": 5_000_000_000,
        "rent_cycle_sec": 3600,
        "rent_amount": 16_500_000,
        "aliases": ["송파", "est_songpa_apt"],
    },
    "est_yongsan_tower": {
        "id": "est_yongsan_tower",
        "name": "서울 용산 타워뷰 레지던스",
        "region": "서울",
        "emoji": "🗼",
        "price": 8_000_000_000,
        "rent_cycle_sec": 3600,
        "rent_amount": 26_000_000,
        "aliases": ["용산", "est_yongsan_tower"],
    },
    "est_cheongdam_shop": {
        "id": "est_cheongdam_shop",
        "name": "서울 청담 로데오 상가",
        "region": "서울",
        "emoji": "💎",
        "price": 12_000_000_000,
        "rent_cycle_sec": 3600,
        "rent_amount": 39_000_000,
        "aliases": ["청담", "로데오", "est_cheongdam_shop"],
    },
    "est_samsung_tower": {
        "id": "est_samsung_tower",
        "name": "서울 삼성동 프라임 오피스",
        "region": "서울",
        "emoji": "🏛️",
        "price": 20_000_000_000,
        "rent_cycle_sec": 3600,
        "rent_amount": 65_000_000,
        "aliases": ["삼성동", "프라임", "est_samsung_tower"],
    },
}

SELL_BACK_RATE = 0.70


def _alias_index() -> Dict[str, str]:
    out: Dict[str, str] = {}
    for eid, e in ESTATE_CATALOG.items():
        out[eid.lower()] = eid
        out[e["name"].lower().replace(" ", "")] = eid
        for a in e.get("aliases", []):
            out[str(a).lower().replace(" ", "")] = eid
    return out


_ALIAS_INDEX = _alias_index()


def resolve_estate(query: str) -> Optional[str]:
    q = (query or "").strip().lower().replace(" ", "")
    return _ALIAS_INDEX.get(q)


def fmt_estate_price(n: int) -> str:
    if n >= 100_000_000:
        eok = n / 100_000_000
        if eok == int(eok):
            return f"{int(eok)}억원"
        return f"{eok:.1f}억원"
    return f"{n:,}원"


def pending_rent(record: dict, estate: dict, now: int) -> tuple[int, int, int]:
    """반환: (받을 월세 총액, 틱 수, 다음 수령까지 남은 초)"""
    last = int(record.get("last_rent", record.get("bought_at", now)))
    cycle = int(estate["rent_cycle_sec"])
    per = int(estate["rent_amount"])
    elapsed = max(0, now - last)
    ticks = elapsed // cycle
    if ticks <= 0:
        wait = cycle - elapsed if elapsed < cycle else cycle
        return 0, 0, int(wait)
    amount = ticks * per
    wait = cycle - (elapsed % cycle)
    if wait == cycle and ticks > 0:
        wait = 0
    return amount, ticks, int(wait)


def estate_list_line(eid: str) -> str:
    e = ESTATE_CATALOG[eid]
    rent_h = int(e["rent_amount"])
    return (
        f"{e['emoji']} **{e['name']}** ({e['region']})\n"
        f"  └ 매입 **{fmt_estate_price(e['price'])}** · 시간당 월세 **{rent_h:,}원**\n"
        f"  └ `!부동산구매 {eid}`"
    )
