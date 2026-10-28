import re
from sentence_transformers import SentenceTransformer, util
from utils.db_helper import execute_query
from models.ontology import is_related_major, get_keywords, get_ncs_dclas, get_related_majors

try:
    from utils.model_cache import get_sbert_model
    model = get_sbert_model()
except Exception:
    model = SentenceTransformer("jhgan/ko-sroberta-multitask")

# ── 상수 정의 ──────────────────────────────────────────────────────────────────
GRADE_KEYWORDS = ['기술사', '기능장', '기사', '산업기사', '기능사']

SERVICE_CERTS = {
    '사회조사분석사1급': {'required': '사회조사분석사2급', 'career': 2, 'alt_career': 3},
    '직업상담사1급':    {'required': '직업상담사2급',    'career': 2, 'alt_career': 3},
    '컨벤션기획사1급':  {'required': '컨벤션기획사2급',  'career': 3, 'alt_career': 4},
    '소비자전문상담사1급': {'required': '소비자전문상담사2급', 'career': 2, 'alt_career': 3},
    '임상심리사1급':   {'education': '대학원',      'career': 2},
    '임상심리사2급':   {'education': '4년제대졸이상', 'career': 1, 'alt_career': 2},
    '국제의료관광코디네이터': {'language_test': True, 'education': '4년제대졸이상', 'alt_career': 4},
}

EDUCATION_RANK = {
    '고졸':         1,
    '2년제전문대졸': 2,
    '3년제전문대졸': 3,
    '4년제대졸이상': 4,
    '대학원':       5,
}


# ── 헬퍼 함수들 ────────────────────────────────────────────────────────────────

def get_domain(cert_name):
    """자격증명에서 등급 키워드 및 숫자급 접미사 제거"""
    for kw in GRADE_KEYWORDS:
        cert_name = cert_name.replace(kw, '').strip()
    # 1급, 2급, 3급 등 숫자급 접미사 제거 (컴활, 사회조사분석사 등)
    cert_name = re.sub(r'\d+급$', '', cert_name).strip()
    return cert_name


def check_related_major(major_name, cert_name):
    """
    전공명이 자격증과 관련학과인지 판단 (온톨로지 기반)
    기존 SBERT 방식에서 교체 - 속도/정확도 향상
    """
    return is_related_major(cert_name, major_name)


def is_same_domain(cert_a, cert_b, threshold=0.85):
    """두 자격증이 동일직무인지 SBERT 유사도로 판단"""
    domain_a = get_domain(cert_a)
    domain_b = get_domain(cert_b)
    if not domain_a or not domain_b:
        return False
    emb_a = model.encode(domain_a, convert_to_tensor=True)
    emb_b = model.encode(domain_b, convert_to_tensor=True)
    score = util.cos_sim(emb_a, emb_b).item()
    return score >= threshold


def get_owned_cert_level(cert_name, owned_certs_db):
    """보유 자격증 중 동일직무인 자격증의 ncs_level 반환"""
    for owned in owned_certs_db:
        if is_same_domain(cert_name, owned['cert_name']):
            return owned['ncs_level']
    return None


def edu_rank(education):
    """학력 문자열 → 순위 숫자 변환"""
    return EDUCATION_RANK.get(education, 0)


# ── 서비스분야 필터 ────────────────────────────────────────────────────────────

LANGUAGE_MIN_SCORES = {
    'TOEIC':     700,
    'TOEFL iBT': 71,
    'IELTS':     5.5,
    'TEPS':      625,
}
OPIC_PASSING = ['IM1', 'IM2', 'IM3', 'IH', 'AL']


def _check_language_test(language_test):
    """어학성적이 기준 이상인지 확인"""
    if not language_test:
        return False
    test_type = language_test.get('type', '')
    if test_type == 'OPIc':
        return language_test.get('grade', '') in OPIC_PASSING
    min_score = LANGUAGE_MIN_SCORES.get(test_type)
    if min_score is None:
        return False
    return float(language_test.get('score', 0)) >= min_score


