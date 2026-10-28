# data/import_csv.py
import pandas as pd
import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

CSV_PATH = r"C:\Users\DK\career_navigator\data\한국산업인력공단_국가기술자격 종목별 시험정보_20240624.csv"
df = pd.read_csv(CSV_PATH, encoding='euc-kr')

pivot = df.pivot_table(
    index='종목명',
    columns='항목',
    values='내용',
    aggfunc='first'
).reset_index()

print(f"✅ 자격증 수: {len(pivot)}개")
print(f"✅ 컬럼: {pivot.columns.tolist()}")

conn = pymysql.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME'),
    charset='utf8mb4'
)
cursor = conn.cursor()

success = 0
fail = 0

for _, row in pivot.iterrows():
    cert_name   = str(row.get('종목명', '') or '')
    issuing_org = str(row.get('실시기관명', '') or '한국산업인력공단')
    description = str(row.get('수행직무', '') or '')
    overview    = str(row.get('개요', '') or '')

    if not description or description == 'nan':
        description = overview

    try:
        cursor.execute("""
            INSERT INTO certifications
                (cert_name, issuing_org, description, cert_type)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                issuing_org = VALUES(issuing_org),
                description = VALUES(description)
        """, (
            cert_name,
            issuing_org if issuing_org != 'nan' else '한국산업인력공단',
            description if description != 'nan' else '',
            '국가기술자격'
        ))
        success += 1
    except Exception as e:
        print(f"❌ 실패: {cert_name} — {e}")
        fail += 1

conn.commit()
cursor.close()
conn.close()

print(f"\n🎉 완료! 성공: {success}개 / 실패: {fail}개")