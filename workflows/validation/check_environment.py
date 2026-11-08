"""Record explicit runtime identity; never install or infer scientific success."""
import argparse,importlib.metadata,json,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--rscript',type=Path);p.add_argument('--r-library',type=Path);p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
if a.output.exists():p.error('Receipt exists; choose a new path')
if bool(a.rscript)!=bool(a.r_library):p.error('Provide both R arguments')
observed={};fail=[]
for name in ['pandas','numpy','python-dateutil','six','tzdata','pillow','packaging']:
 try:observed[name]=importlib.metadata.version(name)
 except importlib.metadata.PackageNotFoundError:fail.append(name)
r={'python':sys.version,'executable':sys.executable,'packages':observed,'missing':fail,'R':'NOT_TESTED','scope':'Runtime availability only; no science or new-install proof'}
if a.rscript:
 expr='.libPaths(c('+json.dumps(a.r_library.resolve().as_posix())+',.Library),include.site=FALSE); p<-c("ggplot2","patchwork","jsonlite","xml2","pdftools","png","colorspace","magick","digest","svglite","ragg"); stopifnot(all(vapply(p,requireNamespace,logical(1),quietly=TRUE))); print(R.version.string); print(.libPaths()); print(sapply(p,function(x)as.character(packageVersion(x)))); sessionInfo()'
 cp=subprocess.run([str(a.rscript),'--vanilla','-e',expr],capture_output=True,text=True,encoding='utf-8',errors='replace')
 r['R']={'returncode':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr};fail.extend(['R'] if cp.returncode else [])
r['status']='FAIL' if fail else 'PASS_RUNTIME_AVAILABILITY_ONLY'
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(r['status']);sys.exit(bool(fail))
