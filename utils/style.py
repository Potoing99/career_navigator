import streamlit as st

LEVEL_COLORS = {
    3: {'bg': '#E8F5E9', 'text': '#2E7D32', 'label': '기능사',   'bar': '#2E7D32'},
    5: {'bg': '#E0F2F1', 'text': '#00695C', 'label': '산업기사', 'bar': '#00695C'},
    6: {'bg': '#E3F2FD', 'text': '#1565C0', 'label': '기사',     'bar': '#1565C0'},
    7: {'bg': '#FFF3E0', 'text': '#E65100', 'label': '기능장',   'bar': '#E65100'},
    8: {'bg': '#F3E5F5', 'text': '#6A1B9A', 'label': '기술사',   'bar': '#6A1B9A'},
}

_CSS = """
<style>
/* ── 섹션 헤더 ── */
h3 {
    color: #1B4F8A;
    margin-top: 1.4rem !important;
    margin-bottom: 0.4rem !important;
}

/* ── 레벨 칩 ── */
.lv-chip {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 4px;
    font-size: 0.8em;
    font-weight: 600;
    margin-right: 4px;
}
.lv-3  { background: #E8F5E9; color: #2E7D32; }
.lv-5  { background: #E0F2F1; color: #00695C; }
.lv-6  { background: #E3F2FD; color: #1565C0; }
.lv-7  { background: #FFF3E0; color: #E65100; }
.lv-8  { background: #F3E5F5; color: #6A1B9A; }

/* ── 응시가능 배지 ── */
.badge-ok    { background: #E8F5E9; color: #2E7D32; padding: 3px 12px; border-radius: 4px; font-size: 0.82em; font-weight: 600; }
.badge-warn  { background: #FFF3E0; color: #E65100; padding: 3px 12px; border-radius: 4px; font-size: 0.82em; font-weight: 600; }
.badge-owned { background: #E3F2FD; color: #1565C0; padding: 3px 12px; border-radius: 4px; font-size: 0.82em; font-weight: 600; }

/* ── 추천 이유 박스 ── */
.reason-box {
    background: #F0F4FF;
    border-left: 3px solid #1B4F8A;
    padding: 8px 12px;
    border-radius: 0 6px 6px 0;
    font-size: 0.88em;
    color: #2D3748;
    margin-top: 8px;
}

/* ── D-Day 칩 ── */
.dday-urgent { color: #C62828; font-weight: 700; font-size: 1.05em; }
.dday-soon   { color: #1565C0; font-weight: 700; font-size: 1.05em; }
.dday-past   { color: #9E9E9E; font-weight: 500; font-size: 1.0em; }
</style>
"""


def inject_css():
    st.markdown(_CSS, unsafe_allow_html=True)


def level_chip(ncs_level: int) -> str:
    c = LEVEL_COLORS.get(ncs_level)
    if not c:
        return ''
    return f"<span class='lv-chip lv-{ncs_level}'>{c['label']}</span>"


def eligible_badge(ok: bool, owned: bool = False) -> str:
    if owned:
        return "<span class='badge-owned'>보유 중</span>"
    if ok:
        return "<span class='badge-ok'>응시 가능</span>"
    return "<span class='badge-warn'>응시자격 확인 필요</span>"


def reason_box(text: str) -> str:
    return f"<div class='reason-box'>{text}</div>"
