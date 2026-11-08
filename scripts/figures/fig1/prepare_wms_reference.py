"""Reproduce final unions from the approved WMS response, without geometry repair.

Port of final production: normalize recorded text encoding and union native LOC_4.
"""
from pathlib import Path
import argparse,json,hashlib,csv
from shapely.geometry import shape,mapping
from shapely import union_all,normalize,to_wkb
from pyproj import CRS
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--raw-geojson',required=True,type=Path);p.add_argument('--output-root',required=True,type=Path)
    a=p.parse_args();source=a.raw_geojson.resolve(strict=True);out=a.output_root.resolve();repo=Path(__file__).resolve().parents[3]
    if out.exists() or out.is_relative_to(source.parent) or source.is_relative_to(out) or out.is_relative_to(repo):p.error('Output must be new and separate from input and repository')
    contract=json.loads((repo/'data/schema/fig1_final_contract.json').read_text('utf-8'))
    if sha(source)!=contract['raw_wms_sha256']:raise ValueError('Unqualified WMS snapshot; do not weaken hash guards')
    n=json.loads(source.read_text('utf-8'))
    if CRS.from_user_input(n['crs']['properties']['name']).to_epsg()!=25829:raise ValueError('Expected EPSG:25829')
    fs=n['features'];ids=[x['properties']['OBJECTID'] for x in fs]
    if len(fs)!=58 or len(set(ids))!=58:raise ValueError('Expected 58 unique OBJECTID values')
    fixes=[]
    for x in fs:
        g=shape(x['geometry'])
        if g.is_empty or not g.is_valid or g.geom_type!='MultiPolygon':raise ValueError('Invalid native geometry')
        for k,v in x['properties'].items():
            if isinstance(v,str) and any(z in v for z in ['Ã','Â']):
                fixed=v.encode('latin-1').decode('utf-8');fixes.append(dict(OBJECTID=x['properties']['OBJECTID'],field=k,old=v,new=fixed));x['properties'][k]=fixed
    if len(fixes)!=34:raise ValueError('Unexpected encoding repair set')
    us=[];lineage=[]
    for code,parent,count in [('PNC','PARQUE NACIONAL DE DOÑANA',30),('SB','SALINAS DE BONANZA',2)]:
        ff=[x for x in fs if x['properties']['LOC_4']==parent]
        if len(ff)!=count:raise ValueError('Native LOC_4 membership mismatch')
        g=union_all([shape(x['geometry']) for x in ff])
        if not g.is_valid or g.is_empty:raise ValueError('Invalid union')
        us.append(dict(type='Feature',id=code,properties=dict(sector=code,parent_native=parent,native_parcels=len(ff),source='Official post-2013 reference geography; WMS full-resolution reacquisition 2026-11-08; not verified individual-flight footprints'),geometry=mapping(g)))
        for x in ff:lineage.append(dict(sector=code,OBJECTID=x['properties']['OBJECTID'],LOCALIDAD=x['properties']['LOCALIDAD'],LOC_24=x['properties']['LOC_24'],LOC_4=parent,normalized_geometry_sha256=hashlib.sha256(to_wkb(normalize(shape(x['geometry'])))).hexdigest()))
    uf=dict(type='FeatureCollection',name='POST2013_PERMITTED_WMS_PARENT_UNIONS',crs=n['crs'],features=us)
    # Preserve the final Windows production serialization as well as geometry.
    content=json.dumps(uf,ensure_ascii=False,indent=2).replace('\n','\r\n').encode('utf-8')
    if hashlib.sha256(content).hexdigest()!=contract['union_sha256']:raise ValueError('Union differs from final production identity')
    out.mkdir(parents=True);(out/'POST2013_PERMITTED_WMS_PARENT_UNIONS.geojson').write_bytes(content)
    (out/'POST2013_PERMITTED_WMS_ATTRIBUTES_UTF8.geojson').write_text(json.dumps(n,ensure_ascii=False,indent=2),'utf-8')
    (out/'UTF8_ATTRIBUTE_REPAIR_LEDGER.json').write_text(json.dumps(fixes,ensure_ascii=False,indent=2),'utf-8')
    with (out/'PERMITTED_CHILD_TO_PARENT_LINEAGE_32.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(lineage[0]));w.writeheader();w.writerows(lineage)
    receipt=dict(raw_sha256=sha(source),union_sha256=hashlib.sha256(content).hexdigest(),features=58,crs='EPSG:25829',encoding_repairs=34,parent_counts={'PNC':30,'SB':2},geometry_repair=False,simplification=False,scope='Post-2013 context, not individual-flight footprints')
    (out/'AGGREGATION_QA.json').write_text(json.dumps(receipt,indent=2),'utf-8');print(json.dumps(receipt))
if __name__=='__main__':main()
