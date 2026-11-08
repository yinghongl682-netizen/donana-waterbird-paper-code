"""Compare keyed numeric cells against an explicitly supplied authorized frozen oracle."""
from pathlib import Path
import argparse,csv,hashlib,json,math,sys
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--output-root',type=Path,required=True);p.add_argument('--expectations',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
a=p.parse_args()
if a.report.exists():p.error('Report exists; retain prior attempts')
oracle=list(csv.DictReader(a.expectations.open(encoding='utf-8-sig',newline='')))
if not oracle:p.error('Empty oracle is not a passing test')
cache={};checks=[]
for e in oracle:
 rel=e['output_relative_path'];target=(a.output_root/rel).resolve()
 target.relative_to(a.output_root.resolve())
 rec={k:e[k] for k in ['output_relative_path','row_key','field','expected_value','applied_tolerance','source_sha256']}
 try:
  if rel not in cache:cache[rel]=list(csv.DictReader(target.open(encoding='utf-8-sig',newline='')))
  keys=dict(x.split('=',1) for x in e['row_key'].split(';'))
  selected=[r for r in cache[rel] if all(r.get(k)==v for k,v in keys.items())]
  if len(selected)!=1:raise ValueError('Key matches '+str(len(selected))+' rows')
  if e['applied_tolerance']=='EXACT_SERIALIZED_IDENTITY':
   actual=selected[0][e['field']]
   rec.update(actual_value=actual,status='PASS' if actual==e['expected_value'] else 'FAIL',comparison='EXACT_SERIALIZED_IDENTITY')
   checks.append(rec)
   continue
  expected=float(e['expected_value']);actual=float(selected[0][e['field']]);tol=float(e['applied_tolerance'])
  if not math.isfinite(tol) or tol<0:raise ValueError('Tolerance must be finite and non-negative')
  if not math.isfinite(expected) or not math.isfinite(actual):raise ValueError('Expected and actual numeric values must be finite')
  diff=abs(actual-expected)
  if not math.isfinite(diff):raise ValueError('Numeric difference is not finite')
  passed=diff<=tol
  rec.update(actual_value=actual,absolute_error=diff,status='PASS' if passed else 'FAIL')
 except Exception as exc:rec.update(status='FAIL',reason=type(exc).__name__+': '+str(exc))
 checks.append(rec)
failed=sum(c['status']!='PASS' for c in checks)
report={'status':'FAIL' if failed else 'PASS_BOUNDED_NUMERIC_REGRESSION','checks':len(checks),'passed':len(checks)-failed,'failed':failed,'oracle_sha256':hashlib.sha256(a.expectations.read_bytes()).hexdigest(),'maximum_absolute_error':max((c.get('absolute_error',0) for c in checks),default=0),'scope':'Frozen result consistency; not independent estimation or whole-paper Level 3','results':checks}
a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='results'}));sys.exit(bool(failed))
