import streamlit as st
import hashlib
from utils.db_helper import execute_query, execute_insert
from utils.style import inject_css

st.title("로그인 / 회원가입")
inject_css()


def _hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode('utf-8')).hexdigest()


def _load_user_to_session(user: dict):
    owned_str = user.get('owned_certs') or ''
    owned_list = [c.strip() for c in owned_str.split(',') if c.strip()]
    st.session_state['user'] = {
        'user_id':   user['user_id'],
        'email':     user['email'],
        'name':      user['name'],
        'major':     user.get('major') or '',
        'education': user.get('education') or '4년제대졸이상',
        'career_years': user.get('career_years') or 0,
        'owned_certs':  owned_str,
        'interest_field': user.get('interest_field') or '',
        'experience': user.get('experience') or '',
    }
    # 자격증 추천·커리어 로드맵 자동완성용 session 키 초기화
    st.session_state['profile_education']    = user.get('education') or '4년제대졸이상'
    st.session_state['profile_career_years'] = int(user.get('career_years') or 0)
    st.session_state['profile_major']        = user.get('major') or ''
    st.session_state['profile_owned_certs']  = owned_list
    st.session_state.pop('bookmarked_cert_ids', None)  # 캐시 초기화


# ── 이미 로그인된 경우 ────────────────────────────────────────────────────────
if 'user' in st.session_state:
    u = st.session_state['user']
    st.success(f"{u['name']}님으로 로그인되어 있습니다.")
    if st.button("로그아웃"):
        del st.session_state['user']
        st.session_state.pop('bookmarked_cert_ids', None)
        st.rerun()
    st.stop()

# ── 탭 구성 ──────────────────────────────────────────────────────────────────
tab_login, tab_register = st.tabs(["로그인", "회원가입"])

# ─── 로그인 탭 ──────────────────────────────────────────────────────────────
with tab_login:
    with st.form("login_form"):
        email = st.text_input("이메일")
        pw    = st.text_input("비밀번호", type="password")
        submitted = st.form_submit_button("로그인", use_container_width=True, type="primary")

    if submitted:
        if not email or not pw:
            st.warning("이메일과 비밀번호를 입력하세요.")
        else:
            rows = execute_query(
                "SELECT * FROM users WHERE email=%s AND password=%s",
                (email, _hash_pw(pw))
            )
            if rows:
                _load_user_to_session(rows[0])
                st.success(f"{rows[0]['name']}님, 환영합니다!")
                st.rerun()
            else:
                st.error("이메일 또는 비밀번호가 올바르지 않습니다.")

# ─── 회원가입 탭 ─────────────────────────────────────────────────────────────
with tab_register:
    with st.form("register_form"):
        col1, col2 = st.columns(2)
        with col1:
            reg_name  = st.text_input("이름 *")
            reg_email = st.text_input("이메일 *")
        with col2:
            reg_pw    = st.text_input("비밀번호 *", type="password")
            reg_pw2   = st.text_input("비밀번호 확인 *", type="password")

        reg_major = st.text_input("전공 (선택)", placeholder="예: 컴퓨터시스템공학")
        reg_edu   = st.selectbox(
            "최종학력 (선택)",
            ["고졸", "2년제전문대졸", "3년제전문대졸", "4년제대졸이상", "대학원"],
            index=3
        )
        submitted2 = st.form_submit_button("회원가입", use_container_width=True, type="primary")

    if submitted2:
        if not reg_name or not reg_email or not reg_pw or not reg_pw2:
            st.warning("필수 항목(*)을 모두 입력하세요.")
        elif reg_pw != reg_pw2:
            st.error("비밀번호가 일치하지 않습니다.")
        elif len(reg_pw) < 6:
            st.error("비밀번호는 6자 이상이어야 합니다.")
        else:
            existing = execute_query("SELECT user_id FROM users WHERE email=%s", (reg_email,))
            if existing:
                st.error("이미 사용 중인 이메일입니다.")
            else:
                execute_insert(
                    "INSERT INTO users (email, password, name, major, education) VALUES (%s,%s,%s,%s,%s)",
                    (reg_email, _hash_pw(reg_pw), reg_name, reg_major, reg_edu)
                )
                rows = execute_query("SELECT * FROM users WHERE email=%s", (reg_email,))
                _load_user_to_session(rows[0])
                st.success(f"회원가입 완료! {reg_name}님, 환영합니다!")
                st.rerun()