def _check_service_cert(cert_name, user_input, owned_cert_names):
    rule = SERVICE_CERTS[cert_name]
    education     = user_input['education']
    career_years  = user_input['career_years']
    language_test = user_input.get('language_test')

    if rule.get('language_test') and not _check_language_test(language_test):
        return False

    if 'required' in rule:
        required = rule['required']
        if required in owned_cert_names:
            return True
        if career_years >= rule.get('alt_career', 99):
            return True
        return False

    if 'education' in rule:
        if edu_rank(education) >= edu_rank(rule['education']):
            if career_years >= rule.get('career', 0):
                return True
        if career_years >= rule.get('alt_career', 99):
            return True
        return False

    return True


# ── 등급별 응시자격 체크 ───────────────────────────────────────────────────────

def _check_level5(user_input, owned_certs_db, cert_name):
    """산업기사(level 5) 응시자격 체크"""
    education    = user_input['education']
    career_years = user_input['career_years']
    use_major    = user_input.get('use_major', False)
    major        = user_input.get('major', '')
    extra        = user_input.get('extra_qualifications', [])

    is_related = use_major and check_related_major(major, cert_name)

    # ① 전문대 이상 + 관련학과
    if edu_rank(education) >= edu_rank('2년제전문대졸') and is_related:
        return True
    # ② 경력 2년 이상
    if career_years >= 2:
        return True
    # ③ 보유 기능사 (동일직무) + 경력 1년
    owned_level = get_owned_cert_level(cert_name, owned_certs_db)
    if owned_level == 3 and career_years >= 1:
        return True
    # ④ 동일직무 산업기사 보유
    if owned_level == 5:
        return True
    # ⑤ 기술훈련과정 이수
    if '산업기사수준 기술훈련과정 이수' in extra:
        return True
    # ⑥ 기능경기대회 입상
    if '기능경기대회 입상' in extra:
        return True

    return False


def _check_level6(user_input, owned_certs_db, cert_name):
    """기사(level 6) 응시자격 체크"""
    education    = user_input['education']
    career_years = user_input['career_years']
    use_major    = user_input.get('use_major', False)
    major        = user_input.get('major', '')
    extra        = user_input.get('extra_qualifications', [])

    is_related = use_major and check_related_major(major, cert_name)

    # ① 4년제대졸 + 관련학과
    if edu_rank(education) >= edu_rank('4년제대졸이상') and is_related:
        return True
    # ② 3년제전문대졸 + 관련학과 + 경력 1년
    if edu_rank(education) >= edu_rank('3년제전문대졸') and is_related and career_years >= 1:
        return True
    # ③ 2년제전문대졸 + 관련학과 + 경력 2년
    if edu_rank(education) >= edu_rank('2년제전문대졸') and is_related and career_years >= 2:
        return True
    # ④ 경력 4년 이상
    if career_years >= 4:
        return True
    # ⑤ 기사수준 기술훈련과정 이수
    if '기사수준 기술훈련과정 이수' in extra:
        return True
    # ⑥ 보유 산업기사 (동일직무) + 경력 1년
    owned_level = get_owned_cert_level(cert_name, owned_certs_db)
    if owned_level == 5 and career_years >= 1:
        return True
    # ⑦ 보유 기능사 (동일직무) + 경력 3년
    if owned_level == 3 and career_years >= 3:
        return True
    # ⑧ 동일직무 기사 보유
    if owned_level == 6:
        return True

    return False


def _check_level7(user_input, owned_certs_db, cert_name):
    """기능장(level 7) 응시자격 체크"""
    career_years = user_input['career_years']
    extra        = user_input.get('extra_qualifications', [])

    owned_level = get_owned_cert_level(cert_name, owned_certs_db)

    if owned_level == 5 and career_years >= 5:
        return True
    if owned_level == 3 and career_years >= 7:
        return True
    if '기능대학 기능장과정 이수' in extra:
        return True
    if owned_level == 7:
        return True
    if career_years >= 9:
        return True

    return False


