import hashlib,json,pathlib
R=pathlib.Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H1_twofold_prediction_20261106_v1');C=R/'control'
Q='90df035abba6cb6651f323ce65f5477f2a9bd0b3a7a505a5ebcc376b7436c147'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
assert sha(R/'H1_C_D_development_execution_request_v1.json')==Q
q=read(R/'H1_C_D_development_execution_request_v1.json')
assert {p.name for p in C.iterdir()}=={'prediction_authorization_v1.json','prediction_runtime_v1.json','prediction_launch_once_v1.sh','single_attempt_claim_v1.json'}
for k,h in [('authorization','bf03677582ce6a26f93cc1fd4622cc414bc0b596398aa0b501a7c3c12147b9f7'),('runtime','09f68e75a6b4b34e49f825886fb559050b189d5d7e108d0abf494e423898e04a'),('launcher','0b1331205a53ad382c1459768ddbd69f6b4b27fd3e3b7da508cd5bfa37cc88d1')]:assert sha(pathlib.Path(q['launch_contract'][k]))==h
a=read(pathlib.Path(q['launch_contract']['authorization']));assert a['schema']=='bcsp-development-authorization-v1' and a['request_sha256']==Q and a['explicit_user_authorization'] is True
assert read(pathlib.Path(q['launch_contract']['runtime']))==dict(schema='bcsp-development-runtime-v1',request_sha256=Q,authorization_sha256=sha(pathlib.Path(q['launch_contract']['authorization'])))
assert read(pathlib.Path(q['launch_attempt']))==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=Q)
recs=[q[k] for k in ['entry','input_index','protocol','P3','static_config','numeric_policy','helper']]+list(q['implementation'].values())+list(q['training_audits'].values())
for r in recs:
 p=pathlib.Path(r['path']);assert not any(x.is_symlink() for x in (p,*p.parents))
 assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],str(p)
assert q['forward_budget']==210 and q['optimizer_steps']==q['backward']==q['loss_calls']==q['BNCal']==0
cfg=read(pathlib.Path(q['static_config']['path']))['model'];h=cfg.pop('coarse_geometry_guard')
assert h==dict(enabled=True,mode='centroid_radius',weight=.1,smooth_l1_beta=.1,cvar_fraction=.1,eps=1e-6)
assert read(pathlib.Path(q['P3']['path']))['entry_sha256']==q['entry']['sha256']
print(json.dumps(dict(status='FROZEN_REQUEST_CONTROL_SOURCE_H1_BINDINGS_PASS',exact_bindings=len(recs),H1=h,request_sha256=Q,server_writes=0)),flush=True)
