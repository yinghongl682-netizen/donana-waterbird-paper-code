"""Render the authorized Fig. 3–4 presentation addendum from a completed original run."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,subprocess,sys
REPO=Path(__file__).resolve().parents[2]
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--input-run',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True)
 p.add_argument('--rscript',type=Path,required=True)
 p.add_argument('--r-library',type=Path,required=True)
 a=p.parse_args();inp=a.input_run.resolve();out=a.output.resolve()
 if not inp.is_dir():p.error('Completed input run does not exist')
 if not a.rscript.is_file() or not a.r_library.is_dir():p.error('Rscript and isolated R library must exist')
 if out.exists():p.error('Output must be new; preserve prior attempts')
 if out.is_relative_to(inp) or out.is_relative_to(REPO):p.error('Output must be outside input and repository')
 required=['f23/06_FIGURE_3/Fig3_CURRENT_SOURCE_REPLAY_PLOT.rds','f23/formal/03_repaired_figure_sources/F2/FIG3_EXACT_DISPLAY_DATA.csv','fig4/figures/FIG4_L1_DIAMOND_LEGEND.svg']
 if any(not (inp/x).is_file() for x in required):p.error('Run the original numerical and R figure entry first')
 out.mkdir(parents=True)
 scripts=REPO/'scripts/figures'
 env=os.environ.copy();env.update(R_LIBS_USER=str(a.r_library.resolve()),R_LIBS_SITE=str(a.r_library.resolve()))
 def sha(x):return hashlib.sha256(x.read_bytes()).hexdigest()
 code={n:sha(scripts/n) for n in ['render_fig3_legibility.R','render_fig4_legibility.R','render_fig4.R']}
 rec={'scope':'Presentation-only Fig.3–4 addendum; original scientific calculations unchanged','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':code,'steps':[],'status':'RUNNING'}
 def save():(out/'LEGIBILITY_RUN_RECORD.json').write_text(json.dumps(rec,indent=2)+'\n',encoding='utf-8')
 commands=[
 ('Fig3',[str(a.rscript),'--vanilla',str(scripts/'render_fig3_legibility.R'),str(inp),str(out/'Fig3'),str(a.r_library.resolve())]),
 ('Fig4',[str(a.rscript),'--vanilla',str(scripts/'render_fig4_legibility.R'),'--input-run',str(inp),'--output',str(out/'Fig4'),'--r-library',str(a.r_library.resolve()),'--original-source',str(scripts/'render_fig4.R')])]
 save()
 for label,cmd in commands:
  with (out/(label+'.stdout.txt')).open('w',encoding='utf-8') as so,(out/(label+'.stderr.txt')).open('w',encoding='utf-8') as se:
   cp=subprocess.run(cmd,cwd=out,env=env,stdout=so,stderr=se)
  rec['steps'].append({'figure':label,'command':cmd,'returncode':cp.returncode});save()
  if cp.returncode:rec['status']='FAILED';save();return cp.returncode
 rec['status']='RENDERED_SCIENTIFIC_LOCK_CHECKS_PASSED_VISUAL_REVIEW_SEPARATE'
 rec['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
 print(rec['status']);return 0
if __name__=='__main__':sys.exit(main())
