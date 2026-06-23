import json
import os
import requests
from datetime import datetime

BASE_URL = "https://www.smart-factory.kr"
API_URL  = f"{BASE_URL}/usr/bg/ba/ma/bsnsPbanc/selectBsnsPbancPage.do"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Referer": f"{BASE_URL}/usr/bg/ba/ma/bsnsPblanc",
}

PAGE_SIZE = 100  # 한 번에 최대한 많이

def fetch_page(status_code="", page=1):
    payload = {
        "key": "list",
        "bizYr": "",
        "bizClsfYrNm": "",
        "dtlPbancNm": "",
        "rcptStts": status_code,
        "ordrSe": "REG",
        "pageBasic": str(page),
        "blockPage": str(PAGE_SIZE),
    }
    res = requests.post(API_URL, json=payload, headers=HEADERS, timeout=15)
    res.raise_for_status()
    data = res.json()
    rows = data["modelAndView"]["model"]["pbancList"]
    total = int(data["paginationInfo"]["totalCount"])
    return rows, total

def crawl():
    results = []
    seen = set()

    # 접수중 + 접수예정만 수집
    for status_code in ["ING", "YET"]:
        page = 1
        while True:
            rows, total = fetch_page(status_code, page)
            label = "접수중" if status_code == "ING" else "접수예정"
            print(f"[{label}] 페이지 {page} → {len(rows)}건 (전체 {total}건)")
            if not rows:
                break
            for row in rows:
                sn = str(row.get("pbancSn") or row.get("pbancId") or "")
                if sn and sn not in seen:
                    seen.add(sn)
                    results.append(parse_row(row))
            if len(seen) >= total or len(rows) < PAGE_SIZE:
                break
            page += 1

    # 상태별 카운트 계산
    open_count = sum(1 for r in results if r["status"] == "접수중")
    soon_count = sum(1 for r in results if r["status"] == "접수예정")
    closed_count = sum(1 for r in results if r["status"] == "마감")

    output = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "count": len(results),
        "open_count": open_count,
        "soon_count": soon_count,
        "closed_count": closed_count,
        "items": results
    }

    os.makedirs("data", exist_ok=True)
    with open("data/announcements.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 완료: 전체 {len(results)}건 | 접수중 {open_count} | 접수예정 {soon_count} | 마감 {closed_count}")


def parse_row(row: dict) -> dict:
    # 상태 코드 → 한글
    status_map = {
        "1": "접수중", "ING": "접수중",
        "2": "접수예정", "YET": "접수예정",
        "3": "마감", "END": "마감", "0": "마감",
    }

    sn      = str(row.get("pbancSn") or row.get("pbancId") or "")
    title   = row.get("dtlPbancNm") or row.get("pbancNm") or "(제목없음)"
    st_raw  = str(row.get("rcptStts") or "")
    status  = status_map.get(st_raw, st_raw or "확인필요")
    start   = fmt_date(row.get("rcptYmdDa2001") or row.get("rcptBgngDt") or "")
    end     = fmt_date(row.get("rcptYmdDa2002") or row.get("rcptEndDt") or "")

    # 상세 링크 - pbancId 파라미터 방식과 경로 방식 둘 다 시도
    pbancId = row.get("pbancId") or ""
    if pbancId:
        link = f"{BASE_URL}/usr/bg/ba/ma/bsnsPbanc?pbancId={pbancId}"
    elif sn:
        link = f"{BASE_URL}/usr/bg/ba/ma/bsnsPbanc?pbancSn={sn}"
    else:
        link = f"{BASE_URL}/usr/bg/ba/ma/bsnsPbanc"

    return {
        "title":  title,
        "status": status,
        "start":  start,
        "end":    end,
        "link":   link,
    }


def fmt_date(d):
    """20260101 → 2026-01-01"""
    d = str(d).strip()
    if len(d) == 8 and d.isdigit():
        return f"{d[:4]}-{d[4:6]}-{d[6:]}"
    return d


if __name__ == "__main__":
    crawl()