def _check_level8(user_input, owned_certs_db, cert_name):
    """기술사(level 8) 응시자격 체크"""
    education    = user_input['education']
    career_years = user_input['career_years']
    use_major    = user_input.get('use_major', False)
    major        = user_input.get('major', '')
    extra        = user_input.get('extra_qualifications', [])

    is_related  = use_major and check_related_major(major, cert_name)
    owned_level = get_owned_cert_level(cert_name, owned_certs_db)

    if owned_level == 6 and career_years >= 4:
        return True
    if owned_level == 5 and career_years >= 5:
        return True
    if owned_level == 3 and career_years >= 7:
        return True
    if edu_rank(education) >= edu_rank('4년제대졸이상') and is_related and career_years >= 6:
        return True
    if edu_rank(education) >= edu_rank('3년제전문대졸') and is_related and career_years >= 7:
        return True
    if edu_rank(education) >= edu_rank('2년제전문대졸') and is_related and career_years >= 8:
        return True
    if '기사수준 기술훈련과정 이수' in extra and career_years >= 6:
        return True
    if owned_level == 8:
        return True
    if career_years >= 9:
        return True

    return False


# ── STEP 1 메인 함수 ───────────────────────────────────────────────────────────

def step1_filter(certs, user_input):
    """
    응시자격 필터링

    user_input = {
        'education'            : str,   # 최종학력
        'career_years'         : int,   # 희망분야 경력 년수
        'owned_certs'          : list,  # 보유 자격증
        'use_major'            : bool,  # True=전공 살려서, False=희망분야로 새롭게
        'major'                : str,   # 전공명
        'language_test'        : dict or None,
        'extra_qualifications' : list,
        'ncs_field'            : str,   # STEP 3에서 사용
        'region'               : str,   # 추후 사용
        'weight_mode'          : str,   # STEP 4에서 사용
    }
    """

    owned_certs_db   = []
    owned_cert_names = []

    for owned in user_input.get('owned_certs', []):
        if isinstance(owned, dict):
            owned_certs_db.append(owned)
            owned_cert_names.append(owned['cert_name'])
        else:
            rows = execute_query(
                "SELECT cert_name, ncs_level FROM certifications WHERE cert_name = %s",
                (owned,)
            )
            if rows:
                owned_certs_db.append(rows[0])
                owned_cert_names.append(rows[0]['cert_name'])
            else:
                owned_certs_db.append({'cert_name': owned, 'ncs_level': None})
                owned_cert_names.append(owned)

    use_major = user_input.get('use_major', False)
    filtered = []

    for cert in certs:
        cert_name = cert['cert_name']
        cert_type = cert['cert_type']
        ncs_level = cert['ncs_level']

        # ① 국가전문자격 → 전부 통과
        if cert_type == '국가전문자격':
            filtered.append({**cert, 'eligible': True})
            continue

        # ② ncs_level = 3 (기능사/기타)
        if ncs_level == 3 or ncs_level is None:
            if cert_name in SERVICE_CERTS:
                ok = _check_service_cert(cert_name, user_input, owned_cert_names)
                if ok or not use_major:
                    filtered.append({**cert, 'eligible': ok})
            else:
                filtered.append({**cert, 'eligible': True})
            continue

        # ③ ncs_level 5~8
        passed = False
        if ncs_level == 5:
            passed = _check_level5(user_input, owned_certs_db, cert_name)
        elif ncs_level == 6:
            passed = _check_level6(user_input, owned_certs_db, cert_name)
        elif ncs_level == 7:
            passed = _check_level7(user_input, owned_certs_db, cert_name)
        elif ncs_level == 8:
            passed = _check_level8(user_input, owned_certs_db, cert_name)

        if passed:
            filtered.append({**cert, 'eligible': True})
        elif not use_major or ncs_level in (7, 8):
            # 희망분야 탐색 모드 또는 기능장/기술사: 응시불가도 포함하되 eligible=False 표시
            filtered.append({**cert, 'eligible': False})

    return filtered


# ── STEP 2: SBERT 유사도 계산 ─────────────────────────────────────────────────

