import streamlit as st
from utils.db_helper import execute_query
from utils.style import inject_css, eligible_badge

st.title("커리어 로드맵")
inject_css()
st.markdown("자격증명을 검색하면 같은 분야의 단계적 취득 경로를 안내합니다.")

LEVEL_SUFFIXES = ['기술사', '기능장', '산업기사', '기사', '기능사']
SUFFIX_TO_LEVEL = {'기술사': 8, '기능장': 7, '기사': 6, '산업기사': 5, '기능사': 3}

LEVEL_META = {
    8: {'label': '기술사',   'color': '#6A1B9A', 'desc': '최고급 기술 전문가 수준'},
    7: {'label': '기능장',   'color': '#E65100', 'desc': '최상급 숙련 기능인 수준'},
    6: {'label': '기사',     'color': '#1565C0', 'desc': '대학 졸업 수준 전문 기술'},
    5: {'label': '산업기사', 'color': '#00695C', 'desc': '전문대 졸업 수준 기술'},
    3: {'label': '기능사',   'color': '#2E7D32', 'desc': '기초 기능 검정'},
}
LEVEL_ORDER = [3, 5, 6, 7, 8]
EDU_RANK = {'고졸': 1, '2년제전문대졸': 2, '3년제전문대졸': 3, '4년제대졸이상': 4, '대학원': 5}


def _extract_domain(cert_name: str) -> str:
    for suf in LEVEL_SUFFIXES:
        if cert_name.endswith(suf):
            return cert_name[: -len(suf)]
    return cert_name


def _owned_domain_level(domain: str, owned: set) -> int | None:
    """보유 자격증 중 같은 도메인의 최고 레벨 반환 (문자열 기반)"""
    for name in owned:
        if _extract_domain(name) == domain:
            for suf in LEVEL_SUFFIXES:
                if name.endswith(suf):
                    return SUFFIX_TO_LEVEL[suf]
    return None


def _check_eligible(lv: int, domain: str, owned: set, education: str, career: int) -> bool:
    edu = EDU_RANK.get(education, 0)
    olv = _owned_domain_level(domain, owned)
    if lv == 3:
        return True
    if lv == 5:
        return edu >= 2 or career >= 2 or (olv == 3 and career >= 1) or olv == 5
    if lv == 6:
        return (edu >= 4 or (edu >= 3 and career >= 1) or (edu >= 2 and career >= 2)
                or career >= 4 or (olv == 5 and career >= 1) or (olv == 3 and career >= 3) or olv == 6)
    if lv == 7:
        return career >= 9 or (olv == 5 and career >= 5) or (olv == 3 and career >= 7) or olv == 7
    if lv == 8:
        return ((olv == 6 and career >= 4) or (olv == 5 and career >= 5)
                or (olv == 3 and career >= 7) or (edu >= 4 and career >= 6) or olv == 8)
    return True


# ── 검색 입력 ──────────────────────────────────────────────────────────────────
search_term = st.text_input(
    "자격증 검색",
    placeholder="예: 전기, 정보처리, 가스, 건설기계...",
    help="자격증명 일부를 입력하면 관련 자격증 목록이 나옵니다."
)

if not search_term.strip():
    st.info("자격증명을 입력해서 커리어 로드맵을 확인하세요.")
    st.caption("예시: '정보처리기사', '전기기능사', '가스기사' 등을 검색해보세요.")
    st.stop()

# ── 검색 결과 ──────────────────────────────────────────────────────────────────
cert_rows = execute_query(
    "SELECT cert_id, cert_name, cert_type, ncs_level, pass_rate, career_path, competency_units "
    "FROM certifications WHERE cert_name LIKE %s AND cert_type='국가기술자격' ORDER BY cert_name",
    (f"%{search_term.strip()}%",)
)

if not cert_rows:
    st.warning("검색 결과가 없습니다. 다른 키워드로 검색해보세요.")
    st.stop()

# ── 도메인 패밀리 구성 ──────────────────────────────────────────────────────────
domains_found = {_extract_domain(r['cert_name']) for r in cert_rows}

