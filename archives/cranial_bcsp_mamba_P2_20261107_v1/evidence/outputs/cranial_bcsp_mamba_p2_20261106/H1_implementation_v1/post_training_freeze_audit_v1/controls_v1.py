import hashlib,json,pathlib
R=pathlib.Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_h1_foldC_20261106_v1')
Q='e5fa766a408762a9a3bf3e2bd1dc993886b3422f7afaf69f9a994dc0ca20413d'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def exact(r):
 p=pathlib.Path(r['path']);assert not any(x.is_symlink() for x in (p,*p.parents))
 assert p.is_file() and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],str(p)
def read(p):return json.loads(p.read_bytes())
assert sha(R/'M_H1_foldC_seed0_training_execution_request_v1.json')==Q
q=read(R/'M_H1_foldC_seed0_training_execution_request_v1.json');C=R/'control'
assert {p.name for p in C.iterdir()}=={'H1_authorization_v1.json','H1_runtime_v1.json','H1_launch_once_v1.sh','single_attempt_claim_v1.json'}
auth=read(C/'H1_authorization_v1.json');assert auth['schema']=='bcsp-p2-H1-training-authorization-v1' and auth['request_sha256']==Q and auth['explicit_user_authorization'] is True
assert read(C/'H1_runtime_v1.json')==dict(schema='bcsp-p2-H1-training-runtime-v1',request_sha256=Q,authorization_sha256=sha(C/'H1_authorization_v1.json'))
assert read(C/'single_attempt_claim_v1.json')==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=Q)
hashes=['0643bc5525a05bc4fbe6da54e86bbabd3cc6cff746d4862e7fbdaad7669450c7','0a3aa794499b2e14eff9c7ef254e3dfb2adc62c5e8070e7ca817d908b431b89b','0db0e1d9ab21b361bca671f979602fefe20024a003a5a7523169bc302c9aaad8']
assert [sha(C/n) for n in ['H1_authorization_v1.json','H1_runtime_v1.json','H1_launch_once_v1.sh']]==hashes
for r in q['implementation'].values():exact(r)
for k in ('static_config','baseline_request','baseline_audit','h1_formula','p3'):exact(q[k])
new=read(pathlib.Path(q['static_config']['path']));base=read(pathlib.Path(q['baseline_request']['path']));exact(base['static_config'])
cfg=read(pathlib.Path(base['static_config']['path']));h=new['model'].pop('coarse_geometry_guard')
assert new==cfg and h==q['h1_config']==read(pathlib.Path(q['h1_formula']['path']))['parameters']
assert h==dict(enabled=True,mode='centroid_radius',weight=.1,smooth_l1_beta=.1,cvar_fraction=.1,eps=1e-6)
assert read(pathlib.Path(q['p3']['path']))['status']=='LOCAL_P2_H1_IMPLEMENTATION_P3_PASS'
print(json.dumps(dict(status='CONTROLS_IMPLEMENTATION_H1_CONFIG_PASS',request_sha256=Q,control_hashes=hashes,H1=h,only_scientific_delta='H1',server_writes=0)),flush=True)