def step2_similarity(user_input, filtered_certs):
    """
    유사도 계산
    
    "희망분야로 새롭게": 선택한 dclas_nm으로 온톨로지 ncs_dclas 매칭
    "전공 살려서": 전공명으로 온톨로지 관련키워드 매칭 + SBERT 보조
    """
    use_major  = user_input.get('use_major', False)
    major      = user_input.get('major', '')
    dclas_nm   = user_input.get('ncs_dclas', '')
    ncs_mclas  = user_input.get('ncs_mclas', '')

    # 희망분야 모드: 선택한 중분류에 속하는 dclas 전체 조회 (필터용)
    mclas_dclas_set = set()
    if not use_major and ncs_mclas:
        rows = execute_query(
            "SELECT DISTINCT dclas_nm FROM ncs_categories WHERE mclas_nm = %s",
            (ncs_mclas,)
        )
        mclas_dclas_set = {r['dclas_nm'] for r in rows}

    results = []

    for cert in filtered_certs:
        cert_name = cert['cert_name']
        score = 0.0

        if not use_major:
            # ── 희망분야로 새롭게: dclas_nm 매칭 ──
            if not dclas_nm:
                score = 0.0
            else:
                cert_dclas = get_ncs_dclas(cert_name)

                # ── NCS 중분류 필터: 해당 중분류 dclas와 겹치지 않으면 제외 ──
                if mclas_dclas_set and cert_dclas:
                    if not any(d in mclas_dclas_set for d in cert_dclas):
                        results.append({**cert, 'similarity': 0.0})
                        continue

                # "전체" 선택 시 쉼표로 묶인 dclas 리스트, 단일 선택 시 리스트 1개
                query_dclas = [d.strip() for d in dclas_nm.split(",") if d.strip()]
                is_broad = len(query_dclas) > 1
                sim_threshold = 0.5 if is_broad else 0.6

                if any(d in cert_dclas for d in query_dclas):
                    score = 1.0
                else:
                    if cert_dclas and query_dclas:
                        emb_query = model.encode(query_dclas, convert_to_tensor=True)
                        emb_certs = model.encode(cert_dclas, convert_to_tensor=True)
                        sims = util.cos_sim(emb_query, emb_certs)
                        max_score = float(sims.max())
                        score = max_score if max_score >= sim_threshold else 0.0
                    else:
                        score = 0.0

        else:
            # ── 전공 살려서: 하이브리드 유사도 (온톨로지 60% + 도메인 40%) ──
            # - related_score: 온톨로지 관련전공 리스트 vs 입력전공 → 광범위 커버리지
            # - domain_score:  자격증명 도메인 vs 입력전공 → 정밀 순위 분별
            from models.ontology import get_related_majors
            related_majors = get_related_majors(cert_name)

            if not related_majors:
                score = 0.0
            else:
                emb_major   = model.encode(major, convert_to_tensor=True)
                emb_related = model.encode(related_majors, convert_to_tensor=True)
                related_score = float(util.cos_sim(emb_major, emb_related).max())

                cert_domain = get_domain(cert_name)
                if cert_domain:
                    emb_domain   = model.encode(cert_domain, convert_to_tensor=True)
                    domain_score = float(util.cos_sim(emb_major, emb_domain).item())
                else:
                    domain_score = related_score

                score = 0.6 * related_score + 0.4 * domain_score

        results.append({**cert, 'similarity': score})

    # 유사도 기준 내림차순 정렬
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results

# ── STEP 3: 최종 점수 합산 ────────────────────────────────────────────────────

WEIGHT_MODES = {
    'easy':   {'w1': 0.5, 'w2': 0.4, 'w3': 0.1},  # 입문용 - 합격률 우선
    'career': {'w1': 0.5, 'w2': 0.1, 'w3': 0.4},  # 실용형 - 등급 우선
}

NCS_LEVEL_NORM = {
    3: 0.3,
    5: 0.5,
    6: 0.6,
    7: 0.7,
    8: 0.8,
}

