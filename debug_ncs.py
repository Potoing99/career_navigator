import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from utils.db_helper import execute_query
from models.ontology import CERT_ONTOLOGY

# ncs_categories의 모든 dclas_nm
db_dclas = set(r['dclas_nm'] for r in execute_query("SELECT DISTINCT dclas_nm FROM ncs_categories"))

# 온톨로지의 모든 dclas 수집
onto_dclas = set()
for cert_name, data in CERT_ONTOLOGY.items():
    for d in data.get('ncs_dclas', []):
        onto_dclas.add(d)

matched   = onto_dclas & db_dclas
unmatched = onto_dclas - db_dclas

print(f"온톨로지 dclas 종류: {len(onto_dclas)}개")
print(f"DB dclas 종류: {len(db_dclas)}개")
print(f"일치: {len(matched)}개")
print(f"불일치 (온톨로지에만 있음): {len(unmatched)}개")

if unmatched:
    print("\n불일치 목록 (샘플 20개):")
    for d in sorted(unmatched)[:20]:
        print(f"  '{d}'")
