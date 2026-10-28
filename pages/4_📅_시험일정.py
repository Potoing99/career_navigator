import streamlit as st
import datetime
from utils.db_helper import execute_query
from utils.style import inject_css

st.title("시험 일정")
inject_css()
st.markdown("자격증별 필기·실기 시험 일정을 확인하세요.")

today = datetime.date.today()

# ── 필터 + 보기 방식 ──────────────────────────────────────────────────────────
fcol1, fcol2, fcol3, fcol4 = st.columns([2, 1, 2, 1])
with fcol1:
    level_filter = st.selectbox(
        "자격증 종류",
        ["전체", "기능사", "산업기사", "기사", "기능장", "기술사", "국가전문자격", "기타(상공회의소 등)"],
    )
with fcol2:
    exam_type_filter = st.selectbox("구분", ["전체", "필기", "실기"])
with fcol3:
    period_filter = st.selectbox("기간", ["다가오는 일정", "올해 전체", "모든 일정"])
with fcol4:
    view_mode = st.radio("보기", ["카드", "달력"], horizontal=True)

cert_search = st.text_input(
    "자격증명 검색 (선택사항)",
    placeholder="예: 전기, 정보처리, 용접 — 비워두면 전체 표시"
)

st.markdown("---")

# ── 상수 ──────────────────────────────────────────────────────────────────────
LEVEL_MAP   = {'기능사': 3, '산업기사': 5, '기사': 6, '기능장': 7, '기술사': 8}
LEVEL_LABEL = {3: '기능사', 5: '산업기사', 6: '기사', 7: '기능장', 8: '기술사'}
EXAM_COLOR  = {'필기': '#1565C0', '실기': '#2E7D32'}

# ── 쿼리 조건 ─────────────────────────────────────────────────────────────────
where_clauses, params = [], []
is_prof  = (level_filter == "국가전문자격")
is_other = (level_filter == "기타(상공회의소 등)")

if is_prof:
    where_clauses.append("c.cert_type = '국가전문자격'")
elif is_other:
    where_clauses.append(
        "c.cert_type = '국가기술자격' "
        "AND c.issuing_org NOT LIKE '한국산업인력공단%%' "
        "AND c.issuing_org NOT LIKE ' 한국산업인력공단%%'"
    )
elif level_filter != "전체":
    where_clauses.append(
        "c.ncs_level = %s AND c.cert_type = '국가기술자격' "
        "AND (c.issuing_org LIKE '한국산업인력공단%%' OR c.issuing_org LIKE ' 한국산업인력공단%%')"
    )
    params.append(LEVEL_MAP[level_filter])

if exam_type_filter != "전체":
    where_clauses.append("s.exam_type = %s")
    params.append(exam_type_filter)

if period_filter == "다가오는 일정":
    where_clauses.append("s.exam_date >= %s")
    params.append(str(today))
elif period_filter == "올해 전체":
    where_clauses.append("YEAR(s.exam_date) = %s")
    params.append(today.year)

if cert_search.strip():
    where_clauses.append("c.cert_name LIKE %s")
    params.append(f"%{cert_search.strip()}%")

where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

# 개별 표시: 국가전문자격, 기타, 검색어 있을 때
show_individual = bool(cert_search.strip()) or is_prof or is_other

# ── 쿼리 실행 ─────────────────────────────────────────────────────────────────
if show_individual:
    rows = execute_query(f"""
        SELECT DISTINCT c.cert_name, c.cert_type, c.ncs_level, c.issuing_org,
               s.round_name, s.exam_type,
               s.apply_start, s.apply_end, s.exam_date, s.result_date
        FROM certifications c
        JOIN cert_schedules s ON c.cert_id = s.cert_id
        {where_sql}
        ORDER BY s.exam_date ASC, c.cert_name ASC
    """, tuple(params) if params else None)
else:
    rows = execute_query(f"""
        SELECT c.ncs_level,
               s.round_name, s.exam_type,
               s.apply_start, s.apply_end, s.exam_date, s.result_date,
               COUNT(DISTINCT c.cert_id) as cert_count
        FROM certifications c
        JOIN cert_schedules s ON c.cert_id = s.cert_id
        {where_sql}
        GROUP BY c.ncs_level, s.round_name, s.exam_type,
                 s.apply_start, s.apply_end, s.exam_date, s.result_date
        ORDER BY c.ncs_level ASC, s.exam_date ASC
    """, tuple(params) if params else None)

if not rows:
    st.info("조건에 맞는 시험 일정이 없습니다.")
    st.stop()

# ── 헬퍼 함수 ─────────────────────────────────────────────────────────────────
def _fmt(d) -> str:
    if d is None:
        return "-"
    if isinstance(d, str):
        d = datetime.date.fromisoformat(d)
    return d.strftime("%Y.%m.%d")

