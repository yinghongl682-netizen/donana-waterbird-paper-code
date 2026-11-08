"""Produce only local author-review candidates from the sealed Fig. 1 inputs."""
from pathlib import Path
import os,sys,json,csv,hashlib,importlib.util,base64,io,gc,argparse
P=argparse.ArgumentParser(description=__doc__)
P.add_argument('--input-root',type=Path,required=True)
P.add_argument('--output-root',type=Path,required=True)
P.add_argument('--candidates',nargs='+',choices=['S1'],default=['S1'])
P.add_argument('--validate-inputs-only',action='store_true')
P.add_argument('--reference-union',type=Path,required=True,help='Explicit new licensed WMS parent-union file')
CLI=P.parse_args()
INPUT=CLI.input_root.resolve(strict=True);R=CLI.output_root.resolve()
from fig1_input_contract import validate_inputs
validation=validate_inputs(INPUT,CLI.reference_union)
if R==INPUT or INPUT in R.parents or R in INPUT.parents:
 raise ValueError('Outputs must be separate from inputs')
if R.is_relative_to(Path(__file__).resolve().parents[3]):
 raise ValueError('Outputs must be outside the source repository')
if R.exists():raise ValueError('Output must be new; preserve previous attempts')
if CLI.validate_inputs_only:
 print(json.dumps(validation));raise SystemExit(0)
