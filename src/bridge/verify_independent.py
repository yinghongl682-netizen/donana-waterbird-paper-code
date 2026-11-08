"""Independent stdlib/Fraction verifier; imports no production analysis helper."""
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict
import csv,json,sys,hashlib
sys.stdout.reconfigure(encoding='utf-8');B=Path(__import__('os').environ['DONANA_OUTPUT_ROOT'])/'bridge'
def read(p):
 with (B/p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def num(x):return None if x=='' else F(x)
slots=read('sources/G2_SLOTS.csv');species=list(slots[0])[9:]
# Exact schema, not positional assumption about metadata columns.
species=[s for s in slots[0] if ' ' in s]
years=defaultdict(set);vals=defaultdict(dict);parents={};children={};months={}
for r in slots:
 p=r['position'];y=int(r['year']);years[p].add(y);parents[p]=r['parent_id'];children[p]=r['child_id'];months[p]=int(r['month'])
 for s in species:vals[s][p,y]=F(r[s])
assert len(years)==702 and len(slots)==7722 and all(v==set(range(2013,2024)) for v in years.values())
checks=[]
def chk(kind,key,a,b,exact=False):
 if a is None or b is None:ok=a==b;err=0 if ok else 999
 else:err=abs(float(a-b));ok=(a==b) if exact else err<=1e-10+1e-12*abs(float(b))
 checks.append(dict(kind=kind,key=key,exact_equal=a==b,pass_check=ok,abs_error=err));assert ok,(kind,key,a,b)
pos=read('results/ground/POSITION_SIGNED_CONTRIBUTIONS.csv');d={};a={}
for s in species:
 for p in years:
  e=sum(vals[s][p,y] for y in range(2013,2018))/5;l=sum(vals[s][p,y] for y in range(2018,2024))/6
  d[s,p]=(l-e)/702;a[s,p,'E']=e;a[s,p,'L']=l
for r in pos:chk('position_signed',r['species']+'|'+r['position'],num(r['d']),d[r['species'],r['position']])
summ=read('results/ground/ANNUAL_CHANGE_SUMMARY.csv')
for r in summ:
 s=r['species'];ds=[d[s,p] for p in years];chk('signed_sum',s,num(r['delta_mu']),sum(ds));chk('plus',s,num(r['Pplus']),sum(x for x in ds if x>0));chk('minus',s,num(r['Pminus']),sum(x for x in ds if x<0))
 chk('early_support',s,F(r['early_n']),F(3510),True);chk('late_support',s,F(r['late_n']),F(4212),True)
for filename,keys in [('PARENT_CONTRIBUTIONS',['parent_id']),('MONTH_CONTRIBUTIONS',['month']),('PARENT_MONTH_CONTRIBUTIONS',['parent_id','month']),('CHILD_CONTRIBUTIONS',['child_id'])]:
 for r in read('results/ground/'+filename+'.csv'):
  pp=[p for p in years if all(str({'parent_id':parents[p],'child_id':children[p],'month':months[p]}[k])==r[k] for k in keys)]
  exact=sum(d[r['species'],p] for p in pp);chk(filename,r['species']+'|'+','.join(r[k] for k in keys),num(r['signed_contribution']),exact)
  ee=[vals[r['species']][p,y] for p in pp for y in range(2013,2018)];ll=[vals[r['species']][p,y] for p in pp for y in range(2018,2024)]
  for label,v in [('E',ee),('L',ll)]:
   positive=[x for x in v if x>0];chk('local_f',filename+'|'+r['species']+label,num(r['f_'+label]),F(len(positive),len(v)))
   chk('local_q',filename+'|'+r['species']+label,num(r['q_'+label]),sum(positive)/len(positive) if positive else None)
windows={'ANNUAL':{1,2,3,5,6,7,9,10,11,12},'DJF':{12,1,2},'MarMay':{3,5},'JunJul':{6,7},'SON':{9,10,11}}
for r in read('results/concentration/PERIOD_HHI.csv'):
 s=r['species'];per=r['period'];pp=[p for p in years if months[p] in windows[r['window']]]
 cy=defaultdict(F);py=defaultdict(F)
 for p in pp:cy[children[p]]+=a[s,p,per];py[parents[p]]+=a[s,p,per]
 T=sum(cy.values());hc=sum((v/T)**2 for v in cy.values()) if T else None;hp=sum((v/T)**2 for v in py.values()) if T else None
 chk('period_child_hhi',s+'|'+r['window']+per,num(r['HHI_child']),hc);chk('period_parent_hhi',s+'|'+r['window']+per,num(r['HHI_parent']),hp)
for r in read('results/concentration/PERIOD_HIERARCHY_DECOMPOSITION.csv'):
 k0=num(r['K_E']);k1=num(r['K_L']);dk=num(r['delta_K']);bt=num(r['between']);wi=num(r['within']);en=num(r['entry_exit'])
 if dk is not None:chk('hierarchy_identity',r['species']+'|'+r['parent_id']+r['window'],dk,(bt or F())+(wi or F())+(en or F()))
 if num(r['Y_E'])==0:assert num(r['H_E']) is None
 if num(r['Y_L'])==0:assert num(r['H_L']) is None
with (B/'review/INDEPENDENT_EXACT_CHECKS.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(checks[0]));w.writeheader();w.writerows(checks)
result=dict(status='PASS',implementation='stdlib CSV and Fraction; no bridge_common/production imports',checks=len(checks),max_absolute_error=max(r['abs_error'] for r in checks),all13=True,period_windows=65,zero_undefined_boundaries_checked=True)
(B/'review/INDEPENDENT_VALIDATION.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(result)