def _dday(exam_date):
    if exam_date is None:
        return "", ""
    if isinstance(exam_date, str):
        exam_date = datetime.date.fromisoformat(exam_date)
    delta = (exam_date - today).days
    if delta < 0:
        return f"D+{abs(delta)}", "dday-past"
    elif delta == 0:
        return "D-DAY", "dday-urgent"
    elif delta <= 14:
        return f"D-{delta}", "dday-urgent"
    else:
        return f"D-{delta}", "dday-soon"

def _exam_chip(exam_type: str) -> str:
    color = EXAM_COLOR.get(exam_type, '#555')
    return (
        f"<span style='background:{color};color:white;padding:2px 10px;"
        f"border-radius:4px;font-size:0.8em;font-weight:600'>{exam_type}</span>"
    )

def _render_card(cert_name, lv_label, exam_type, round_name,
                 apply_start, apply_end, exam_date, result_date, issuing_org=""):

    # ── 상시시험(CBT) 특별 처리 ────────────────────────────────────────────────
    if round_name == '상시시험(CBT)':
        with st.container(border=True):
            st.markdown(
                f"{_exam_chip(exam_type)} &nbsp;"
                f"<span style='font-weight:700;font-size:1.05em'>{cert_name}</span>",
                unsafe_allow_html=True
            )
            if lv_label or issuing_org:
                meta = " · ".join(x for x in [lv_label, issuing_org] if x)
                st.caption(meta)
            st.markdown(
                "<span style='background:#E65100;color:white;padding:5px 16px;"
                "border-radius:6px;font-weight:700;font-size:0.95em;letter-spacing:0.03em'>"
                "연중 상시시험 (CBT)</span>",
                unsafe_allow_html=True
            )
            st.caption("원하는 날짜에 수시 접수 · 시험 가능 — 대한상공회의소 자격평가사업단 license.korcham.net")
        return

    exam_dday_str,  exam_dday_cls  = _dday(exam_date)
    apply_dday_str, apply_dday_cls = _dday(apply_end)

    with st.container(border=True):
        top_l, top_r = st.columns([5, 1])
        with top_l:
            st.markdown(
                f"{_exam_chip(exam_type)} &nbsp;"
                f"<span style='font-weight:700;font-size:1.05em'>{cert_name}</span>"
                + (f" &nbsp; <span style='color:#9E9E9E;font-size:0.88em'>{round_name}</span>" if round_name else ""),
                unsafe_allow_html=True
            )
            if lv_label or issuing_org:
                meta = " · ".join(x for x in [lv_label, issuing_org] if x)
                st.caption(meta)
        with top_r:
            st.markdown(
                f"<div style='text-align:right' class='{exam_dday_cls}'>{exam_dday_str}</div>",
                unsafe_allow_html=True
            )

        ra, rb = st.columns(2)

        start_dday_str, start_dday_cls = _dday(apply_start)
        end_dday_str,   end_dday_cls   = _dday(apply_end)

        if start_dday_str and "D+" not in start_dday_str:
            apply_tag = (
                f" &nbsp; <span class='{start_dday_cls}' style='font-size:0.85em'>"
                f"접수시작 {start_dday_str}</span>"
            )
        elif end_dday_str and "D+" not in end_dday_str:
            apply_tag = (
                f" &nbsp; <span class='{end_dday_cls}' style='font-size:0.85em'>"
                f"접수마감 {end_dday_str}</span>"
            )
        else:
            apply_tag = ""

        ra.markdown(
            f"접수 &nbsp; {_fmt(apply_start)} ~ {_fmt(apply_end)}{apply_tag}",
            unsafe_allow_html=True
        )
        rb.markdown(f"시험 &nbsp; {_fmt(exam_date)} &nbsp; 발표 &nbsp; {_fmt(result_date)}")

