import json
import os
from datetime import datetime

def load_data():
    try:
        with open("data/announcements.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"updated_at": "-", "count": 0, "items": []}

def status_badge(status):
    if "접수중" in status:
        return f'<span class="badge open">🟢 {status}</span>'
    elif "예정" in status:
        return f'<span class="badge soon">🔵 {status}</span>'
    elif "마감" in status or "종료" in status:
        return f'<span class="badge closed">⚫ {status}</span>'
    else:
        return f'<span class="badge etc">⚪ {status or "확인필요"}</span>'

def build_rows(items):
    if not items:
        return '<tr><td colspan="5" class="empty">현재 공고 데이터가 없습니다.</td></tr>'

    rows = []
    for i, item in enumerate(items, 1):
        title  = (item.get("title") or "-").replace("'", "\\'")
        status = item.get("status", "")
        start  = item.get("start") or "-"
        end    = item.get("end") or "-"
        pbanc_id = item.get("pbancId", "")
        pbanc_sn = item.get("pbancSn", "")
        period = f"{start} ~ {end}" if end and end != "-" else start or "-"

        rows.append(f"""
        <tr>
            <td class="num">{i}</td>
            <td class="title">
                <a href="#" onclick="openModal('{pbanc_id}','{pbanc_sn}','{title}'); return false;">{item.get('title','')}</a>
            </td>
            <td>{status_badge(status)}</td>
            <td class="period">{period}</td>
            <td>
                <button class="btn-detail" onclick="openModal('{pbanc_id}','{pbanc_sn}','{title}')">상세보기</button>
            </td>
        </tr>""")

    return "\n".join(rows)

def build_html(data):
    updated    = data.get("updated_at", "-")
    count      = data.get("count", 0)
    items      = data.get("items", [])
    open_count = sum(1 for i in items if "접수중" in i.get("status", ""))
    soon_count = sum(1 for i in items if "예정"  in i.get("status", ""))
    rows_html  = build_rows(items)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>스마트공장 사업공고 대시보드</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Pretendard','Apple SD Gothic Neo',sans-serif; background:#f4f6f9; color:#222; min-height:100vh; }}
    header {{ background:linear-gradient(135deg,#1a4fa0,#2d7dd2); color:white; padding:28px 40px; }}
    header h1 {{ font-size:1.6rem; font-weight:700; margin-bottom:6px; }}
    header p {{ font-size:0.85rem; opacity:0.8; }}
    .stats {{ display:flex; gap:16px; padding:24px 40px; background:white; border-bottom:1px solid #e0e0e0; }}
    .stat-card {{ background:#f8faff; border:1px solid #d0dff5; border-radius:10px; padding:14px 24px; text-align:center; min-width:120px; }}
    .stat-card .num {{ font-size:2rem; font-weight:800; color:#1a4fa0; }}
    .stat-card .label {{ font-size:0.78rem; color:#666; margin-top:4px; }}
    .toolbar {{ padding:16px 40px; display:flex; align-items:center; gap:12px; }}
    .toolbar input {{ padding:8px 14px; border:1px solid #ccc; border-radius:6px; font-size:0.9rem; width:260px; }}
    .toolbar select {{ padding:8px 12px; border:1px solid #ccc; border-radius:6px; font-size:0.9rem; background:white; }}
    .container {{ padding:0 40px 40px; }}
    table {{ width:100%; border-collapse:collapse; background:white; border-radius:12px; overflow:hidden; box-shadow:0 2px 12px rgba(0,0,0,0.07); }}
    thead {{ background:#1a4fa0; color:white; }}
    thead th {{ padding:14px 16px; font-size:0.85rem; font-weight:600; text-align:left; }}
    tbody tr {{ border-bottom:1px solid #f0f0f0; transition:background 0.15s; }}
    tbody tr:hover {{ background:#f5f8ff; }}
    td {{ padding:14px 16px; font-size:0.88rem; vertical-align:middle; }}
    td.num {{ color:#999; width:50px; text-align:center; }}
    td.title a {{ color:#1a1a1a; text-decoration:none; font-weight:500; line-height:1.5; }}
    td.title a:hover {{ color:#1a4fa0; text-decoration:underline; }}
    td.period {{ color:#555; font-size:0.82rem; white-space:nowrap; }}
    .badge {{ display:inline-block; padding:4px 10px; border-radius:20px; font-size:0.78rem; font-weight:600; white-space:nowrap; }}
    .badge.open   {{ background:#e6f7ee; color:#1a7a40; }}
    .badge.soon   {{ background:#e8f0fe; color:#1a4fa0; }}
    .badge.closed {{ background:#f0f0f0; color:#777; }}
    .badge.etc    {{ background:#fafafa; color:#999; }}
    .btn-detail {{ display:inline-block; padding:5px 12px; background:#1a4fa0; color:white; border-radius:5px; font-size:0.78rem; border:none; cursor:pointer; white-space:nowrap; }}
    .btn-detail:hover {{ background:#153d80; }}
    td.empty {{ text-align:center; padding:40px; color:#aaa; }}
    .source-link {{ text-align:right; padding:16px 40px; font-size:0.8rem; color:#999; }}
    .source-link a {{ color:#1a4fa0; }}

    /* 모달 */
    .modal-overlay {{ display:none; position:fixed; inset:0; background:rgba(0,0,0,0.5); z-index:1000; align-items:center; justify-content:center; }}
    .modal-overlay.active {{ display:flex; }}
    .modal {{ background:white; border-radius:16px; width:90%; max-width:720px; max-height:85vh; overflow-y:auto; box-shadow:0 8px 40px rgba(0,0,0,0.2); }}
    .modal-header {{ padding:24px 28px 16px; border-bottom:1px solid #eee; display:flex; justify-content:space-between; align-items:flex-start; gap:16px; }}
    .modal-header h2 {{ font-size:1.05rem; font-weight:700; line-height:1.5; color:#111; }}
    .modal-close {{ background:none; border:none; font-size:1.5rem; cursor:pointer; color:#999; flex-shrink:0; }}
    .modal-close:hover {{ color:#333; }}
    .modal-body {{ padding:24px 28px; }}
    .modal-body .loading {{ text-align:center; color:#999; padding:40px 0; }}
    .detail-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:20px; }}
    .detail-item {{ background:#f8faff; border-radius:8px; padding:14px 16px; }}
    .detail-item .label {{ font-size:0.75rem; color:#888; margin-bottom:4px; }}
    .detail-item .value {{ font-size:0.9rem; font-weight:600; color:#111; }}
    .detail-desc {{ background:#f8f8f8; border-radius:8px; padding:16px; font-size:0.88rem; line-height:1.7; color:#333; white-space:pre-wrap; word-break:break-all; }}
    .modal-footer {{ padding:16px 28px 24px; display:flex; justify-content:flex-end; gap:10px; }}
    .btn-site {{ padding:9px 20px; background:#1a4fa0; color:white; border-radius:6px; text-decoration:none; font-size:0.88rem; font-weight:600; }}
    .btn-site:hover {{ background:#153d80; }}
    .btn-cancel {{ padding:9px 20px; background:#f0f0f0; color:#555; border:none; border-radius:6px; font-size:0.88rem; cursor:pointer; }}

    @media (max-width:768px) {{
      header,.stats,.toolbar,.container,.source-link {{ padding-left:16px; padding-right:16px; }}
      .stats {{ flex-wrap:wrap; }}
      thead th:nth-child(1), thead th:nth-child(4), td.num, td.period {{ display:none; }}
      .detail-grid {{ grid-template-columns:1fr; }}
    }}
  </style>
</head>
<body>

<header>
  <h1>🏭 스마트공장 사업공고 대시보드</h1>
  <p>smart-factory.kr 공식 사업공고를 자동 수집합니다 · 최종 업데이트: {updated}</p>
</header>

<div class="stats">
  <div class="stat-card">
    <div class="num">{count}</div>
    <div class="label">전체 공고</div>
  </div>
  <div class="stat-card">
    <div class="num" style="color:#1a7a40">{open_count}</div>
    <div class="label">🟢 접수중</div>
  </div>
  <div class="stat-card">
    <div class="num" style="color:#2d7dd2">{soon_count}</div>
    <div class="label">🔵 접수예정</div>
  </div>
</div>

<div class="toolbar">
  <input type="text" id="searchInput" placeholder="🔍 공고명 검색..." oninput="filterTable()">
  <select id="statusFilter" onchange="filterTable()">
    <option value="">전체 상태</option>
    <option value="접수중">🟢 접수중</option>
    <option value="접수예정">🔵 접수예정</option>
    <option value="마감">⚫ 마감</option>
  </select>
</div>

<div class="container">
  <table id="mainTable">
    <thead>
      <tr>
        <th style="width:50px">No.</th>
        <th>공고명</th>
        <th style="width:120px">상태</th>
        <th style="width:200px">접수기간</th>
        <th style="width:90px">상세보기</th>
      </tr>
    </thead>
    <tbody id="tableBody">
      {rows_html}
    </tbody>
  </table>
</div>

<div class="source-link">
  데이터 출처: <a href="https://www.smart-factory.kr/usr/bg/ba/ma/bsnsPblanc" target="_blank">smart-factory.kr 사업공고</a>
</div>

<!-- 모달 -->
<div class="modal-overlay" id="modalOverlay" onclick="closeModalOutside(event)">
  <div class="modal">
    <div class="modal-header">
      <h2 id="modalTitle">공고 상세</h2>
      <button class="modal-close" onclick="closeModal()">✕</button>
    </div>
    <div class="modal-body" id="modalBody">
      <div class="loading">불러오는 중...</div>
    </div>
    <div class="modal-footer">
      <button class="btn-cancel" onclick="closeModal()">닫기</button>
      <a class="btn-site" href="https://www.smart-factory.kr/usr/bg/ba/ma/bsnsPblanc" target="_blank" id="modalSiteLink">공고 목록 보기 →</a>
    </div>
  </div>
</div>

<script>
const API_DTL = 'https://www.smart-factory.kr/usr/bg/ba/ma/bsnsPbanc/selectBsnsPbancDtlPage.do';

async function openModal(pbancId, pbancSn, title) {{
  document.getElementById('modalTitle').textContent = title;
  document.getElementById('modalBody').innerHTML = '<div class="loading">⏳ 공고 내용을 불러오는 중...</div>';
  document.getElementById('modalOverlay').classList.add('active');
  document.body.style.overflow = 'hidden';

  try {{
    const res = await fetch(API_DTL, {{
      method: 'POST',
      headers: {{
        'Content-Type': 'application/json',
        'Referer': 'https://www.smart-factory.kr/usr/bg/ba/ma/bsnsPbancDtl'
      }},
      body: JSON.stringify({{ key: 'info', pbancId: pbancId, pbancSn: parseInt(pbancSn) }})
    }});
    const data = await res.json();
    const info = data?.modelAndView?.model?.pbancInfo || data?.pbancInfo || data;
    renderModal(info);
  }} catch(e) {{
    document.getElementById('modalBody').innerHTML = `
      <div class="loading">
        ⚠️ 상세 정보를 불러올 수 없습니다.<br>
        <a href="https://www.smart-factory.kr/usr/bg/ba/ma/bsnsPblanc" target="_blank" style="color:#1a4fa0">공고 목록에서 직접 확인하기 →</a>
      </div>`;
  }}
}}

function renderModal(info) {{
  if (!info || Object.keys(info).length === 0) {{
    document.getElementById('modalBody').innerHTML = '<div class="loading">상세 정보가 없습니다.</div>';
    return;
  }}

  const get = (...keys) => {{ for(const k of keys) if(info[k]) return info[k]; return '-'; }};
  const fmtDate = d => d && d.length===8 ? d.slice(0,4)+'-'+d.slice(4,6)+'-'+d.slice(6) : (d||'-');

  document.getElementById('modalBody').innerHTML = `
    <div class="detail-grid">
      <div class="detail-item"><div class="label">접수 시작일</div><div class="value">${{fmtDate(get('rcptYmdDa2001','rcptBgngDt'))}}</div></div>
      <div class="detail-item"><div class="label">접수 마감일</div><div class="value">${{fmtDate(get('rcptYmdDa2002','rcptEndDt'))}}</div></div>
      <div class="detail-item"><div class="label">사업 연도</div><div class="value">${{get('bizYr')}}</div></div>
      <div class="detail-item"><div class="label">공고 번호</div><div class="value">${{get('pbancNo','pbancId')}}</div></div>
    </div>
    <div class="detail-desc">${{get('pbancCn','dtlPbancNm','cn','content').replace(/</g,'&lt;').replace(/>/g,'&gt;')}}</div>
  `;
}}

function closeModal() {{
  document.getElementById('modalOverlay').classList.remove('active');
  document.body.style.overflow = '';
}}

function closeModalOutside(e) {{
  if (e.target === document.getElementById('modalOverlay')) closeModal();
}}

document.addEventListener('keydown', e => {{ if(e.key==='Escape') closeModal(); }});

function filterTable() {{
  const search = document.getElementById('searchInput').value.toLowerCase();
  const status = document.getElementById('statusFilter').value;
  document.querySelectorAll('#tableBody tr').forEach(row => {{
    const title  = row.querySelector('.title')?.textContent.toLowerCase() || '';
    const badge  = row.querySelector('.badge')?.textContent || '';
    row.style.display = (!search || title.includes(search)) && (!status || badge.includes(status)) ? '' : 'none';
  }});
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
