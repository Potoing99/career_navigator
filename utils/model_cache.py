import streamlit as st


@st.cache_resource(show_spinner="AI 모델 로딩 중...")
def get_sbert_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("jhgan/ko-sroberta-multitask")
