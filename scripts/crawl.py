import json
import os
import requests
from datetime import datetime

BASE_URL = "https://www.smart-factory.kr"
API_URL = f"{BASE_URL}/usr/bg/ba/ma/bsnsPbanc/selectBsnsPbancPage.do"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Referer": f"{BASE_URL}/usr/bg/ba/ma/bsnsPblanc",
}

def crawl():
    results = []

    # 접수중(ING) + 접수예정(YET) 둘 다 수집
    for status_code in ["ING", "YET", ""]:
        payload = {
            "key": "list",
            "bizYr": "",
            "bizClsfYrNm": "",
            "dtlPbancNm": "",
            "rcptStts": status_code,
            "ordrSe": "REG"
        }

        try:
            res = requests.post(API_URL, json=payload, headers=HEADERS, timeout=15)
            res.raise_for_status()
            data = res.json()
            print(f"[{status_code or '전체'}] 응답 키: {list(data.keys()) if isinstance(data, dict) else type(data)}")

            # 데이터 위치 탐색
            rows = None
            if isinstance(data, list):
                rows = data
            elif isinstance(data, dict):
                # modelAndView.model.pbancList 구조 대응
                try:
                    rows = data["modelAndView"]["model"]["pbancList"]
                except (KeyError, TypeError):
                    pass
                if not rows:
                    for key in ["list", "items", "content", "data", "result", "rows", "pbancList"]:
                        if key in data:
                            rows = data[key]
                            break

            if rows:
                print(f"  → {len(rows)}건 발견")
                for row in rows:
                    results.append(parse_row(row))
            else:
                print(f"  → 데이터 없음. 전체 응답: {str(data)[:300]}")

        except Exception as e:
            print(f"[ERROR] {status_code}: {e}")

    # 중복 제거 (title 기준)
    seen = set()
    unique = []
    for r in results:
        key = r["title"]
        if key not in seen:
            seen.add(key)
            unique.append(r)

    output = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "count": len(unique),
        "items": unique
    }

    os.makedirs("data", exist_ok=True)
    with open("data/announcements.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 완료: {len(unique)}건 저장")
    return unique


def parse_row(row: dict) -> dict:
    def get(*keys):
        for k in keys:
            if k in row and row[k]:
                return str(row[k])
        return ""

    title = get("pbancNm", "dtlPbancNm", "bsnsPbancNm", "title", "ttl", "subject")
    status = get("rcptSttsNm", "rcptStatNm", "statNm", "status")
    start  = get("rcptBgngDt", "bgngDt", "startDt", "startDate")
    end    = get("rcptEndDt",  "endDt",  "closeDt",  "endDate")
    sn     = get("pbancSn", "sn", "seq", "id", "no")
    link   = f"{BASE_URL}/usr/bg/ba/ma/bsnsPblanc/{sn}" if sn else BASE_URL

    # 날짜 형식 정리 (20260101 → 2026-01-01)
    def fmt(d):
        if d and len(d) == 8 and d.isdigit():
            return f"{d[:4]}-{d[4:6]}-{d[6:]}"
        return d

    # 디버그: 첫 번째 행 키 출력
    if not hasattr(parse_row, "_printed"):
        print(f"  [row 키 샘플] {list(row.keys())}")
        parse_row._printed = True

    return {
        "title":  title  or "(제목없음)",
        "status": status or "",
        "start":  fmt(start),
        "end":    fmt(end),
        "link":   link,
    }


if __name__ == "__main__":
    crawl()
