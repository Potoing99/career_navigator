import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

_DB_CONFIG = dict(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "career_nav"),
    charset="utf8mb4",
    cursorclass=pymysql.cursors.DictCursor,
)


def _get_conn():
    try:
        import streamlit as st
        @st.cache_resource
        def _cached():
            return pymysql.connect(**_DB_CONFIG)
        conn = _cached()
        conn.ping(reconnect=True)
        return conn
    except Exception:
        return pymysql.connect(**_DB_CONFIG)


def execute_query(query, params=None):
    conn = _get_conn()
    with conn.cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchall()


def execute_insert(query, params=None):
    conn = _get_conn()
    with conn.cursor() as cursor:
        cursor.execute(query, params)
    conn.commit()
