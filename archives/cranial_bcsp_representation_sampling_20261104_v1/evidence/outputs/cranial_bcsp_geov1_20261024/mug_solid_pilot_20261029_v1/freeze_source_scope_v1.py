"""Metadata-only scope for exact3 NRRD payloads and3 already bound clear STLs."""
from pathlib import Path
import hashlib,json,zipfile
N=Path(__file__).resolve().parent;ROOT=next(p for p in N.parents if p.name=='mamba-ccf-c-1-high-resolution')
def bind(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
test=json.loads((N/'artificial_CPU_tests_v1.json').read_bytes());assert test['status']=='PASS' and test['tests']==8 and test['implementation_sha256']==bind(N/'source_admission_v1.py')['sha256']
old=ROOT/'outputs/cranial_geometry_diagnostic_20261023/mug_mesh_v1/scope.json';prior=json.loads(old.read_bytes())
archive=Path('E:/dataset/MUG500plus/raw_v20/archives/d6_development100_v1/batch_001/A0136-A0140.zip');st=archive.stat();cases=[]
with zipfile.ZipFile(archive) as z:
 for sid in ['A0136','A0137','A0138']:
  oldrow=next(x for x in prior['cases'] if x['record']['skull_id']=='mug500plus__'+sid);p=Path(oldrow['stl']);name='A0136-A0140/'+sid+'/'+sid+'.nrrd';i=z.getinfo(name)
  cases.append(dict(source_id=sid,nrrd=dict(member=name,bytes=i.file_size,CRC=i.CRC),clear_stl=dict(path=str(p),bytes=p.stat().st_size,sha256=oldrow['stl_sha256_before']),historical_ellipsoid=oldrow['record']['geometry']))
scope=dict(schema='mug-fixed3-solid-pilot-source-admission-v1',date_Asia_Shanghai='2026-10-29',cases=cases,archive=dict(path=str(archive),bytes=st.st_size,mtime_ns=st.st_mtime_ns),
 historical_geometry_scope=bind(old),formal_plan=bind(ROOT/'docs/cranial_bcsp_geov1_20261024/cranial_bcsp_geov1_formal_experiment_plan_zh_v1_1.md'),
 implementation_sha256=bind(N/'source_admission_v1.py')['sha256'],CPU_contract_tests=bind(N/'artificial_CPU_tests_v1.json'),output=str(N/'results'),
 admission='First establish complete bone-mask semantics and trusted physical correspondence;gray/intensity data or incomplete/unknown source stops that case;no automatic thresholding,ICP,mesh repair or source replacement',
 frozen_future_cut_family='ellipsoid_medium using exact historical center/frame/radii only after source admission',
 frozen_future_point_budget=dict(input=8192,target=8192),limits=dict(total_wall_seconds=3600,case_wall_seconds=900,RSS_bytes=8589934592,output_bytes=1073741824,threads=2),
 excluded_sources=['A0139','A0140'],server_calls=0,GPU_calls=0,training=0)
with (N/'scope_v1.json').open('x') as f:json.dump(scope,f,indent=2)
print(json.dumps(dict(scope_sha256=hashlib.sha256((N/'scope_v1.json').read_bytes()).hexdigest(),sources=3,NRRD_payload_reads=0)))
