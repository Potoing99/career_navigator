import sys, io, time, os, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pymysql
from dotenv import load_dotenv
load_dotenv()
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

OUT  = r'C:\Users\DK\Downloads\screenshots'
BASE = 'http://localhost:8504'
os.makedirs(OUT, exist_ok=True)

DEMO_EMAIL = 'demo@career.nav'
DEMO_PW    = 'demo1234'
DEMO_NAME  = '발표데모'

# ── 데모 계정 DB 준비 ───────────────────────────────────────────────────────
def ensure_demo_account():
    pw_hash = hashlib.sha256(DEMO_PW.encode()).hexdigest()
    try:
        conn = pymysql.connect(host='localhost', user='root', password=os.getenv('DB_PASSWORD', ''),
                               database='career_nav', charset='utf8mb4')
        cur  = conn.cursor()
        cur.execute("SELECT user_id FROM users WHERE email=%s", (DEMO_EMAIL,))
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO users (email, password, name, major, education) "
                "VALUES (%s,%s,%s,%s,%s)",
                (DEMO_EMAIL, pw_hash, DEMO_NAME, '컴퓨터시스템공학', '3년제전문대졸')
            )
            conn.commit()
            print(f'  [DB] 데모 계정 생성: {DEMO_EMAIL}')
        else:
            print(f'  [DB] 데모 계정 확인: {DEMO_EMAIL}')
        conn.close()
    except Exception as e:
        print(f'  [DB] 오류 (스킵): {e}')

ensure_demo_account()

# ── ChromeDriver ────────────────────────────────────────────────────────────
opts = Options()
opts.add_argument('--window-size=1350,860')
opts.add_argument('--force-device-scale-factor=1')
opts.add_experimental_option('excludeSwitches', ['enable-logging'])

driver = webdriver.Chrome(options=opts)


def sleep(n=2):
    time.sleep(n)


def ss(name):
    path = os.path.join(OUT, f'{name}.png')
    driver.save_screenshot(path)
    print(f'  [저장] {name}.png')


def wait_loaded(sec=2.5):
    sleep(sec)
    for _ in range(20):
        try:
            driver.find_element(By.CSS_SELECTOR, '[data-testid="stStatusWidget"]')
            sleep(0.5)
        except NoSuchElementException:
            break
    sleep(0.8)


def nav(url, wait=3):
    driver.get(url)
    wait_loaded(wait)


def get_sidebar_urls():
    """사이드바 링크에서 실제 URL 수집"""
    urls = {}
    links = driver.find_elements(By.CSS_SELECTOR, '[data-testid="stSidebarNavLink"]')
    for link in links:
        href = link.get_attribute('href') or ''
        full_text = link.text.strip()
        # Streamlit 1.5x: 아이콘명\n페이지명 형식 → 페이지명만 추출
        text = full_text.split('\n')[-1].strip() if '\n' in full_text else full_text
        if href and text:
            urls[text] = href
            print(f'    [{text}] -> {href}')
    if not urls:
        # 대안: PARTIAL_LINK_TEXT로 직접 찾기
        for name in ['로그인', '프로필', '자격증 추천', '시험 일정', '커리어 로드맵', '즐겨찾기']:
            try:
                el = driver.find_element(By.PARTIAL_LINK_TEXT, name)
                href = el.get_attribute('href') or ''
                if href:
                    urls[name] = href
                    print(f'    [{name}] -> {href}')
            except Exception:
                pass
    return urls