def _get_owned_grade(cert_name: str, owned_cert_names: list) -> int | None:
    """
    보유 자격증 중 동일 도메인의 숫자급 번호 반환 (컴활2급→2, 없으면 None)
    """
    my_domain = get_domain(cert_name)
    if not my_domain:
        return None
    # 1급이면 여기서 몇 급인지 추출
    m = re.search(r'(\d+)급$', cert_name)
    my_grade = int(m.group(1)) if m else None

    for owned in owned_cert_names:
        om = re.search(r'(\d+)급$', owned)
        if not om:
            continue
        owned_domain = get_domain(owned)
        if owned_domain == my_domain:
            return int(om.group(1))
    return None


def step3_score(user_input, certs_with_similarity):
    weight_mode = user_input.get('weight_mode', 'career')
    weights = WEIGHT_MODES.get(weight_mode, WEIGHT_MODES['career'])
    w1 = weights['w1']
    w2 = weights['w2']
    w3 = weights['w3']

    owned_cert_names = []
    for owned in user_input.get('owned_certs', []):
        owned_cert_names.append(owned if isinstance(owned, str) else owned.get('cert_name', ''))

    results = []
    for cert in certs_with_similarity:
        similarity = cert.get('similarity', 0.0)
        pass_rate  = cert.get('pass_rate')
        cert_type  = cert.get('cert_type', '')
        ncs_level  = cert.get('ncs_level')
        cert_name  = cert.get('cert_name', '')

        # 유사도 threshold 이하 제외 (레벨별 기준 다름)
        if ncs_level == 8 or cert_type == '국가전문자격':
            min_sim = 0.65
        elif ncs_level == 7:
            min_sim = 0.60
        else:
            min_sim = 0.5
        if similarity < min_sim:
            continue

        # NCS레벨 정규화
        level_norm = NCS_LEVEL_NORM.get(ncs_level, 0.3)

        if cert_type == '국가전문자격' or pass_rate is None:
            final_score = similarity * w1 + level_norm * w3
        else:
            pass_rate_norm = pass_rate / 100.0
            final_score = similarity * w1 + pass_rate_norm * w2 + level_norm * w3

        # ── 업그레이드 경로 보너스 ────────────────────────────────────────────
        # 보유 자격증보다 상위급(숫자 작을수록 상위: 2급→1급)이면 +0.25 가산
        my_m = re.search(r'(\d+)급$', cert_name)
        if my_m and owned_cert_names:
            my_grade     = int(my_m.group(1))
            owned_grade  = _get_owned_grade(cert_name, owned_cert_names)
            if owned_grade is not None and my_grade < owned_grade:
                final_score += 0.25

        results.append({**cert, 'final_score': final_score})

    results.sort(key=lambda x: x['final_score'], reverse=True)
    return results

# ── STEP 4: 추천 결과 반환 ────────────────────────────────────────────────────

NCS_LEVEL_LABEL = {
    3: '기능사',
    5: '산업기사',
    6: '기사',
    7: '기능장',
    8: '기술사',
}

def _make_reason(cert, user_input):
    """추천 이유 텍스트 한 줄 생성"""
    parts = []

    similarity = cert.get('similarity', 0.0)
    use_major  = user_input.get('use_major', False)

    if similarity >= 0.99:
        if use_major:
            parts.append(f"{user_input.get('major', '')} 전공과 완전 일치")
        else:
            parts.append(f"{user_input.get('ncs_dclas', '')} 직무와 완전 일치")
    elif similarity >= 0.75:
        if use_major:
            parts.append(f"{user_input.get('major', '')} 전공과 관련 높음")
        else:
            parts.append(f"{user_input.get('ncs_dclas', '')} 직무와 관련 높음")
    else:
        if use_major:
            parts.append(f"{user_input.get('major', '')} 전공과 관련 있음")
        else:
            parts.append(f"{user_input.get('ncs_dclas', '')} 직무와 관련 있음")

    pass_rate = cert.get('pass_rate')
    if pass_rate is not None:
        parts.append(f"합격률 {pass_rate:.1f}%")

    ncs_level = cert.get('ncs_level')
    level_label = NCS_LEVEL_LABEL.get(ncs_level)
    if level_label:
        parts.append(f"{level_label}급")

    return ' · '.join(parts)


