"""Render the final-submission figure presentation layer from a completed scientific run."""
from pathlib import Path
import argparse,subprocess,os,json,hashlib,datetime,sys
REPO=Path(__file__).resolve().parents[2]
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--input-run',required=True,type=Path)
 p.add_argument('--validate-inputs-only',action='store_true')
 p.add_argument('--fig2-reference-run',type=Path,help='Explicit qualified frozen Fig.2 plot artifact; fresh data/graphics must match')
 p.add_argument('--output',required=True,type=Path)
 p.add_argument('--rscript',required=True,type=Path)
 p.add_argument('--r-library',required=True,type=Path)
 a=p.parse_args();inp=a.input_run.resolve(strict=True);out=a.output.resolve()
 if out.exists():p.error('Output must be new; preserve earlier attempts')
 if out.is_relative_to(inp) or out.is_relative_to(REPO):p.error('Output must be outside input and source')
 if not a.rscript.is_file() or not a.r_library.is_dir():p.error('Supply existing R runtime and isolated library')
 from figure_input_contract import validate_run
 preflight=validate_run(inp)
 if a.fig2_reference_run:
  if out.is_relative_to(a.fig2_reference_run.resolve(strict=True)):p.error('Output must be outside the qualified Fig.2 reference run')
  preflight['fig2_reference']=validate_run(a.fig2_reference_run.resolve(strict=True),figures=('Fig2',))
 if a.validate_inputs_only:
  print(json.dumps(preflight,indent=2));return 0
 out.mkdir(parents=True)
 src=REPO/'scripts/figures/figpolish'
 env=os.environ.copy();env.update(R_LIBS_USER=str(a.r_library.resolve()),R_LIBS_SITE=str(a.r_library.resolve()))
 env.pop('R_PROFILE_USER',None);env.pop('R_ENVIRON_USER',None)
 def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
 def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
 fig2inp=inp;reference_checks=[]
 if a.fig2_reference_run:
  fig2inp=a.fig2_reference_run.resolve(strict=True)
  for rel in ['03_F2/Fig2_FIGV1_SELECTED_SYSTEM_CANDIDATE.svg','formal/03_repaired_figure_sources/F2/FIG2_EXACT_DISPLAY_DATA.csv','formal/03_repaired_figure_sources/F2/FIG2_SOURCE_DEFINED_PEAK_MARKS.csv','formal/03_repaired_figure_sources/F2/F2_DISPLACED_ANNOTATION_SOURCE_LINK.csv']:
   old,new=fig2inp/'f23'/rel,inp/'f23'/rel
   if sha(old)!=sha(new):raise ValueError('Fresh/reference Fig.2 source mismatch: '+rel)
   reference_checks.append(dict(file=rel,sha256=sha(new),byte_identical=True))
 commands=[
 ('Fig2',[str(a.rscript),'--vanilla',str(src/'render_fig2_polish.R'),str(fig2inp/'f23'),str(a.r_library),str(out/'Fig2')]),
 ('Fig3',[str(a.rscript),'--vanilla',str(src/'render_fig3_figpolish.R'),str(inp),str(out/'Fig3'),str(a.r_library)]),
 ('Fig4',[str(a.rscript),'--vanilla',str(src/'render_fig4_figpolish.R'),'--input-run',str(inp),'--output',str(out/'Fig4'),'--r-library',str(a.r_library),'--original-source',str(REPO/'scripts/figures/render_fig4.R')]),
 ('Fig5',[str(a.rscript),'--vanilla',str(src/'render_fig5_figpolish.R'),str(inp/'r2/04_MAIN_FIGURES_AND_TABLES/plot_data'),str(out/'Fig5'),str(a.r_library)])]
 if a.fig2_reference_run:
  commands.insert(0,('Fig2_semantic_bridge',[str(a.rscript),'--vanilla',str(REPO/'tests/reproducibility/compare_fig2_plot_semantics.R'),str(fig2inp/'f23/03_F2/Fig2_FIGV1_SELECTED_SYSTEM_CANDIDATE_PLOT.rds'),str(inp/'f23/03_F2/Fig2_FIGV1_SELECTED_SYSTEM_CANDIDATE_PLOT.rds'),str(a.r_library),str(out/'FIG2_FRESH_VS_FROZEN_PLOT_SEMANTICS.json')]))
 rec=dict(input_validation=preflight,fig2_reference_artifact_used=bool(a.fig2_reference_run),fig2_reference_source_checks=reference_checks,status='RUNNING',started_utc=now(),source_sha256={f.name:sha(f) for f in src.glob('*.R')},steps=[],scope='Presentation replay with native scientific locks; no new scientific estimates')
 def save():(out/'FIGPOLISH_RUN_RECORD.json').write_text(json.dumps(rec,indent=2),'utf-8')
 save()
 for name,cmd in commands:
  with (out/(name+'.stdout.txt')).open('w',encoding='utf-8') as so,(out/(name+'.stderr.txt')).open('w',encoding='utf-8') as se:
   cp=subprocess.run(cmd,cwd=out,env=env,stdout=so,stderr=se)
  rec['steps'].append(dict(figure=name,command=cmd,returncode=cp.returncode));save()
  if cp.returncode:rec.update(status='FAILED',ended_utc=now());save();return cp.returncode
 rec.update(status='RENDERED_WITH_NATIVE_SCIENTIFIC_LOCKS_VISUAL_AND_PIXEL_COMPARISON_REQUIRED',ended_utc=now());save()
 print(rec['status']);return 0
if __name__=='__main__':sys.exit(main())

