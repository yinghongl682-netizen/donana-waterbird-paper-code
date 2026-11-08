"""Typography pass of the frozen 20261101 Figure 1 Python renderer.

The original prepared map, orthophoto and observation calendar are read directly
from the sealed original package. Only this run's output directory is written.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("original_package", type=Path)
parser.add_argument("output_directory", type=Path)
args = parser.parse_args()
BASE = args.original_package.resolve(strict=True)
OUT = args.output_directory.resolve()
if OUT == BASE or BASE in OUT.parents or OUT in BASE.parents:
    raise ValueError("Output must be separate from the original package")
OUT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(OUT / ".mpl"))

def rows(p):
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def csvout(p, records):
    with p.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

def filehash(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path as MPath
from matplotlib.patches import PathPatch,Rectangle
import matplotlib.patheffects as pe
from PIL import Image
import pymupdf
from matplotlib import font_manager
from matplotlib.ft2font import FT2Font
from matplotlib.text import Annotation, Text

plt.rcParams.update({'font.family':'Arial','font.size':8,'axes.linewidth':.5,'svg.fonttype':'none','pdf.fonttype':42,'ps.fonttype':42,'savefig.facecolor':'white','path.simplify':False,'agg.path.chunksize':0})
INPUTS = {
    "map": BASE / "support/plot_data/MAP_LAYERS.json",
    "calendar": BASE / "support/plot_data/CALENDAR_396_LOCKED_STATES.csv",
    "orthophoto": BASE / "support/sources/PNOA_2022_ORIGINAL.png",
}
INPUT_HASHES = {name: filehash(path) for name, path in INPUTS.items()}
DATA = json.loads(INPUTS["map"].read_text(encoding="utf-8"))
CELLS = rows(INPUTS["calendar"])
IMG = np.asarray(Image.open(INPUTS["orthophoto"]))
C={'PNC':'#0072B2','SB':'#D55E00','GROUND':'#686F73'}
E=DATA['extent'];ART=[];MAPART=[]
CT={'PNC':'#00527D','SB':'#9D4700','GROUND':'#4A5154'}

def lines(geom):
 typ=geom['type'];co=geom['coordinates']
 if typ=='Polygon':return co
 if typ=='MultiPolygon':return [r for p in co for r in p]
 if typ=='LineString':return [co]
 if typ=='MultiLineString':return co
 raise ValueError(typ)

def path(geom):
 vertices=[];codes=[]
 for r in lines(geom):
  vertices.extend(r);codes.extend([MPath.MOVETO]+[MPath.LINETO]*(len(r)-2)+[MPath.CLOSEPOLY])
 return MPath(vertices,codes)

def axmm(fig,x,y,w,h):
 fw,fh=np.array(fig.get_size_inches())*25.4
 return fig.add_axes([x/fw,y/fh,w/fw,h/fh])

def text(fig,x,y,s,**kw):
 fw,fh=np.array(fig.get_size_inches())*25.4
 return fig.text(x/fw,y/fh,s,**kw)

def imagebase(ax):
 ax.set_facecolor('#E8F1F3')
 im=ax.imshow(IMG,extent=E,origin='upper',interpolation='antialiased',zorder=0)
 mask=PathPatch(path(DATA['F1_OFFICIAL_MAINLAND_MASK']['features'][0]['geometry']),transform=ax.transData,facecolor='none')
 im.set_clip_path(mask)
 # Archived IHM COSTA composite linework. The separate mainland mask uses high-tide closing segments.
 for f in DATA['F1_COAST']['features']:
  for r in lines(f['geometry']):
   xy=np.asarray(r);ax.plot(xy[:,0],xy[:,1],color='#56666B',lw=.35,zorder=2)

def sectorlines(ax,label):
 for f in DATA['sectors']['features']:
  s=f['properties']['sector']
  for j,r in enumerate(lines(f['geometry'])):
   xy=np.asarray(r);line,=ax.plot(xy[:,0],xy[:,1],color=C[s],lw=1.05 if label=='main' else 1.25,
    linestyle='-' if s=='PNC' else (0,(4,1.8)),zorder=5,
    path_effects=[pe.Stroke(linewidth=2.1 if label=='main' else 2.5,foreground='white'),pe.Normal()])
   line.set_gid(f'{label}_{s}_native_ring_{j+1}')
   MAPART.append(dict(panel=label,sector=s,ring=j+1,vertices=len(r),coordinate_sha256=hashlib.sha256(np.asarray(line.get_xydata(),dtype='<f8').tobytes()).hexdigest()))

def tag(ax,s,xy,xytext=None,color='black',size=8):
 kw=dict(fontsize=size,color=color,zorder=12,bbox=dict(facecolor='white',edgecolor='none',alpha=.94,pad=1.5))
 if xytext:
  ax.annotate(s,xy=xy,xytext=xytext,arrowprops=dict(arrowstyle='-',color=color,lw=.55),**kw)
 else:ax.text(*xy,s,**kw)

def scale(ax,x,y,length,label):
 ax.plot([x,x+length],[y,y],color='white',lw=4,zorder=10)
 ax.plot([x,x+length],[y,y],color='#18262B',lw=1.2,zorder=11)
 ax.plot([x,x],[y-400,y+400],color='#18262B',lw=.8,zorder=11)
 ax.plot([x+length,x+length],[y-400,y+400],color='#18262B',lw=.8,zorder=11)
 ax.text(x+length/2,y+1100,label,ha='center',fontsize=8,zorder=11,bbox=dict(fc='white',ec='none',pad=.8))

def mainmap(ax):
 imagebase(ax);sectorlines(ax,'main')
 # Only the qualified Guadalquivir feature is retained; other rivers are retired display elements.
 for f in DATA['F1_RIVERS']['features']:
  if f['properties'].get('nombre')=='Río Guadalquivir':
   for r in lines(f['geometry']):
    xy=np.asarray(r);ax.plot(xy[:,0],xy[:,1],color='#74B5C5',lw=.45,zorder=3,path_effects=[pe.Stroke(linewidth=1.1,foreground='white'),pe.Normal()])
 ax.set_xlim(E[:2]);ax.set_ylim(E[2:]);ax.set_aspect('equal');ax.set_xticks([]);ax.set_yticks([])
 tag(ax,'PNC',(735300,4109500),(719400,4112500),CT['PNC'],8)
 tag(ax,'SB',(740800,4080500),(747200,4078000),CT['SB'],8)
 # Existing point-on-surface child locators retained exactly, with VLP affiliation explicit.
 for f in DATA['F1_DATED_CHILD_LOCATORS']['features']:
  x,y=f['geometry']['coordinates'];name=f['properties']['nombre']
  ax.plot(x,y,'o',mfc='white',mec='#222222',ms=3.1,mew=.75,zorder=10)
  if name=='El Italiano':tag(ax,'El Italiano (VLP)*',(x,y),(744500,4098500),size=8)
  else:tag(ax,'Salinas Hidalgo*',(x,y),(744000,4086500),size=8)
 ax.text(698000,4087000,'Atlantic\nOcean',fontsize=8,color='#334B53',style='italic')
 # Geographic name is contextual; not a new observation or inferred measurement.
 tag(ax,'Guadalquivir\nestuary',(758698.4468079765,4105692.5464367494),(740000,4109800),color='#263A42',size=8)
 anchor=DATA['north']['anchor'];v=np.array(DATA['north']['unit'])*4500
 ax.annotate('',xy=np.array(anchor)+v,xytext=anchor,arrowprops=dict(arrowstyle='-|>',lw=1.2,color='white'),zorder=11)
 ax.text(anchor[0]+v[0],anchor[1]+v[1]+1500,'N',ha='center',fontsize=8,bbox=dict(fc='white',ec='none',pad=1),zorder=11)
 scale(ax,698000,4076000,10000,'10 km')
 # This is the detail's exact viewing rectangle, not another survey boundary.
 x0,x1,y0,y1=DETAIL
 ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fill=False,ec='#333333',lw=.65,ls=':',zorder=6))

DETAIL=[735200,745800,4074500,4089000]
def detail(ax):
 imagebase(ax);sectorlines(ax,'SB_detail');ax.set_xlim(DETAIL[:2]);ax.set_ylim(DETAIL[2:]);ax.set_aspect('equal');ax.set_xticks([]);ax.set_yticks([])
 for f in DATA['F1_DATED_CHILD_LOCATORS']['features']:
  if f['properties']['nombre']=='Salinas Hidalgo':
   x,y=f['geometry']['coordinates'];ax.plot(x,y,'o',mfc='white',mec='#222',ms=3,mew=.7,zorder=10)
   tag(ax,'Hidalgo*',(x,y),(738400,4084200),size=8)
 scale(ax,736000,4076000,2000,'2 km')

def locator(ax):
 ax.set_facecolor('#EDF3F5')
 for f in DATA['world']['features']:
  isp=f['properties']['ADMIN']=='Spain'
  ax.add_patch(PathPatch(path(f['geometry']),facecolor='#CCD3D1' if isp else '#F0F0ED',edgecolor='#919A9C',lw=.45))
 ax.set_xlim(-10,4.5);ax.set_ylim(34,44.5);ax.set_aspect(1.23);ax.set_xticks([]);ax.set_yticks([])
 ax.text(-4.2,40.3,'Spain',ha='center',fontsize=8)
 p=DATA['locator_point'];ax.plot(*p,'o',color='#7C3149',ms=3,zorder=5)
 ax.annotate('Doñana',xy=p,xytext=(-2.4,35.2),fontsize=8,ha='center',arrowprops=dict(arrowstyle='-',color='#7C3149',lw=.6))

def calendar(ax,source,option):
 for r in CELLS:
  if r['source']!=source:continue
  y=int(r['year']);m=int(r['month']);present=int(r['included'])
  rect=Rectangle((m-.5,y-.5),1,1,facecolor=C[source] if present else 'white',edgecolor='#CED3D5',lw=.35)
  gid=f'{option}_{source}_{y}_{m:02}_{present}';rect.set_gid(gid);ax.add_patch(rect)
  ART.append(dict(option=option,source=source,year=y,month=m,included=present,artist_gid=gid))
 ax.set_xlim(.5,12.5);ax.set_ylim(2023.5,2012.5)
 ax.set_xticks(range(1,13));ax.set_xticklabels([str(x) for x in range(1,13)],fontsize=8)
 ax.set_yticks(range(2013,2024));ax.set_yticklabels([str(x) for x in range(2013,2024)],fontsize=8)
 ax.xaxis.tick_top();ax.tick_params(length=0,pad=2)
 for s in ax.spines.values():s.set_visible(False)
 titles={'PNC':'PNC · aerial','SB':'SB · aerial','GROUND':'Ground'}
 ax.set_title(titles[source],fontsize=9,fontweight='bold',color=CT[source],pad=18)

def credits(fig):
    # Exact inherited source formulas are visible at the final 174-mm width.
    text(fig, 5, 12.3, "Obra derivada de PNOA 2022 CC-BY 4.0 scne.es · © IGN/CNIG", fontsize=8, color="#303638")
    text(fig, 5, 8.8, "Obra derivada de LC 2023 CC-BY 4.0 armada.mde.es/ihm/ · DERA rivers © IECA/Junta de Andalucía (CC BY 4.0)", fontsize=8, color="#303638")
    text(fig, 5, 5.3, "Natural Earth public domain · ICTS-Doñana/EBD-CSIC sector and locator derivatives (CC BY-SA 4.0)", fontsize=8, color="#303638")

def render():
    fig = plt.figure(figsize=(174 / 25.4, 200 / 25.4), dpi=300)
    text(fig, 5, 194.6, "a", weight="bold", fontsize=11)
    text(fig, 11, 194.6, "Doñana study area", weight="bold", fontsize=10)
    mainmap(axmm(fig, 5, 80.3, 111, 110))
    locator(axmm(fig, 122, 154.3, 47, 36))
    text(fig, 122, 149.7, "SB detail", fontsize=9, weight="bold", color=CT["SB"])
    detail(axmm(fig, 122, 94.5, 47, 53.2))

    text(fig, 122, 91.0, "Sector outlines", fontsize=8, weight="bold")
    text(fig, 122, 86.7, "PNC", fontsize=8, color=CT["PNC"])
    text(fig, 146, 86.7, "SB", fontsize=8, color=CT["SB"])
    for x, col, style in [(131, C["PNC"], "-"), (153, C["SB"], (0, (4, 1.8)))]:
        key = axmm(fig, x, 86.9, 8, 1)
        key.plot([0, 1], [.5, .5], color=col, lw=1.2, ls=style)
        key.set_axis_off()
    text(fig, 122, 82.6, "22 June 2026 source event", fontsize=8, color="#303638")
    text(fig, 122, 79.1, "* Named child locators", fontsize=8, color="#303638")
    text(fig, 5, 76.1, "PNOA orthophoto · June–July 2022", fontsize=8, color="#303638")
    text(fig, 5, 72.6, "Boundaries and locators are geographic context, not survey-period footprints.", fontsize=8, color="#303638")

    text(fig, 5, 66.7, "b", weight="bold", fontsize=11)
    text(fig, 11, 66.7, "Included observation months", weight="bold", fontsize=10)
    text(fig, 169, 66.7, "2013–2023", ha="right", fontsize=8)
    for s, x in zip(["PNC", "SB", "GROUND"], [14.5, 69.5, 124.5]):
        calendar(axmm(fig, x, 21, 44.5, 35.0), s, "A")
    text(fig, 5, 16.9, "Months 1–12 · Filled: included observation month; blank: no included observation, not zero birds.", fontsize=8)
    credits(fig)

    fig.canvas.draw()
    metadata = collect_text(fig)
    prefix = OUT / "FIG1_POLISHED"
    for ext, dpi in [("pdf", 300), ("svg", 300), ("png", 600), ("tiff", 600)]:
        suffix = "_600dpi" if ext in {"png", "tiff"} else ""
        kwargs = {"pil_kwargs": {"compression": "tiff_lzw"}} if ext == "tiff" else {}
        fig.savefig(OUT / f"{prefix.name}{suffix}.{ext}", dpi=dpi, **kwargs)
    with matplotlib.rc_context({"svg.fonttype": "path"}):
        fig.savefig(OUT / f"{prefix.name}_WORD.svg", dpi=300)
    plt.close(fig)

    assert INPUT_HASHES == {name: filehash(path) for name, path in INPUTS.items()}
    expected = [(r["source"], int(r["year"]), int(r["month"]), int(r["included"])) for r in CELLS]
    actual = [(r["source"], r["year"], r["month"], r["included"]) for r in ART]
    assert expected == actual and len(actual) == 396
    baseline_rings = json.loads((BASE / "support/qa/MAP_RENDERED_RINGS.json").read_text(encoding="utf-8"))
    assert baseline_rings[:len(MAPART)] == MAPART
    csvout(OUT / "F1_CALENDAR_RENDERED_ARTISTS.csv", ART)
    csvout(OUT / "F1_TEXT_ARTIST_INVENTORY.csv", metadata)
    (OUT / "F1_COORDINATE_AND_INPUT_LOCK.json").write_text(
        json.dumps({"input_sha256": INPUT_HASHES, "calendar_state_count": len(actual),
                    "included_by_source": {s: sum(r[3] for r in actual if r[0] == s) for s in C},
                    "sector_rings_match_original_in_order": True, "sector_rings": MAPART,
                    "sector_plot_palette": C, "orthophoto_native_pixels": [IMG.shape[1], IMG.shape[0]],
                    "main_extent": E, "detail_extent": DETAIL}, indent=2), encoding="utf-8")
    with pymupdf.open(OUT / "FIG1_POLISHED.pdf") as doc:
        page = doc[0]
        page.get_pixmap(matrix=pymupdf.Matrix(1.65, 1.65), alpha=False).save(OUT / "F1_POLISHED_PDF_PROOF.png")
    with Image.open(OUT / "FIG1_POLISHED_600dpi.png") as im:
        im.convert("L").resize((1030, 1184), Image.Resampling.LANCZOS).save(OUT / "F1_GRAYSCALE_PROOF.png")

def collect_text(fig):
    renderer = fig.canvas.get_renderer()
    metadata = []
    charmap = {}
    axes_names = ["a-main", "a-Spain", "a-SB detail", "a-legend", "a-legend", "b-PNC", "b-SB", "b-Ground"]
    items = [(a, "a" if a.get_position()[1] > 0.34 else "b") for a in fig.texts]
    for ax, label in zip(fig.axes, axes_names, strict=True):
        if ax.axison:
            items.extend((a, label) for a in ax.findobj(Text))
    seen = set()
    for artist, panel in items:
        label = artist.get_text()
        if id(artist) in seen or not artist.get_visible() or not label:
            continue
        seen.add(id(artist))
        path = font_manager.findfont(artist.get_fontproperties(), fallback_to_default=False)
        if path not in charmap:
            font = FT2Font(path)
            charmap[path] = (font.postscript_name, font.get_charmap())
        font_name, cmap = charmap[path]
        chars = set(c for c in label if c != "\n")
        missing = sorted(c for c in chars if ord(c) not in cmap)
        assert not missing, (label, font_name, missing)
        # Annotation.get_window_extent includes the leader. Measure just the label.
        bbox = Text.get_window_extent(artist, renderer) if isinstance(artist, Annotation) else artist.get_window_extent(renderer)
        mm = 25.4 / fig.dpi
        x0, y0, x1, y1 = bbox.extents * mm
        metadata.append(dict(figure="Fig. 1", panel=panel, expected_text=label,
                             unicode=" ".join(f"U+{ord(c):04X}" for c in label),
                             actual_font=font_name, fontsize_pt=artist.get_fontsize(),
                             italic=artist.get_fontstyle() == "italic", bold=artist.get_fontweight() == "bold",
                             xmin_mm=round(x0, 3), ymax_mm=round(200-y0, 3),
                             xmax_mm=round(x1, 3), ymin_mm=round(200-y1, 3),
                             missing_glyphs="".join(missing)))
        if not (x0 >= 0 and y0 >= 0 and x1 <= 174 and y1 <= 200):
            raise ValueError(f"Text outside canvas: {label!r} at {bbox.extents * mm}")
    return metadata

if __name__ == "__main__":
    render()
