import streamlit as st
import datetime
from utils.db_helper import execute_query
from utils.style import inject_css

inject_css()

st.title("NCS 기반 지능형 커리어 네비게이터")
st.subheader("나에게 딱 맞는 자격증을 찾아보세요")

today = datetime.date.today()

if 'user' in st.session_state:
    u = st.session_state['user']
    st.info(f"{u['name']}님, 환영합니다.")

    # ── 즐겨찾기 D-Day 위젯 ────────────────────────────────────────────────────
    uid = u['user_id']
    upcoming = execute_query("""
        SELECT c.cert_name, s.exam_type, s.round_name,
               s.apply_start, s.apply_end, s.exam_date
        FROM user_bookmarks b
        JOIN certifications c  ON b.cert_id  = c.cert_id
        JOIN cert_schedules s  ON b.cert_id  = s.cert_id
        WHERE b.user_id = %s
          AND s.exam_date >= %s
        ORDER BY s.exam_date ASC
        LIMIT 10
    """, (uid, str(today)))

    if upcoming:
        # 각 일정의 가장 긴박한 날짜 계산
        def _key_item(row):
            def _d(v):
                if v is None: return None
                return datetime.date.fromisoformat(str(v)) if isinstance(v, str) else v
            apply_start = _d(row['apply_start'])
            apply_end   = _d(row['apply_end'])
            exam_date   = _d(row['exam_date'])
            if apply_start and apply_start > today:
                return apply_start, f"접수 시작 D-{(apply_start - today).days}", '#1565C0'
            elif apply_end and apply_end >= today:
                delta = (apply_end - today).days
                txt = '접수 마감 D-DAY' if delta == 0 else f'접수 마감 D-{delta}'
                color = '#C62828' if delta <= 3 else ('#E65100' if delta <= 7 else '#FF8F00')
                return apply_end, txt, color
            elif exam_date:
                delta = (exam_date - today).days
                txt = '시험 D-DAY' if delta == 0 else f'시험 D-{delta}'
                color = '#C62828' if delta <= 14 else '#1565C0'
                return exam_date, txt, color
            return exam_date, '', '#9E9E9E'

        items = sorted(
            [(*_key_item(r), r) for r in upcoming],
            key=lambda x: x[0]
        )[:4]

        EXAM_COLOR = {'필기': '#1565C0', '실기': '#2E7D32'}

        st.markdown("#### 즐겨찾기 일정")
        cols = st.columns(len(items))
        for col, (key_date, label, color, row) in zip(cols, items):
            exam_color = EXAM_COLOR.get(row['exam_type'], '#555')
            with col:
                with st.container(border=True):
                    st.markdown(
                        f"<span style='background:{exam_color};color:white;padding:1px 7px;"
                        f"border-radius:4px;font-size:0.75em'>{row['exam_type']}</span>",
                        unsafe_allow_html=True
                    )
                    st.markdown(f"**{row['cert_name']}**")
                    st.caption(row['round_name'] or '')
                    st.markdown(
                        f"<span style='color:{color};font-weight:700;font-size:1.1em'>{label}</span>",
                        unsafe_allow_html=True
                    )
        st.markdown("")
else:
    st.caption("로그인하면 프로필을 저장하고 다음에도 자동완성으로 편리하게 사용할 수 있습니다.")

st.markdown("---")

# ── DB 통계 ─────────────────────────────────────────────────────────────────────
try:
    stats = {
        'total_certs': execute_query("SELECT COUNT(*) as cnt FROM certifications")[0]['cnt'],
        'ncs_cats':    execute_query("SELECT COUNT(*) as cnt FROM ncs_categories")[0]['cnt'],
        'users':       execute_query("SELECT COUNT(*) as cnt FROM users")[0]['cnt'],
        'schedules':   execute_query("SELECT COUNT(*) as cnt FROM cert_schedules")[0]['cnt'],
    }
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("등록 자격증", f"{stats['total_certs']:,}개")
    c2.metric("NCS 직무 분류", f"{stats['ncs_cats']:,}개")
    c3.metric("가입 사용자", f"{stats['users']:,}명")
    c4.metric("시험 일정", f"{stats['schedules']:,}건")
except Exception:
    pass

st.markdown("---")

col_intro, col_how = st.columns(2)

with col_intro:
    st.markdown("### 서비스 소개")
    st.markdown("""
NCS(국가직무능력표준) 분류 체계를 기반으로,
전공·경력·관심분야에 맞는 **자격증을 AI가 지능형으로 추천**해드립니다.

- **SBERT 의미론적 유사도** 분석으로 전공·분야 매칭
- **학력·경력 조건 필터링**으로 응시 가능한 자격증만 추천
- **레벨별 그룹 추천** (기능사 → 기사 → 기술사)
- **커리어 로드맵** 제시로 단계적 취득 전략 수립
""")

with col_how:
    st.markdown("### 사용 방법")
    st.markdown("""
1. **로그인 / 회원가입** — 내 계정 만들기
2. **프로필 입력** — 전공·경력·보유 자격증 등록
3. **자격증 추천** — AI 맞춤 추천 받기
4. **커리어 로드맵** — 단계별 취득 경로 확인
5. **시험 일정** — 접수·시험 날짜 확인
""")

st.markdown("---")

st.markdown("### 빠른 시작")
qc1, qc2, qc3 = st.columns(3)
with qc1:
    st.page_link("pages/3_🔍_자격증추천.py", label="자격증 추천 받기", use_container_width=True)
with qc2:
    st.page_link("pages/5_🗺️_커리어로드맵.py", label="커리어 로드맵", use_container_width=True)
with qc3:
    st.page_link("pages/4_📅_시험일정.py", label="시험 일정 확인", use_container_width=True)