R.mkdir(parents=True);(R/'qa').mkdir()
(R/'qa/INPUT_VALIDATION.json').write_text(json.dumps(validation,indent=2),'utf-8')
os.environ['MPLCONFIGDIR']=str(R/'qa/.mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.text import Text,Annotation
from matplotlib import font_manager
from matplotlib.ft2font import FT2Font
import numpy as np
from PIL import Image
import pymupdf
from fontTools import subset
from fontTools.ttLib import TTFont
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
SOURCE=Path(__file__).resolve().with_name('render_fig1_final_base.py')
BASE=INPUT/'F1'
UNION=CLI.reference_union.resolve(strict=True)
features=json.loads(UNION.read_text('utf-8'))
configs=[
 dict(key='S1',stem='FIG1_PERMITTED_WMS_NO_EVENT_LOCATORS_AUTHOR_REVIEW',sentinel=True,outline=True),
 dict(key='S2',stem='FIG1_S2_SENTINEL2_REFERENCE_LABELS',sentinel=True,outline=False),
 dict(key='CONTROL_P',stem='FIG1_CONTROL_P_PNOA_REFERENCE_GEOGRAPHY',sentinel=False,outline=True)]
receipts=[]
for c in [v for v in configs if v['key'] in CLI.candidates]:
 out=R;out.mkdir(exist_ok=True)
 sys.argv=[str(SOURCE),str(BASE),str(out)]
 spec=importlib.util.spec_from_file_location('sourcefigure_'+c['key'],SOURCE)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 # Source-only old event-sector outlines are explicitly excluded in every new candidate.
 m.DATA['sectors']=features
 # This authorized comparison removes the two event-derived example locators only.
 m.DATA['F1_DATED_CHILD_LOCATORS']['features']=[]
 imagep=INPUT/'SENTINEL2_20220720.png' if c['sentinel'] else m.INPUTS['background']
 m.IMG=np.asarray(Image.open(imagep))
 if c['sentinel']:
  assert sha(imagep)=='2b75267781fa2be57e8212cd8c60b10ef83c48d4dfef4afaf3cbfc59b78ea741'
  iq=json.loads((INPUT/'SENTINEL2_20220720_QA.json').read_text())
  assert m.E==[iq['bounds'][0],iq['bounds'][2],iq['bounds'][1],iq['bounds'][3]]
 def sectorlines(ax,label):
  if not c['outline']:return
  for f in features['features']:
   s=f['properties']['sector']
   for j,r in enumerate(m.lines(f['geometry'])):
    xy=np.asarray(r)
    line,=ax.plot(xy[:,0],xy[:,1],color=m.C[s],lw=1.05 if label=='main' else 1.25,
     linestyle='-' if s=='PNC' else (0,(4,1.8)),zorder=5,
     path_effects=[pe.Stroke(linewidth=2.1 if label=='main' else 2.5,foreground='white'),pe.Normal()])
    line.set_gid(f'{label}_{s}_post2013_reference_ring_{j+1}')
    m.MAPART.append(dict(panel=label,sector=s,ring=j+1,vertices=len(r),
      coordinate_sha256=hashlib.sha256(np.asarray(line.get_xydata(),dtype='<f8').tobytes()).hexdigest()))
 m.sectorlines=sectorlines
 fig=plt.figure(figsize=(174/25.4,200/25.4),dpi=300);T=m.text;A=m.axmm
 T(fig,5,194.6,'a',weight='bold',fontsize=11)
 T(fig,11,194.6,'Doñana study area',weight='bold',fontsize=10)
 m.mainmap(A(fig,5,80.3,111,110));m.locator(A(fig,122,154.3,47,36))
 T(fig,122,149.7,'SB detail',fontsize=9,weight='bold',color=m.CT['SB'])
 m.detail(A(fig,122,94.5,47,53.2))
 if c['outline']:
  T(fig,122,91.0,'Post-2013 aerial census',fontsize=8,weight='bold')
  T(fig,122,87.4,'reference geography',fontsize=8,weight='bold')
  T(fig,122,82.9,'PNC',fontsize=8,color=m.CT['PNC'])
  T(fig,146,82.9,'SB',fontsize=8,color=m.CT['SB'])
  for x,col,style in [(131,m.C['PNC'],'-'),(153,m.C['SB'],(0,(4,1.8)))]:
   ax=A(fig,x,83.1,8,1);ax.plot([0,1],[.5,.5],color=col,lw=1.2,ls=style);ax.set_axis_off()
 else:
  T(fig,122,91.0,'Reference locations',fontsize=8,weight='bold')
  T(fig,122,86.7,'PNC / SB',fontsize=8)
  T(fig,122,82.6,'Labels indicate position',fontsize=8,color='#303638')
 T(fig,5,76.1,'Sentinel-2B · 20 July 2022 · same-date mosaic' if c['sentinel'] else 'PNOA orthophoto · June–July 2022',fontsize=8,color='#303638')
 qualification='Reference outlines are geographic context, not verified individual-flight footprints.' if c['outline'] else 'Reference positions are geographic context; no individual-flight footprints are shown.'
 T(fig,5,72.6,qualification,fontsize=8,color='#303638')
 T(fig,5,66.7,'b',weight='bold',fontsize=11);T(fig,11,66.7,'Included observation months',weight='bold',fontsize=10)
 T(fig,169,66.7,'2013–2023',ha='right',fontsize=8)
 for s,x in zip(['PNC','SB','GROUND'],[14.5,69.5,124.5]):m.calendar(A(fig,x,21,44.5,35),s,c['key'])
 T(fig,5,16.9,'Months 1–12 · Filled: included observation month; blank: no included observation, not zero birds.',fontsize=8)
 T(fig,5,12.3,'Contains modified Copernicus Sentinel data 2022' if c['sentinel'] else 'Obra derivada de PNOA 2022 CC-BY 4.0 scne.es · © IGN/CNIG',fontsize=8,color='#303638')
 T(fig,5,8.8,'Obra derivada de LC 2023 CC-BY 4.0 armada.mde.es/ihm/ · DERA rivers © IECA/Junta de Andalucía (CC BY 4.0)',fontsize=8,color='#303638')
 bottom=('Natural Earth public domain · Reference WMS: LAST-EBD/ICTS-Doñana (CC BY 4.0)' if c['outline']
 else 'Natural Earth public domain · ICTS-Doñana/EBD-CSIC event locators (CC BY-SA 4.0)')
 T(fig,5,5.3,bottom,fontsize=8,color='#303638')
 fig.canvas.draw();inventory=[];fontchars={}
 for a in fig.findobj(Text):
  if not a.get_visible() or not a.get_text():continue
  label=a.get_text();fp=font_manager.findfont(a.get_fontproperties(),fallback_to_default=False)
  font=FT2Font(fp);chars=set(label)-set('\n\t')
  assert all(ord(ch) in font.get_charmap() for ch in chars),(label,fp)
  box=Text.get_window_extent(a,fig.canvas.get_renderer()) if isinstance(a,Annotation) else a.get_window_extent(fig.canvas.get_renderer())
  ext=box.extents*25.4/fig.dpi
  assert ext[0]>=0 and ext[1]>=0 and ext[2]<=174 and ext[3]<=200,(label,ext.tolist())
  inventory.append(dict(text=label,font=font.postscript_name,fontsize_pt=a.get_fontsize(),bounds_mm=ext.tolist()))
  if fp not in fontchars:fontchars[fp]=dict(chars=set(),style=a.get_fontstyle(),weight=a.get_fontweight())
  fontchars[fp]['chars'].update(chars)
 assert min(x['fontsize_pt'] for x in inventory)>=8
 stem=out/c['stem']
 for ext in ['pdf','svg','png','tiff']:
  suffix='_600dpi' if ext in ('png','tiff') else ''
  kw={'pil_kwargs':{'compression':'tiff_lzw'}} if ext=='tiff' else {}
  fig.savefig(str(stem)+suffix+'.'+ext,dpi=600,**kw)
 # Independent path glyph version is robust to Word SVG font-substitution.
 with matplotlib.rc_context({'svg.fonttype':'path'}):fig.savefig(str(stem)+'_WORD.svg',dpi=600)
 # Retain editable text and make its fonts self-contained for SVG-aware renderers.
 svgpath=Path(str(stem)+'.svg');svg=svgpath.read_text('utf-8');styles=[];fontreceipts=[]
 for fp,v in fontchars.items():
  font=TTFont(fp);opt=subset.Options();opt.flavor='woff';sub=subset.Subsetter(options=opt)
  sub.populate(text=''.join(sorted(v['chars'])));sub.subset(font);font.flavor='woff'
  buf=io.BytesIO();font.save(buf);data=buf.getvalue()
  wt='700' if v['weight'] in ('bold',700) else '400'
  st='italic' if v['style']=='italic' else 'normal'
  styles.append("@font-face{font-family:Arial;font-style:"+st+";font-weight:"+wt+";src:url(data:font/woff;base64,"+base64.b64encode(data).decode()+") format('woff');}")
  fontreceipts.append(dict(source_font=Path(fp).name,source_sha256=sha(Path(fp)),style=st,weight=wt,subset_bytes=len(data),subset_sha256=hashlib.sha256(data).hexdigest()))
 svg=svg.replace('</defs>','<style type="text/css"><![CDATA['+'\n'.join(styles)+']]></style></defs>',1)
 svgpath.write_text(svg,'utf-8')
 plt.close(fig)
 actual=[(x['source'],x['year'],x['month'],x['included']) for x in m.ART]
 expected=[(x['source'],int(x['year']),int(x['month']),int(x['included'])) for x in m.CELLS]
 assert actual==expected and len(actual)==396
 assert m.INPUT_HASHES=={k:sha(p) for k,p in m.INPUTS.items()}
 m.csvout(out/'CALENDAR_396_RENDERED_STATES.csv',m.ART)
 (out/'TEXT_ARTIST_INVENTORY.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2),'utf-8')
 (out/'RENDERED_REFERENCE_RINGS.json').write_text(json.dumps(m.MAPART,indent=2),'utf-8')
 with pymupdf.open(str(stem)+'.pdf') as doc:
  assert len(doc)==1
  p=doc[0];size=[p.rect.width*25.4/72,p.rect.height*25.4/72]
  assert abs(size[0]-174)<0.01 and abs(size[1]-200)<0.01
  p.get_pixmap(matrix=pymupdf.Matrix(2,2),alpha=False).save(out/'PDF_PROOF.png')
  pdftext=p.get_text()
  assert 'LC 2023 CC-BY 4.0 armada.mde.es/ihm/' in pdftext
  fonts=[]
  for f in p.get_fonts(full=True):
   n,e,t,content=doc.extract_font(f[0]);assert len(content)>0
   fonts.append(dict(name=n,extension=e,type=t,embedded_bytes=len(content)))
 Image.open(out/'PDF_PROOF.png').convert('L').save(out/'GRAYSCALE_PROOF.png')
 q=dict(candidate='PERMITTED_WMS_NO_EVENT_LOCATORS_AUTHOR_REVIEW',selected_for_author_review=False,width_mm=174,height_mm=200,
   map_extent=m.E,detail_extent=m.DETAIL,image_sha256=sha(imagep),image_pixels=[m.IMG.shape[1],m.IMG.shape[0]],
   calendar_sha256=sha(m.INPUTS['calendar']),calendar_states=len(actual),
   included_by_source={s:sum(x[3] for x in actual if x[0]==s) for s in m.C},
   official_outline_drawn=c['outline'],source_reference_union_sha256=sha(UNION) if c['outline'] else None,
   old_event_sector_outline_drawn=False,event_child_locators_retained=False,rendered_reference_ring_count=len(m.MAPART),
   minimum_text_size_pt=min(x['fontsize_pt'] for x in inventory),all_text_within_canvas=True,no_missing_glyphs=True,
   pdf_fonts=fonts,svg_embedded_fonts=fontreceipts,svg_word_glyphs='outlined',
   source_renderer_sha256=sha(SOURCE),new_renderer_sha256=sha(Path(__file__)),
   rights_status='FINAL_SOURCE_ALIGNMENT_REPLAY_NOT_A_NEW_RELEASE_APPROVAL')
 (out/'RENDER_QA.json').write_text(json.dumps(q,ensure_ascii=False,indent=2),'utf-8')
 receipts.append(q);print('COMPLETE',c['key'],flush=True)
 del m;gc.collect()
all_receipts=[json.loads((R/'RENDER_QA.json').read_text('utf-8'))]
(R/'qa/FINAL_RENDER_RECEIPTS.json').write_text(json.dumps(all_receipts,ensure_ascii=False,indent=2),'utf-8')
