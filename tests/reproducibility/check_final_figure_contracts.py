"""Exercise final interface guards against externally authorized real inputs.

All deliberate mutations affect a new external test directory only.
"""
from pathlib import Path
import argparse,json,sys,shutil,subprocess,hashlib
REPO=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(REPO/'scripts/figures/fig1'),str(REPO/'workflows/main_results')]
from fig1_input_contract import validate_inputs
from figure_input_contract import validate_run
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('fig1-input-root','union','fresh-sentinel-root','completed-run','reference-run','work-dir','rscript','r-library'):
  p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();work=a.work_dir.resolve()
 if work.exists() or work.is_relative_to(REPO):p.error('Use a new external test directory')
 for root in (a.fig1_input_root,a.fresh_sentinel_root,a.completed_run,a.reference_run):
  if work.is_relative_to(root.resolve()):p.error('Tests must be outside inputs')
 work.mkdir(parents=True);checks=[]
 def check(name,condition):
  checks.append(dict(check=name,passed=bool(condition)))
  if not condition:raise AssertionError(name)
 def rejects(name,fn):
  try:fn()
  except (ValueError,FileNotFoundError):check(name,True)
  else:check(name,False)
 check('qualified_map_inputs',validate_inputs(a.fig1_input_root,a.union)['calendar_states']==396)
 stage=work/'regenerated_map_inputs';shutil.copytree(a.fig1_input_root,stage)
 for name in ('SENTINEL2_20220720.png','SENTINEL2_20220720_QA.json'):shutil.copyfile(a.fresh_sentinel_root/name,stage/name)
 check('fresh_RGB_and_QA_semantically_accepted',validate_inputs(stage,a.union)['sentinel_qa_semantics_equal'])
 check('no_legacy_union_or_PNOA_required',not (stage/'OFFICIAL_SINCE2013_LOC4_PARENT_UNIONS.geojson').exists() and not (stage/'F1/support/sources/PNOA_2022_ORIGINAL.png').exists())
 qa=stage/'SENTINEL2_20220720_QA.json';original=qa.read_bytes();obj=json.loads(original);obj['bounds'][0]+=1;qa.write_text(json.dumps(obj),'utf-8')
 rejects('changed_image_extent_rejected',lambda:validate_inputs(stage,a.union));qa.write_bytes(original)
 mp=stage/'F1/support/plot_data/MAP_LAYERS_FINAL.json';original=mp.read_bytes();obj=json.loads(original);obj['F1_DATED_CHILD_LOCATORS']={'features':[]};mp.write_text(json.dumps(obj),'utf-8')
 rejects('extra_event_layer_rejected',lambda:validate_inputs(stage,a.union));mp.write_bytes(original)
 cp=stage/'F1/support/plot_data/CALENDAR_396_LOCKED_STATES.csv';original=cp.read_bytes();cp.write_bytes(original+b'\n')
 rejects('calendar_identity_change_rejected',lambda:validate_inputs(stage,a.union));cp.write_bytes(original)
 wrong=work/'wrong_union.geojson';wrong.write_text('{}','utf-8')
 rejects('wrong_union_rejected',lambda:validate_inputs(stage,wrong))
 render=[sys.executable,'-B',str(REPO/'scripts/figures/fig1/render_fig1_final.py'),'--input-root',str(stage),'--reference-union',str(a.union)]
 def command(name,cmd,expected):
  result=subprocess.run(cmd,capture_output=True,text=True)
  (work/(name+'.stdout.txt')).write_text(result.stdout,'utf-8');(work/(name+'.stderr.txt')).write_text(result.stderr,'utf-8')
  check(name,result.returncode==0 if expected else result.returncode!=0)
 command('validate_only',render+['--output-root',str(work/'not_created'),'--validate-inputs-only'],True)
 check('validate_only_no_write',not (work/'not_created').exists())
 command('existing_output_rejected',render+['--output-root',str(stage)],False)
 check('all_16_figure_interfaces',len(validate_run(a.completed_run)['files'])==16)
 broken=work/'broken_run';contract=json.loads((REPO/'data/schema/figures_2_5_contract.json').read_text('utf-8'))
 for item in contract['figures']['Fig5']:
  target=broken/item['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a.completed_run/item['path'],target)
 (broken/contract['figures']['Fig5'][0]['path']).write_text('wrong_column\n1\n','utf-8')
 rejects('wrong_Fig5_schema_rejected',lambda:validate_run(broken,figures=('Fig5',)))
 nested=a.reference_run/'SHOULD_NOT_BE_CREATED_BY_CONTRACT_TEST'
 if nested.exists():raise ValueError('Refuse ambiguous existing negative-test target')
 command('output_inside_Fig2_reference_rejected',[sys.executable,'-B',str(REPO/'workflows/main_results/render_submission_figures.py'),'--input-run',str(a.completed_run),'--fig2-reference-run',str(a.reference_run),'--output',str(nested),'--rscript',str(a.rscript),'--r-library',str(a.r_library),'--validate-inputs-only'],False)
 check('frozen_reference_not_written',not nested.exists())
 report=dict(status='PASS',checks=checks,total=len(checks),scope='Interface acceptance/rejection, not scientific estimation',regenerated_map_inputs=str(stage))
 (work/'CONTRACT_TEST_RESULTS.json').write_text(json.dumps(report,indent=2),'utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
