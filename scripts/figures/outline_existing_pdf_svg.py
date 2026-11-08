from pathlib import Path
import sys,json,hashlib,pymupdf
if len(sys.argv)!=3:raise SystemExit('Usage: outline_existing_pdf_svg.py INPUT_PDF NEW_EXTERNAL_SVG')
pdf=Path(sys.argv[1]).resolve(strict=True);svg=Path(sys.argv[2]).resolve()
if svg.exists() or svg.with_suffix('.conversion.json').exists() or svg.is_relative_to(Path(__file__).resolve().parents[2]):
 raise ValueError('Output SVG and receipt must be new and outside the repository')
if pdf==svg:raise ValueError('Output cannot overwrite input')
svg.parent.mkdir(parents=True,exist_ok=True)
with pymupdf.open(pdf) as doc:
 assert len(doc)==1
 page=doc[0];box=list(page.rect);text=page.get_svg_image(text_as_path=True)
svg.write_text(text,encoding='utf-8',newline='')
rec={'tool':'PyMuPDF','version':pymupdf.__version__,'function':'Page.get_svg_image(text_as_path=True)','input_pdf':str(pdf),'input_pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'page_rect_points':box,'output_svg':str(svg),'output_sha256':hashlib.sha256(svg.read_bytes()).hexdigest(),'new_plot_or_data_transformation':False,'text_editability':'Glyph outlines; original editable R SVG is retained separately.'}
svg.with_suffix('.conversion.json').write_text(json.dumps(rec,indent=2),encoding='utf-8')
print(json.dumps(rec))
