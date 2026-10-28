import json
import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

def get_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'career_nav'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

with open('data/ncs_categories.json', 'r', encoding='utf-8') as f:
    dclas_list = json.load(f)
print(f'JSON에서 {len(dclas_list)}개 로드 완료')

conn = get_connection()
try:
    with conn.cursor() as cursor:
        for dc in dclas_list:
            cursor.execute('''
                INSERT INTO ncs_categories
                (lclas_cd, lclas_nm, mclas_cd, mclas_nm, sclas_cd, sclas_nm, dclas_cd, dclas_nm, duty_def)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                dc.get('NCS_LCLAS_CD'), dc.get('NCS_LCLAS_CDNM'),
                dc.get('NCS_MCLAS_CD'), dc.get('NCS_MCLAS_CDNM'),
                dc.get('NCS_SCLAS_CD'), dc.get('NCS_SCLAS_CDNM'),
                dc.get('NCS_SUBD_CD'),  dc.get('NCS_SUBD_CDNM'),
                dc.get('DUTY_DEF'),
            ))
    conn.commit()
    print(f'저장 완료! 총 {len(dclas_list)}개')
finally:
    conn.close()