def do_login():
    """로그인 탭(기본)에서 이메일+비밀번호 입력 후 제출"""
    try:
        # 이메일 입력 (로그인 탭의 첫 번째 텍스트 input)
        all_text = driver.find_elements(
            By.CSS_SELECTOR, '[data-testid="stTextInput"] input[type="text"]')
        if not all_text:
            all_text = driver.find_elements(By.CSS_SELECTOR, 'input[type="text"]')

        # 비밀번호 input
        pw_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="password"]')

        if all_text:
            all_text[0].clear()
            all_text[0].send_keys(DEMO_EMAIL)
        if pw_inputs:
            pw_inputs[0].clear()
            pw_inputs[0].send_keys(DEMO_PW)

        sleep(0.5)

        # "로그인" 버튼 클릭 (tabs의 "로그인" 탭이 아닌 form submit 버튼)
        # Streamlit form submit은 button[kind="primaryFormSubmit"] 또는 첫번째 type="submit"
        btn_clicked = False
        for xpath in [
            '//button[@data-testid="baseButton-primaryFormSubmit"]',
            '//button[@kind="primaryFormSubmit"]',
            '//form[@data-testid="stForm"]//button',
            '//button[normalize-space(.)="로그인" and not(@role="tab")]',
        ]:
            try:
                btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                # 탭 버튼이 아닌지 확인
                role = btn.get_attribute('role') or ''
                if role == 'tab':
                    continue
                driver.execute_script('arguments[0].scrollIntoView({block:"center"});', btn)
                sleep(0.2)
                btn.click()
                btn_clicked = True
                break
            except Exception:
                pass

        if not btn_clicked:
            print('  → 로그인 버튼 못 찾음, Enter 시도')
            if pw_inputs:
                from selenium.webdriver.common.keys import Keys
                pw_inputs[0].send_keys(Keys.RETURN)

        sleep(4)
        if 'user' in driver.page_source or DEMO_NAME in driver.page_source:
            print('  → 로그인 성공')
            return True
        else:
            print('  → 로그인 상태 불확실')
            return False
    except Exception as e:
        print(f'  → 로그인 실패: {e}')
        return False


def click_radio(text):
    try:
        el = driver.find_element(By.XPATH, f'//label[contains(., "{text}")]')
        el.click()
        sleep(0.5)
        return True
    except Exception:
        return False


# ════════════════════════════════════════════════════════════════════════════
print('\nStreamlit 접속...')
driver.get(BASE)
sleep(6)

# 사이드바 URL 수집
page_urls = get_sidebar_urls()
print(f'  발견된 페이지: {list(page_urls.keys())}')

# URL 매핑 (사이드바에서 못 찾으면 Streamlit 1.x st.navigation 기본 경로 사용)
def _url(korean_key, fallback_path):
    if korean_key in page_urls:
        return page_urls[korean_key]
    # URL-인코딩 없이 시도 (Streamlit이 그대로 서빙)
    return f'{BASE}/{fallback_path}'

login_url    = _url('로그인',       '1_%F0%9F%91%A4_%EB%A1%9C%EA%B7%B8%EC%9D%B8')
profile_url  = _url('프로필',        '2_%F0%9F%93%9D_%ED%94%84%EB%A1%9C%ED%95%84')
rec_url      = _url('자격증 추천',   '3_%F0%9F%94%8D_%EC%9E%90%EA%B2%A9%EC%A6%9D%EC%B6%94%EC%B2%9C')
sched_url    = _url('시험 일정',     '4_%F0%9F%93%85_%EC%8B%9C%ED%97%98%EC%9D%BC%EC%A0%95')
roadmap_url  = _url('커리어 로드맵', '5_%F0%9F%97%BA%EF%B8%8F_%EC%BB%A4%EB%A6%AC%EC%96%B4%EB%A1%9C%EB%93%9C%EB%A7%B5')
bookmark_url = _url('즐겨찾기',      '6_%E2%AD%90_%EC%A6%90%EA%B2%A8%EC%B0%BE%EA%B8%B0')

print(f'  로그인 URL: {login_url}')
print(f'  프로필 URL: {profile_url}')

# ── [1] 홈 ──────────────────────────────────────────────────────────────────
print('\n[1] 홈')
ss('01_home')

# ── [2] 로그인 페이지 (로그인 전 상태) ──────────────────────────────────────
print('\n[2] 로그인 페이지')
nav(login_url, wait=3)
ss('02_login')

# ── 로그인 실행 ──────────────────────────────────────────────────────────────
print('\n[로그인]')
do_login()
sleep(1)

# ── [3] 프로필 ───────────────────────────────────────────────────────────────
print('\n[3] 프로필')
nav(profile_url, wait=3)
sleep(1)

# 전공 입력란 채우기
try:
    text_inputs = driver.find_elements(By.CSS_SELECTOR, '[data-testid="stTextInput"] input')
    for inp in text_inputs:
        ph = inp.get_attribute('placeholder') or ''
        val = inp.get_attribute('value') or ''
        if not val and ('전공' in ph or '학과' in ph or '공학' in ph):
            inp.clear()
            inp.send_keys('컴퓨터시스템공학')
            sleep(0.3)
            break
except Exception:
    pass

sleep(1)
ss('03_profile')

