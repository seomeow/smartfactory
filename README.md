[README.md](https://github.com/user-attachments/files/29252210/README.md)
# smartfactory# 🏭 스마트공장 사업공고 대시보드

smart-factory.kr 사업공고를 매일 자동 수집해서 GitHub Pages로 보여주는 대시보드입니다.

---

## 📁 구조

```
smart-factory-dashboard/
├── .github/workflows/crawl.yml   # GitHub Actions (자동 크롤링 + 배포)
├── scripts/
│   ├── crawl.py                  # Playwright 크롤러
│   └── build_html.py             # JSON → HTML 빌더
├── data/
│   └── announcements.json        # 크롤링 결과 (자동 생성)
└── docs/
    └── index.html                # 배포될 HTML (자동 생성)
```

---

## 🚀 배포 방법 (복붙만 하면 됨)

### 1단계: GitHub 레포 생성
- GitHub에서 새 레포 생성 (public 권장)
- 이 파일들 전부 업로드

### 2단계: GitHub Pages 설정
- 레포 → Settings → Pages
- Source: **Deploy from a branch**
- Branch: `main` / Folder: `/docs`
- Save

### 3단계: 끝
- Actions 탭 → `스마트공장 공고 자동 수집` → `Run workflow` 클릭
- 1~2분 후 `https://{username}.github.io/{레포이름}` 접속

---

## ⏰ 자동 실행 스케줄
- 매일 오전 10시 (KST) 자동 실행
- 수동 실행: Actions 탭 → Run workflow

---

## ⚠️ 크롤링 결과가 비어있을 때

smart-factory.kr가 SPA(React)라 초기 실행 시 API 엔드포인트를 못 잡을 수 있어요.

그럴 경우:
1. 브라우저 개발자도구 → Network 탭 → smart-factory.kr 공고 페이지 접속
2. XHR/Fetch 필터 → JSON 응답 URL 확인
3. `crawl.py` 상단 `TARGET_URL` 또는 인터셉트 키워드 수정
