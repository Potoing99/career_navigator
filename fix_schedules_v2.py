"""
2026 국가전문자격 시험일정 2차 정정 스크립트
출처: 한국산업인력공단 사전공고 PDF, Q-Net, 각 주관기관 공고 (2026-05-26 기준)
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from utils.db_helper import execute_query, execute_insert

# ── 1단계: 날짜 업데이트 ────────────────────────────────────────────────────────
UPDATES = [
    # 물류관리사: 04-07 접수/06-06 시험 → 06-22 접수/07-25 시험 (Q-Net 제30회 공고)
    {
        'cert': '물류관리사', 'round': '2026년', 'exam_type': '필기',
        'apply_start': '2026-06-22', 'apply_end': '2026-06-26',
        'exam_date': '2026-07-25', 'result_date': '2026-08-19',
    },

    # 산업안전지도사 1차: 01-06 접수/02-28 시험 → 02-23 접수/03-28 시험 (국자넷 확인)
    {
        'cert': '산업안전지도사', 'round': '2026년 1차', 'exam_type': '필기',
        'apply_start': '2026-02-23', 'apply_end': '2026-02-27',
        'exam_date': '2026-03-28', 'result_date': '2026-04-16',
    },
    # 산업안전지도사 2차: 04-21~05-01 접수/06-06 시험 → 05-07~05-08 접수/05-28~05-29 시험
    {
        'cert': '산업안전지도사', 'round': '2026년 2차', 'exam_type': '실기',
        'apply_start': '2026-03-19', 'apply_end': '2026-03-20',
        'exam_date': '2026-05-28', 'result_date': '2026-06-25',
    },

    # 산업보건지도사 1차: 동일 정정
    {
        'cert': '산업보건지도사', 'round': '2026년 1차', 'exam_type': '필기',
        'apply_start': '2026-02-23', 'apply_end': '2026-02-27',
        'exam_date': '2026-03-28', 'result_date': '2026-04-16',
    },
    {
        'cert': '산업보건지도사', 'round': '2026년 2차', 'exam_type': '실기',
        'apply_start': '2026-03-19', 'apply_end': '2026-03-20',
        'exam_date': '2026-05-28', 'result_date': '2026-06-25',
    },

    # 소방시설관리사 1차: 04-07 접수/05-30 시험 → 03-30 접수/05-02 시험 (국자넷 확인)
    {
        'cert': '소방시설관리사', 'round': '2026년 1차', 'exam_type': '필기',
        'apply_start': '2026-03-30', 'apply_end': '2026-04-03',
        'exam_date': '2026-05-02', 'result_date': '2026-05-28',
    },

    # 소방안전교육사 1차: 04-07 접수/05-23 시험 → 06-08 접수/08-15 시험 (한국산업인력공단 사전공고)
    {
        'cert': '소방안전교육사', 'round': '2026년 1차', 'exam_type': '필기',
        'apply_start': '2026-06-08', 'apply_end': '2026-06-12',
        'exam_date': '2026-08-15', 'result_date': '2026-09-10',
    },
    # 소방안전교육사 2차: 07-07 접수/08-08 시험 → 08-24 접수/09-26 시험 (추정)
    {
        'cert': '소방안전교육사', 'round': '2026년 2차', 'exam_type': '실기',
        'apply_start': '2026-08-24', 'apply_end': '2026-08-28',
        'exam_date': '2026-09-26', 'result_date': '2026-10-21',
    },

    # 경매사 1차: 04-07 접수/05-30 시험 → 02-02 접수/03-07 시험 (한국산업인력공단 사전공고)
    {
        'cert': '경매사', 'round': '2026년 1차', 'exam_type': '필기',
        'apply_start': '2026-02-02', 'apply_end': '2026-02-06',
        'exam_date': '2026-03-07', 'result_date': '2026-03-25',
    },
    # 경매사 2차: 07-07 접수/08-08 시험 → 05-18 접수/06-20 시험 (한국산업인력공단 사전공고)
    {
        'cert': '경매사', 'round': '2026년 2차', 'exam_type': '실기',
        'apply_start': '2026-05-18', 'apply_end': '2026-05-22',
        'exam_date': '2026-06-20', 'result_date': '2026-07-08',
    },

    # 관광통역안내사 1차: 04-07 접수/05-09 시험 → 07-06 접수/09-05 시험 (한국관광공사)
    {
        'cert': '관광통역안내사', 'round': '2026년 1차', 'exam_type': '필기',
        'apply_start': '2026-07-06', 'apply_end': '2026-07-10',
        'exam_date': '2026-09-05', 'result_date': '2026-10-07',
    },
    # 관광통역안내사 2차(면접): 07-07 접수/08-15 → 09-14 접수/11-14~11-15 시험
    {
        'cert': '관광통역안내사', 'round': '2026년 2차', 'exam_type': '실기',
        'apply_start': '2026-09-14', 'apply_end': '2026-09-18',
        'exam_date': '2026-11-14', 'result_date': '2026-12-09',
    },

    # 국내여행안내사 1차: 관광통역안내사와 같은 주관(한국관광공사), 동일 시험일 적용
    {
        'cert': '국내여행안내사', 'round': '2026년 1차', 'exam_type': '필기',
        'apply_start': '2026-07-06', 'apply_end': '2026-07-10',
        'exam_date': '2026-09-05', 'result_date': '2026-10-07',
    },
    {
        'cert': '국내여행안내사', 'round': '2026년 2차', 'exam_type': '실기',
        'apply_start': '2026-09-14', 'apply_end': '2026-09-18',
        'exam_date': '2026-11-14', 'result_date': '2026-12-09',
    },

    # 가맹거래사: 07-07 접수/09-05 시험 → 1차 01-26 접수/03-07 시험 (이미 지남, DB 정확도 위해 정정)
    {
        'cert': '가맹거래사', 'round': '2026년', 'exam_type': '필기',
        'apply_start': '2026-01-26', 'apply_end': '2026-01-30',
        'exam_date': '2026-03-07', 'result_date': '2026-03-25',
    },

    # 검수사: 07-07 접수/09-05 시험 → 1차 04-20 접수/05-30 시험 (한국산업인력공단 사전공고)
    {
        'cert': '검수사', 'round': '2026년', 'exam_type': '필기',
        'apply_start': '2026-04-20', 'apply_end': '2026-04-24',
        'exam_date': '2026-05-30', 'result_date': '2026-06-17',
    },

    # 한글속기 — 연 2회 정기시험으로 수정 (대한상공회의소, 스마트속기협회 확인)
    # 기존 1분기(01-25) → 1회(03-28), 기존 2분기(04-25) → 삭제, 3분기(07-25) → 2회(09-05), 4분기(10-24) → 삭제
    # 실기 포함 전부 수정
    {'cert': '한글속기1급', 'round': '2026년 1분기', 'exam_type': '필기',
     'apply_start': '2026-02-16', 'apply_end': '2026-02-27',
     'exam_date': '2026-03-28', 'result_date': '2026-04-15'},
    {'cert': '한글속기1급', 'round': '2026년 1분기', 'exam_type': '실기',
     'apply_start': '2026-02-16', 'apply_end': '2026-02-27',
     'exam_date': '2026-03-28', 'result_date': '2026-04-15'},
    {'cert': '한글속기1급', 'round': '2026년 3분기', 'exam_type': '필기',
     'apply_start': '2026-08-10', 'apply_end': '2026-08-21',
     'exam_date': '2026-09-05', 'result_date': '2026-09-23'},
    {'cert': '한글속기1급', 'round': '2026년 3분기', 'exam_type': '실기',
     'apply_start': '2026-08-10', 'apply_end': '2026-08-21',
     'exam_date': '2026-09-05', 'result_date': '2026-09-23'},
    {'cert': '한글속기2급', 'round': '2026년 1분기', 'exam_type': '필기',
     'apply_start': '2026-02-16', 'apply_end': '2026-02-27',
     'exam_date': '2026-03-28', 'result_date': '2026-04-15'},
    {'cert': '한글속기2급', 'round': '2026년 1분기', 'exam_type': '실기',
     'apply_start': '2026-02-16', 'apply_end': '2026-02-27',
     'exam_date': '2026-03-28', 'result_date': '2026-04-15'},
    {'cert': '한글속기2급', 'round': '2026년 3분기', 'exam_type': '필기',
     'apply_start': '2026-08-10', 'apply_end': '2026-08-21',
     'exam_date': '2026-09-05', 'result_date': '2026-09-23'},
    {'cert': '한글속기2급', 'round': '2026년 3분기', 'exam_type': '실기',
     'apply_start': '2026-08-10', 'apply_end': '2026-08-21',
     'exam_date': '2026-09-05', 'result_date': '2026-09-23'},
    {'cert': '한글속기3급', 'round': '2026년 1분기', 'exam_type': '필기',
     'apply_start': '2026-02-16', 'apply_end': '2026-02-27',
     'exam_date': '2026-03-28', 'result_date': '2026-04-15'},
    {'cert': '한글속기3급', 'round': '2026년 1분기', 'exam_type': '실기',
     'apply_start': '2026-02-16', 'apply_end': '2026-02-27',
     'exam_date': '2026-03-28', 'result_date': '2026-04-15'},
    {'cert': '한글속기3급', 'round': '2026년 3분기', 'exam_type': '필기',
     'apply_start': '2026-08-10', 'apply_end': '2026-08-21',
     'exam_date': '2026-09-05', 'result_date': '2026-09-23'},
    {'cert': '한글속기3급', 'round': '2026년 3분기', 'exam_type': '실기',
     'apply_start': '2026-08-10', 'apply_end': '2026-08-21',
     'exam_date': '2026-09-05', 'result_date': '2026-09-23'},
]

# ── 2단계: 한글속기 가짜 분기(2분기, 4분기) 삭제 ────────────────────────────────
DELETE_ROUNDS = [
    ('한글속기1급', '2026년 2분기'),
    ('한글속기1급', '2026년 4분기'),
    ('한글속기2급', '2026년 2분기'),
    ('한글속기2급', '2026년 4분기'),
    ('한글속기3급', '2026년 2분기'),
    ('한글속기3급', '2026년 4분기'),
]

# ── 3단계: 대한상공회의소 CBT 종목 모든 분기 일정 삭제 후 안내 문구로 대체 ───────
# (컴퓨터활용능력, 워드프로세서, 비서, 전산회계, 전자상거래는 상시CBT — 분기별 고정일 없음)
CBT_CERTS = [
    '컴퓨터활용능력1급', '컴퓨터활용능력2급', '컴퓨터활용능력3급',
    '워드프로세서1급', '워드프로세서2급', '워드프로세서3급',
    '비서1급', '비서2급', '비서3급',
    '전산회계운용사 1급', '전산회계운용사 2급', '전산회계운용사 3급',
    '전자상거래관리사1급', '전자상거래관리사2급', '전자상거래운용사',
]
CBT_REPLACE = {
    'round_name':   '상시시험(CBT)',
    'exam_type':    '필기',
    'apply_start':  '2026-01-01',
    'apply_end':    '2026-12-31',
    'exam_date':    '2026-12-31',
    'result_date':  '2026-12-31',
}

# ──────────────────────────────────────────────────────────────────────────────
updated = skipped = deleted = 0

# UPDATE
for u in UPDATES:
    cert_rows = execute_query("SELECT cert_id FROM certifications WHERE cert_name=%s", (u['cert'],))
    if not cert_rows:
        print(f"[SKIP] 자격증 없음: {u['cert']}")
        skipped += 1
        continue

    cert_ids = [r['cert_id'] for r in cert_rows]
    phs = ','.join(['%s'] * len(cert_ids))
    existing = execute_query(
        f"SELECT schedule_id FROM cert_schedules "
        f"WHERE cert_id IN ({phs}) AND round_name=%s AND exam_type=%s",
        tuple(cert_ids) + (u['round'], u['exam_type'])
    )
    if not existing:
        print(f"[SKIP] 스케줄 없음: {u['cert']} {u['round']} {u['exam_type']}")
        skipped += 1
        continue
    for row in existing:
        execute_insert(
            "UPDATE cert_schedules SET apply_start=%s, apply_end=%s, exam_date=%s, result_date=%s WHERE schedule_id=%s",
            (u['apply_start'], u['apply_end'], u['exam_date'], u['result_date'], row['schedule_id'])
        )
        print(f"[OK] {u['cert']} {u['round']} {u['exam_type']} → {u['exam_date']}")
        updated += 1

# DELETE 가짜 분기
for cert_name, round_name in DELETE_ROUNDS:
    cert_rows = execute_query("SELECT cert_id FROM certifications WHERE cert_name=%s", (cert_name,))
    if not cert_rows:
        continue
    cert_ids = [r['cert_id'] for r in cert_rows]
    phs = ','.join(['%s'] * len(cert_ids))
    rows = execute_query(
        f"SELECT schedule_id FROM cert_schedules WHERE cert_id IN ({phs}) AND round_name=%s",
        tuple(cert_ids) + (round_name,)
    )
    for row in rows:
        execute_insert("DELETE FROM cert_schedules WHERE schedule_id=%s", (row['schedule_id'],))
        print(f"[DEL] {cert_name} {round_name}")
        deleted += 1

# CBT 종목 — 모든 분기 일정 삭제하고 단일 "상시시험(CBT)" 레코드로 대체
for cert_name in CBT_CERTS:
    cert_rows = execute_query("SELECT cert_id FROM certifications WHERE cert_name=%s", (cert_name,))
    if not cert_rows:
        continue
    cid = cert_rows[0]['cert_id']

    # 기존 분기 일정 전부 삭제
    execute_insert("DELETE FROM cert_schedules WHERE cert_id=%s", (cid,))
    deleted_cnt = execute_query("SELECT ROW_COUNT() as n")[0].get('n', '?')

    # 상시시험 단일 레코드 삽입
    execute_insert(
        "INSERT INTO cert_schedules (cert_id, round_name, exam_type, apply_start, apply_end, exam_date, result_date) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (cid, CBT_REPLACE['round_name'], CBT_REPLACE['exam_type'],
         CBT_REPLACE['apply_start'], CBT_REPLACE['apply_end'],
         CBT_REPLACE['exam_date'],  CBT_REPLACE['result_date'])
    )
    print(f"[CBT] {cert_name} → 상시시험(CBT) 단일 레코드로 대체")
    deleted += 1
    updated += 1

print(f"\n완료: {updated}건 수정/삽입, {deleted}건 삭제, {skipped}건 스킵")
