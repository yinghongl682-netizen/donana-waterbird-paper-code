from pathlib import Path
import json,csv,hashlib,datetime,sys,subprocess,platform,importlib.metadata,os
sys.dont_write_bytecode=True
sys.stdout.reconfigure(encoding='utf-8')
from runtime_config import INPUT,OUTPUT
O=OUTPUT/'temporal';S=O/'support';W=INPUT;PROJECT=INPUT
C=OUTPUT/'aerial'
D=OUTPUT/'bridge'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()
def jout(p,obj):
 p=Path(p);p=p if p.is_absolute() else O/p;p.resolve().relative_to(O.resolve());p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False,default=str)+'\n',encoding='utf-8')
def write(p,text):
 p=Path(p);p=p if p.is_absolute() else O/p;p.resolve().relative_to(O.resolve());p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text.strip()+'\n',encoding='utf-8')
def protect(p,role='read-only actual input'):
 p=Path(p).resolve();assert p.is_file(),p
 if p.is_relative_to(O.resolve()):return p
 q=S/'INPUT_HASHES_BEFORE.json';r=json.loads(q.read_text(encoding='utf-8')) if q.exists() else {}
 h=sha(p)
 if str(p) in r:assert r[str(p)]['sha256']==h,('PROTECTED_INPUT_DRIFT',str(p))
 else:r[str(p)]=dict(sha256=h,bytes=p.stat().st_size,role=role,before_use_utc=now());jout(q,r)
 return p
def readj(p):return json.loads(protect(p).read_text(encoding='utf-8-sig'))
def readc(p):
 with protect(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def csvout(p,rows,fields=None):
 p=Path(p);p=p if p.is_absolute() else O/p;p.resolve().relative_to(O.resolve());p.parent.mkdir(parents=True,exist_ok=True)
 assert rows or fields,'No empty completed diagnostic'
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  cw=csv.DictWriter(f,fieldnames=fields or list(dict.fromkeys(k for r in rows for k in r)));cw.writeheader();cw.writerows(rows)
def verify_inputs():
 r=json.loads((S/'INPUT_HASHES_BEFORE.json').read_text(encoding='utf-8'));bad=[p for p,v in r.items() if not Path(p).is_file() or sha(p)!=v['sha256']];assert not bad,bad;return len(r)
def gate():
 r=json.loads((S/'PROSPECTIVE_SPECIFICATION_SEAL.json').read_text(encoding='utf-8'))
 assert sha(O/'01_DESIGN_AND_SOURCE_SUPPORT/01_ACTUAL_INPUTS_AND_BOUNDED_ANALYSIS_PLAN.md')==r['specification_sha256']
 assert r['sensitivities_executed_before_seal'] is False
def execute(label,args):
 q=S/'executions'/f'{label}.json';assert not q.exists(),'Preserve previous execution and use a forward receipt name'
 r=dict(command=list(map(str,args)),cwd=str(O),start_utc=now(),status='STARTED');jout(q,r)
 env=os.environ.copy();env['PYTHONIOENCODING']='utf-8';env['PYTHONDONTWRITEBYTECODE']='1'
 cp=subprocess.run(list(map(str,args)),cwd=O,capture_output=True,text=True,encoding='utf-8',errors='replace',env=env)
 write(q.with_suffix('.stdout.txt'),cp.stdout or '(no stdout)');write(q.with_suffix('.stderr.txt'),cp.stderr or '(no stderr)')
 r.update(returncode=cp.returncode,end_utc=now(),status='EXECUTED' if cp.returncode==0 else 'FAILED');jout(q,r)
 print(cp.stdout[-12000:]);assert cp.returncode==0,cp.stderr[-5000:]
if __name__=='__main__':execute(sys.argv[1],sys.argv[2:])
