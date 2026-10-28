import streamlit as st
from utils.db_helper import execute_query, execute_insert
from models.recommender import recommend
from utils.style import inject_css, level_chip, reason_box

st.title("자격증 추천")
inject_css()
st.markdown("학력·경력·전공 정보를 입력하면 NCS 기반으로 맞춤 자격증을 추천해드려요.")

# ── 북마크 헬퍼 ───────────────────────────────────────────────────────────────
def _get_bookmark_ids() -> set:
    if 'user' not in st.session_state:
        return set()
    if 'bookmarked_cert_ids' not in st.session_state:
        uid = st.session_state['user']['user_id']
        rows = execute_query("SELECT cert_id FROM user_bookmarks WHERE user_id=%s", (uid,))
        st.session_state['bookmarked_cert_ids'] = {r['cert_id'] for r in rows}
    return st.session_state['bookmarked_cert_ids']


def _toggle_bookmark(cert_id: int):
    uid = st.session_state['user']['user_id']
    ids = _get_bookmark_ids()
    if cert_id in ids:
        execute_insert(
            "DELETE FROM user_bookmarks WHERE user_id=%s AND cert_id=%s",
            (uid, cert_id)
        )
        ids.discard(cert_id)
    else:
        execute_insert(
            "INSERT IGNORE INTO user_bookmarks (user_id, cert_id) VALUES (%s,%s)",
            (uid, cert_id)
        )
        ids.add(cert_id)


# ── 프로필 자동완성 배너 ───────────────────────────────────────────────────────
_has_profile = any(k in st.session_state for k in ('profile_education', 'profile_major'))
if _has_profile:
    st.info("프로필 정보가 자동으로 채워졌습니다. 수정 후 추천받으세요.")
elif 'user' not in st.session_state:
    st.caption("프로필 페이지에서 정보를 저장하면 여기에 자동으로 채워집니다.")

# ── 섹션 1: 기본 정보 ─────────────────────────────────────────────────────────
st.markdown("### 기본 정보")

_edu_options = ["고졸", "2년제전문대졸", "3년제전문대졸", "4년제대졸이상", "대학원"]
_edu_default = st.session_state.get('profile_education', '4년제대졸이상')
_edu_idx     = _edu_options.index(_edu_default) if _edu_default in _edu_options else 3

col1, col2 = st.columns(2)
with col1:
    education = st.selectbox("최종학력", _edu_options, index=_edu_idx)
with col2:
    career_years = st.number_input(
        "희망분야 관련 경력 (년)",
        min_value=0, max_value=40,
        value=int(st.session_state.get('profile_career_years', 0)),
        step=1,
        help="관련 분야에서 실제로 일한 기간을 입력하세요. 없으면 0"
    )

st.markdown("---")

# ── 섹션 2: 추천 방식 ─────────────────────────────────────────────────────────
st.markdown("### 추천 방식")
use_major_str = st.radio(
    "어떤 방식으로 추천받으시겠어요?",
    ["전공 살려서", "희망분야로 새롭게"],
    horizontal=True,
    help="전공 살려서: 현재 전공과 관련된 자격증 추천\n희망분야로 새롭게: NCS 직무 분류로 원하는 분야의 자격증 추천"
)

major    = ""
ncs_dclas = ""

if use_major_str == "전공 살려서":
    major = st.text_input(
        "전공명",
        value=st.session_state.get('profile_major', ''),
        placeholder="예: 컴퓨터공학, 전기공학, 기계공학, 경영학",
        help="전공명을 입력하면 관련 자격증을 찾아드려요."
    )
else:
    st.caption("NCS 분류를 단계적으로 선택해주세요 (대분류 → 중분류 → 소분류 → 세분류)")
    c1, c2 = st.columns(2)
    with c1:
        lclas_rows  = execute_query("SELECT DISTINCT lclas_nm FROM ncs_categories ORDER BY lclas_nm")
        lclas_names = [r['lclas_nm'] for r in lclas_rows]
        lclas_sel   = st.selectbox("대분류", lclas_names)
    with c2:
        mclas_rows  = execute_query(
            "SELECT DISTINCT mclas_nm FROM ncs_categories WHERE lclas_nm=%s ORDER BY mclas_nm",
            (lclas_sel,)
        )
        mclas_names = [r['mclas_nm'] for r in mclas_rows]
        mclas_sel   = st.selectbox("중분류", mclas_names)

    c3, c4 = st.columns(2)
    with c3:
        sclas_rows  = execute_query(
            "SELECT DISTINCT sclas_nm FROM ncs_categories WHERE lclas_nm=%s AND mclas_nm=%s ORDER BY sclas_nm",
            (lclas_sel, mclas_sel)
        )
        sclas_names = [r['sclas_nm'] for r in sclas_rows]
        sclas_sel   = st.selectbox("소분류", sclas_names)
    with c4:
        dclas_rows  = execute_query(
            "SELECT DISTINCT dclas_nm FROM ncs_categories "
            "WHERE lclas_nm=%s AND mclas_nm=%s AND sclas_nm=%s ORDER BY dclas_nm",
            (lclas_sel, mclas_sel, sclas_sel)
        )
        dclas_names = [r['dclas_nm'] for r in dclas_rows]
        ncs_dclas   = st.selectbox("세분류 (직무)", ["전체 (소분류 전체)"] + dclas_names)
        if ncs_dclas == "전체 (소분류 전체)":
            ncs_dclas = ",".join(dclas_names)

