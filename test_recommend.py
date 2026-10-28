import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from models.recommender import recommend

user_input = {
    'education': '4년제대졸이상',
    'career_years': 0,
    'owned_certs': [],
    'use_major': True,
    'major': '컴퓨터공학',
    'ncs_dclas': '',
    'extra_qualifications': [],
    'language_test': None,
    'weight_mode': 'career'
}

result = recommend(user_input)

labels = {
    'level8': '기술사급',
    'level7': '기능장급',
    'level6': '기사급',
    'level5': '산업기사급',
    'level3': '기능사급',
    'prof':   '국가전문자격',
}

for key, label in labels.items():
    group = result[key]
    if not group:
        continue
    print(f'\n=== {label} ===')
    for r in group:
        print(f"  {r['cert_name']} | {r['reason']}")