all_certs = execute_query(
    "SELECT cert_id, cert_name, cert_type, ncs_level, pass_rate, career_path, competency_units "
    "FROM certifications WHERE cert_type='국가기술자격' ORDER BY ncs_level ASC, cert_name ASC"
)

families: dict[str, list] = {}
for r in all_certs:
    families.setdefault(_extract_domain(r['cert_name']), []).append(r)

target_families = {d: families[d] for d in domains_found if d in families and len(families[d]) >= 2}
if not target_families:
    for r in cert_rows[:5]:
        d = _extract_domain(r['cert_name'])
        if d in families:
            target_families[d] = families[d]

# ── 세션에서 보유 자격증 ────────────────────────────────────────────────────────
owned: set = set(st.session_state.get('profile_owned_certs', []))
if 'user' in st.session_state:
    owned_str = st.session_state['user'].get('owned_certs', '') or ''
    owned |= {c.strip() for c in owned_str.split(',') if c.strip()}

education   = st.session_state.get('profile_education', '4년제대졸이상')
career_years = int(st.session_state.get('profile_career_years', 0))

# ── 로드맵 표시 ───────────────────────────────────────────────────────────────
if not target_families:
    st.warning("경로 분석 가능한 자격증 패밀리가 없습니다.")
    st.stop()

for domain, family in sorted(target_families.items()):
    level_map: dict[int, list] = {}
    for cert in family:
        lv = cert.get('ncs_level') or 0
        level_map.setdefault(lv, []).append(cert)

    sorted_levels = [lv for lv in LEVEL_ORDER if lv in level_map]
    if not sorted_levels:
        continue

    st.markdown(f"## {domain} 분야 커리어 로드맵")

    owned_in_family = [c for lv in sorted_levels for c in level_map[lv] if c['cert_name'] in owned]
    if owned_in_family:
        max_owned_level = max((c.get('ncs_level') or 0) for c in owned_in_family)
        achieved = [lv for lv in sorted_levels if lv <= max_owned_level]
        progress = len(achieved) / len(sorted_levels)
        st.progress(progress, text=f"달성도: {int(progress*100)}% ({LEVEL_META.get(max_owned_level, {}).get('label', '?')} 취득 완료)")

    for idx, lv in enumerate(sorted_levels):
        meta = LEVEL_META.get(lv, {'label': str(lv), 'color': '#555', 'desc': ''})
        certs_at_level = level_map[lv]

        if idx > 0:
            st.markdown(
                "<div style='text-align:center;font-size:1.4em;color:#9E9E9E;margin:4px 0'>↑</div>",
                unsafe_allow_html=True
            )

        for cert in certs_at_level:
            is_owned = cert['cert_name'] in owned
            ok = _check_eligible(lv, domain, owned, education, career_years)

            with st.container(border=True):
                col_badge, col_info = st.columns([1, 4])
                with col_badge:
                    st.markdown(
                        f"<div style='background:{meta['color']};color:white;border-radius:8px;"
                        f"padding:12px 6px;text-align:center;font-weight:700;font-size:0.95em'>"
                        f"{meta['label']}</div>",
                        unsafe_allow_html=True
                    )
                with col_info:
                    st.markdown(eligible_badge(ok=ok, owned=is_owned), unsafe_allow_html=True)
                    st.markdown(f"### {cert['cert_name']}")
                    st.caption(meta['desc'])
                    icol1, icol2 = st.columns(2)
                    with icol1:
                        if cert.get('pass_rate') is not None:
                            st.metric("합격률", f"{cert['pass_rate']:.1f}%")
                    with icol2:
                        st.metric("NCS 레벨", f"Level {lv}")

                    career = (cert.get('career_path') or '').strip()
                    if career:
                        with st.expander("취업 진로 보기"):
                            st.write(career[:300] + ("..." if len(career) > 300 else ""))

    st.markdown("---")

st.caption("로드맵은 국가기술자격 기준입니다. 국가전문자격은 해당 주무부처 자격 정보를 확인하세요.")