st.markdown("---")

# ── 섹션 3: 보유 자격증 ───────────────────────────────────────────────────────
st.markdown("### 보유 자격증")
cert_rows      = execute_query("SELECT cert_name FROM certifications ORDER BY cert_name")
cert_names     = [r['cert_name'] for r in cert_rows]
_profile_certs = st.session_state.get('profile_owned_certs', [])
_valid_defaults = [c for c in _profile_certs if c in cert_names]
owned_certs = st.multiselect(
    "보유 자격증 선택 (검색해서 선택, 여러 개 가능)",
    cert_names,
    default=_valid_defaults,
    placeholder="자격증명을 입력해서 검색하세요",
    help="이미 갖고 있는 자격증을 선택하세요. 없으면 건너뛰세요."
)

st.markdown("---")

# ── 섹션 4: 추가 자격요건 ─────────────────────────────────────────────────────
st.markdown("### 추가 자격요건")
st.caption("해당하는 항목이 있으면 선택하세요. 없으면 건너뛰세요.")

extra_options = {
    '산업기사수준 기술훈련과정 이수': '산업기사 수준 기술훈련과정 이수',
    '기사수준 기술훈련과정 이수':    '기사 수준 기술훈련과정 이수',
    '기능경기대회 입상':             '기능경기대회 입상',
    '기능대학 기능장과정 이수':       '기능대학 기능장과정 이수',
}
extra_qualifications = []
cols_extra = st.columns(2)
for i, (key, label) in enumerate(extra_options.items()):
    with cols_extra[i % 2]:
        if st.checkbox(label):
            extra_qualifications.append(key)

st.caption("어학성적이 있으면 선택하세요. 국제의료관광코디네이터 등 일부 자격증 응시에 필요합니다.")
lang_type = st.selectbox(
    "어학시험 종류",
    ["없음", "TOEIC", "TOEFL iBT", "IELTS", "TEPS", "OPIc"],
)

language_test = None
if lang_type != "없음":
    if lang_type == "OPIc":
        opic_grade = st.selectbox(
            "OPIc 등급",
            ["NL", "NM", "NH", "IL", "IM1", "IM2", "IM3", "IH", "AL"],
            index=4,
            help="IM1 이상이면 기준 충족"
        )
        language_test = {'type': 'OPIc', 'grade': opic_grade}
    else:
        score_hints = {'TOEIC': '700점 이상', 'TOEFL iBT': '71점 이상', 'IELTS': '5.5 이상', 'TEPS': '625점 이상'}
        score = st.number_input(
            f"{lang_type} 점수 ({score_hints.get(lang_type, '')})",
            min_value=0.0, max_value=990.0, value=0.0, step=1.0 if lang_type != 'IELTS' else 0.5
        )
        language_test = {'type': lang_type, 'score': score}

st.markdown("---")

# ── 섹션 5: 추천 모드 ─────────────────────────────────────────────────────────
st.markdown("### 추천 모드")
weight_mode = st.radio(
    "어떤 기준으로 추천받으시겠어요?",
    ["career", "easy"],
    format_func=lambda x: (
        "취업 중심 — 높은 레벨의 자격증 우선 추천"
        if x == "career" else
        "입문 중심 — 합격률 높은 자격증 우선 추천"
    ),
    horizontal=True
)

st.markdown("---")

# ── 추천 실행 버튼 ─────────────────────────────────────────────────────────────
run_btn = st.button("맞춤 자격증 추천 받기", use_container_width=True, type="primary")

