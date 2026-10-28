import streamlit as st
import datetime
from collections import defaultdict
from utils.db_helper import execute_query, execute_insert
from utils.style import inject_css, level_chip

st.title("즐겨찾기")
inject_css()

if 'user' not in st.session_state:
    st.info("즐겨찾기를 이용하려면 로그인이 필요합니다.")
    st.page_link("pages/1_👤_로그인.py", label="로그인하러 가기", icon=":material/person:")
    st.stop()

user_id = st.session_state['user']['user_id']
today   = datetime.date.today()

LEVEL_LABEL = {3: '기능사', 5: '산업기사', 6: '기사', 7: '기능장', 8: '기술사'}
EXAM_COLOR  = {'필기': '#1565C0', '실기': '#2E7D32'}


def _to_date(d):
    if d is None:
        return None
    if isinstance(d, str):
        return datetime.date.fromisoformat(d)
    return d


def _fmt(d) -> str:
    d = _to_date(d)
    return d.strftime("%Y.%m.%d") if d else "-"


def _exam_chip(exam_type: str) -> str:
    color = EXAM_COLOR.get(exam_type, '#555')
    return (f"<span style='background:{color};color:white;padding:2px 8px;"
            f"border-radius:4px;font-size:0.8em;font-weight:600'>{exam_type}</span>")


# ── 데이터 로드 ─────────────────────────────────────────────────────────────────
bookmarks = execute_query("""
    SELECT b.bookmark_id, b.cert_id, c.cert_name, c.cert_type, c.ncs_level,
           c.pass_rate, c.issuing_org, b.created_at
    FROM user_bookmarks b
    JOIN certifications c ON b.cert_id = c.cert_id
    WHERE b.user_id = %s
    ORDER BY b.created_at DESC
""", (user_id,))

if not bookmarks:
    st.info("즐겨찾기한 자격증이 없습니다.")
    st.caption("자격증 추천 결과에서 ☆ 버튼을 눌러 즐겨찾기에 추가하세요.")
    st.page_link("pages/3_🔍_자격증추천.py", label="자격증 추천 받으러 가기", icon=":material/search:")
    st.stop()

# 모든 upcoming 일정 로드
cert_ids = [bk['cert_id'] for bk in bookmarks]
phs = ','.join(['%s'] * len(cert_ids))
all_schedules = execute_query(
    f"SELECT cert_id, schedule_id, exam_type, round_name, "
    f"apply_start, apply_end, exam_date, result_date "
    f"FROM cert_schedules "
    f"WHERE cert_id IN ({phs}) AND exam_date >= %s "
    f"ORDER BY exam_date ASC",
    tuple(cert_ids) + (str(today),)
)

sched_by_cert: dict = defaultdict(list)
for s in all_schedules:
    sched_by_cert[s['cert_id']].append(s)


# ── 이벤트 구성 ─────────────────────────────────────────────────────────────────
def _build_event(bk, s) -> dict | None:
    if s.get('round_name') == '상시시험(CBT)':
        return dict(key_date=datetime.date(2099, 12, 31), delta=99999,
                    status='cbt', status_text='연중 상시시험 (CBT)', status_color='#E65100')

    apply_start = _to_date(s['apply_start'])
    apply_end   = _to_date(s['apply_end'])
    exam_date   = _to_date(s['exam_date'])

    if apply_start and apply_start > today:
        delta = (apply_start - today).days
        return dict(key_date=apply_start, delta=delta, status='pre_apply',
                    status_text=f'접수 시작 D-{delta}', status_color='#1565C0')
    elif apply_end and apply_end >= today:
        delta = (apply_end - today).days
        txt   = '접수 마감 D-DAY' if delta == 0 else f'접수 마감 D-{delta}'
        color = '#C62828' if delta <= 3 else ('#E65100' if delta <= 7 else '#FF8F00')
        return dict(key_date=apply_end, delta=delta, status='applying',
                    status_text=txt, status_color=color)
    elif exam_date and exam_date >= today:
        delta = (exam_date - today).days
        txt   = '시험 D-DAY' if delta == 0 else f'시험 D-{delta}'
        color = '#C62828' if delta <= 14 else '#1565C0'
        return dict(key_date=exam_date, delta=delta, status='pre_exam',
                    status_text=txt, status_color=color)
    return None


events: list = []
cbt_certs: list = []
no_sched_certs: list = []

for bk in bookmarks:
    cid    = bk['cert_id']
    scheds = sched_by_cert.get(cid, [])
    if not scheds:
        no_sched_certs.append(bk)
        continue
    added = False
    for s in scheds:
        ev = _build_event(bk, s)
        if ev:
            if ev['status'] == 'cbt':
                if not added:
                    cbt_certs.append({'bk': bk, 's': s})
                    added = True
            else:
                ev['bk'] = bk
                ev['s']  = s
                events.append(ev)
                added = True
    if not added:
        no_sched_certs.append(bk)

events.sort(key=lambda x: x['key_date'])


# ── 요약 메트릭 ─────────────────────────────────────────────────────────────────
st.markdown(f"총 **{len(bookmarks)}개** 자격증")

mc1, mc2, mc3 = st.columns(3)
mc1.metric("접수 중", f"{sum(1 for e in events if e['status'] == 'applying')}건")
mc2.metric("7일 이내 마감/시험", f"{sum(1 for e in events if e['delta'] <= 7)}건")
mc3.metric("전체 예정 일정", f"{len(events)}건")

st.markdown("---")


