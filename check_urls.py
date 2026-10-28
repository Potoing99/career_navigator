import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

opts = Options()
opts.add_argument('--window-size=1200,800')
opts.add_experimental_option('excludeSwitches', ['enable-logging'])

driver = webdriver.Chrome(options=opts)
driver.get('http://localhost:8501')
time.sleep(4)

print('Current URL:', driver.current_url)

# 모든 a[href] 링크
links = driver.find_elements(By.CSS_SELECTOR, 'a[href]')
print(f'\na[href] 링크 {len(links)}개:')
for lnk in links:
    href = lnk.get_attribute('href') or ''
    text = lnk.text.strip()
    if 'localhost' in href:
        print(f'  "{text}" -> {href}')

# PARTIAL_LINK_TEXT로 각 페이지 찾기
names = ['로그인', '프로필', '자격증 추천', '시험 일정', '커리어 로드맵', '즐겨찾기']
print('\nPARTIAL_LINK_TEXT 검색:')
for name in names:
    try:
        el = driver.find_element(By.PARTIAL_LINK_TEXT, name)
        print(f'  "{name}": href={el.get_attribute("href")}')
    except Exception:
        print(f'  "{name}": 못 찾음')

driver.quit()
