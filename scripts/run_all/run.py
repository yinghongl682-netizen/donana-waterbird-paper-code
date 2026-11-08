"""Run recovered modules using explicit inputs and a fresh, external output folder."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,shutil,subprocess,sys
REPO=Path(__file__).resolve().parents[2]
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--input-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--rscript',type=Path);p.add_argument('--r-library',type=Path)
 a=p.parse_args();inp=a.input_root.resolve();out=a.output.resolve()
 if not inp.is_dir():p.error('Input root does not exist')
 if out.exists():p.error('Output must be a new directory; failed attempts must be retained')
 if out.is_relative_to(inp) or out.is_relative_to(REPO):p.error('Use an output directory outside inputs and source repository')
 if bool(a.rscript)!=bool(a.r_library):p.error('Provide both --rscript and --r-library')
 out.mkdir(parents=True);log=out/'execution';log.mkdir()
 env=os.environ.copy();env.update(DONANA_INPUT_ROOT=str(inp),DONANA_OUTPUT_ROOT=str(out),PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
 env.pop('PYTHONPATH',None);env.pop('PYTHONHOME',None)
 for rel in ['bridge/sources','bridge/support','bridge/review','bridge/results/cross_source','bridge/support/cross_source','temporal/support','temporal/02_TEMPORAL_TREND_DIAGNOSTICS','aerial/raw_rebuild']:(out/rel).mkdir(parents=True,exist_ok=True)
 # Original locked specifications and archived baseline gate, never substituted with invented PASS records.
 for sub in ['bridge','temporal']:
  for f in (inp/'protocols'/sub).rglob('*'):
   if f.is_file():
    dest=out/sub/f.relative_to(inp/'protocols'/sub);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest)
 inputs=[{'relative_path':f.relative_to(inp).as_posix(),'bytes':f.stat().st_size,'sha256':sha(f)} for f in inp.rglob('*') if f.is_file()]
 code=[{'relative_path':f.relative_to(REPO).as_posix(),'sha256':sha(f)} for f in REPO.rglob('*') if f.is_file() and '.git' not in f.parts]
 state=dict(start_utc=now(),python=sys.version,executable=sys.executable,code=code,inputs=inputs,steps=[],status='RUNNING',environment_scope='Caller supplies isolated runtime; inspect environment receipt before making a clean-environment claim')
 def seal():(log/'RUN_RECORD.json').write_text(json.dumps(state,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 seal()
 paths=[str(REPO/'src'),str(REPO/'src/bridge'),str(REPO/'src/temporal'),str(REPO/'src/aerial')]
 bootstrap='import sys,runpy;sys.path[:0]='+repr(paths)+';runpy.run_path(sys.argv[1],run_name="__main__")'
 steps=[('01_aerial','src/aerial/run_aerial.py',[]),('02_ground_raw','src/bridge/recover_native.py',[]),('03_ground_baseline','src/bridge/reproduce_baseline.py',[]),('04_ground_contributions','src/bridge/analyze_ground.py',[]),('05_ground_summary','src/bridge/summarize_results.py',[]),('06_environment','src/bridge/environment/environment_analysis.py',['--estimate']),('07_environment_independent','src/bridge/environment/environment_verify.py',[]),('08_cross_source','src/bridge/cross_source/run_cross_source.py',[]),('09_date_boundary','src/bridge/cross_source/date_boundary_sensitivity.py',[]),('10_exact_verifier','src/bridge/verify_independent.py',[]),('11_temporal','src/temporal/temporal_diagnostics.py',[]),('12_tables','scripts/tables/export_tables.py',[]),('13_existing_exports','src/bridge/complete_outputs.py',[])]
 for label,rel,extra in steps:
  cmd=[sys.executable,'-I','-B','-X','utf8','-c',bootstrap,str(REPO/rel),*extra]
  rec=dict(label=label,start_utc=now(),command=cmd);state['steps'].append(rec);seal()
  with (log/(label+'.stdout.txt')).open('w',encoding='utf-8') as so,(log/(label+'.stderr.txt')).open('w',encoding='utf-8') as se:
   cp=subprocess.run(cmd,cwd=out,env=env,stdout=so,stderr=se)
  rec.update(end_utc=now(),returncode=cp.returncode);seal();print(label,cp.returncode,flush=True)
  if cp.returncode:state.update(status='FAILED',end_utc=now());seal();return cp.returncode
 if a.rscript:
  env.update(DONANA_REPLAY_RLIB=str(a.r_library.resolve()),R_LIBS_USER=str(a.r_library.resolve()),R_LIBS_SITE=str(a.r_library.resolve()))
  rec=dict(label='14_R_figures',start_utc=now());state['steps'].append(rec);seal()
  with (log/'14_R_figures.stdout.txt').open('w',encoding='utf-8') as so,(log/'14_R_figures.stderr.txt').open('w',encoding='utf-8') as se:
   cp=subprocess.run([str(a.rscript),'--vanilla',str(REPO/'scripts/figures/render_all.R')],cwd=out,env=env,stdout=so,stderr=se)
  rec.update(end_utc=now(),returncode=cp.returncode);seal();print('14_R_figures',cp.returncode,flush=True)
  if cp.returncode:state.update(status='FAILED',end_utc=now());seal();return cp.returncode
 state.update(status='EXECUTED_OUTPUT_COMPARISON_REQUIRED',end_utc=now(),graphics_executed=bool(a.rscript),inputs_unchanged=all(sha(inp/r['relative_path'])==r['sha256'] for r in inputs));seal()
 return 0
if __name__=='__main__':sys.exit(main())
