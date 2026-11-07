import json,math,pathlib
R=pathlib.Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_h1_foldD_20261106_v1')
q=json.loads((R/'M_H1_foldD_seed0_training_execution_request_v1.json').read_bytes());O=pathlib.Path(q['output'])
rows=[json.loads(s) for s in (O/'metrics.jsonl').read_text().splitlines()]
c=json.loads((O/'completion.json').read_bytes())
assert len(rows)==3900 and c['counts']==dict(forward=3900,backward=3900,clip=3900,step=3900,lr_scheduler=100,bn_scheduler=100)
assert c['optimizer_updates']==3900 and c['traversals']==100 and c['case_exposures']==31200
assert c['bncal_executed'] is c['evaluation_executed'] is c['resume'] is False
def close(a,b):return math.isclose(a,b,rel_tol=2e-6,abs_tol=2e-7)
for i,r in enumerate(rows):
 assert (r['step'],r['epoch'],r['batch'])==(i+1,i//39,i%39)
 assert r['optimizer_step_committed'] is r['H1_enabled'] is r['H1_log_is_detached_recomputation'] is True
 values=[r[k] for k in ['loss','loss_sparse','loss_dense','loss_denoise','loss_reconstruction','H1_centroid','H1_radius','H1_raw','H1_weighted','loss_without_H1_derived','grad_norm_before_clip']]
 assert all(math.isfinite(x) for x in values)
 assert all(r[k]>=0 for k in ['H1_centroid','H1_radius','H1_raw','H1_weighted'])
 assert close(r['H1_raw'],.5*(r['H1_centroid']+r['H1_radius'])) and close(r['H1_weighted'],.1*r['H1_raw'])
 assert close(r['loss_without_H1_derived']+r['H1_weighted'],r['loss'])
 assert r['loss_sparse']==r['loss_denoise']==0 and r['loss_dense']==r['loss_reconstruction'] and close(r['loss'],r['loss_dense'])
 assert r['clip_max_norm']==10
print(json.dumps(dict(status='ALL3900_COUNTS_H1_LOGS_PASS',counts=c['counts'],exposures=31200,traversals=100,nonfinite_records=0,H1_records=3900,first={k:rows[0][k] for k in ['loss','H1_raw','H1_weighted']},last={k:rows[-1][k] for k in ['loss','H1_raw','H1_weighted']},BNCal=False,evaluation=False,resume=False,server_writes=0,limitation='Saved logs and verified runtime, not independent tensor/loss replay')),flush=True)
