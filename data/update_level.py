# data/update_level.py
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

# 1. competency_units NULL인 것들 → description으로 채우기
cursor.execute("""
    UPDATE certifications
    SET competency_units = description
    WHERE competency_units IS NULL
    AND description IS NOT NULL AND description != ''
""")
print(f"📝 수행직무로 채운 자격증: {cursor.rowcount}개")

# 2. ncs_level → 자격증 등급으로 채우기
level_map = [
    ('기술사', 8),
    ('기능장', 7),
    ('기사', 6),
    ('산업기사', 5),
    ('기능사', 3),
]

for keyword, level in level_map:
    cursor.execute("""
        UPDATE certifications
        SET ncs_level = %s
        WHERE cert_name LIKE %s
        AND ncs_level IS NULL
    """, (level, f'%{keyword}%'))
    print(f"  {keyword} → 수준 {level}: {cursor.rowcount}개")

# 매칭 안 된 나머지 → 기본값 3
cursor.execute("""
    UPDATE certifications
    SET ncs_level = 3
    WHERE ncs_level IS NULL
""")
print(f"  기타 → 수준 3: {cursor.rowcount}개")

conn.commit()
cursor.close()
conn.close()

print(f"\n🎉 완료!")