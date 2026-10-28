import streamlit as st
from utils.db_helper import execute_query, execute_insert
from utils.style import inject_css

st.title("내 프로필")
inject_css()

# ── 로그인 체크 ───────────────────────────────────────────────────────────────
if 'user' not in st.session_state:
    st.info("프로필을 저장하거나 자동완성을 사용하려면 먼저 로그인하세요.")
    st.page_link("pages/1_👤_로그인.py", label="로그인 / 회원가입 바로가기")
    st.divider()

# ── 프로필 폼 ─────────────────────────────────────────────────────────────────
st.markdown("### 기본 정보")
st.caption("입력한 정보는 자격증 추천 시 자동으로 채워집니다.")

user = st.session_state.get('user', {})

col1, col2 = st.columns(2)
with col1:
    edu_options = ["고졸", "2년제전문대졸", "3년제전문대졸", "4년제대졸이상", "대학원"]
    edu_default = user.get('education', '4년제대졸이상')
    edu_idx     = edu_options.index(edu_default) if edu_default in edu_options else 3
    education   = st.selectbox("최종학력", edu_options, index=edu_idx)

with col2:
    career_years = st.number_input(
        "희망분야 관련 경력 (년)",
        min_value=0, max_value=40,
        value=int(user.get('career_years', 0)),
        step=1
    )

major = st.text_input(
    "전공",
    value=user.get('major', ''),
    placeholder="예: 컴퓨터시스템공학, 전기공학, 경영학"
)

st.markdown("---")
st.markdown("### 보유 자격증")

cert_rows  = execute_query("SELECT cert_name FROM certifications ORDER BY cert_name")
cert_names = [r['cert_name'] for r in cert_rows]

saved_certs_str = user.get('owned_certs', '') or ''
saved_certs     = [c.strip() for c in saved_certs_str.split(',') if c.strip()] if saved_certs_str else []
valid_defaults  = [c for c in saved_certs if c in cert_names]

owned_certs = st.multiselect(
    "보유 자격증 (검색해서 선택, 여러 개 가능)",
    cert_names,
    default=valid_defaults,
    placeholder="자격증명을 입력해서 검색하세요",
)

st.markdown("---")
st.markdown("### 관심 분야")

ncs_fields = [
    "01. 사업관리", "02. 경영·회계·사무", "03. 금융·보험",
    "04. 교육·자연·사회과학", "05. 법률·경찰·소방·교도·국방",
    "06. 보건·의료", "07. 사회복지·종교", "08. 문화·예술·디자인·방송",
    "09. 운전·운송", "10. 영업·판매", "11. 경비·청소",
    "12. 이용·숙박·여행·오락·스포츠", "13. 음식서비스",
    "14. 건설", "15. 기계", "16. 재료",
    "17. 화학·바이오", "18. 섬유·의복", "19. 전기·전자",
    "20. 정보통신", "21. 식품가공", "22. 인쇄·목재·가구·공예",
    "23. 환경·에너지·안전", "24. 농림어업",
]

saved_interest = user.get('interest_field', '') or ''
saved_fields   = [f.strip() for f in saved_interest.split(',') if f.strip()] if saved_interest else []
valid_fields   = [f for f in saved_fields if f in ncs_fields]

interest_field = st.multiselect(
    "관심 NCS 분야 (복수 선택 가능)",
    ncs_fields,
    default=valid_fields,
    placeholder="관심 있는 분야를 선택하세요"
)

st.markdown("---")
st.markdown("### 경력 / 경험")
experience = st.text_area(
    "경력·경험 (선택사항)",
    value=user.get('experience', '') or '',
    placeholder="예: 웹개발 인턴 6개월, Python 프로젝트 경험",
    height=100
)

st.markdown("---")

# ── 저장 버튼 ─────────────────────────────────────────────────────────────────
col_save, col_apply = st.columns(2)

with col_apply:
    if st.button("추천 폼에 바로 적용 (저장 없이)", use_container_width=True):
        st.session_state['profile_education']   = education
        st.session_state['profile_career_years'] = int(career_years)
        st.session_state['profile_major']        = major
        st.session_state['profile_owned_certs']  = owned_certs
        st.success("추천 폼에 적용됐습니다. 자격증 추천 페이지로 이동하세요.")
        st.page_link("pages/3_🔍_자격증추천.py", label="자격증 추천 받기")

with col_save:
    if st.button("프로필 저장 (DB)", use_container_width=True, type="primary"):
        profile_data = {
            'education':      education,
            'career_years':   int(career_years),
            'major':          major,
            'owned_certs':    ','.join(owned_certs),
            'interest_field': ','.join(interest_field),
            'experience':     experience,
        }

        if 'user' in st.session_state:
            uid = st.session_state['user']['user_id']
            execute_insert(
                """UPDATE users SET major=%s, education=%s, career_years=%s,
                   owned_certs=%s, interest_field=%s, experience=%s
                   WHERE user_id=%s""",
                (major, education, int(career_years),
                 ','.join(owned_certs), ','.join(interest_field), experience, uid)
            )
            st.session_state['user'].update(profile_data)

        st.session_state['profile_education']    = education
        st.session_state['profile_career_years'] = int(career_years)
        st.session_state['profile_major']        = major
        st.session_state['profile_owned_certs']  = owned_certs

        msg = "프로필이 저장되고 추천 폼에 적용됐습니다." if 'user' in st.session_state else \
              "추천 폼에 적용됐습니다. (로그인하면 DB에도 저장됩니다)"
        st.success(msg)
        st.page_link("pages/3_🔍_자격증추천.py", label="자격증 추천 받기")
