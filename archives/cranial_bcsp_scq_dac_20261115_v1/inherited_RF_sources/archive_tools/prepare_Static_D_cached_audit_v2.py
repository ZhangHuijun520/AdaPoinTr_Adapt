from pathlib import Path
import ast
R=Path(__file__).resolve().parent.parent
p=R/'local_tools/audit_RF_Static_D_post_training_pair_v1.py';s=p.read_text(encoding='utf-8')
header=s[:s.index('def call(')]
header=header.replace("with (D/n).open", "with (V/n).open")
header+="V=H/'post_training_freeze_local_review_v2'\nV.mkdir()\nchecks={}\ndef check(n,v):\n checks[n]=bool(v);assert v,n\n"
setup=s[s.index(" assert sha(Q)"):s.index(' code="""')]
inventory=s[s.index(" names={'launch.log'"):s.index(" for n in sorted(names-")]
tail=s[s.index(" out=D/'output'"):]
tail=tail.replace("{'coarse','dense','Q0','Q1','Q2','delta','delta0','delta1','N0_N1_equal'} and parts['N0_N1_equal'] is True", "{'coarse','dense','Q0','Q1','Q2','delta','delta0','delta1','N0_N1_equal','neighbor_set_overlap'} and parts['N0_N1_equal'] is True\n  assert parts['neighbor_set_overlap']==[1.]*8")
prefix='''try:
'''+setup+''' inv=read(D/'remote_inventory_before_v2.json');after=read(D/'remote_inventory_after_v2.json')
 check('two_remote_stream_hash_inventories_identical',inv==after)
 check('cached_current_host_uid_and_exit',inv['hostname']==q['identity']['hostname'] and inv['uid']==1000 and inv['exit_code']==0 and inv['worker_not_live'] and inv['tmux_absent'])
'''+inventory+''' for folder in ['output','control']:
  for f in (D/folder).iterdir():
   assert f.is_file() and not f.is_symlink()
   key=('output/' if folder=='output' else 'install/control/')+f.name
   assert inv['files'][key]==dict(bytes=f.stat().st_size,sha256=sha(f))
 check('all19_local_readback_content_hashes_reverified',sum(1 for folder in ['output','control'] for f in (D/folder).iterdir())==19)
 emit('audit_helper_correction_v2.json',dict(scope='Audit-only exact geometry JSON key set includes existing neighbor_set_overlap; require Static overlap all ones for all 3900 records.',original_failed_audit_sha256=sha(D/'audit_failure_v1.json'),original_audit_source_sha256=sha(R/'local_tools/audit_RF_Static_D_post_training_pair_v1.py'),remote_inventory_before_sha256=sha(D/'remote_inventory_before_v2.json'),remote_inventory_after_sha256=sha(D/'remote_inventory_after_v2.json'),new_remote_calls=0,new_forward=0,training_modified=False))
'''
tail=tail.replace("operations=dict(new_forward=0,new_backward=0,server_writes=0,checkpoint_loaded=False,checkpoint_downloaded=False)","operations=dict(new_forward=0,new_backward=0,server_writes=0,checkpoint_loaded=False,checkpoint_downloaded=False,additional_remote_calls_in_v2=0),remote_freeze_evidence=str(D)")
result=header+prefix+tail
ast.parse(result)
dest=R/'local_tools/audit_RF_Static_D_cached_post_training_pair_v2.py'
with dest.open('x',encoding='utf-8') as f:f.write(result)
print(dest)
