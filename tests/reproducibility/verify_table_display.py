"""Verify all ordered cells and displayed signs of supplied manuscript tables."""
from pathlib import Path
import argparse,re,json,hashlib
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--reference-md',required=True,type=Path)
p.add_argument('--candidate-md',required=True,type=Path)
p.add_argument('--report',required=True,type=Path)
a=p.parse_args()
def tables(path):
 s=path.read_text('utf-8-sig')
 blocks=re.findall(r'(?m)(?:^\|[^\n]*\n)+',s)
 return [[ [x.strip() for x in line.strip().strip('|').split('|')] for line in block.splitlines()
  if not re.fullmatch(r'[| :\-]+',line)] for block in blocks]
ref=tables(a.reference_md);current=tables(a.candidate_md)
assert len(ref)==len(current)==3,'Expected Table 1, Table 2a, Table 2b'
assert ref==current,'A table cell or its display changed'
cells=sum(len(row) for block in current for row in block)
assert cells==175,('Unexpected ordered-cell universe',cells)
minus=sum(cell.count('\u2212') for block in current for row in block for cell in row)
assert minus==30,('Unexpected mathematical minus count',minus)
bad=[cell for row in current[2] for cell in row if re.search(r'(^|[ (])-\d',cell)]
assert not bad,('ASCII negative sign in Table 2b',bad)
result=dict(status='TABLE_1_2_ORDERED_CELLS_AND_SIGNS_PASS',table_blocks=3,ordered_cells=cells,
 mathematical_minus_characters=minus,all_cells_exact=True,
 reference_sha256=hashlib.sha256(a.reference_md.read_bytes()).hexdigest(),
 candidate_sha256=hashlib.sha256(a.candidate_md.read_bytes()).hexdigest(),
 scope='Markdown table display identity, not native Word/LaTeX layout or independent result estimation')
if a.report.exists():raise ValueError('Retain earlier report; choose a fresh report path')
a.report.parent.mkdir(parents=True,exist_ok=True)
a.report.write_text(json.dumps(result,indent=2),'utf-8')
print(json.dumps(result))
