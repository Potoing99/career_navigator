# data/fix_level.py
import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

conn = pymysql.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME'),
    charset='utf8mb4'
)
cursor = conn.cursor()

cursor.execute("UPDATE certifications SET ncs_level = 5 WHERE cert_name LIKE '%산업기사%'")
print(f'산업기사 업데이트: {cursor.rowcount}개')

conn.commit()
cursor.close()
conn.close()
print('완료!')