# ── 달력 뷰 ──────────────────────────────────────────────────────────────────
if view_mode == "달력":
    from streamlit_calendar import calendar as st_calendar

    cal_events = []

    if show_individual:
        # 개별 자격증 모드 — rows 그대로 사용 (cert_name 있음)
        for row in rows:
            cname     = row.get('cert_name', '')
            exam_type = row['exam_type']
            bg_color  = EXAM_COLOR.get(exam_type, '#555')
            round_nm  = row.get('round_name') or ''

            if row.get('apply_end'):
                cal_events.append({
                    "title":           f"[접수마감] {cname} {exam_type}",
                    "start":           str(row['apply_end']),
                    "backgroundColor": bg_color + '55',
                    "borderColor":     bg_color,
                    "textColor":       bg_color,
                })
            if row.get('exam_date'):
                cal_events.append({
                    "title":           f"[시험] {cname} {exam_type}",
                    "start":           str(row['exam_date']),
                    "backgroundColor": bg_color,
                    "borderColor":     bg_color,
                })
    else:
        # 그룹 모드 — 레벨별로 묶어서 표시 (카드 뷰와 동일 기준)
        for row in rows:
            lv = row.get('ncs_level')
            if lv not in LEVEL_LABEL:
                continue
            lv_label  = LEVEL_LABEL[lv]
            exam_type = row['exam_type']
            bg_color  = EXAM_COLOR.get(exam_type, '#555')
            round_nm  = row.get('round_name') or ''
            cnt       = row.get('cert_count', '')
            title_base = f"{lv_label} {exam_type} {round_nm}"

            if row.get('apply_end'):
                cal_events.append({
                    "title":           f"[접수마감] {title_base}",
                    "start":           str(row['apply_end']),
                    "backgroundColor": bg_color + '55',
                    "borderColor":     bg_color,
                    "textColor":       bg_color,
                })
            if row.get('exam_date'):
                cal_events.append({
                    "title":           f"[시험] {title_base}",
                    "start":           str(row['exam_date']),
                    "backgroundColor": bg_color,
                    "borderColor":     bg_color,
                })

    cal_options = {
        "initialView":   "listMonth",   # 목록형이 기본 — 이벤트 많아도 가독성 좋음
        "locale":        "ko",
        "height":        620,
        "headerToolbar": {
            "left":   "prev,next today",
            "center": "title",
            "right":  "listMonth,dayGridMonth",
        },
        "buttonText": {
            "today": "오늘",
            "month": "격자",
            "list":  "목록",
        },
        "noEventsText": "해당 기간에 일정이 없습니다.",
    }

    st.caption(
        "<span style='background:#1565C055;border:1px solid #1565C0;padding:1px 6px;"
        "border-radius:3px;font-size:0.8em;color:#1565C0'>필기 접수마감</span> &nbsp;"
        "<span style='background:#1565C0;padding:1px 6px;border-radius:3px;"
        "font-size:0.8em;color:white'>필기 시험</span> &nbsp;"
        "<span style='background:#2E7D3255;border:1px solid #2E7D32;padding:1px 6px;"
        "border-radius:3px;font-size:0.8em;color:#2E7D32'>실기 접수마감</span> &nbsp;"
        "<span style='background:#2E7D32;padding:1px 6px;border-radius:3px;"
        "font-size:0.8em;color:white'>실기 시험</span>",
        unsafe_allow_html=True
    )
    st_calendar(events=cal_events, options=cal_options, key="exam_cal")

# ── 카드 뷰 ──────────────────────────────────────────────────────────────────
else:
    if show_individual:
        label_suffix = "국가전문자격" if is_prof else ("기타 국가기술자격" if is_other else "검색 결과")
        st.markdown(f"**{len(rows)}건** ({label_suffix})")

        for row in rows:
            lv_label = LEVEL_LABEL.get(row.get('ncs_level'), '')
            _render_card(
                cert_name   = row.get('cert_name', ''),
                lv_label    = lv_label,
                exam_type   = row['exam_type'],
                round_name  = row['round_name'],
                apply_start = row['apply_start'],
                apply_end   = row['apply_end'],
                exam_date   = row['exam_date'],
                result_date = row['result_date'],
                issuing_org = row.get('issuing_org', '') or '',
            )

    else:
        current_level = None
        for row in rows:
            lv = row.get('ncs_level')
            if lv not in LEVEL_LABEL:
                continue

            lv_label = LEVEL_LABEL[lv]

            if lv != current_level:
                st.markdown(f"### {lv_label} 시험 일정")
                cnt_row = execute_query(
                    "SELECT COUNT(*) as cnt FROM certifications "
                    "WHERE ncs_level=%s AND (issuing_org LIKE '한국산업인력공단%%' OR issuing_org LIKE ' 한국산업인력공단%%')",
                    (lv,)
                )
                cert_cnt = cnt_row[0]['cnt'] if cnt_row else '?'
                st.caption(f"한국산업인력공단 시행 {cert_cnt}개 자격증에 동일 적용")
                current_level = lv

            _render_card(
                cert_name   = row['round_name'],
                lv_label    = "",
                exam_type   = row['exam_type'],
                round_name  = "",
                apply_start = row['apply_start'],
                apply_end   = row['apply_end'],
                exam_date   = row['exam_date'],
                result_date = row['result_date'],
            )

st.markdown("---")
st.caption(
    "한국산업인력공단 국가기술자격 2026년 시험 일정 기준.  "
    "정확한 일정은 [Q-Net](https://www.q-net.or.kr)에서 확인하세요.  "
    "컴퓨터활용능력 등 대한상공회의소 시행 자격증은 [자격평가사업단](https://license.korcham.net)에서 확인하세요."
)
