from pathlib import Path
import ast,json
S=Path(__file__).resolve().parent;V=S/'output_policy_hotfix_v3';V.mkdir()
old=(S/'binding_hotfix_v2/bcsp_spcg_cuda_entry_v2.py').read_text(encoding='utf-8')
extra='''
def exact_output_paths(out):
    out=clean(out)
    return [out/('real_D_%02d.npz'%i) for i in range(5)]

def traceback_source_guard(parent,q):
    # Fixed four already-bound infrastructure sources; reuse existing fd/hash guard.
    return parent.ExactSourceReads(dict(encoder=q['parent_helper'],factory=q['helper'],f0_decoder=q['timezone_implementation'],f0_factory=q['entry']))

'''
new=old.replace('\ndef main():',extra+'\ndef main():',1)
needle="f0_factory=q['entry']))]";assert new.count(needle)==1;new=new.replace(needle,"f0_factory=q['entry'])),traceback_source_guard(parent,q)]")
needle="out,[r['path'] for r in q['real_inputs']],[],[],utc,Both())";assert new.count(needle)==1;new=new.replace(needle,"out,[r['path'] for r in q['real_inputs']],[],exact_output_paths(out),utc,Both())")
needle="np.savez_compressed(out/('real_D_%02d.npz'%i),**arrays)";assert new.count(needle)==1;new=new.replace(needle,"np.savez_compressed(exact_output_paths(out)[i],**arrays)")
ast.parse(new);(V/'bcsp_spcg_cuda_entry_v3.py').write_text(new,encoding='utf-8')
scope=dict(status='FROZEN_BEFORE_SINGLE_CPU_BATCH',attempts=1,tests=['five output paths unique owned','real inherited policy writes five NPZ','unlisted neighboring NPZ denied','real input writes denied','bound source read succeeds','bound source writes denied','unlisted source read denied','actual traceback linecache under audit hook succeeds','precise helper UTC entry source set','source hash drift refused','only main modified plus two helpers','science resource fixture unchanged'],server_calls=0,SMI=0,models=0)
(V/'CPU_scope_v3.json').write_text(json.dumps(scope,indent=2),encoding='utf-8')
print('V3_PREPARED')
