# 낚시 RPG 디스코드 봇

JSON 파일로 데이터(돈/인벤/낚시대/쿨타임/보스)를 분리 저장하는 **장기 운영형 낚시 RPG 봇 MVP**입니다.

## 기능(현재)

- `!낚시`: 쿨타임 기반 낚시
- `!인벤`: 인벤토리 조회
- `!판매 <이름|all>`: 물고기 판매
- `!낚시대`: 낚시대/쿨타임 정보
- `!강화`: 낚시대 강화
- `!상점`, `!구매 <rod_id>`: 낚시대 상점/구매
- `!랭킹`: 보유금 TOP 10
- `!보스`, `!보스공격`: 하루 1회 스폰 + 공동 레이드

## 설치

PowerShell 기준:

```bash
py -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## 설정(.env)

`.env.example`을 복사해서 `.env`를 만들고 토큰을 넣어주세요.

```bash
copy .env.example .env
```

## 실행

```bash
py bot.py
```

## 데이터 파일

실행하면 자동 생성됩니다.

- `data/money.json`
- `data/inventory.json`
- `data/rods.json`
- `data/cooldown.json`
- `data/stats.json`
- `data/boss.json`

