"""Preserve failed v1; correct only inherited QC area field before predictions."""
from pathlib import Path
import hashlib,json
N=Path(__file__).resolve().parent
def bind(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def dump(name,obj):
 with (N/name).open('x') as f:json.dump(obj,f,indent=2)
old=(N/'build_reference_bank_v1.py').read_text()
new=old.replace('reference_preparation_scope_v1.json','reference_preparation_scope_v2.json').replace("qc['G_J_area_mm2']","qc['D_J_area_mm2']")
assert new!=old and old.count("qc['G_J_area_mm2']")==1
compile(new,'reference_builder_v2','exec')
with (N/'build_reference_bank_v2.py').open('x') as f:f.write(new)
old=(N/'invoke_reference_build_v1.py').read_text()
for stem in ['reference_preparation_scope','reference_build_attempt','build_reference_bank','reference_build_capture']:old=old.replace(stem+'_v1',stem+'_v2')
with (N/'invoke_reference_build_v2.py').open('x') as f:f.write(old)
scope=json.loads((N/'reference_preparation_scope_v1.json').read_bytes())
rows=json.loads(Path(scope['case_index']['path']).read_bytes())['cases']
assert len(rows)==210 and not list((N/'reference_bank_v1').glob('*.npz'))
for r in rows:
 qc=json.loads(Path(r['original_case_QC']['path']).read_bytes())
 assert {'J_face_keys_paired','D_J_area_mm2','G_native_area_mm2','center','scale'}<=set(qc)
 assert qc['D_J_area_mm2']>0 and qc['J_face_keys_paired']>0
scope.update(implementation=[bind(N/'bcsp_eval_metrics_v1.py'),bind(N/'build_reference_bank_v2.py')],output=str(N/'reference_bank_v2'),
 revision='QC schema field mapping only; shared D/G interface area remains fixed; v1 preserved, no model execution')
dump('reference_preparation_scope_v2.json',scope)
dump('reference_schema_regression_v2.json',dict(status='PASS',cases_checked=210,mapping='G_shared_interface_area <- inherited D_J_area_mm2',
 old_attempt=bind(N/'reference_build_capture_v1.json'),metric_implementation_unchanged=bind(N/'bcsp_eval_metrics_v1.py'),reference_files_in_v1=0))
