"""User-confirmed read-only audit relocation; original training identity stays immutable."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parent.parent
H=R/'outputs/scq_rf_Requery_D_implementation_20261115_v1'
s=(R/'local_tools/audit_RF_Requery_D_post_training_pair_v1.py').read_text(encoding='utf-8')
s=s.replace("D=H/'post_training_freeze_v1'","D=H/'post_training_freeze_v2'")
s=s.replace("values=dict(HOST=q['identity']['hostname']", "values=dict(HOST='shu-common-25721452-notebook-qx2k0r-0'")
anchor=" inv=remote('inventory_before',code,values);"
assert s.count(anchor)==1
continuity=''' continuity=remote('confirmed_container_continuity',"""from pathlib import Path
import socket,os,hashlib,json
assert socket.gethostname()==HOST and os.getuid()==1000
project=Path(PROJECT);root=Path(ROOT);out=Path(OUT)
for p in [project,root,out]:assert p.is_dir() and p.resolve()==p and not any(x.is_symlink() for x in (p,*p.parents))
req=root/'SCQ_RF_Requery_D_training_execution_request_v1.json'
assert hashlib.sha256(req.read_bytes()).hexdigest()==DIGEST
for r in CONTROLS:
 p=Path(r['path']);assert p.is_file() and not p.is_symlink() and p.stat().st_size==r['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
comp=json.loads((out/'completion.json').read_bytes());assert comp['optimizer_updates']==3900 and comp['checkpoint_sha256']==CHECKPOINT and (out/'exit_code.txt').read_text().strip()=='0'
print(json.dumps(dict(status='USER_CONFIRMED_RELOCATED_AUDIT_CONTINUITY_PASS',hostname=socket.gethostname(),uid=os.getuid(),project=str(project),request_sha256=DIGEST,recorded_checkpoint_sha256=comp['checkpoint_sha256'],server_writes=0,new_forward=0)))
""",dict(HOST='shu-common-25721452-notebook-qx2k0r-0',PROJECT=q['identity']['project'],ROOT=C,OUT=q['output'],DIGEST=RH,CHECKPOINT='068288d4beb237dfe820286e22e122a5f427e4e32846c63087320aabc5b25bba',CONTROLS=[dict(path=L[k],bytes=(A/n).stat().st_size,sha256=sha(A/n)) for k,n in [('authorization_path','authorization_v1.json'),('runtime_path','runtime_v1.json'),('launcher_path','launch_once_v1.sh')]]))
 emit('confirmed_container_continuity_v1.json',continuity)
 check('confirmed_new_audit_host_original_training_request_and_controls',continuity['status']=='USER_CONFIRMED_RELOCATED_AUDIT_CONTINUITY_PASS')
'''
s=s.replace(anchor,continuity+anchor)
s=s.replace("identity=q['identity'],request_sha256=RH", "identity=q['identity'],audit_identity=dict(hostname=inv['hostname'],uid=inv['uid']),training_identity_preserved=True,user_confirmed_audit_container='qx2k0r-0',request_sha256=RH")
s=s.replace("'Neighbor equality and overlap are recorded summaries, not independently recomputed KNN from full tensors in this read-only audit.'", "'Neighbor equality and overlap are recorded summaries, not independently recomputed KNN from full tensors in this read-only audit.','Audit performed in user-confirmed qx2k0r-0 after training in zbpgzu-0. Exact original request/controls and stable artifacts verified; no claim that the new container is the training device.'")
ast.parse(s);compile(s,'Requery_D_relocated_readonly_audit','exec')
p=R/'local_tools/audit_RF_Requery_D_post_training_pair_v2.py'
with p.open('x',encoding='utf-8',newline='\n') as f:f.write(s)
scope=dict(status='USER_CONFIRMED_READONLY_AUDIT_LOCATION_CHANGE_NOT_TRAINING_REBIND',training_hostname='shu-common-25721452-notebook-zbpgzu-0',confirmed_audit_hostname='shu-common-25721452-notebook-qx2k0r-0',authorization='User confirmed qx2k0r-0 is current container after prior audit identity stop',controller_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),criteria='Original audit criteria unchanged; prepend exact request/control/completion continuity check; retain training identity separately',original_request_changed=False,server_writes=0,new_forward=0)
with (H/'readonly_audit_location_scope_v2.json').open('x',encoding='utf-8') as f:json.dump(scope,f,indent=2)
print('RELOCATED_READONLY_AUDIT_STATIC_PASS')