def step4_result(scored_certs, user_input, top_n=5):
    """
    레벨별 그룹핑 후 각 그룹 상위 top_n개 반환
    각 항목에 추천 이유 텍스트 추가

    반환 구조:
    {
        'level8': [...],  # 기술사
        'level7': [...],  # 기능장
        'level6': [...],  # 기사
        'level5': [...],  # 산업기사
        'level3': [...],  # 기능사
        'other':  [...],  # 기타 기술자격 (컴활·워드 등 급수제 자격)
        'prof':   [...],  # 국가전문자격
    }
    """
    groups = {'level8': [], 'level7': [], 'level6': [],
              'level5': [], 'level3': [], 'other': [], 'prof': []}

    _grade_keywords = ['기술사', '기능장', '기사', '산업기사', '기능사']

    for cert in scored_certs:
        cert_with_reason = {**cert, 'reason': _make_reason(cert, user_input)}
        cert_name = cert.get('cert_name', '')
        if cert.get('cert_type') == '국가전문자격':
            groups['prof'].append(cert_with_reason)
        elif not any(kw in cert_name for kw in _grade_keywords):
            # 등급 키워드가 없는 자격증 → 기타 기술자격 (컴활, 워드, 게임프로그래밍 등)
            groups['other'].append(cert_with_reason)
        else:
            level = cert.get('ncs_level')
            key = f'level{level}' if f'level{level}' in groups else 'level3'
            groups[key].append(cert_with_reason)

    # 각 그룹 top_n개로 자르기
    return {k: v[:top_n] for k, v in groups.items()}


# ── 메인 추천 함수 ─────────────────────────────────────────────────────────────
def recommend(user_input, top_n=5):
    certs    = execute_query("SELECT * FROM certifications")
    filtered = step1_filter(certs, user_input)
    scored   = step3_score(user_input, step2_similarity(user_input, filtered))
    return step4_result(scored, user_input, top_n=top_n)


# ── 테스트 ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    certs = execute_query("SELECT * FROM certifications")

    for mode in ['easy', 'career']:
        user_input_test1 = {
            "education": "4년제대졸이상",
            "career_years": 0,
            "owned_certs": [],
            "use_major": True,          # 전공 살려서로 변경
            "major": "컴퓨터공학",
            "ncs_dclas": "응용SW엔지니어링",
            "extra_qualifications": [],
            "language_test": None,
            "weight_mode": mode
        }

        user_input_test2 = {
            "education": "4년제대졸이상",
            "career_years": 0,
            "owned_certs": [],
            "use_major": True,
            "major": "컴퓨터공학",
            "ncs_dclas": "",
            "extra_qualifications": [],
            "language_test": None,
            "weight_mode": mode
        }

        filtered1 = step1_filter(certs, user_input_test1)
        result1 = step2_similarity(user_input_test1, filtered1)
        scored1 = step3_score(user_input_test1, result1)
        print(f"\n[희망분야: 응용SW엔지니어링 - {mode} 상위 10개]")
        for r in scored1[:10]:
            print(f"  {r['cert_name']}: 유사도={r['similarity']:.3f}, 합격률={r.get('pass_rate')}%, 레벨={r.get('ncs_level')}, 최종={r['final_score']:.3f}")

        filtered2 = step1_filter(certs, user_input_test2)
        result2 = step2_similarity(user_input_test2, filtered2)
        scored2 = step3_score(user_input_test2, result2)
        print(f"\n[전공 살려서: 컴퓨터공학 - {mode} 상위 10개]")
        for r in scored2[:10]:
            print(f"  {r['cert_name']}: 유사도={r['similarity']:.3f}, 합격률={r.get('pass_rate')}%, 레벨={r.get('ncs_level')}, 최종={r['final_score']:.3f}")

        print(f"\n[정보처리 관련 - {mode}]")
        for r in scored2:
            if '정보처리' in r['cert_name']:
                print(f"  {r['cert_name']}: 유사도={r['similarity']:.3f}, 합격률={r.get('pass_rate')}%, 레벨={r.get('ncs_level')}, 최종={r['final_score']:.3f}")