from pathlib import Path
import ast
R=Path(__file__).resolve().parent.parent
s=(R/'local_tools/collect_scq_post_prediction_freeze_v2.py').read_text(encoding='utf-8')
s=s.replace('outputs/cranial_bcsp_scq_BS_CD_native_prediction_preparation_20261114_v1/implementation_v1/resource_rebind_v2/pending_request_v2','outputs/scq_rf_sixmodel_native_prediction_preparation_20261115_v1/implementation_v1/input_path_fix_v2/pending_request_v2')
s=s.replace("F=B/'post_prediction_freeze_audit_v1'", "F=R/'outputs/scq_rf_pred_freeze_20261115_v2'")
s=s.replace('SCQ_BS_CD_native_prediction_execution_request_v2.json','SCQ_RF_sixmodel_native_prediction_execution_request_v2.json').replace('ce4b4b672a299934721d0b0f1fb22ea23de1bc41fd998ff94e10368fe1ebee5a','5dd2daae783133d1456054a362c359779a29033cc92fb1c5e775fa1cb45f39d9')
s=s.replace('len(files)<600','len(files)<800').replace('426','636').replace('420','630').replace('434','644').replace('expected_installed_files=22','expected_installed_files=24')
s=s.replace("assert len(z.files)==4 and set(z.files)=={'prediction','coarse','Qraw','delta'}", "assert len(z.files)==9 and set(z.files)=={'prediction','coarse','Qraw','delta','Q0','Q1','Q2','delta0','delta1'}")
s=s.replace("assert n.allclose(r+v,c,rtol=2e-6,atol=2e-7)\n  if row['variant']=='B':assert n.array_equal(r,c) and n.count_nonzero(v)==0", "assert n.allclose(r+v,c,rtol=2e-5,atol=2e-6)\n  a,b,e,f,g=z['Q0'],z['Q1'],z['Q2'],z['delta0'],z['delta1']\n  assert all(x.shape==(256,3) and x.dtype==n.float32 and n.isfinite(x).all() for x in [a,b,e,f,g])\n  assert n.array_equal(a,r) and n.array_equal(e,c) and n.allclose(a+f,b,rtol=2e-5,atol=2e-6) and n.allclose(b+g,e,rtol=2e-5,atol=2e-6)\n  if row['variant']=='S':assert n.array_equal(b,e) and n.array_equal(f,v) and n.count_nonzero(g)==0")
# Independently verify stage-centroid logs from saved arrays without another model call.
marker="sources['inventory_after']=inventory"
extra='''sources['RF_stages']="""sys.path.insert(0,'/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages')
import numpy as n
idx=json.loads(Path(q['input_index']['path']).read_bytes());gs=[json.loads(x) for x in (O/'geometry_summary.jsonl').read_text().splitlines()];assert len(gs)==630
for row,g in zip(idx['inputs'],gs):
 assert g['run']==row['run'] and g['case_id']==row['case_id'] and g['RF_second_stage_applicable'] is (row['variant']!='S')
 with n.load(O/row['prediction_filename'],allow_pickle=False) as z:
  assert set(g['stage_centroids'])=={'Q0','Q1','Q2','delta0','delta1'}
  for k in g['stage_centroids']:assert n.array_equal(n.asarray(g['stage_centroids'][k]),z[k].mean(0))
print(json.dumps(dict(status='ALL630_RF_STAGE_CENTROID_LOGS_RECOMPUTED_PASS',predictions=630,new_forward=0,GT_read=False)))
"""
'''
s=s.replace(marker,extra+marker).replace("['archive','arrays','geometry','inventory_after']", "['archive','arrays','geometry','RF_stages','inventory_after']")
ast.parse(s);compile(s,'RF_collector','exec')
p=R/'local_tools/collect_RF_post_prediction_freeze_v2.py'
with p.open('x',encoding='utf-8') as f:f.write(s)
print(p)
