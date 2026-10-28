# data/update_competency.py
# competency_units 재구성
# = 자격증명 + 능력단위/수행직무 + 진로전망 (있는 것만 조합)

import pymysql
import re
from dotenv import load_dotenv
import os

load_dotenv()

conn = pymysql.connect(
    host=os.getenv('DB_HOST'), user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'), database=os.getenv('DB_NAME'),
    charset='utf8mb4'
)
cursor = conn.cursor()

cursor.execute("SELECT cert_id, cert_name, competency_units, description, career_path FROM certifications")
rows = cursor.fetchall()

print(f"✅ 전체 자격증: {len(rows)}개")

success = 0
for cert_id, cert_name, competency_units, description, career_path in rows:
    parts = []

    # 1. 자격증명
    if cert_name:
        parts.append(cert_name.strip())

    # 2. 능력단위 or 수행직무
    base_text = competency_units or description or ""
    base_text = base_text.strip()
    if base_text:
        # - 제거 및 공백 정리
        base_text = re.sub(r'\s*[-·]\s*', ' ', base_text)
        base_text = re.sub(r'\s+', ' ', base_text).strip()
        parts.append(base_text)

    # 3. 진로전망
    if career_path and career_path.strip():
        cp = career_path.strip()
        cp = re.sub(r'\s*[-·]\s*', ' ', cp)
        cp = re.sub(r'\s+', ' ', cp).strip()
        parts.append(cp)

    new_competency = ' '.join(parts)

    cursor.execute(
        "UPDATE certifications SET competency_units = %s WHERE cert_id = %s",
        (new_competency, cert_id)
    )
    success += 1

conn.commit()
cursor.close()
conn.close()
print(f"🎉 완료! {success}개 competency_units 재구성됨")