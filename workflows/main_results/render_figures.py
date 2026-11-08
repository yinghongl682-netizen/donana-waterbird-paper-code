"""Invoke the retained R figure chain using explicit external roots."""
import argparse,json,os,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
for key in ['input-root','output-root','rscript','r-library']:p.add_argument('--'+key,type=Path,required=True)
a=p.parse_args();r=Path(__file__).resolve().parents[2]
if not a.input_root.is_dir() or not a.r_library.is_dir() or not a.rscript.is_file():p.error('Input root, R library and Rscript must exist')
if not (a.output_root/'bridge/results').is_dir() or not (a.output_root/'aerial/m9/native_data').is_dir():p.error('Completed numerical output is required')
if a.output_root.resolve().is_relative_to(a.input_root.resolve()) or a.output_root.resolve().is_relative_to(r):p.error('Output must be outside input and repository roots')
if any((a.output_root/name).exists() for name in ['r2','fig4','fig5','f23']):p.error('Graphic outputs already exist; preserve the prior run')
receipt=a.output_root/'execution/P1_FIGURE_ENTRY.json'
if receipt.exists():p.error('This figure entry already ran; retain prior receipt')
env=os.environ.copy();env.update(DONANA_INPUT_ROOT=str(a.input_root.resolve()),DONANA_OUTPUT_ROOT=str(a.output_root.resolve()),DONANA_REPLAY_RLIB=str(a.r_library.resolve()),R_LIBS_USER=str(a.r_library.resolve()),R_LIBS_SITE=str(a.r_library.resolve()))
cmd=[str(a.rscript),'--vanilla',str(r/'scripts/figures/render_all.R')]
cp=subprocess.run(cmd,cwd=a.output_root,env=env)
receipt.parent.mkdir(parents=True,exist_ok=True);receipt.write_text(json.dumps({'command':cmd,'returncode':cp.returncode,'scope':'R figure chain only; separate numerical and artifact comparison required'},indent=2)+'\n',encoding='utf-8');sys.exit(cp.returncode)
