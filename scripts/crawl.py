import asyncio
import json
import os
import re
from datetime import datetime
from playwright.async_api import async_playwright

BASE_URL = "https://www.smart-factory.kr"
TARGET_URL = f"{BASE_URL}/usr/bg/ba/ma/bsnsPblanc"

async def crawl():
    results = []import json
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
                for key in ["list", "items", "content", "data", "result", "rows"]:
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


    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # XHR 응답 인터셉트 - API 엔드포인트 자동 캐치
        api_data = []

        async def handle_response(response):
            url = response.url
            if "bsnsPblanc" in url or "pbanc" in url.lower() or "notice" in url.lower():
                try:
                    ct = response.headers.get("content-type", "")
                    if "json" in ct:
                        body = await response.json()
                        api_data.append({"url": url, "data": body})
                        print(f"[API 캐치] {url}")
                except Exception:
                    pass

        page.on("response", handle_response)

        print(f"페이지 로딩: {TARGET_URL}")
        await page.goto(TARGET_URL, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)

        # --- 방법 1: API 데이터로 파싱 ---
        if api_data:
            print(f"API 데이터 {len(api_data)}건 캐치됨")
            for item in api_data:
                data = item["data"]
                # 공통 패턴: list, items, content, data 키
                rows = None
                for key in ["list", "items", "content", "data", "result", "rows"]:
                    if isinstance(data, dict) and key in data:
                        rows = data[key]
                        break
                if isinstance(data, list):
                    rows = data

                if rows:
                    for row in rows:
                        results.append(parse_row(row))

        # --- 방법 2: DOM 파싱 (API 못 잡은 경우 fallback) ---
        if not results:
            print("DOM 파싱 시도...")
            rows = await page.query_selector_all("table tbody tr, .list-item, .board-item, li[class*='item']")
            print(f"DOM 행 {len(rows)}개 발견")

            for row in rows:
                text = await row.inner_text()
                text = text.strip()
                if not text or len(text) < 5:
                    continue

                # 링크 추출
                link_el = await row.query_selector("a")
                href = ""
                if link_el:
                    href = await link_el.get_attribute("href") or ""
                    if href and not href.startswith("http"):
                        href = BASE_URL + href

                # 날짜 패턴 추출
                date_match = re.search(r"(\d{4}[-./]\d{2}[-./]\d{2})", text)
                date_str = date_match.group(1) if date_match else ""

                # 상태 추출
                status = ""
                if "접수중" in text:
                    status = "접수중"
                elif "접수예정" in text or "예정" in text:
                    status = "접수예정"
                elif "마감" in text or "종료" in text:
                    status = "마감"

                lines = [l.strip() for l in text.split("\n") if l.strip()]
                title = lines[0] if lines else text[:50]

                results.append({
                    "title": title,
                    "status": status,
                    "date": date_str,
                    "link": href,
                    "raw": text[:200]
                })

        await browser.close()

    # 결과 저장
    output = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "count": len(results),
        "items": results
    }

    os.makedirs("data", exist_ok=True)
    with open("data/announcements.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 완료: {len(results)}건 저장 → data/announcements.json")
    return results


def parse_row(row: dict) -> dict:
    """API JSON 행을 공통 포맷으로 변환"""
    # 흔한 키 이름 매핑
    def get(keys):
        for k in keys:
            if k in row:
                return str(row[k])
        return ""

    title = get(["pbancNm", "title", "ttl", "subject", "name", "bsnsPbancNm"])
    status = get(["rcptStatNm", "status", "stat", "statNm", "rcptStat"])
    start = get(["rcptBgngDt", "startDate", "bgngDt", "startDt", "fromDt"])
    end = get(["rcptEndDt", "endDate", "endDt", "toDt", "closeDt"])
    link_id = get(["pbancSn", "id", "sn", "seq", "no"])
    link = f"{BASE_URL}/usr/bg/ba/ma/bsnsPblanc/{link_id}" if link_id else BASE_URL

    return {
        "title": title,
        "status": status,
        "start": start,
        "end": end,
        "link": link,
        "raw_keys": list(row.keys())[:10]  # 디버그용
    }


if __name__ == "__main__":
    asyncio.run(crawl())
