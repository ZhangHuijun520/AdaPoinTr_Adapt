from pathlib import Path
import json,hashlib,os,socket
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_G0C_training_20261116_v3');qp=r/'SPCG_G0_C_training_execution_request_v3.json';qb=qp.read_bytes();assert hashlib.sha256(qb).hexdigest()=='871c5216815d5e479446108da979e8c77ce6ea5aec2578ac0573652e51a75d63';q=json.loads(qb);o=Path(q['output'])
def read(p):return json.loads(p.read_text())
from collections import Counter
import math
plan=read(o/'order_plan.json');exp=read(o/'exposure.json');M=[json.loads(l) for l in (o/'metrics.jsonl').read_text().splitlines()];G=[json.loads(l) for l in (o/'SPCG_geometry.jsonl').read_text().splitlines()];checks=dict(metrics3900=len(M)==3900,geometry3900=len(G)==3900);cases=Counter();sources=Counter();drop=Counter()
def close(a,b):return math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-10)
for i,(m,g) in enumerate(zip(M,G),1):
 ep,ba=divmod(i-1,39);ids=plan['epochs'][ep]['batches'][ba];assert m['step']==g['step']==i and m['epoch']==g['epoch']==ep and m['batch']==g['batch']==ba and m['case_ids']==g['case_ids']==ids
 assert len(ids)==8 and m['source_ids']==['train:'+x.split('__')[1] for x in ids] and m['optimizer_step_committed'] and m['loss_sparse']==m['loss_denoise']==0 and close(m['loss'],m['loss_dense']) and close(m['loss'],sum(g['loss_components'].values()))
 assert all(close(x,1e-4*max(.9**(ep/21),.02)) for x in m['LR']) and close(m['BN_momentum'],max(.9*.5**(ep/21),.01)) and m['clip_max_norm']==10 and all(math.isfinite(m[k]) for k in ['loss','grad_norm_before_clip'])
 cases.update(ids);sources.update(m['source_ids'])
for row in plan['epochs']:drop.update(row['dropped'])
checks.update(exposure=exp['case']==dict(cases) and exp['source']==dict(sources) and exp['dropped_case']==dict(drop),counts=sum(cases.values())==31200 and sum(drop.values())==300)
detailed=[g for g in G if 'total_loss_Q_gradient' in g];checks['five_gradient_steps']=[g['step'] for g in detailed]==[1,39,390,1950,3900] and all(g['total_loss_Q_gradient']['origin']=='TOTAL_LOSS_NOT_ISOLATED_COARSE' and g['total_loss_Q_gradient']['L2']>0 and math.isfinite(g['total_loss_Q_gradient']['L2']) for g in detailed)
R=[json.loads(l) for l in (o/'resources.jsonl').read_text().splitlines()];checks['resources']=len(R)==3902 and all(x['resource_guard_passed'] and all(x['checks'].values()) for x in R)
print(json.dumps(dict(checks=checks,metrics_count=len(M),geometry_count=len(G),resource_count=len(R),sources=len(sources),cases=len(cases),exposures=sum(cases.values()),drops=sum(drop.values()),detailed=detailed,first=M[0],last=M[-1],resource_last=R[-1],peaks={k:max(x[k] for x in R) for k in ['RSS','output_bytes','peak_allocated','peak_reserved','device_MiB']})))
