# data/update_ncs.py
import pandas as pd
import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

cert_ncs = pd.read_csv(
    r"C:\Users\DK\career_navigator\data\한국산업인력공단_NCS능력단위별_자격종목조회_20251231.csv",
    encoding='cp949'
)
ncs_level = pd.read_csv(
    r"C:\Users\DK\career_navigator\data\한국산업인력공단_국가직무능력표준 정보_20251231.csv",
    encoding='cp949'
)

cert_ncs['코드키'] = cert_ncs['능력단위코드'].str[:10]
ncs_level['코드키'] = ncs_level['분류번호'].str[:10]

merged = cert_ncs.merge(ncs_level[['코드키','수준']], on='코드키', how='left')

grouped = merged.groupby('자격종목명').agg(
    competency_units=('능력단위명', lambda x: ', '.join(x.dropna().unique())),
).reset_index()

print(f"✅ 자격증 수: {len(grouped)}개")

conn = pymysql.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME'),
    charset='utf8mb4'
)
cursor = conn.cursor()

success = 0
for _, row in grouped.iterrows():
    cursor.execute("""
        UPDATE certifications
        SET competency_units = %s
        WHERE cert_name = %s
    """, (
        row['competency_units'],
        row['자격종목명']
    ))
    if cursor.rowcount > 0:
        success += 1

conn.commit()
cursor.close()
conn.close()

print(f"\n🎉 완료! {success}개 자격증 업데이트됨")