# ── 카드 렌더링 ─────────────────────────────────────────────────────────────────
def _render_event_card(ev: dict):
    bk  = ev['bk']
    s   = ev['s']
    cid = bk['cert_id']
    lv  = bk.get('ncs_level')

    with st.container(border=True):
        top_l, top_r = st.columns([6, 1])
        with top_l:
            chip = level_chip(lv) if lv else ''
            st.markdown(
                f"{_exam_chip(s['exam_type'])} &nbsp; {chip} &nbsp;"
                f"<span style='font-weight:700;font-size:1.05em'>{bk['cert_name']}</span>"
                f" &nbsp; <span style='color:#9E9E9E;font-size:0.88em'>{s['round_name']}</span>",
                unsafe_allow_html=True
            )
            meta = []
            if lv in LEVEL_LABEL:
                meta.append(LEVEL_LABEL[lv])
            org = (bk.get('issuing_org') or '').strip()
            if org:
                meta.append(org)
            if bk.get('pass_rate') is not None:
                meta.append(f"합격률 {bk['pass_rate']:.1f}%")
            if meta:
                st.caption(" · ".join(meta))

        with top_r:
            if st.button("삭제", key=f"del_{bk['bookmark_id']}_{s['schedule_id']}"):
                execute_insert(
                    "DELETE FROM user_bookmarks WHERE bookmark_id=%s",
                    (bk['bookmark_id'],)
                )
                if 'bookmarked_cert_ids' in st.session_state:
                    st.session_state['bookmarked_cert_ids'].discard(cid)
                st.rerun()

        st.markdown(
            f"<span style='color:{ev['status_color']};font-weight:700;font-size:1.15em'>"
            f"{ev['status_text']}</span>",
            unsafe_allow_html=True
        )

        dc1, dc2 = st.columns(2)
        dc1.markdown(f"접수 &nbsp; {_fmt(s['apply_start'])} ~ {_fmt(s['apply_end'])}")
        dc2.markdown(f"시험 &nbsp; {_fmt(s['exam_date'])} &nbsp; 발표 &nbsp; {_fmt(s.get('result_date'))}")


# ── 섹션별 출력 ─────────────────────────────────────────────────────────────────
if not events:
    st.info("예정된 시험 일정이 없습니다.")
else:
    sections = [
        ('이번 주',  [ev for ev in events if ev['delta'] <= 7]),
        ('이번 달',  [ev for ev in events if 8  <= ev['delta'] <= 30]),
        ('나중에',   [ev for ev in events if ev['delta'] > 30]),
    ]
    for title, group in sections:
        if not group:
            continue
        st.markdown(f"### {title}")
        for ev in group:
            _render_event_card(ev)

# 상시시험(CBT) 자격증
if cbt_certs:
    st.markdown("### 상시시험 (CBT)")
    for item in cbt_certs:
        bk  = item['bk']
        cid = bk['cert_id']
        lv  = bk.get('ncs_level')
        with st.container(border=True):
            top_l, top_r = st.columns([6, 1])
            with top_l:
                chip = level_chip(lv) if lv else ''
                st.markdown(
                    f"{chip} &nbsp; <span style='font-weight:700;font-size:1.05em'>{bk['cert_name']}</span>",
                    unsafe_allow_html=True
                )
                meta = []
                if lv in LEVEL_LABEL:
                    meta.append(LEVEL_LABEL[lv])
                org = (bk.get('issuing_org') or '').strip()
                if org:
                    meta.append(org)
                if bk.get('pass_rate') is not None:
                    meta.append(f"합격률 {bk['pass_rate']:.1f}%")
                if meta:
                    st.caption(" · ".join(meta))
                st.markdown(
                    "<span style='background:#E65100;color:white;padding:4px 14px;"
                    "border-radius:6px;font-weight:700;font-size:0.95em;letter-spacing:0.03em'>"
                    "연중 상시시험 (CBT)</span>",
                    unsafe_allow_html=True
                )
                st.caption("원하는 날짜에 수시 접수 · 시험 가능 — 대한상공회의소 자격평가사업단 license.korcham.net")
            with top_r:
                if st.button("삭제", key=f"del_{bk['bookmark_id']}_cbt"):
                    execute_insert(
                        "DELETE FROM user_bookmarks WHERE bookmark_id=%s",
                        (bk['bookmark_id'],)
                    )
                    if 'bookmarked_cert_ids' in st.session_state:
                        st.session_state['bookmarked_cert_ids'].discard(cid)
                    st.rerun()

# 일정 없는 자격증
if no_sched_certs:
    st.markdown("### 일정 없음")
    for bk in no_sched_certs:
        lv = bk.get('ncs_level')
        with st.container(border=True):
            top_l, top_r = st.columns([6, 1])
            with top_l:
                chip = level_chip(lv) if lv else ''
                st.markdown(f"{chip} &nbsp; **{bk['cert_name']}**", unsafe_allow_html=True)
                meta = []
                if lv in LEVEL_LABEL:
                    meta.append(LEVEL_LABEL[lv])
                org = (bk.get('issuing_org') or '').strip()
                if org:
                    meta.append(org)
                if meta:
                    st.caption(" · ".join(meta))
                st.caption("예정된 시험 일정 없음")
            with top_r:
                if st.button("삭제", key=f"del_{bk['bookmark_id']}_0"):
                    execute_insert(
                        "DELETE FROM user_bookmarks WHERE bookmark_id=%s",
                        (bk['bookmark_id'],)
                    )
                    if 'bookmarked_cert_ids' in st.session_state:
                        st.session_state['bookmarked_cert_ids'].discard(bk['cert_id'])
                    st.rerun()

st.markdown("---")
st.page_link("pages/3_🔍_자격증추천.py", label="자격증 추천으로 돌아가기", icon=":material/search:")
