"""Retain only fields consumed by final Fig. 1; coordinates are copied unchanged."""
from pathlib import Path
import argparse,json,hashlib
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--map-layers',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();source=a.map_layers.resolve(strict=True);out=a.output.resolve();repo=Path(__file__).resolve().parents[3]
    if out.exists() or out.is_relative_to(repo):p.error('Output must be a new external file')
    original=json.loads(source.read_text('utf-8'));data={k:original[k] for k in ('extent','north','locator_point')}
    for name,props in [('F1_OFFICIAL_MAINLAND_MASK',()),('F1_COAST',()),('F1_RIVERS',('nombre',)),('world',('ADMIN',))]:
        data[name]=dict(type='FeatureCollection',features=[dict(type='Feature',geometry=f['geometry'],properties={k:f['properties'][k] for k in props}) for f in original[name]['features'] if name!='F1_RIVERS' or f['properties'].get('nombre')=='Río Guadalquivir'])
    content=json.dumps(data,ensure_ascii=False,indent=2).replace('\n','\r\n').encode('utf-8')
    contract=json.loads((repo/'data/schema/fig1_final_contract.json').read_text('utf-8'))
    if hashlib.sha256(content).hexdigest()!=contract['files']['F1/support/plot_data/MAP_LAYERS_FINAL.json']:raise ValueError('Projected map differs from final qualified input')
    out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(content)
    print(json.dumps(dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),output_sha256=hashlib.sha256(content).hexdigest(),coordinates_transformed=False)))
if __name__=='__main__':main()