# ── [4] 자격증 추천 — 입력 ───────────────────────────────────────────────────
print('\n[4] 자격증 추천 입력')
nav(rec_url, wait=3)
sleep(1)
ss('04_recommend_input')

# ── [5] 자격증 추천 — 결과 ───────────────────────────────────────────────────
print('\n[5] 자격증 추천 결과 (최대 90초 대기)')
try:
    click_radio('전공 살려서')
    sleep(0.5)

    text_inputs = driver.find_elements(By.CSS_SELECTOR, '[data-testid="stTextInput"] input')
    for inp in text_inputs:
        ph = inp.get_attribute('placeholder') or ''
        if any(k in ph for k in ['전공', '학과', '공학', '컴퓨터']):
            inp.clear()
            inp.send_keys('컴퓨터시스템공학')
            sleep(0.3)
            break
    else:
        if text_inputs:
            text_inputs[0].clear()
            text_inputs[0].send_keys('컴퓨터시스템공학')

    sleep(1)  # 텍스트 입력 후 Streamlit 안정화 대기

    # 추천 버튼 클릭 (JavaScript로 직접 클릭 — 스크롤 위치 무관)
    clicked = driver.execute_script("""
        var btns = Array.from(document.querySelectorAll('button'));
        var btn = btns.find(b => b.textContent.includes('추천 받기'));
        if (btn) {
            btn.scrollIntoView({block:'center'});
            btn.click();
            return true;
        }
        return false;
    """)
    if clicked:
        print('  → 추천 버튼 클릭 성공')
    else:
        print('  → 추천 버튼 못 찾음 — 텍스트로 재시도')
        try:
            btn = driver.find_element(By.XPATH, '//button[contains(., "추천")]')
            driver.execute_script('arguments[0].click()', btn)
            print('  → XPath 재시도 성공')
        except Exception as e:
            print(f'  → 재시도 실패: {e}')

    print('  → SBERT 추론 대기...')
    for _ in range(90):
        try:
            driver.find_element(By.CSS_SELECTOR, '[data-testid="stStatusWidget"]')
            sleep(1)
        except NoSuchElementException:
            break
    sleep(3)
    driver.execute_script('window.scrollTo(0, 400)')
    sleep(0.5)
    ss('05_recommend_result')
    print('  → 완료')
except Exception as e:
    print(f'  → 실패: {e}')
    ss('05_recommend_result_fail')

# ── [6] 시험 일정 ─────────────────────────────────────────────────────────────
print('\n[6] 시험 일정')
nav(sched_url, wait=3)
ss('06_schedule')

try:
    radio_labels = driver.find_elements(By.CSS_SELECTOR, '[data-testid="stRadio"] label')
    print(f'  라디오 라벨 {len(radio_labels)}개: {[l.text for l in radio_labels]}')
    found = False
    for lbl in radio_labels:
        if '달력' in lbl.text:
            lbl.click()
            sleep(2.5)
            ss('06_schedule_calendar')
            found = True
            break
    if not found:
        # Streamlit 1.5x 대체 selector
        all_btns = driver.find_elements(By.XPATH, '//*[contains(text(), "달력")]')
        print(f'  달력 텍스트 요소: {[b.tag_name for b in all_btns]}')
        for btn in all_btns:
            if btn.is_displayed():
                btn.click()
                sleep(2.5)
                ss('06_schedule_calendar')
                break
except Exception as e:
    print(f'  달력 뷰 오류: {e}')

# ── [7] 커리어 로드맵 ─────────────────────────────────────────────────────────
print('\n[7] 커리어 로드맵')
nav(roadmap_url, wait=3)
sleep(1)
try:
    inputs = driver.find_elements(By.CSS_SELECTOR, '[data-testid="stTextInput"] input')
    if inputs:
        inputs[0].clear()
        inputs[0].send_keys('전기')
        sleep(4)
        driver.execute_script('window.scrollTo(0, 300)')
        sleep(0.5)
except Exception as e:
    print(f'  → 입력 실패: {e}')
ss('07_roadmap')

# ── [8] 즐겨찾기 ─────────────────────────────────────────────────────────────
print('\n[8] 즐겨찾기')
nav(bookmark_url, wait=3)
ss('08_bookmark')

# ════════════════════════════════════════════════════════════════════════════
print(f'\n완료! 저장 위치: {OUT}')
saved = [f for f in os.listdir(OUT) if f.endswith('.png')]
print(f'저장된 파일 {len(saved)}개: {sorted(saved)}')
driver.quit()
