"""
2026 국가전문자격 시험일정 정정 스크립트
검색 출처: Q-Net, 법률저널, 각 주관기관 공고 (2026-05-26 기준)
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from utils.db_helper import execute_query, execute_insert

UPDATES = [
    # ── 공인노무사 (2026년 제35회) ──────────────────────────────────
    # 출처: welfarenote.com, gukja.net
    {
        'cert': '공인노무사', 'round': '2026년 1차', 'exam_type': '필기',
        'apply_start': '2026-03-30', 'apply_end': '2026-04-03',
        'exam_date': '2026-05-23', 'result_date': '2026-06-24',
    },
    {
        'cert': '공인노무사', 'round': '2026년 2차', 'exam_type': '실기',
        'apply_start': '2026-07-13', 'apply_end': '2026-07-17',
        'exam_date': '2026-08-29', 'result_date': '2026-11-18',
    },

    # ── 세무사 (2026년 제63회) ──────────────────────────────────────
    # 출처: taxtimes.co.kr, tax-manager.co.kr
    {
        'cert': '세무사', 'round': '2026년 1차', 'exam_type': '필기',
        'apply_start': '2026-03-23', 'apply_end': '2026-03-27',
        'exam_date': '2026-04-25', 'result_date': '2026-05-27',
    },
    {
        'cert': '세무사', 'round': '2026년 2차', 'exam_type': '실기',
        'apply_start': '2026-06-15', 'apply_end': '2026-06-19',
        'exam_date': '2026-07-18', 'result_date': '2026-10-28',
    },

    # ── 관세사 (2026년 제43회) ──────────────────────────────────────
    # 출처: gosiweek.com, taxtimes.co.kr
    {
        'cert': '관세사', 'round': '2026년 1차', 'exam_type': '필기',
        'apply_start': '2026-02-02', 'apply_end': '2026-02-06',
        'exam_date': '2026-03-14', 'result_date': '2026-04-15',
    },
    {
        'cert': '관세사', 'round': '2026년 2차', 'exam_type': '실기',
        'apply_start': '2026-05-11', 'apply_end': '2026-05-15',
        'exam_date': '2026-06-13', 'result_date': '2026-10-14',
    },

    # ── 변리사 (2026년) ─────────────────────────────────────────────
    # 출처: day.2gnd.com, taxtimes.co.kr
    {
        'cert': '변리사', 'round': '2026년 1차', 'exam_type': '필기',
        'apply_start': '2026-01-12', 'apply_end': '2026-01-16',
        'exam_date': '2026-02-28', 'result_date': '2026-03-25',
    },
    {
        'cert': '변리사', 'round': '2026년 2차', 'exam_type': '실기',
        'apply_start': '2026-04-20', 'apply_end': '2026-04-24',
        'exam_date': '2026-07-31', 'result_date': '2026-10-28',
    },

    # ── 감정평가사 (2026년 제37회) ──────────────────────────────────
    # 출처: land-it.co.kr, welfarenote.com
    {
        'cert': '감정평가사', 'round': '2026년 1차', 'exam_type': '필기',
        'apply_start': '2026-02-02', 'apply_end': '2026-02-06',
        'exam_date': '2026-04-04', 'result_date': '2026-05-06',
    },
    {
        'cert': '감정평가사', 'round': '2026년 2차', 'exam_type': '실기',
        'apply_start': '2026-05-18', 'apply_end': '2026-05-22',
        'exam_date': '2026-07-04', 'result_date': '2026-10-21',
    },

    # ── 공인중개사 (2026년 제37회) ──────────────────────────────────
    # 출처: Q-Net, ebs.co.kr
    {
        'cert': '공인중개사', 'round': '2026년 1·2차', 'exam_type': '필기',
        'apply_start': '2026-08-03', 'apply_end': '2026-08-07',
        'exam_date': '2026-10-31', 'result_date': '2026-12-02',
    },

    # ── 사회복지사1급 (2026년 제24회) ──────────────────────────────
    # 출처: welfare24.net, Q-Net
    {
        'cert': '사회복지사1급', 'round': '2026년', 'exam_type': '필기',
        'apply_start': '2025-12-08', 'apply_end': '2025-12-12',
        'exam_date': '2026-01-17', 'result_date': '2026-03-25',
    },

    # ── 주택관리사보 (2026년 제29회) ────────────────────────────────
    # 출처: khma.org, hapt.co.kr
    {
        'cert': '주택관리사보', 'round': '2026년 1차', 'exam_type': '필기',
        'apply_start': '2026-05-11', 'apply_end': '2026-05-15',
        'exam_date': '2026-06-27', 'result_date': '2026-07-29',
    },
    {
        'cert': '주택관리사보', 'round': '2026년 2차', 'exam_type': '필기',
        'apply_start': '2026-08-10', 'apply_end': '2026-08-14',
        'exam_date': '2026-09-19', 'result_date': '2026-12-02',
    },

    # ── 경비지도사 (2026년 제28회) ──────────────────────────────────
    # 출처: dealbada.com, joandalice.com — 1차+2차 동일 날짜 시행
    {
        'cert': '경비지도사', 'round': '2026년 1차', 'exam_type': '필기',
        'apply_start': '2026-09-14', 'apply_end': '2026-09-18',
        'exam_date': '2026-11-21', 'result_date': '2026-12-31',
    },
    {
        'cert': '경비지도사', 'round': '2026년 2차', 'exam_type': '실기',
        'apply_start': '2026-09-14', 'apply_end': '2026-09-18',
        'exam_date': '2026-11-21', 'result_date': '2026-12-31',
    },

    # ── 행정사 (2026년 제14회) ──────────────────────────────────────
    # 출처: pmg.co.kr, adm.lawschool.co.kr
    {
        'cert': '행정사', 'round': '2026년 1차', 'exam_type': '필기',
        'apply_start': '2026-03-23', 'apply_end': '2026-03-27',
        'exam_date': '2026-05-30', 'result_date': '2026-07-01',
    },
    {
        'cert': '행정사', 'round': '2026년 2차', 'exam_type': '실기',
        'apply_start': '2026-07-27', 'apply_end': '2026-07-31',
        'exam_date': '2026-10-03', 'result_date': '2026-12-16',
    },

    # ── 손해평가사 ──────────────────────────────────────────────────
    # 출처: mainedu.co.kr, winspec.co.kr — 2차 시험일 수정
    {
        'cert': '손해평가사', 'round': '2026년 2차', 'exam_type': '실기',
        'apply_start': '2026-07-07', 'apply_end': '2026-07-10',
        'exam_date': '2026-08-29', 'result_date': '2026-09-26',
    },
]

updated = 0
skipped = 0

for u in UPDATES:
    cert_rows = execute_query(
        "SELECT cert_id FROM certifications WHERE cert_name=%s", (u['cert'],)
    )
    if not cert_rows:
        print(f"[SKIP] 자격증 없음: {u['cert']}")
        skipped += 1
        continue

    cert_ids = [r['cert_id'] for r in cert_rows]
    placeholders = ','.join(['%s'] * len(cert_ids))

    existing = execute_query(
        f"SELECT schedule_id FROM cert_schedules "
        f"WHERE cert_id IN ({placeholders}) AND round_name=%s AND exam_type=%s",
        tuple(cert_ids) + (u['round'], u['exam_type'])
    )

    if not existing:
        print(f"[SKIP] 스케줄 없음: {u['cert']} {u['round']} {u['exam_type']}")
        skipped += 1
        continue

    for row in existing:
        execute_insert(
            """UPDATE cert_schedules
               SET apply_start=%s, apply_end=%s, exam_date=%s, result_date=%s
               WHERE schedule_id=%s""",
            (u['apply_start'], u['apply_end'], u['exam_date'], u['result_date'], row['schedule_id'])
        )
        print(f"[OK] {u['cert']} {u['round']} {u['exam_type']} → 시험 {u['exam_date']}")
        updated += 1

print(f"\n완료: {updated}건 수정, {skipped}건 스킵")
