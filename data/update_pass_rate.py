import pandas as pd
import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

EXCEL_PATH = r"C:\Users\DK\career_navigator\data\2025_통계연보 2.검정형 국가기술자격★.xlsx"

SHEET_GRADE = {
    '2-1(기술사)':   '기술사',
    '2-1(기능장)':   '기능장',
    '2-1(기사)':     '기사',
    '2-1(산업기사)': '산업기사',
    '2-1(기능사)':   '기능사',
}

# 등급별 평균 합격률 (매칭 안 된 자격증 대체용)
GRADE_AVG = {
    '기술사':   53.7,
    '기능장':   32.9,
    '기사':     39.3,
    '산업기사': 45.3,
    '기능사':   50.3,
    '국가전문자격': 45.0,  # 전문자격 평균
}

def get_pass_rates():
    """엑셀에서 자격증별 합격률 계산 (5개년 합산)"""
    results = {}
    for sheet, grade in SHEET_GRADE.items():
        df = pd.read_excel(EXCEL_PATH, sheet_name=sheet, header=None)
        df[0] = df[0].ffill()
        filtered = df[(df[2] == '전체') & (df[1].isin([20,21,22,23,24]))]

        for cert_name, group in filtered.groupby(0):
            cert_name = str(cert_name).strip()
            if cert_name in ['합계', 'nan'] or cert_name.endswith('분야'):
                continue
            applicants = pd.to_numeric(group[8], errors='coerce').sum()
            passed = pd.to_numeric(group[9], errors='coerce').sum()
            if applicants < 30:
                continue
            full_name = cert_name + grade
            results[full_name] = round(passed / applicants * 100, 1)
    return results

def main():
    conn = pymysql.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
        charset='utf8mb4'
    )
    cursor = conn.cursor()

    # 1. 기존 합격률 전부 초기화
    cursor.execute("UPDATE certifications SET pass_rate = NULL")
    print("기존 합격률 초기화 완료")

    # 2. 엑셀에서 합격률 계산
    pass_rates = get_pass_rates()
    print(f"엑셀에서 계산된 자격증: {len(pass_rates)}개")

    # 3. DB 자격증 전체 조회
    cursor.execute("SELECT cert_name, cert_type, ncs_level FROM certifications")
    all_certs = cursor.fetchall()

    updated_excel = 0
    updated_avg = 0

    for cert_name, cert_type, ncs_level in all_certs:
        if cert_name in pass_rates:
            # 엑셀 데이터로 업데이트
            cursor.execute(
                "UPDATE certifications SET pass_rate = %s WHERE cert_name = %s",
                (pass_rates[cert_name], cert_name)
            )
            updated_excel += 1
        else:
            # 등급별 평균으로 대체
            if cert_type == '국가전문자격':
                avg = GRADE_AVG['국가전문자격']
            elif ncs_level == 8:
                avg = GRADE_AVG['기술사']
            elif ncs_level == 7:
                avg = GRADE_AVG['기능장']
            elif ncs_level == 6:
                avg = GRADE_AVG['기사']
            elif ncs_level == 5:
                avg = GRADE_AVG['산업기사']
            else:
                avg = GRADE_AVG['기능사']

            cursor.execute(
                "UPDATE certifications SET pass_rate = %s WHERE cert_name = %s",
                (avg, cert_name)
            )
            updated_avg += 1

    conn.commit()
    cursor.close()
    conn.close()

    print(f"엑셀 데이터로 업데이트: {updated_excel}개")
    print(f"등급별 평균으로 대체: {updated_avg}개")
    print(f"완료!")

if __name__ == "__main__":
    main()