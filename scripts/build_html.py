import json
import os
import re

def load_data():
    try:
        with open("data/announcements.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"updated_at": "-", "count": 0, "items": []}

def extract_org(title):
    """제목에서 주관기관 추출 - [현대자동차그룹] 형태"""
    m = re.match(r'\[([^\]]+)\]', title)
    return m.group(1).strip() if m else "기타"

def extract_year(title):
    m = re.search(r'(20\d{2})년', title)
    return m.group(1) if m else "기타"

REGIONS = ["서울","부산","대구","인천","광주","대전","울산","세종","경기","강원","충북","충남","전북","전남","경북","경남","제주","전국","수도권"]

def extract_region(title):
    for r in REGIONS:
        if r in title:
            return r
    return "전국/기타"

def status_badge(status):
    if "접수중" in status:
        return f'<span class="badge open">🟢 접수중</span>'
    elif "예정" in status:
        return f'<span class="badge soon">🔵 접수예정</span>'
    elif "마감" in status or "종료" in status:
        return f'<span class="badge closed">⚫ 마감</span>'
    else:
        return f'<span class="badge etc">⚪ {status or "-"}</span>'

def build_rows(items):
    if not items:
        return '<tr><td colspan="5" class="empty">현재 공고 데이터가 없습니다.</td></tr>'
    rows = []
    for i, item in enumerate(items, 1):
        title  = item.get("title", "-")
        status = item.get("status", "")
        start  = item.get("start") or "-"
        end    = item.get("end") or ""
        org    = extract_org(title)
        year   = extract_year(title)
        region = extract_region(title)
        period = f"{start}" if not end else f"{start} ~ {end}"

        rows.append(f"""<tr data-status="{status}" data-org="{org}" data-year="{year}" data-region="{region}">
            <td class="num">{i}</td>
            <td class="title">{title}</td>
            <td>{status_badge(status)}</td>
            <td class="period">{period}</td>
            <td><span class="tag-org">{org}</span></td>
        </tr>""")
    return "\n".join(rows)

def get_unique(items, fn):
    seen = []
    for item in items:
        v = fn(item.get("title",""))
        if v not in seen:
            seen.append(v)
    return sorted(seen)

def build_html(data):
    updated    = data.get("updated_at", "-")
    count      = data.get("count", 0)
    items      = data.get("items", [])
    open_count = sum(1 for i in items if "접수중" in i.get("status",""))
    soon_count = sum(1 for i in items if "예정"  in i.get("status",""))
    rows_html  = build_rows(items)

    orgs    = get_unique(items, extract_org)
    years   = get_unique(items, extract_year)
    regions = get_unique(items, extract_region)

    org_opts    = "\n".join(f'<option value="{o}">{o}</option>' for o in orgs)
    year_opts   = "\n".join(f'<option value="{y}">{y}년</option>' for y in years)
    region_opts = "\n".join(f'<option value="{r}">{r}</option>' for r in regions)

    # 마감임박 (start 필드에 날짜 포함된 것 기준 - 단순 카운트)
    deadline_count = sum(1 for i in items if i.get("start") and "2026-06" in i.get("start",""))

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>스마트공장 사업공고 대시보드</title>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0;}}
    body{{font-family:'Pretendard','Apple SD Gothic Neo',sans-serif;background:#eef2f7;color:#1a1a1a;min-height:100vh;}}

    /* 헤더 */
    header{{background:linear-gradient(135deg,#0f3470,#1a6fd4);color:white;padding:28px 40px;display:flex;justify-content:space-between;align-items:center;}}
    header h1{{font-size:1.5rem;font-weight:800;letter-spacing:-0.5px;}}
    header p{{font-size:0.8rem;opacity:0.75;margin-top:5px;}}
    .btn-official{{padding:10px 20px;background:white;color:#1a4fa0;border-radius:8px;font-size:0.85rem;font-weight:700;text-decoration:none;white-space:nowrap;transition:all 0.2s;}}
    .btn-official:hover{{background:#e8f0fe;}}

    /* KPI 카드 */
    .kpi-section{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;padding:24px 40px;}}
    .kpi-card{{background:white;border-radius:14px;padding:20px 24px;box-shadow:0 2px 10px rgba(0,0,0,0.06);display:flex;align-items:center;gap:16px;}}
    .kpi-icon{{width:48px;height:48px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:1.4rem;flex-shrink:0;}}
    .kpi-icon.blue{{background:#e8f0fe;}}
    .kpi-icon.green{{background:#e6f7ee;}}
    .kpi-icon.orange{{background:#fff4e6;}}
    .kpi-icon.purple{{background:#f3eeff;}}
    .kpi-num{{font-size:1.9rem;font-weight:900;line-height:1;}}
    .kpi-num.blue{{color:#1a4fa0;}}
    .kpi-num.green{{color:#1a7a40;}}
    .kpi-num.orange{{color:#d4720a;}}
    .kpi-num.purple{{color:#6b3fa0;}}
    .kpi-label{{font-size:0.78rem;color:#888;margin-top:3px;}}

    /* 필터 툴바 */
    .toolbar{{background:white;margin:0 40px 20px;border-radius:12px;padding:16px 20px;display:flex;flex-wrap:wrap;gap:10px;align-items:center;box-shadow:0 2px 8px rgba(0,0,0,0.05);}}
    .toolbar input{{padding:8px 14px;border:1.5px solid #dde3ef;border-radius:8px;font-size:0.88rem;width:240px;outline:none;transition:border 0.2s;}}
    .toolbar input:focus{{border-color:#1a4fa0;}}
    .toolbar select{{padding:8px 12px;border:1.5px solid #dde3ef;border-radius:8px;font-size:0.88rem;background:white;outline:none;cursor:pointer;}}
    .toolbar select:focus{{border-color:#1a4fa0;}}
    .filter-label{{font-size:0.78rem;color:#888;font-weight:600;}}
    .btn-reset{{padding:8px 14px;background:#f0f0f0;border:none;border-radius:8px;font-size:0.82rem;color:#555;cursor:pointer;}}
    .btn-reset:hover{{background:#e0e0e0;}}
    .result-count{{margin-left:auto;font-size:0.82rem;color:#888;}}

    /* 테이블 */
    .table-wrap{{margin:0 40px 40px;background:white;border-radius:14px;box-shadow:0 2px 10px rgba(0,0,0,0.06);overflow:hidden;}}
    .table-scroll{{max-height:520px;overflow-y:auto;}}
    .table-scroll::-webkit-scrollbar{{width:6px;}}
    .table-scroll::-webkit-scrollbar-thumb{{background:#c5d0e0;border-radius:3px;}}
    table{{width:100%;border-collapse:collapse;}}
    thead{{position:sticky;top:0;z-index:10;}}
    thead tr{{background:#1a4fa0;color:white;}}
    thead th{{padding:13px 16px;font-size:0.82rem;font-weight:600;text-align:left;white-space:nowrap;}}
    tbody tr{{border-bottom:1px solid #f0f4fa;transition:background 0.12s;}}
    tbody tr:last-child{{border-bottom:none;}}
    tbody tr:hover{{background:#f5f8ff;}}
    td{{padding:13px 16px;font-size:0.86rem;vertical-align:middle;}}
    td.num{{color:#bbb;width:44px;text-align:center;font-size:0.78rem;}}
    td.title{{font-weight:500;line-height:1.5;color:#1a1a1a;max-width:380px;}}
    td.period{{color:#555;font-size:0.8rem;white-space:nowrap;}}
    .tag-org{{display:inline-block;padding:3px 9px;background:#eef2f7;color:#556;border-radius:20px;font-size:0.75rem;font-weight:600;}}
    .badge{{display:inline-block;padding:4px 10px;border-radius:20px;font-size:0.76rem;font-weight:700;white-space:nowrap;}}
    .badge.open{{background:#e6f7ee;color:#1a7a40;}}
    .badge.soon{{background:#e8f0fe;color:#1a4fa0;}}
    .badge.closed{{background:#f0f0f0;color:#999;}}
    .badge.etc{{background:#fafafa;color:#bbb;}}
    td.empty{{text-align:center;padding:60px;color:#bbb;font-size:0.9rem;}}

    /* 하단 */
    .footer{{text-align:center;padding:20px;font-size:0.78rem;color:#aaa;}}
    .footer a{{color:#1a4fa0;}}

    @media(max-width:900px){{
      .kpi-section{{grid-template-columns:1fr 1fr;padding:16px;}}
      header,.toolbar,.table-wrap{{padding-left:16px;padding-right:16px;margin-left:0;margin-right:0;}}
      .toolbar{{margin:0 0 16px;border-radius:0;}}
      .table-wrap{{margin:0 0 24px;border-radius:0;}}
      thead th:nth-child(1),td.num{{display:none;}}
      td.title{{max-width:200px;}}
    }}
  </style>
</head>
<body>

<header>
  <div>
    <h1>🏭 스마트공장 사업공고 대시보드</h1>
    <p>smart-factory.kr 공식 공고를 매일 자동 수집 · 최종 업데이트: {updated}</p>
  </div>
  <a class="btn-official" href="https://www.smart-factory.kr/usr/bg/ba/ma/bsnsPblanc" target="_blank">📋 공식 공고 목록 →</a>
</header>

<!-- KPI -->
<div class="kpi-section">
  <div class="kpi-card">
    <div class="kpi-icon blue">📋</div>
    <div>
      <div class="kpi-num blue">{count}</div>
      <div class="kpi-label">전체 접수중 공고</div>
    </div>
  </div>
  <div class="kpi-card">
    <div class="kpi-icon green">✅</div>
    <div>
      <div class="kpi-num green">{open_count}</div>
      <div class="kpi-label">접수중</div>
    </div>
  </div>
  <div class="kpi-card">
    <div class="kpi-icon orange">🔔</div>
    <div>
      <div class="kpi-num orange">{soon_count}</div>
      <div class="kpi-label">접수예정</div>
    </div>
  </div>
  <div class="kpi-card">
    <div class="kpi-icon purple">⏰</div>
    <div>
      <div class="kpi-num purple">{deadline_count}</div>
      <div class="kpi-label">이달 마감</div>
    </div>
  </div>
</div>

<!-- 필터 -->
<div class="toolbar">
  <span class="filter-label">🔍</span>
  <input type="text" id="searchInput" placeholder="공고명 검색..." oninput="applyFilter()">
  <select id="statusFilter" onchange="applyFilter()">
    <option value="">전체 상태</option>
    <option value="접수중">🟢 접수중</option>
    <option value="접수예정">🔵 접수예정</option>
  </select>
  <select id="yearFilter" onchange="applyFilter()">
    <option value="">전체 연도</option>
    {year_opts}
  </select>
  <select id="orgFilter" onchange="applyFilter()">
    <option value="">전체 주관기관</option>
    {org_opts}
  </select>
  <select id="regionFilter" onchange="applyFilter()">
    <option value="">전체 지역</option>
    {region_opts}
  </select>
  <button class="btn-reset" onclick="resetFilter()">초기화</button>
  <span class="result-count" id="resultCount">{count}건</span>
</div>

<!-- 테이블 -->
<div class="table-wrap">
  <div class="table-scroll">
    <table id="mainTable">
      <thead>
        <tr>
          <th style="width:44px">No.</th>
          <th>공고명</th>
          <th style="width:110px">상태</th>
          <th style="width:210px">접수기간</th>
          <th style="width:130px">주관기관</th>
        </tr>
      </thead>
      <tbody id="tableBody">
        {rows_html}
      </tbody>
    </table>
  </div>
</div>

<div class="footer">
  데이터 출처: <a href="https://www.smart-factory.kr/usr/bg/ba/ma/bsnsPblanc" target="_blank">스마트공장 사업관리시스템</a> · 매일 오전 10시 자동 갱신
</div>

<script>
function applyFilter() {{
  const search  = document.getElementById('searchInput').value.toLowerCase();
  const status  = document.getElementById('statusFilter').value;
  const year    = document.getElementById('yearFilter').value;
  const org     = document.getElementById('orgFilter').value;
  const region  = document.getElementById('regionFilter').value;
  let count = 0;
  document.querySelectorAll('#tableBody tr').forEach(row => {{
    const title   = row.querySelector('.title')?.textContent.toLowerCase() || '';
    const badge   = row.querySelector('.badge')?.textContent || '';
    const rowOrg  = row.dataset.org || '';
    const rowYear = row.dataset.year || '';
    const rowReg  = row.dataset.region || '';
    const ok = (!search || title.includes(search))
            && (!status || badge.includes(status))
            && (!year   || rowYear === year)
            && (!org    || rowOrg  === org)
            && (!region || rowReg  === region);
    row.style.display = ok ? '' : 'none';
    if(ok) count++;
  }});
  document.getElementById('resultCount').textContent = count + '건';
}}

function resetFilter() {{
  ['searchInput'].forEach(id => document.getElementById(id).value = '');
  ['statusFilter','yearFilter','orgFilter','regionFilter'].forEach(id => document.getElementById(id).selectedIndex = 0);
  applyFilter();
}}
</script>
</body>
</html>"""

def main():
    data = load_data()
    html = build_html(data)
    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ HTML 생성 완료: docs/index.html ({data['count']}건)")

if __name__ == "__main__":
    main()