if run_btn:
    if use_major_str == "전공 살려서" and not major.strip():
        st.warning("전공명을 입력해주세요.")
        st.stop()
    if use_major_str == "희망분야로 새롭게" and not ncs_dclas:
        st.warning("NCS 세분류(직무)를 선택해주세요.")
        st.stop()

    user_input = {
        'education':            education,
        'career_years':         int(career_years),
        'owned_certs':          owned_certs,
        'use_major':            use_major_str == "전공 살려서",
        'major':                major.strip(),
        'ncs_dclas':            ncs_dclas,
        'ncs_mclas':            mclas_sel if use_major_str == "희망분야로 새롭게" else '',
        'extra_qualifications': extra_qualifications,
        'language_test':        language_test,
        'weight_mode':          weight_mode,
    }

    with st.spinner("AI가 분석 중입니다..."):
        st.session_state['recommend_result'] = recommend(user_input)
        st.session_state['recommend_user_input'] = user_input

# ── 결과 렌더링 ───────────────────────────────────────────────────────────────
if 'recommend_result' not in st.session_state:
    st.stop()

result     = st.session_state['recommend_result']
user_input = st.session_state.get('recommend_user_input', {})

is_logged_in = 'user' in st.session_state

LEVEL_LABELS = {
    'level8': '기술사급',
    'level7': '기능장급',
    'level6': '기사급',
    'level5': '산업기사급',
    'level3': '기능사급',
    'other':  '기타 기술자격',
    'prof':   '국가전문자격',
}
LEVEL_NCS        = {'level8': 8, 'level7': 7, 'level6': 6, 'level5': 5, 'level3': 3}
_level_label_map = {3: '기능사', 5: '산업기사', 6: '기사', 7: '기능장', 8: '기술사'}

any_result = any(result.get(k) for k in LEVEL_LABELS)

if not any_result:
    st.markdown("---")
    if not user_input.get('use_major') and user_input.get('ncs_dclas'):
        st.warning("선택한 직무 분야와 연관된 자격증이 데이터에 없습니다.")
        st.info("세분류 드롭다운에서 '전체 (소분류 전체)'를 선택하거나, '전공 살려서' 방식으로 시도해보세요.")
    else:
        st.warning("조건에 맞는 추천 자격증이 없습니다. 학력이나 경력 조건을 조정해보세요.")
    st.stop()

st.markdown("---")

bm_ids = _get_bookmark_ids()

for key, label in LEVEL_LABELS.items():
    group = result.get(key, [])
    if not group:
        continue

    lv_num = LEVEL_NCS.get(key)
    if lv_num:
        st.markdown(
            f"### {label} &nbsp; {level_chip(lv_num)}",
            unsafe_allow_html=True
        )
    else:
        st.markdown(f"### {label}")

    cols = st.columns(min(len(group), 2))
    for i, cert in enumerate(group):
        cert_id = cert.get('cert_id')
        with cols[i % 2]:
            with st.container(border=True):
                head_l, head_r = st.columns([5, 1])
                with head_l:
                    eligible = cert.get('eligible', True)
                    if eligible:
                        st.markdown("<span class='badge-ok'>응시 가능</span>", unsafe_allow_html=True)
                    else:
                        st.markdown("<span class='badge-warn'>응시자격 확인 필요</span>", unsafe_allow_html=True)
                    st.markdown(f"**{cert['cert_name']}**")
                with head_r:
                    if cert_id and is_logged_in:
                        is_bm = cert_id in bm_ids
                        if st.button(
                            "★" if is_bm else "☆",
                            key=f"bm_{cert_id}",
                            help="즐겨찾기 해제" if is_bm else "즐겨찾기 추가",
                        ):
                            _toggle_bookmark(cert_id)
                            st.rerun()

                meta_col1, meta_col2 = st.columns(2)
                with meta_col1:
                    if cert.get('issuing_org'):
                        st.caption(cert['issuing_org'])
                    if cert.get('ncs_level') and key != 'other':
                        st.caption(_level_label_map.get(cert['ncs_level'], '-') + '급')
                with meta_col2:
                    if cert.get('pass_rate') is not None:
                        st.caption(f"합격률 {cert['pass_rate']:.1f}%")

                if cert.get('reason'):
                    st.markdown(reason_box(cert['reason']), unsafe_allow_html=True)

    st.markdown("")

st.markdown("---")
col_road, col_sched = st.columns(2)
with col_road:
    st.page_link("pages/5_🗺️_커리어로드맵.py", label="커리어 로드맵 — 단계별 취득 경로 보기")
with col_sched:
    st.page_link("pages/4_📅_시험일정.py", label="시험 일정 — 접수·시험 날짜 확인하기")
