import streamlit as st

st.set_page_config(
    page_title="NCS 커리어 네비게이터",
    page_icon="🎯",
    layout="wide"
)

pg = st.navigation(
    {
        "": [
            st.Page("home.py", title="홈", icon=":material/home:"),
        ],
        "내 정보": [
            st.Page("pages/1_👤_로그인.py",  title="로그인",  icon=":material/person:"),
            st.Page("pages/2_📝_프로필.py",  title="프로필",  icon=":material/edit:"),
        ],
        "자격증": [
            st.Page("pages/3_🔍_자격증추천.py",  title="자격증 추천",   icon=":material/search:"),
            st.Page("pages/4_📅_시험일정.py",    title="시험 일정",     icon=":material/calendar_month:"),
            st.Page("pages/5_🗺️_커리어로드맵.py", title="커리어 로드맵", icon=":material/map:"),
            st.Page("pages/6_⭐_즐겨찾기.py",    title="즐겨찾기",      icon=":material/star:"),
        ],
    }
)

pg.run()
