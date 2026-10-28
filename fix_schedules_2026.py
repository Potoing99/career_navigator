"""
2026년 한국산업인력공단 공식 시험일정으로 DB 업데이트
출처: Q-Net / 한국산업인력공단 지역본부 공고
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pymysql, os
from dotenv import load_dotenv
load_dotenv()

conn = pymysql.connect(
    host=os.getenv('DB_HOST','localhost'), user=os.getenv('DB_USER','root'),
    password=os.getenv('DB_PASSWORD',''), database=os.getenv('DB_NAME','career_nav'),
    charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor
)

# ── 실제 2026년 공식 일정 ──────────────────────────────────────────────────────

# 기사/산업기사 (ncs_level 5, 6) — 3회
GISA_SESSIONS = [
    ('2026년 1회', '필기', '2026-01-12', '2026-01-15', '2026-01-30', '2026-03-11'),
    ('2026년 1회', '실기', '2026-03-23', '2026-03-26', '2026-04-18', '2026-06-05'),
    ('2026년 2회', '필기', '2026-04-20', '2026-04-23', '2026-05-09', '2026-06-10'),
    ('2026년 2회', '실기', '2026-06-22', '2026-06-25', '2026-07-18', '2026-09-04'),
    ('2026년 3회', '필기', '2026-07-20', '2026-07-23', '2026-08-07', '2026-09-09'),
    ('2026년 3회', '실기', '2026-09-21', '2026-09-28', '2026-10-24', '2026-12-11'),
]

# 기능사 (ncs_level 3, 한국산업인력공단) — 4회
GINEUNGSA_SESSIONS = [
    ('2026년 1회', '필기', '2026-01-06', '2026-01-09', '2026-01-20', '2026-01-30'),
    ('2026년 1회', '실기', '2026-02-02', '2026-02-05', '2026-03-14', '2026-04-10'),
    ('2026년 2회', '필기', '2026-03-16', '2026-03-20', '2026-04-04', '2026-04-22'),
    ('2026년 2회', '실기', '2026-04-27', '2026-04-30', '2026-05-30', '2026-06-26'),
    ('2026년 3회', '필기', '2026-06-08', '2026-06-11', '2026-06-27', '2026-07-15'),
    ('2026년 3회', '실기', '2026-07-27', '2026-07-30', '2026-08-29', '2026-10-02'),
    ('2026년 4회', '필기', '2026-08-24', '2026-08-27', '2026-09-16', '2026-10-07'),
    ('2026년 4회', '실기', '2026-10-12', '2026-10-15', '2026-11-14', '2026-12-11'),
]

# 기능장 (ncs_level 7) — 2회 (79회, 80회)
GINEUNGJAN_SESSIONS = [
    ('2026년 1회(79회)', '필기', '2026-01-06', '2026-01-09', '2026-01-24', '2026-01-30'),
    ('2026년 1회(79회)', '실기', '2026-02-02', '2026-02-05', '2026-03-14', '2026-04-10'),
    ('2026년 2회(80회)', '필기', '2026-06-08', '2026-06-11', '2026-06-27', '2026-07-15'),
    ('2026년 2회(80회)', '실기', '2026-07-27', '2026-07-30', '2026-08-29', '2026-10-02'),
]

# 기술사 (ncs_level 8) — 3회 (138회, 139회, 140회), 실기=구술면접
GISULSA_SESSIONS = [
    ('2026년 1회(138회)', '필기', '2026-01-06', '2026-01-09', '2026-02-07', '2026-03-25'),
    ('2026년 1회(138회)', '실기', '2026-03-03', '2026-03-21', '2026-05-02', '2026-05-29'),
    ('2026년 2회(139회)', '필기', '2026-04-13', '2026-04-16', '2026-05-16', '2026-06-24'),
    ('2026년 2회(139회)', '실기', '2026-06-08', '2026-06-11', '2026-08-01', '2026-08-28'),
    ('2026년 3회(140회)', '필기', '2026-07-13', '2026-07-16', '2026-08-22', '2026-10-07'),
    ('2026년 3회(140회)', '실기', '2026-08-31', '2026-09-03', '2026-11-14', '2026-12-11'),
]

# 대한상공회의소 상시시험 (컴활 등) — 변경 없음, 그대로 유지

with conn.cursor() as cur:
    # 한국산업인력공단 국가기술자격만 삭제 후 재삽입
    cur.execute("""
        DELETE cs FROM cert_schedules cs
        JOIN certifications c ON cs.cert_id = c.cert_id
        WHERE c.cert_type = '국가기술자격'
          AND (c.issuing_org LIKE '한국산업인력공단%' OR c.issuing_org LIKE ' 한국산업인력공단%')
    """)
    deleted = cur.rowcount
    print(f'Deleted {deleted} old rows')

    # 레벨별 cert_id 조회
    cur.execute("""
        SELECT cert_id, ncs_level FROM certifications
        WHERE cert_type='국가기술자격'
          AND (issuing_org LIKE '한국산업인력공단%' OR issuing_org LIKE ' 한국산업인력공단%')
    """)
    hrd_certs = cur.fetchall()

    level_ids = {3: [], 5: [], 6: [], 7: [], 8: []}
    for c in hrd_certs:
        lv = c['ncs_level']
        if lv in level_ids:
            level_ids[lv].append(c['cert_id'])

    for lv, ids in level_ids.items():
        print(f'  Level {lv}: {len(ids)}개')

    def bulk_insert(cert_ids, sessions):
        rows = [(cid, s[0], s[1], s[2], s[3], s[4], s[5]) for cid in cert_ids for s in sessions]
        if rows:
            cur.executemany(
                'INSERT INTO cert_schedules (cert_id, round_name, exam_type, apply_start, apply_end, exam_date, result_date) VALUES (%s,%s,%s,%s,%s,%s,%s)',
                rows
            )
        return len(rows)

    cnt = 0
    cnt += bulk_insert(level_ids[3], GINEUNGSA_SESSIONS)
    cnt += bulk_insert(level_ids[5], GISA_SESSIONS)
    cnt += bulk_insert(level_ids[6], GISA_SESSIONS)
    cnt += bulk_insert(level_ids[7], GINEUNGJAN_SESSIONS)
    cnt += bulk_insert(level_ids[8], GISULSA_SESSIONS)

conn.commit()
conn.close()
print(f'\nInserted {cnt} rows')
print('Done!')
