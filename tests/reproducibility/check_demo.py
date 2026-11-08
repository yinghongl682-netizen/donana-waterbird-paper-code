"""Independent exact checks of the invented demo, without production helper imports."""
from pathlib import Path
from fractions import Fraction as F
import argparse,csv,json
p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args()
R=Path(__file__).resolve().parents[2]
with (R/'data/synthetic_examples/normalized_ground_slots.csv').open(encoding='utf-8-sig',newline='') as f:raw=list(csv.DictReader(f))
with (a.output/'synthetic_components.csv').open(encoding='utf-8-sig',newline='') as f:result=list(csv.DictReader(f))
checks=0
for r in result:
 s=r['species'];st=[]
 for period in ['early','late']:
  vals=[F(x[s]) for x in raw if (int(x['year'])<=2017)==(period=='early')];positive=[v for v in vals if v>0]
  n=len(vals);f=F(len(positive),n);mu=sum(vals,F())/n;q=sum(positive,F())/len(positive) if positive else None
  for field,value in [('n',F(n)),('f',f),('mu',mu),('q',q)]:
   got=r[period+'_'+field];assert got=='' if value is None else abs(float(got)-float(value))<1e-12,(s,period,field);checks+=1
  st.append((f,mu,q))
 e,l=st
 if e[2] is not None and l[2] is not None:
  cf=(l[0]-e[0])*(e[2]+l[2])/2;cq=(l[2]-e[2])*(e[0]+l[0])/2
  assert cf+cq==l[1]-e[1];assert abs(float(r['Cf'])-float(cf))<1e-12 and abs(float(r['Cq'])-float(cq))<1e-12;checks+=3
 else:assert r['Cf']==r['Cq']=='';checks+=1
with (a.output/'synthetic_concentration.csv').open(newline='') as f:indices=list(csv.DictReader(f))
for row in indices:
 vals={}
 for x in raw:
  if (int(x['year'])<=2017)==(row['period']=='E'):
   vals.setdefault((x['parent_id'],x['child_id']),[]).append(F(x[row['species']]))
 child={k:sum(v,F())/len(v) for k,v in vals.items()};total=sum(child.values(),F())
 if not total:assert row['HHI_child']==row['HHI_parent']=='';checks+=2;continue
 parents={}
 for (pa,ch),v in child.items():parents[pa]=parents.get(pa,F())+v
 for k,v in [('HHI_child',sum((v/total)**2 for v in child.values())),('HHI_parent',sum((v/total)**2 for v in parents.values()))]:assert abs(float(row[k])-float(v))<1e-12;checks+=1
print(json.dumps(dict(status='PASS',exact_demo_checks=checks,scientific_reproduction=False)))
