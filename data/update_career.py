# data/update_career.py
# CSV에서 진로전망(career_path) 데이터를 DB에 입력

import pandas as pd
import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

CSV_PATH = r"C:\Users\DK\career_navigator\data\한국산업인력공단_국가기술자격_종목별_시험정보_20240624.csv"
df = pd.read_csv(CSV_PATH, encoding='cp949')

pivot = df.pivot_table(
    index='종목명', columns='항목', values='내용', aggfunc='first'
).reset_index()

print(f"✅ CSV 자격증 수: {len(pivot)}개")

# 진로 및 전망 컬럼명 확인
print(f"✅ 컬럼 목록: {list(pivot.columns)}")

conn = pymysql.connect(
    host=os.getenv('DB_HOST'), user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'), database=os.getenv('DB_NAME'),
    charset='utf8mb4'
)
cursor = conn.cursor()

success = 0
skip = 0

for _, row in pivot.iterrows():
    cert_name = str(row.get('종목명', '') or '')
    
    # 컬럼명이 '진로 및 전망' 또는 '진로전망' 일 수 있음
    career_path = str(row.get('진로 및 전망', '') or '')
    if career_path == 'nan':
        career_path = ''

    if not career_path:
        skip += 1
        continue

    cursor.execute(
        "UPDATE certifications SET career_path = %s WHERE cert_name = %s AND cert_type = '국가기술자격'",
        (career_path, cert_name)
    )
    if cursor.rowcount > 0:
        success += 1

conn.commit()
cursor.close()
conn.close()
print(f"\n🎉 완료! 업데이트: {success}개 / 진로전망 없음: {skip}개")